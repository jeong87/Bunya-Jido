from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


AUDIT_SCHEMA_VERSION = "bunya-jido-worktree-audit-v1"


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
