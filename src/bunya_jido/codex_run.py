from __future__ import annotations

import fnmatch
import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import quote

from .benchmark import audit_worktree
from .blueprint import (
    _generate_agent_route_receipt,
    generate_agent_context,
    generate_agent_context_report,
)


CODEX_RUN_SCHEMA_VERSION = "bunya-jido-codex-run-v1"
KNOWN_CONTEXT_DECISIONS = {
    "MATCH",
    "IN_SCOPE_NO_ROUTE",
    "OUT_OF_SCOPE",
    "UNCERTAIN",
    "DISABLED",
}


class _GuardedCodexRunError(ValueError):
    """A controlled preflight error that prevents a guarded run."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_run_id(now: datetime) -> str:
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_repo_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _resolve_output_dir(root: Path, out_dir: str | Path | None, run_id: str) -> Path:
    if out_dir is None:
        return root / ".bunya-jido" / "runs" / run_id
    candidate = Path(out_dir)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "run_json": output_dir / "run.json",
        "report_markdown": output_dir / "report.md",
        "events_jsonl": output_dir / "events.jsonl",
        "stderr_log": output_dir / "stderr.log",
        "last_message": output_dir / "last-message.txt",
    }


def _artifact_report(paths: Mapping[str, Path], output_dir: Path) -> dict[str, str]:
    return {
        name: path.resolve().relative_to(output_dir.resolve()).as_posix()
        for name, path in paths.items()
    }


def _allowed_artifact_patterns(
    paths: Mapping[str, Path],
    root: Path,
) -> list[str]:
    allowed: list[str] = []
    for path in paths.values():
        try:
            allowed.append(path.resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return sorted(allowed)


def _prepare_artifacts(output_dir: Path, paths: Mapping[str, Path]) -> None:
    collisions = [path for path in paths.values() if path.exists()]
    if collisions:
        joined = ", ".join(str(path) for path in collisions)
        raise _GuardedCodexRunError(
            f"run output would overwrite existing artifacts: {joined}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("events_jsonl", "stderr_log", "last_message"):
        paths[name].write_text("", encoding="utf-8")


def _expected_sandbox(decision: str) -> str:
    return "workspace-write" if decision == "MATCH" else "read-only"


def _validated_sandbox(context_report: Mapping[str, Any]) -> str:
    decision = str(context_report.get("decision") or "")
    if decision not in KNOWN_CONTEXT_DECISIONS:
        raise _GuardedCodexRunError(
            f"unsupported context decision: {decision or 'missing'}"
        )
    expected = _expected_sandbox(decision)
    reported = str(context_report.get("codex_sandbox_mode") or "")
    if reported != expected:
        raise _GuardedCodexRunError(
            f"context sandbox mismatch for {decision}: expected {expected}, got {reported or 'missing'}"
        )
    return expected


def _command_prefix(
    codex_executable: str | Path,
    injected_prefix: Sequence[str] | None,
) -> list[str]:
    if injected_prefix is not None:
        prefix = [str(value) for value in injected_prefix]
    else:
        prefix = [str(codex_executable)]
    if not prefix or not prefix[0].strip():
        raise _GuardedCodexRunError("Codex executable is required.")
    return prefix


def _executable_available(prefix: Sequence[str]) -> bool:
    executable = prefix[0]
    candidate = Path(executable)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate.exists() and candidate.is_file()
    return shutil.which(executable) is not None


def _build_codex_command(
    prefix: Sequence[str],
    *,
    root: Path,
    sandbox_mode: str,
    last_message_path: Path,
    model: str | None,
) -> list[str]:
    command = [
        *prefix,
        "--ask-for-approval",
        "never",
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-c",
        'web_search="disabled"',
        "exec",
        "--strict-config",
        "--ignore-user-config",
        "--ignore-rules",
        "--ephemeral",
        "--json",
        "--color",
        "never",
        "--sandbox",
        sandbox_mode,
        "--cd",
        str(root),
        "--output-last-message",
        str(last_message_path),
    ]
    if model:
        command.extend(["--model", model])
    command.append("-")
    return command


def _display_command(command: Sequence[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(list(command))
    return shlex.join(command)


def _render_prompt(
    *,
    task: str,
    context_markdown: str,
    decision: str,
    sandbox_mode: str,
) -> str:
    if decision == "MATCH":
        action = (
            "Complete the task within the validated semantic guidance. The workspace sandbox "
            "allows repository writes, but safe-edit paths are guidance rather than an OS "
            "allowlist. Bunya-Jido will audit actual changes after the run."
        )
    elif decision == "IN_SCOPE_NO_ROUTE":
        action = (
            "Perform bounded read-only discovery and report useful evidence or a justified "
            "context recheck. Do not modify or create files."
        )
    else:
        action = (
            "Remain read-only. Explain the decision and relevant repository boundary without "
            "modifying or creating files."
        )
    return (
        "# Bunya-Jido Guarded Codex Run\n\n"
        f"Task JSON: {json.dumps(task, ensure_ascii=False)}\n"
        f"Validated context decision: {decision}\n"
        f"OS-enforced Codex sandbox: {sandbox_mode}\n\n"
        f"{action}\n\n"
        "The context below is the compact task-scoped Bunya-Jido handoff. Do not treat semantic "
        "safe-edit guidance as an OS-enforced path boundary.\n\n"
        "<bunya_jido_context>\n"
        f"{context_markdown.rstrip()}\n"
        "</bunya_jido_context>\n"
    )


def _run_process(
    command: Sequence[str],
    *,
    root: Path,
    prompt: str,
    events_path: Path,
    stderr_path: Path,
    timeout: float | None,
    popen_factory: Callable[..., subprocess.Popen[Any]],
    environ: Mapping[str, str] | None,
    monotonic_fn: Callable[[], float],
) -> dict[str, Any]:
    started = monotonic_fn()
    process: subprocess.Popen[Any] | None = None
    timed_out = False
    cancelled = False
    launch_error: str | None = None
    return_code: int | None = None
    with events_path.open("w", encoding="utf-8", newline="\n") as events_stream:
        with stderr_path.open("w", encoding="utf-8", newline="\n") as stderr_stream:
            try:
                process = popen_factory(
                    list(command),
                    cwd=root,
                    stdin=subprocess.PIPE,
                    stdout=events_stream,
                    stderr=stderr_stream,
                    text=True,
                    encoding="utf-8",
                    env=dict(environ) if environ is not None else None,
                    shell=False,
                )
                try:
                    process.communicate(input=prompt, timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    process.terminate()
                    try:
                        process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                except KeyboardInterrupt:
                    cancelled = True
                    process.terminate()
                    try:
                        process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                return_code = process.returncode
            except OSError as exc:
                launch_error = str(exc)
                stderr_stream.write(f"Could not launch Codex: {exc}\n")
    return {
        "launched": process is not None,
        "return_code": return_code,
        "timed_out": timed_out,
        "cancelled": cancelled,
        "launch_error": launch_error,
        "duration_seconds": round(max(0.0, monotonic_fn() - started), 6),
    }


def _safe_edit_allows(path: str, safe_edit_paths: Sequence[str], root: Path) -> bool:
    normalized = _normalize_repo_path(path)
    for raw_guidance in safe_edit_paths:
        guidance = _normalize_repo_path(str(raw_guidance))
        if not guidance:
            continue
        if any(character in guidance for character in "*?["):
            if fnmatch.fnmatchcase(normalized, guidance):
                return True
            continue
        guidance_path = root / guidance
        if str(raw_guidance).replace("\\", "/").endswith("/") or guidance_path.is_dir():
            if normalized == guidance or normalized.startswith(f"{guidance}/"):
                return True
            continue
        if normalized == guidance:
            return True
    return False


def _boundary_audit(
    *,
    context_report: Mapping[str, Any],
    post_audit: Mapping[str, Any],
    root: Path,
) -> dict[str, Any]:
    decision = str(context_report["decision"])
    safe_edit_paths = [
        _normalize_repo_path(str(path))
        for path in context_report.get("safe_edit_paths") or []
        if str(path).strip()
    ]
    activity: dict[str, set[str]] = {}
    for field, source in (
        ("production_file_changes", "final_worktree_change"),
        ("jsonl_production_write_attempts", "jsonl_write_attempt"),
    ):
        for path in post_audit.get(field) or []:
            normalized = _normalize_repo_path(str(path))
            activity.setdefault(normalized, set()).add(source)

    in_boundary_paths: list[str] = []
    violations: list[dict[str, Any]] = []
    for path, sources in sorted(activity.items()):
        allowed = decision == "MATCH" and _safe_edit_allows(path, safe_edit_paths, root)
        if allowed:
            in_boundary_paths.append(path)
        else:
            violations.append(
                {
                    "path": path,
                    "sources": sorted(sources),
                    "reason": (
                        "production activity is forbidden for a non-MATCH decision"
                        if decision != "MATCH"
                        else "path is outside semantic safe-edit guidance"
                    ),
                }
            )
    outside_workspace = list(post_audit.get("jsonl_outside_workspace_changes") or [])
    for event in outside_workspace:
        violations.append(
            {
                "path": str(event.get("path") or ""),
                "sources": ["jsonl_outside_workspace_attempt"],
                "reason": "Codex reported a file-change attempt outside the workspace",
            }
        )
    return {
        "decision": decision,
        "semantic_safe_edit_paths": safe_edit_paths,
        "semantic_guidance_os_enforced": False,
        "observed_production_activity": [
            {"path": path, "sources": sorted(sources)}
            for path, sources in sorted(activity.items())
        ],
        "in_boundary_paths": in_boundary_paths,
        "boundary_violations": violations,
        "outside_workspace_attempts": outside_workspace,
        "has_boundary_violation": bool(violations),
    }


def _route_receipt(root: Path, task: str, output_dir: Path) -> dict[str, Any]:
    receipt = _generate_agent_route_receipt(root, task=task)
    atlas_path = root / "bunya-jido.html"
    route_id = str(receipt.get("route_id") or "")
    receipt["atlas"] = {
        "path": "bunya-jido.html",
        "available": atlas_path.is_file(),
        "route_fragment": f"#route={quote(route_id, safe='')}" if route_id else None,
        "report_href": (
            Path(os.path.relpath(atlas_path, output_dir)).as_posix()
            if atlas_path.is_file()
            else None
        ),
        "build_command": None if atlas_path.is_file() else "bunya-jido build --root .",
    }
    return receipt


def _token_usage_receipt(events_path: Path | None) -> dict[str, Any]:
    unavailable = {
        "availability": "unavailable",
        "reason": "no_turn_completed_usage",
        "event_count": 0,
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_output_tokens": None,
        "total_tokens": None,
    }
    if events_path is None or not events_path.is_file():
        return unavailable
    usages: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = event.get("usage") if isinstance(event, dict) else None
        if (
            isinstance(event, dict)
            and event.get("type") == "turn.completed"
            and isinstance(usage, dict)
        ):
            usages.append(usage)
    if not usages:
        return unavailable
    if len(usages) != 1:
        return {
            **unavailable,
            "availability": "multiple",
            "reason": "multiple_turn_completed_usage_events",
            "event_count": len(usages),
        }
    usage = usages[0]
    fields = {
        name: (
            value
            if isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0
            else None
        )
        for name, value in (
            ("input_tokens", usage.get("input_tokens")),
            ("cached_input_tokens", usage.get("cached_input_tokens")),
            ("output_tokens", usage.get("output_tokens")),
            ("reasoning_output_tokens", usage.get("reasoning_output_tokens")),
            ("total_tokens", usage.get("total_tokens")),
        )
    }
    required_available = fields["input_tokens"] is not None and fields["output_tokens"] is not None
    return {
        "availability": "available" if required_available else "partial",
        "reason": None if required_available else "usage_fields_incomplete",
        "event_count": 1,
        **fields,
    }


def _update_efficiency_receipt(
    report: dict[str, Any],
    *,
    events_path: Path | None,
) -> None:
    post_audit = report.get("post_run_audit") or {}
    boundary = report.get("boundary_audit") or {}
    if report.get("preview"):
        boundary_result = "not_run_preview"
        usage = {
            **_token_usage_receipt(None),
            "reason": "preview_does_not_launch_codex",
        }
    elif report.get("status") == "blocked":
        boundary_result = "not_run_preflight_blocked"
        usage = {
            **_token_usage_receipt(None),
            "reason": "codex_not_launched",
        }
    elif not post_audit.get("jsonl_complete"):
        boundary_result = "audit_incomplete"
        usage = _token_usage_receipt(events_path)
    elif boundary.get("has_boundary_violation"):
        boundary_result = "failed"
        usage = _token_usage_receipt(events_path)
    else:
        boundary_result = "passed"
        usage = _token_usage_receipt(events_path)
    report["context_efficiency_receipt"].update(
        {
            "actual_token_usage": usage,
            "elapsed_execution_seconds": report["execution"].get("duration_seconds"),
            "final_changed_file_count": len(post_audit.get("production_file_changes") or []),
            "observed_production_path_count": len(
                boundary.get("observed_production_activity") or []
            ),
            "boundary_result": boundary_result,
        }
    )


def _base_report(
    *,
    run_id: str,
    root: Path,
    task: str,
    started_at: datetime,
    context_report: Mapping[str, Any],
    context_markdown: str,
    sandbox_mode: str,
    command: Sequence[str],
    executable_available: bool,
    artifacts: Mapping[str, Path],
    output_dir: Path,
    baseline_audit: Mapping[str, Any],
    preview: bool,
    route_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    dirty = not bool(baseline_audit.get("worktree_clean"))
    preflight_reasons = ["dirty_worktree"] if dirty else []
    if not executable_available:
        preflight_reasons.append("codex_executable_not_found")
    return {
        "schema_version": CODEX_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "status": "preview" if preview else "planned",
        "exit_code": 0 if preview else None,
        "reasons": [],
        "root": root.as_posix(),
        "task": task,
        "started_at": _isoformat(started_at),
        "finished_at": None,
        "duration_seconds": None,
        "preview": preview,
        "context": dict(context_report),
        "scoped_context": {
            "profile": "compact",
            "character_count": len(context_markdown),
            "utf8_byte_count": len(context_markdown.encode("utf-8")),
            "content": context_markdown,
        },
        "route_receipt": dict(route_receipt),
        "context_efficiency_receipt": {
            "compact_context_character_count": len(context_markdown),
            "compact_context_utf8_byte_count": len(context_markdown.encode("utf-8")),
            "actual_token_usage": {
                **_token_usage_receipt(None),
                "reason": "pending" if not preview else "preview_does_not_launch_codex",
            },
            "elapsed_execution_seconds": None,
            "final_changed_file_count": 0,
            "observed_production_path_count": 0,
            "boundary_result": "not_run_preview" if preview else "pending",
            "tokens_saved": None,
            "tokens_saved_reason": "requires_compatible_paired_no_map_baseline",
        },
        "execution": {
            "sandbox_mode": sandbox_mode,
            "command": list(command),
            "command_display": _display_command(command),
            "shell": False,
            "prompt_delivery": "stdin",
            "approval_policy": "never",
            "user_config_ignored": True,
            "execpolicy_rules_ignored": True,
            "ephemeral": True,
            "web_search_enabled": False,
            "web_search_mode": "disabled",
            "workspace_network_access": False,
            "codex_executable_available": executable_available,
            "launched": False,
            "return_code": None,
            "timed_out": False,
            "cancelled": False,
            "launch_error": None,
            "duration_seconds": None,
        },
        "preflight": {
            "worktree_clean": not dirty,
            "would_block_execution": bool(preflight_reasons),
            "reasons": preflight_reasons,
        },
        "baseline_audit": dict(baseline_audit),
        "post_run_audit": None,
        "boundary_audit": None,
        "output_directory": _display_path(output_dir, root),
        "artifacts": _artifact_report(artifacts, output_dir),
    }


def _finish_report(
    report: dict[str, Any],
    *,
    finished_at: datetime,
    started_monotonic: float,
    monotonic_fn: Callable[[], float],
) -> None:
    report["finished_at"] = _isoformat(finished_at)
    report["duration_seconds"] = round(
        max(0.0, monotonic_fn() - started_monotonic),
        6,
    )


def _render_markdown(report: Mapping[str, Any]) -> str:
    context = report["context"]
    execution = report["execution"]
    preflight = report["preflight"]
    boundary = report.get("boundary_audit") or {}
    route = report.get("route_receipt") or {}
    efficiency = report.get("context_efficiency_receipt") or {}
    usage = efficiency.get("actual_token_usage") or {}
    lines = [
        "# Bunya-Jido Guarded Codex Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Status: `{report['status']}`",
        f"- Exit code: `{report['exit_code']}`",
        f"- Decision: `{context.get('decision')}`",
        f"- Codex sandbox: `{execution.get('sandbox_mode')}`",
        f"- Worktree clean at baseline: `{str(preflight.get('worktree_clean')).lower()}`",
        "",
        "## Task",
        "",
        str(report["task"]),
        "",
        "## Shared Human-Agent Route",
        "",
        f"- Route available: `{str(bool(route.get('available'))).lower()}`",
        f"- Route ID: `{route.get('route_id') or 'unavailable'}`",
        f"- Route fingerprint: `{route.get('route_fingerprint') or 'unavailable'}`",
        f"- Starting responsibility: `{', '.join(route.get('starting_responsibilities') or []) or 'unavailable'}`",
        f"- First reads: `{route.get('first_read_count', 0)}`",
        f"- Relevant tests: `{route.get('relevant_test_count', 0)}`",
    ]
    atlas = route.get("atlas") or {}
    if atlas.get("available") and atlas.get("route_fragment"):
        lines.append(
            f"- Atlas route: [{atlas.get('path')}]({atlas.get('report_href')}{atlas.get('route_fragment')})"
        )
    elif atlas.get("build_command"):
        lines.append(f"- Atlas: unavailable; build with `{atlas.get('build_command')}`")
    lines.extend(
        [
        "",
        "## Context Efficiency Receipt",
        "",
        f"- Compact context: `{efficiency.get('compact_context_character_count')}` characters / `{efficiency.get('compact_context_utf8_byte_count')}` UTF-8 bytes",
        f"- Actual token usage: `{usage.get('availability')}`",
        f"- Input tokens: `{usage.get('input_tokens')}`",
        f"- Cached input tokens: `{usage.get('cached_input_tokens')}`",
        f"- Output tokens: `{usage.get('output_tokens')}`",
        f"- Reasoning output tokens: `{usage.get('reasoning_output_tokens')}`",
        f"- Total tokens: `{usage.get('total_tokens')}`",
        f"- Token usage reason: `{usage.get('reason')}`",
        f"- Elapsed execution: `{efficiency.get('elapsed_execution_seconds')}` seconds",
        f"- Final changed files: `{efficiency.get('final_changed_file_count')}`",
        f"- Boundary result: `{efficiency.get('boundary_result')}`",
        "- Tokens saved: unavailable from a single run; a compatible paired no-map baseline is required.",
        "",
        "## Enforcement Boundary",
        "",
        "- The Codex sandbox controls OS-level workspace write access.",
        "- Bunya-Jido safe-edit paths are semantic guidance and are audited after execution; they are not an OS path allowlist.",
        "- User and project Codex execpolicy `.rules` files are ignored for deterministic automation; this does not claim to bypass managed requirements.",
        '- Codex web search is explicitly set to `"disabled"`; workspace shell network access is independently disabled.',
        "",
        "## Process",
        "",
        f"- Launched: `{str(execution.get('launched')).lower()}`",
        f"- Return code: `{execution.get('return_code')}`",
        f"- Timed out: `{str(execution.get('timed_out')).lower()}`",
        f"- Cancelled: `{str(execution.get('cancelled')).lower()}`",
        f"- JSONL complete: `{str(bool((report.get('post_run_audit') or {}).get('jsonl_complete'))).lower()}`",
        "",
        "## Boundary Audit",
        "",
        f"- In-boundary paths: `{len(boundary.get('in_boundary_paths') or [])}`",
        f"- Violations: `{len(boundary.get('boundary_violations') or [])}`",
        ]
    )
    for violation in boundary.get("boundary_violations") or []:
        lines.append(f"- `{violation['path']}`: {violation['reason']}")
    lines.extend(["", "## Outcome", ""])
    if report.get("reasons"):
        lines.extend(f"- {reason}" for reason in report["reasons"])
    else:
        lines.append("- No failure reasons recorded.")
    lines.extend(["", "## Artifacts", ""])
    for name, path in report["artifacts"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def _write_report(report: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    paths["run_json"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["report_markdown"].write_text(_render_markdown(report), encoding="utf-8")


def _render_guarded_run_console(report: Mapping[str, Any]) -> str:
    context = report["context"]
    preflight = report["preflight"]
    lines = [
        f"Guarded Codex Run: {report['status']}",
        f"Decision: {context.get('decision')}",
        f"Sandbox: {report['execution'].get('sandbox_mode')}",
        f"Baseline: {'clean' if preflight.get('worktree_clean') else 'dirty'}",
    ]
    if report.get("preview"):
        lines.append(f"Command: {report['execution'].get('command_display')}")
        if preflight.get("would_block_execution"):
            lines.append(
                "Actual execution would be blocked: "
                + ", ".join(preflight.get("reasons") or [])
            )
        lines.extend(
            [
                "",
                "Scoped context:",
                str((report.get("scoped_context") or {}).get("content") or "").rstrip(),
            ]
        )
    else:
        lines.append(f"Exit code: {report['exit_code']}")
        output_directory = str(report.get("output_directory") or "").rstrip("/")
        report_path = str(report["artifacts"]["report_markdown"]).lstrip("/")
        lines.append(f"Report: {output_directory}/{report_path}")
        for reason in report.get("reasons") or []:
            lines.append(f"- {reason}")
    return "\n".join(lines) + "\n"


def _execute_guarded_codex_run(
    *,
    root: str | Path,
    task: str,
    preview: bool = False,
    out_dir: str | Path | None = None,
    model: str | None = None,
    codex_executable: str | Path = "codex",
    timeout: float | None = None,
    command_prefix: Sequence[str] | None = None,
    now_fn: Callable[[], datetime] = _utc_now,
    run_id: str | None = None,
    popen_factory: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
    environ: Mapping[str, str] | None = None,
    monotonic_fn: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Execute the internal Guarded Codex Run workflow used by the CLI.

    This function is intentionally not exported from the package root. Injection
    parameters exist for deterministic tests and fake Codex executables.
    """

    if not isinstance(task, str) or not task.strip():
        raise _GuardedCodexRunError("Guarded Codex Run requires a non-empty task.")
    if timeout is not None and timeout <= 0:
        raise _GuardedCodexRunError("timeout must be greater than zero")
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise _GuardedCodexRunError(f"repository root not found: {root_path}")

    started_at = now_fn()
    started_monotonic = monotonic_fn()
    resolved_run_id = run_id or _default_run_id(started_at)
    output_dir = _resolve_output_dir(root_path, out_dir, resolved_run_id)
    artifacts = _artifact_paths(output_dir)
    context_report = generate_agent_context_report(root_path, task=task)
    context_markdown = generate_agent_context(root_path, task=task)
    route_receipt = _route_receipt(root_path, task, output_dir)
    sandbox_mode = _validated_sandbox(context_report)
    prefix = _command_prefix(codex_executable, command_prefix)
    command = _build_codex_command(
        prefix,
        root=root_path,
        sandbox_mode=sandbox_mode,
        last_message_path=artifacts["last_message"],
        model=model,
    )
    executable_available = _executable_available(prefix)
    try:
        baseline_audit = audit_worktree(root_path)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise _GuardedCodexRunError(f"baseline worktree audit failed: {exc}") from exc

    report = _base_report(
        run_id=resolved_run_id,
        root=root_path,
        task=task.strip(),
        started_at=started_at,
        context_report=context_report,
        context_markdown=context_markdown,
        sandbox_mode=sandbox_mode,
        command=command,
        executable_available=executable_available,
        artifacts=artifacts,
        output_dir=output_dir,
        baseline_audit=baseline_audit,
        preview=preview,
        route_receipt=route_receipt,
    )
    if preview:
        _finish_report(
            report,
            finished_at=now_fn(),
            started_monotonic=started_monotonic,
            monotonic_fn=monotonic_fn,
        )
        _update_efficiency_receipt(report, events_path=None)
        return report

    _prepare_artifacts(output_dir, artifacts)
    if report["preflight"]["would_block_execution"]:
        report["status"] = "blocked"
        report["exit_code"] = 2
        report["reasons"] = list(report["preflight"]["reasons"])
        _finish_report(
            report,
            finished_at=now_fn(),
            started_monotonic=started_monotonic,
            monotonic_fn=monotonic_fn,
        )
        _update_efficiency_receipt(report, events_path=None)
        _write_report(report, artifacts)
        return report

    prompt = _render_prompt(
        task=task.strip(),
        context_markdown=context_markdown,
        decision=str(context_report["decision"]),
        sandbox_mode=sandbox_mode,
    )
    process_result = _run_process(
        command,
        root=root_path,
        prompt=prompt,
        events_path=artifacts["events_jsonl"],
        stderr_path=artifacts["stderr_log"],
        timeout=timeout,
        popen_factory=popen_factory,
        environ=environ,
        monotonic_fn=monotonic_fn,
    )
    report["execution"].update(process_result)

    audit_error: str | None = None
    try:
        post_audit = audit_worktree(
            root_path,
            jsonl_paths=[artifacts["events_jsonl"]],
            allowed_artifacts=_allowed_artifact_patterns(artifacts, root_path),
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        post_audit = None
        audit_error = str(exc)
    report["post_run_audit"] = post_audit
    if post_audit is not None:
        report["boundary_audit"] = _boundary_audit(
            context_report=context_report,
            post_audit=post_audit,
            root=root_path,
        )

    reasons: list[str] = []
    boundary_violation = bool(
        (report.get("boundary_audit") or {}).get("has_boundary_violation")
    )
    jsonl_complete = bool((post_audit or {}).get("jsonl_complete"))
    if process_result["timed_out"]:
        reasons.append("codex_timeout")
    if process_result["cancelled"]:
        reasons.append("codex_cancelled")
    if process_result["launch_error"]:
        reasons.append(f"codex_launch_error: {process_result['launch_error']}")
    if process_result["return_code"] not in {0, None}:
        reasons.append(f"codex_nonzero_exit: {process_result['return_code']}")
    if audit_error:
        reasons.append(f"post_run_audit_failed: {audit_error}")
    elif not jsonl_complete:
        reasons.append("codex_jsonl_incomplete")
    if boundary_violation:
        reasons.append("semantic_boundary_violation")

    if process_result["timed_out"] or process_result["cancelled"]:
        status = "cancelled"
        exit_code = 130
    elif audit_error or not jsonl_complete:
        status = "audit_incomplete"
        exit_code = 2
    elif boundary_violation:
        status = "boundary_violation"
        exit_code = 2
    elif process_result["launch_error"] or process_result["return_code"] != 0:
        status = "codex_failed"
        exit_code = 2
    else:
        status = "succeeded"
        exit_code = 0
    report["status"] = status
    report["exit_code"] = exit_code
    report["reasons"] = reasons
    _finish_report(
        report,
        finished_at=now_fn(),
        started_monotonic=started_monotonic,
        monotonic_fn=monotonic_fn,
    )
    _update_efficiency_receipt(report, events_path=artifacts["events_jsonl"])
    _write_report(report, artifacts)
    return report
