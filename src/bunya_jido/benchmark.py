from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


AUDIT_SCHEMA_VERSION = "bunya-jido-worktree-audit-v1"
TOKEN_EFFICIENCY_SCHEMA_VERSION = "bunya-jido-token-efficiency-report-v1"
TOKEN_RUN_KINDS = {"bugfix", "no_match"}


def _git_output(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _normalize_pattern(pattern: str) -> str:
    return pattern.strip().replace("\\", "/").removeprefix("./")


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _decode_path(value: bytes) -> str:
    return value.decode("utf-8", errors="replace").replace("\\", "/")


def _parse_porcelain_status(payload: bytes) -> list[dict[str, Any]]:
    tokens = payload.split(b"\0")
    entries: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        if len(token) < 4:
            raise ValueError("Unexpected git status porcelain entry.")
        status = token[:2].decode("ascii", errors="replace")
        entry: dict[str, Any] = {
            "status": status,
            "index_status": status[0],
            "worktree_status": status[1],
            "path": _decode_path(token[3:]),
        }
        if "R" in status or "C" in status:
            if index >= len(tokens) or not tokens[index]:
                raise ValueError("Git rename/copy status entry is missing its source path.")
            entry["original_path"] = _decode_path(tokens[index])
            index += 1
        entries.append(entry)
    return entries


def _tracked_changed_lines(root: Path) -> int:
    payload = _git_output(root, "diff", "--numstat", "HEAD", "--")
    total = 0
    for raw_line in payload.splitlines():
        parts = raw_line.split(b"\t", 2)
        if len(parts) < 2:
            continue
        for value in parts[:2]:
            if value.isdigit():
                total += int(value)
    return total


def _workspace_relative_path(raw_path: str, root: Path) -> str | None:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def _jsonl_file_change_events(
    root: Path,
    jsonl_paths: Iterable[str | Path],
) -> tuple[list[dict[str, str]], list[dict[str, str]], int, int, int]:
    workspace_events: dict[tuple[str, str], dict[str, str]] = {}
    outside_events: dict[tuple[str, str], dict[str, str]] = {}
    malformed_lines = 0
    invalid_lines = 0
    event_count = 0

    for jsonl_path in jsonl_paths:
        path = Path(jsonl_path)
        if not path.is_absolute():
            path = root / path
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    malformed_lines += 1
                    continue
                if not isinstance(event, dict):
                    invalid_lines += 1
                    continue
                event_count += 1
                item = event.get("item")
                if not isinstance(item, dict) or item.get("type") != "file_change":
                    continue
                changes = item.get("changes")
                if not isinstance(changes, list):
                    invalid_lines += 1
                    continue
                item_status = str(item.get("status") or event.get("type") or "observed")
                invalid_change = False
                for change in changes:
                    if not isinstance(change, dict) or not isinstance(change.get("path"), str):
                        invalid_change = True
                        continue
                    raw_path = change["path"]
                    kind = str(change.get("kind") or "unknown")
                    relative_path = _workspace_relative_path(raw_path, root)
                    record = {"path": relative_path or raw_path, "kind": kind, "status": item_status}
                    key = (record["path"], kind)
                    if relative_path is None:
                        outside_events[key] = record
                    else:
                        workspace_events[key] = record
                if invalid_change:
                    invalid_lines += 1

    return (
        sorted(workspace_events.values(), key=lambda item: (item["path"], item["kind"])),
        sorted(outside_events.values(), key=lambda item: (item["path"], item["kind"])),
        malformed_lines,
        invalid_lines,
        event_count,
    )


def audit_worktree(
    root: str | Path,
    *,
    jsonl_paths: Iterable[str | Path] = (),
    allowed_artifacts: Iterable[str] = (),
) -> dict[str, Any]:
    """Return machine-readable workspace truth for a benchmark run."""

    resolved_root = Path(root).resolve()
    jsonl_paths = tuple(jsonl_paths)
    patterns = sorted({_normalize_pattern(pattern) for pattern in allowed_artifacts if pattern.strip()})
    status_entries = _parse_porcelain_status(
        _git_output(
            resolved_root,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=no",
        )
    )

    changed_files_tracked: set[str] = set()
    staged_files: set[str] = set()
    deleted_files: set[str] = set()
    untracked_files: set[str] = set()
    renamed_files: list[dict[str, str]] = []

    for entry in status_entries:
        status = entry["status"]
        path = entry["path"]
        original_path = entry.get("original_path")
        paths = {path}
        if original_path:
            paths.add(original_path)
        if status == "??":
            untracked_files.add(path)
            continue
        changed_files_tracked.update(paths)
        if entry["index_status"] not in {" ", "?"}:
            staged_files.update(paths)
        if "D" in status:
            deleted_files.update(paths)
        if original_path:
            renamed_files.append({"from": original_path, "to": path})

    changed_files = changed_files_tracked | untracked_files
    allowed_artifact_changes = sorted(path for path in changed_files if _matches_any(path, patterns))
    production_file_changes = sorted(path for path in changed_files if not _matches_any(path, patterns))
    jsonl_events, outside_events, malformed_lines, invalid_lines, event_count = _jsonl_file_change_events(
        resolved_root,
        jsonl_paths,
    )
    jsonl_production_write_attempts = sorted(
        {event["path"] for event in jsonl_events if not _matches_any(event["path"], patterns)}
    )
    jsonl_allowed_artifact_attempts = sorted(
        {event["path"] for event in jsonl_events if _matches_any(event["path"], patterns)}
    )

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "root": str(resolved_root),
        "worktree_clean": not status_entries,
        "status_entries": status_entries,
        "changed_files_tracked": sorted(changed_files_tracked),
        "staged_files": sorted(staged_files),
        "deleted_files": sorted(deleted_files),
        "renamed_files": sorted(renamed_files, key=lambda item: (item["from"], item["to"])),
        "untracked_files": sorted(untracked_files),
        "changed_lines_tracked": _tracked_changed_lines(resolved_root),
        "allowed_artifact_changes": allowed_artifact_changes,
        "production_file_changes": production_file_changes,
        "jsonl_file_change_events": jsonl_events,
        "jsonl_allowed_artifact_attempts": jsonl_allowed_artifact_attempts,
        "jsonl_production_write_attempts": jsonl_production_write_attempts,
        "jsonl_outside_workspace_changes": outside_events,
        "jsonl_log_count": len(jsonl_paths),
        "jsonl_event_count": event_count,
        "malformed_jsonl_lines": malformed_lines,
        "invalid_jsonl_lines": invalid_lines,
        "jsonl_complete": bool(jsonl_paths) and event_count > 0 and malformed_lines == 0 and invalid_lines == 0,
        "has_production_changes": bool(production_file_changes),
        "has_production_write_attempts": bool(jsonl_production_write_attempts),
    }


