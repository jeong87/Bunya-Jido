# Guarded Codex Run

`bunya-jido codex-run` launches a local Codex CLI under the execution policy
selected by Bunya-Jido context. It does not add a runtime dependency, external
service, telemetry channel, or data upload mechanism.

## Prerequisites

- Run inside a Git worktree.
- Install and authenticate the local Codex CLI separately.
- Keep the worktree clean for an actual run.

Preview does not require a clean baseline:

```bash
bunya-jido codex-run --root . --task "change guarded Codex run orchestration" --preview
```

Preview prints the context decision, sandbox, scoped context, sanitized argv,
baseline cleanliness, and any reason an actual run would be blocked. It does
not launch Codex or create run artifacts.

An actual run is:

```bash
bunya-jido codex-run --root . --task "change guarded Codex run orchestration"
```

Options are limited to `--preview`, `--json`, `--out-dir`, `--model`,
`--codex-executable`, and `--timeout`. `--task` is required. The command does
not expose a sandbox override, dirty-worktree bypass, network enablement, or
arbitrary additional Codex arguments.

## Sandbox Contract

| Context decision | Codex sandbox |
| --- | --- |
| `MATCH` | `workspace-write` |
| `IN_SCOPE_NO_ROUTE` | `read-only` |
| `OUT_OF_SCOPE` | `read-only` |
| `UNCERTAIN` | `read-only` |
| `DISABLED` | `read-only` |

The command invokes Codex with approval disabled, user configuration ignored,
ephemeral sessions, JSONL output, color disabled, the mapped sandbox, and the
selected repository root. Prompt and scoped context are sent as UTF-8 standard
input with an argv list and `shell=False`.

Web search is not enabled. Workspace shell network access is disabled. The
provider connection needed to run the model is a separate Codex control path,
not workspace shell network permission.

## Enforcement and Audit

Codex's OS sandbox enforces filesystem access. Bunya-Jido safe-edit paths do not
grant access; they are semantic instructions and post-run audit criteria.

For `MATCH`, production activity must stay within exact safe-edit paths,
explicit globs, or descendants of explicitly declared directories. A file
path does not implicitly allow its parent directory. Renames check both old and
new paths.

For every non-`MATCH` decision, any production write activity is a violation.
The audit combines final Git changes with production write attempts observed in
Codex JSONL. Write-then-revert and outside-workspace attempts therefore remain
violations even when the final worktree is clean. Run artifacts and existing
generated-noise classifications are excluded from the production boundary.

Malformed, partial, or empty JSONL preserves readable events, stderr, the last
message, and the Codex return code, but the run fails as `audit_incomplete`.

## Artifacts and Result Schema

The default run directory is `.bunya-jido/runs/<run-id>/` and contains:

- `run.json`
- `report.md`
- `events.jsonl`
- `stderr.log`
- `last-message.txt`

`run.json` uses schema `bunya-jido-codex-run-v1`. It records the execution plan,
context decision, process result, baseline and post-run audits, boundary
decision, artifact paths, status, reason, and exit code. Artifact paths are
relative to the run directory. `report.md` renders the same decision, process,
violation, status, and exit-code facts for human review.

## Exit Codes

| Exit code | Meaning |
| --- | --- |
| `0` | Preview, or an execution whose policy, process, and audit all succeeded |
| `2` | Preflight block, Codex failure, incomplete JSONL, or policy/boundary violation |
| `130` | User cancellation or timeout |
| `1` | Unexpected internal error handled by the CLI boundary |

The repository test suite uses a fake Codex executable for deterministic
coverage. Passing fake-executable tests does not prove the behavior of a live
Codex OS sandbox. A real nested Codex run remains a separate, explicit human
approval gate.
