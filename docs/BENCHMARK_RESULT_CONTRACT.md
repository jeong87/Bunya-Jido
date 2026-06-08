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
runner-owned artifacts. Common generated/cache noise is filtered by default,
while runner artifacts must still be explicitly allowed:

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

The built-in generated-noise filter covers Python bytecode/cache output,
common test/cache directories, coverage HTML/data output, and OS/editor temp
files such as `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`,
`.ruff_cache/`, `.hypothesis/`, `.coverage*`, `htmlcov/`, `.DS_Store`,
`Thumbs.db`, swap files, and backup suffixes. Runners may add reviewed
repo-specific generated noise with repeated `--ignore-noise` globs. Use
`--no-default-noise` only to debug classifier behavior.

Backward-compatible runners may keep their existing `changed_files` field for
final production changes while adding the complete `baseline_audit`,
`worktree_audit`, and `observed_production_activity` fields. Boundary,
protected-file, and no-match policy checks should use observed production
activity so a write-then-revert attempt cannot evade them.

Each raw benchmark result should also retain the audit report's
`benchmark_provenance` object. It records the Bunya-Jido CLI version output,
the repository commit under test, and the SHA-256 of the agent-map file
when present, so later analysis can identify exactly which map and package
version produced the run.

## Result Fields

The `bunya-jido-worktree-audit-v2` report records:

- `benchmark_provenance`
  - `bunya_jido_version`
  - `bunya_jido_version_output`
  - `git_commit_sha`
  - `agent_map_path`
  - `agent_map_sha256`
- `worktree_clean`
- `production_clean`
- `changed_files_tracked`
- `staged_files`
- `deleted_files`
- `renamed_files`
- `untracked_files`
- `changed_lines_tracked`
- `allowed_artifact_patterns`
- `generated_noise_patterns`
- `file_change_classification`
- `allowed_artifact_changes`
- `generated_noise_changes`
- `production_file_changes`
- `jsonl_file_change_events`
- `jsonl_file_change_classification`
- `jsonl_allowed_artifact_attempts`
- `jsonl_generated_noise_attempts`
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

`worktree_clean` remains strict git cleanliness. Generated noise and allowed
artifacts still make the worktree non-clean, but they do not make
`production_clean` false and do not count as no-match production activity.

## Required Runner Behavior

1. Run the clean-baseline audit after fixture setup and before agent execution.
2. Record the pre-run report's `worktree_clean` value as the enclosing
   runner result's `baseline_clean` field, and mark the run invalid when
   `--require-clean` fails.
3. Store the complete post-run audit report with the benchmark result.
4. Preserve `benchmark_provenance` in the raw result. At minimum, later
   reports must be able to recover the equivalent of `bunya-jido --version`,
   `git rev-parse HEAD`, and the agent-map SHA-256.
5. Treat all changed paths as production unless they classify as an explicit,
   reviewed `--allow-artifact` glob or generated/cache noise.
6. Do not use `.gitignore` as a blanket production exemption; add only reviewed
   generated-noise globs when the default classifier is insufficient.
7. Treat production JSONL file-change events as policy failures even when the
   final worktree is clean.
8. Use `--require-jsonl` for claims about write-attempt-free execution; a
   missing, empty, malformed, or structurally invalid JSONL log makes that
   evidence incomplete.
9. Keep context-decision and execution-policy fields in the enclosing runner
   result; this audit reports filesystem truth rather than router policy.

## Context Policy For Runners

Benchmark runners should request machine-readable context instead of parsing
Markdown:

```powershell
bunya-jido context --root workspace --task "<task>" --json
```

To force a no-map condition while leaving repository files untouched, set
`BUNYA_JIDO_CONTEXT=off` or `BUNYA_JIDO_DISABLE_CONTEXT=1` before requesting
context. The command then returns `decision=DISABLED`, omits trusted routes,
omits safe-edit paths, and recommends `read-only` sandboxing even if map
artifacts are present.

The context report includes `decision`, `edit_policy`, `execution_policy`, and
`codex_sandbox_mode`. Use `codex_sandbox_mode` directly when launching Codex:

| `decision` | `execution_policy` | `codex_sandbox_mode` |
| --- | --- | --- |
| `MATCH` | `workspace_write` | `workspace-write` |
| `IN_SCOPE_NO_ROUTE` | `read_only_discovery` | `read-only` |
| `OUT_OF_SCOPE` | `read_only` | `read-only` |
| `UNCERTAIN` | `read_only` | `read-only` |
| `DISABLED` | `read_only` | `read-only` |

Do not scrape backtick-wrapped Markdown fields for sandbox selection. If a
legacy runner must consume older Markdown output, it must normalize surrounding
Markdown code ticks before comparison, but JSON context is the supported
integration surface.

## Fixture Coverage

`tests/test_benchmark_audit.py` locks the P0 behavior for clean baselines,
untracked production files, tracked modifications, staged files, deletions,
renames, allowed artifacts, generated/cache noise, malformed JSONL,
outside-workspace events, and write-then-revert attempts.

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

## P4 Time Efficiency Summary

`bunya-jido summarize-time-efficiency` reports measured timing without changing
route selection, matcher thresholds, or discovery behavior:

```powershell
bunya-jido summarize-time-efficiency `
  --results results/time-runs.json `
  --baseline no-map `
  --candidate 0.5-map `
  --require-comparable `
  --json
```

The input object contains optional per-condition map-authoring seconds and a
required run list:

```json
{
  "map_authoring_seconds": {
    "no-map": 0,
    "0.5-map": 1800
  },
  "runs": [
    {
      "condition": "0.5-map",
      "pair_id": "billing-step-units/medium/r1",
      "task_id": "billing-step-units",
      "task_kind": "bugfix",
      "total_resolution_seconds": 74.2,
      "context_generation_seconds": 0.8,
      "discovery_to_first_edit_seconds": 21.4,
      "resolved": true,
      "infrastructure_valid": true,
      "boundary_violation": false,
      "production_write_attempt": true
    }
  ]
}
```

`pair_id` identifies the same task, effort, repetition, and environment across
conditions. It may be omitted only when each condition has one run for a task;
then `task_id` is used. Repeated or mixed-effort runs must provide distinct
pair IDs.

`total_resolution_seconds` is end-to-end time from task handoff through the
final outcome and includes context generation. `context_generation_seconds`
measures the context decision and output step within that boundary.
`discovery_to_first_edit_seconds` measures from handoff to the first production
write attempt and may be `null` when no edit occurs. Missing first-edit timing
remains visible and excludes only that metric's paired comparison.

Time-saving comparisons use only pair IDs that are safe and resolved in both
conditions. The same unresolved, boundary-violation, no-match-write, and
infrastructure-invalid exclusions used by the token report apply. The report
keeps excluded runs visible and reports:

- cumulative, median, and nearest-rank p90 seconds;
- total-resolution, context-generation, and discovery-to-first-edit timings;
- all-task, repair, no-match, and per-task paired comparisons;
- missing first-edit measurement counts and pair IDs;
- optional map-authoring seconds and all-task/repair break-even counts.

Missing optional map-authoring measurements are `null`, never measured zero.
Historical `agent_elapsed_seconds` that excludes context generation does not
alone satisfy this P4 boundary. The report's scope is measurement-only: any
future optimization still needs diverse-repository and holdout evidence, and
must be rejected if safety or resolution quality regresses.