def _require_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _token_exclusion_reasons(run: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not run["infrastructure_valid"]:
        reasons.append("infrastructure_invalid")
    if run["boundary_violation"]:
        reasons.append("boundary_violation")
    if not run["resolved"]:
        reasons.append(
            "unresolved_bugfix" if run["task_kind"] == "bugfix" else "unresolved_no_match"
        )
    if run["task_kind"] == "no_match" and run["production_write_attempt"]:
        reasons.append("no_match_production_write")
    return reasons


def _normalize_token_runs(runs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_run in enumerate(runs):
        if not isinstance(raw_run, dict):
            raise ValueError(f"runs[{index}] must be an object")
        run = dict(raw_run)
        for field in ("condition", "task_id", "task_kind"):
            value = run.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"runs[{index}].{field} must be a non-empty string")
            run[field] = value.strip()
        if run["task_kind"] not in TOKEN_RUN_KINDS:
            raise ValueError(
                f"runs[{index}].task_kind must be bugfix or no_match"
            )
        for field in ("task_tokens", "context_output_tokens"):
            run[field] = _require_nonnegative_int(
                run.get(field), f"runs[{index}].{field}"
            )
        for field in (
            "resolved",
            "infrastructure_valid",
            "boundary_violation",
            "production_write_attempt",
        ):
            run[field] = _require_bool(run.get(field), f"runs[{index}].{field}")
        key = (run["condition"], run["task_id"])
        if key in seen:
            raise ValueError(
                f"duplicate token run for condition/task_id: {key[0]}/{key[1]}"
            )
        seen.add(key)
        run["exclusion_reasons"] = _token_exclusion_reasons(run)
        run["safe_and_resolved"] = not run["exclusion_reasons"]
        normalized.append(run)
    return normalized


def _median(values: list[int]) -> int | float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return round((ordered[midpoint - 1] + ordered[midpoint]) / 2, 2)


def _token_condition_summary(
    runs: list[dict[str, Any]],
    map_authoring_tokens: int | None,
) -> dict[str, Any]:
    safe_runs = [run for run in runs if run["safe_and_resolved"]]
    repair_runs = [run for run in runs if run["task_kind"] == "bugfix"]
    no_match_runs = [run for run in runs if run["task_kind"] == "no_match"]
    safe_no_match_runs = [
        run for run in safe_runs if run["task_kind"] == "no_match"
    ]
    excluded: dict[str, int] = {}
    for run in runs:
        for reason in run["exclusion_reasons"]:
            excluded[reason] = excluded.get(reason, 0) + 1
    return {
        "map_authoring_tokens": map_authoring_tokens,
        "run_count": len(runs),
        "safe_and_resolved_run_count": len(safe_runs),
        "excluded_run_count": len(runs) - len(safe_runs),
        "excluded_run_reasons": dict(sorted(excluded.items())),
        "context_output_tokens": sum(run["context_output_tokens"] for run in runs),
        "median_context_output_tokens": _median(
            [run["context_output_tokens"] for run in runs]
        ),
        "safe_and_resolved_context_output_tokens": sum(
            run["context_output_tokens"] for run in safe_runs
        ),
        "safe_and_resolved_median_task_tokens": _median(
            [run["task_tokens"] for run in safe_runs]
        ),
        "repair_task_tokens": sum(
            run["task_tokens"] for run in repair_runs
        ),
        "repair_median_task_tokens": _median(
            [run["task_tokens"] for run in repair_runs]
        ),
        "safe_and_resolved_task_tokens": sum(
            run["task_tokens"] for run in safe_runs
        ),
        "no_match_tokens": sum(
            run["task_tokens"] for run in no_match_runs
        ),
        "no_match_median_task_tokens": _median(
            [run["task_tokens"] for run in no_match_runs]
        ),
        "safe_and_resolved_no_match_median_task_tokens": _median(
            [run["task_tokens"] for run in safe_no_match_runs]
        ),
    }


def _paired_token_summary(
    baseline_runs: dict[str, dict[str, Any]],
    candidate_runs: dict[str, dict[str, Any]],
    task_ids: list[str],
) -> dict[str, Any]:
    baseline_tokens = sum(baseline_runs[task_id]["task_tokens"] for task_id in task_ids)
    candidate_tokens = sum(candidate_runs[task_id]["task_tokens"] for task_id in task_ids)
    baseline_context = sum(
        baseline_runs[task_id]["context_output_tokens"] for task_id in task_ids
    )
    candidate_context = sum(
        candidate_runs[task_id]["context_output_tokens"] for task_id in task_ids
    )
    saving = baseline_tokens - candidate_tokens
    context_saving = baseline_context - candidate_context
    baseline_values = [baseline_runs[task_id]["task_tokens"] for task_id in task_ids]
    candidate_values = [candidate_runs[task_id]["task_tokens"] for task_id in task_ids]
    baseline_context_values = [
        baseline_runs[task_id]["context_output_tokens"] for task_id in task_ids
    ]
    candidate_context_values = [
        candidate_runs[task_id]["context_output_tokens"] for task_id in task_ids
    ]
    return {
        "paired_task_count": len(task_ids),
        "task_ids": task_ids,
        "baseline_task_tokens": baseline_tokens,
        "candidate_task_tokens": candidate_tokens,
        "task_token_saving": saving,
        "task_token_saving_rate": round(saving / baseline_tokens, 4)
        if baseline_tokens
        else None,
        "average_task_token_saving": round(saving / len(task_ids), 2)
        if task_ids
        else None,
        "baseline_median_task_tokens": _median(baseline_values),
        "candidate_median_task_tokens": _median(candidate_values),
        "baseline_context_output_tokens": baseline_context,
        "candidate_context_output_tokens": candidate_context,
        "baseline_median_context_output_tokens": _median(baseline_context_values),
        "candidate_median_context_output_tokens": _median(candidate_context_values),
        "context_output_token_saving": context_saving,
        "context_output_token_saving_rate": round(
            context_saving / baseline_context, 4
        )
        if baseline_context
        else None,
    }


def summarize_token_efficiency(
    runs: Iterable[dict[str, Any]],
    *,
    baseline_condition: str,
    candidate_condition: str,
    map_authoring_tokens: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Summarize only paired safe-and-resolved runs for token-saving claims."""

    baseline_condition = baseline_condition.strip()
    candidate_condition = candidate_condition.strip()
    if not baseline_condition or not candidate_condition:
        raise ValueError("baseline_condition and candidate_condition are required")
    if baseline_condition == candidate_condition:
        raise ValueError("baseline_condition and candidate_condition must differ")
    normalized = _normalize_token_runs(runs)
    authoring = dict(map_authoring_tokens or {})
    for condition, value in authoring.items():
        authoring[condition] = _require_nonnegative_int(
            value, f"map_authoring_tokens.{condition}"
        )
    by_condition: dict[str, list[dict[str, Any]]] = {}
    for run in normalized:
        by_condition.setdefault(run["condition"], []).append(run)
    for required in (baseline_condition, candidate_condition):
        if required not in by_condition:
            raise ValueError(f"token runs do not include condition: {required}")
    baseline_by_id = {
        run["task_id"]: run for run in by_condition[baseline_condition]
    }
    candidate_by_id = {
        run["task_id"]: run for run in by_condition[candidate_condition]
    }
    shared_ids = sorted(set(baseline_by_id) & set(candidate_by_id))
    baseline_only_ids = sorted(set(baseline_by_id) - set(candidate_by_id))
    candidate_only_ids = sorted(set(candidate_by_id) - set(baseline_by_id))
    for task_id in shared_ids:
        if baseline_by_id[task_id]["task_kind"] != candidate_by_id[task_id]["task_kind"]:
            raise ValueError(f"paired task_kind mismatch for task_id: {task_id}")
    paired_ids = [
        task_id
        for task_id in shared_ids
        if baseline_by_id[task_id]["safe_and_resolved"]
        and candidate_by_id[task_id]["safe_and_resolved"]
    ]
    repair_ids = [
        task_id
        for task_id in paired_ids
        if baseline_by_id[task_id]["task_kind"] == "bugfix"
    ]
    no_match_ids = [
        task_id
        for task_id in paired_ids
        if baseline_by_id[task_id]["task_kind"] == "no_match"
    ]
    comparisons = {
        "all": _paired_token_summary(baseline_by_id, candidate_by_id, paired_ids),
        "repair": _paired_token_summary(
            baseline_by_id, candidate_by_id, repair_ids
        ),
        "no_match": _paired_token_summary(
            baseline_by_id, candidate_by_id, no_match_ids
        ),
    }
    authoring_complete = (
        baseline_condition in authoring and candidate_condition in authoring
    )
    baseline_authoring = authoring.get(baseline_condition)
    candidate_authoring = authoring.get(candidate_condition)
    incremental_authoring = (
        candidate_authoring - baseline_authoring
        if authoring_complete
        and baseline_authoring is not None
        and candidate_authoring is not None
        else None
    )
    break_even: dict[str, float | None] = {}
    for name in ("all", "repair"):
        average_saving = comparisons[name]["average_task_token_saving"]
        break_even[name] = (
            round(incremental_authoring / average_saving, 2)
            if average_saving is not None
            and average_saving > 0
            and incremental_authoring is not None
            and incremental_authoring >= 0
            and authoring_complete
            else None
        )
    excluded_runs = [
        {
            "condition": run["condition"],
            "task_id": run["task_id"],
            "task_kind": run["task_kind"],
            "reasons": run["exclusion_reasons"],
        }
        for run in normalized
        if run["exclusion_reasons"]
    ]
    conditions = {
        condition: _token_condition_summary(
            condition_runs, authoring.get(condition)
        )
        for condition, condition_runs in sorted(by_condition.items())
    }
    return {
        "schema_version": TOKEN_EFFICIENCY_SCHEMA_VERSION,
        "status": "comparable" if paired_ids else "insufficient_data",
        "baseline_condition": baseline_condition,
        "candidate_condition": candidate_condition,
        "conditions": conditions,
        "paired_safe_and_resolved_task_count": len(paired_ids),
        "shared_task_count": len(shared_ids),
        "unpaired_or_excluded_shared_task_count": len(shared_ids) - len(paired_ids),
        "baseline_only_task_ids": baseline_only_ids,
        "candidate_only_task_ids": candidate_only_ids,
        "comparisons": comparisons,
        "map_authoring_tokens": {
            "baseline": baseline_authoring,
            "candidate": candidate_authoring,
            "incremental": incremental_authoring,
            "complete": authoring_complete,
        },
        "break_even_task_count": break_even,
        "excluded_runs": excluded_runs,
        "limitation": (
            "Token-saving comparisons include only task IDs that are safe and "
            "resolved in both conditions. The caller must supply actual measured "
            "tokens and truthful run outcomes."
        ),
    }
