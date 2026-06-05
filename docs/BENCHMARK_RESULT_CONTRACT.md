# Benchmark Worktree Audit Contract

`bunya-jido audit-worktree` provides the P0 workspace-truth primitive for
live-agent benchmark runners. It closes the blind spot created by relying on
`git diff --numstat` alone, which does not report untracked files and cannot
separately describe staged, deleted, or renamed paths.

## Runner Integration

Before a benchmark task, require a clean committed baseline:

```powershell
bunya-jido audit-worktree --root workspace --require-clean --json
```

After the task, include the Codex JSONL event log and explicitly classify
runner-owned artifacts:

```powershell
bunya-jido audit-worktree `
  --root workspace `
  --jsonl results/task.codex.jsonl `
  --allow-artifact "results/**" `
  --require-jsonl `
  --require-no-production-activity `
  --json
```

The Python API exposes the same report:

```python
from bunya_jido.benchmark import audit_worktree

baseline = audit_worktree(workspace)
if not baseline["worktree_clean"]:
    raise RuntimeError("dirty benchmark baseline")

post_run = audit_worktree(
    workspace,
    jsonl_paths=[codex_jsonl],
    allowed_artifacts=["results/**"],
)
observed_production_activity = sorted(
    set(post_run["production_file_changes"])
    | set(post_run["jsonl_production_write_attempts"])
)
```

Backward-compatible runners may keep their existing `changed_files` field for
final production changes while adding the complete `baseline_audit`,
`worktree_audit`, and `observed_production_activity` fields. Boundary,
protected-file, and no-match policy checks should use observed production
activity so a write-then-revert attempt cannot evade them.

## Result Fields

The `bunya-jido-worktree-audit-v1` report records:

- `worktree_clean`
- `changed_files_tracked`
- `staged_files`
- `deleted_files`
- `renamed_files`
- `untracked_files`
- `changed_lines_tracked`
- `allowed_artifact_changes`
- `production_file_changes`
- `jsonl_file_change_events`
- `jsonl_allowed_artifact_attempts`
- `jsonl_production_write_attempts`
- `jsonl_outside_workspace_changes`
- `jsonl_log_count`
- `jsonl_event_count`
- `malformed_jsonl_lines`
- `invalid_jsonl_lines`
- `jsonl_complete`

Final workspace truth and JSONL write attempts are intentionally separate.
A file that an agent writes and then reverts produces no final production
change, but it remains a production write attempt.

## Required Runner Behavior

1. Run the clean-baseline audit after fixture setup and before agent execution.
2. Record the pre-run report's `worktree_clean` value as the enclosing
   runner result's `baseline_clean` field, and mark the run invalid when
   `--require-clean` fails.
3. Store the complete post-run audit report with the benchmark result.
4. Treat all changed paths as production unless they match an explicit,
   reviewed `--allow-artifact` glob.
5. Treat production JSONL file-change events as policy failures even when the
   final worktree is clean.
6. Use `--require-jsonl` for claims about write-attempt-free execution; a
   missing, empty, malformed, or structurally invalid JSONL log makes that
   evidence incomplete.
7. Keep context-decision and execution-policy fields in the enclosing runner
   result; this audit reports filesystem truth rather than router policy.

## Fixture Coverage

`tests/test_benchmark_audit.py` locks the P0 behavior for clean baselines,
untracked production files, tracked modifications, staged files, deletions,
renames, allowed artifacts, malformed JSONL, outside-workspace events, and
write-then-revert attempts.

External benchmark harnesses still need to call this API or CLI and rerun
their benchmark sets. A historical result produced by a runner that only used
`git diff --numstat` is not valid P0 evidence.

## P3 Token Efficiency Summary

`bunya-jido summarize-token-efficiency` accepts measured runner results and
produces a `bunya-jido-token-efficiency-report-v1` report:

```powershell
bunya-jido summarize-token-efficiency `
  --results results/token-runs.json `
  --baseline no-map `
  --candidate 0.5-map `
  --require-comparable `
  --json
```

The input object contains optional per-condition map-authoring tokens and a
required run list:

```json
{
  "map_authoring_tokens": {
    "no-map": 0,
    "0.5-map": 1972223
  },
  "runs": [
    {
      "condition": "0.5-map",
      "task_id": "billing-step-units",
      "task_kind": "bugfix",
      "task_tokens": 42000,
      "context_output_tokens": 900,
      "resolved": true,
      "infrastructure_valid": true,
      "boundary_violation": false,
      "production_write_attempt": true
    }
  ]
}
```

`task_kind` is `bugfix` or `no_match`. A run is excluded from token-saving
comparisons when it is unresolved, infrastructure-invalid, has a boundary
violation, or is a no-match run with a production write attempt. Production
writes are not themselves disqualifying for a resolved in-boundary bugfix.

Savings use only shared task IDs that are safe and resolved in both the
baseline and candidate conditions. The report keeps excluded runs visible and
separately reports:

- map-authoring tokens and incremental authoring cost;
- context-output tokens and medians;
- repair task tokens;
- safe-and-resolved task tokens;
- no-match tokens and safe-and-resolved no-match medians;
- paired all-task, repair, and no-match savings;
- all-task and repair break-even task counts.

Missing optional map-authoring measurements are reported as `null`, never as
measured zero. Break-even remains `null` when map-authoring measurements are
incomplete or the paired tasks do not save tokens. The summary does not repair
invalid runner evidence or prove live-agent resolution; callers must supply
truthful, compatible measured results.
