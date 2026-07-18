# Context Execution Policy

`bunya-jido context --json` separates route-selection meaning from the sandbox
an integration should use.

- `edit_policy` remains the human-facing compatibility field.
- `execution_policy` is the machine-readable integration contract.
- `agent_instruction` explains the required behavior without claiming that
  Bunya-Jido itself controls an external agent runtime.

## Policy Matrix

| Decision | Execution policy | Integration behavior |
|---|---|---|
| `MATCH` | `workspace_write` | Allow writes while following the validated route and its boundaries. |
| `IN_SCOPE_NO_ROUTE` | `read_only_discovery` | Inspect supplied bounded discovery or ordinary repository evidence without editing, then request a new decision or user approval. |
| `OUT_OF_SCOPE` | `read_only` | Block writes and explain the reviewed repository boundary. |
| `UNCERTAIN` | `read_only` | Block writes and request clarification after bounded inspection when useful. |

Only `MATCH` may expose matched trusted routes or safe-edit paths. A route
catalog requested without a task is also read-only and does not expose
safe-edit paths.

`IN_SCOPE_NO_ROUTE` may expose optional `discovery_context`. Its likely areas,
first reads, tests, and search commands are capped and grounded in blueprint
nodes, workflows, or existing repository-relative paths. They are not a
trusted route or edit permission. After discovery, integrations should request
a new decision with a justified `context --node` or `context --workflow`
focus before enabling writes.

## Integration Pattern

Before starting a mapped repair task:

```powershell
bunya-jido context --root workspace --task $task --json --out context-decision.json
```

The runner or IDE integration should parse `execution_policy` before launching
the agent and choose the corresponding sandbox. It should store
`decision`, `route_status`, `edit_policy`, `execution_policy`,
`matched_routes`, and `safe_edit_paths` with the run result.

After execution, combine the decision with
[`audit-worktree`](BENCHMARK_RESULT_CONTRACT.md):

- A write attempt under `read_only` or `read_only_discovery` is a policy
  failure even if the final worktree is clean.
- A non-`MATCH` result with a trusted route or safe-edit path is a context
  contract failure.
- A reviewed unsupported task that becomes merely `UNCERTAIN` is an expected
  decision failure, even when no route leaks.

The CLI reports policy; it does not silently claim to enforce another
process's sandbox. Enforcement belongs to the runner, IDE, or agent host.

## Built-in Codex Integration

`bunya-jido codex-run` is the built-in runner that applies this policy to a
local Codex CLI:

```bash
bunya-jido codex-run --root . --task "change guarded Codex run orchestration" --preview
bunya-jido codex-run --root . --task "change guarded Codex run orchestration"
```

Preview does not launch Codex or create run artifacts. Actual execution requires
a clean Git worktree. Only `MATCH` maps to `workspace-write`; every other
supported decision maps to `read-only`, and the command exposes no sandbox,
dirty-worktree, network, or arbitrary-argument override.

Codex's OS sandbox is the enforcement boundary. Safe-edit paths are scoped
semantic guidance and a post-run audit rule. A safe-edit path never grants
additional OS access. See
[GUARDED_CODEX_RUN.md](GUARDED_CODEX_RUN.md) for the command, artifact, schema,
and exit-code contract.

## Deterministic P1 Gate

`bunya-jido evaluate-agent-utility --require-pass --json` now reports:

- `decision_confusion_matrix`
- `expected_decision_accuracy`
- `false_route_rate`
- `safe_edit_leak_rate`
- `execution_policy_accuracy`
- `trusted_route_recall`
- `bounded_discovery_coverage`
- `actionable_guidance_coverage`
- `normal_bugfix_hard_rejection_rate`

The committed suite automatically fails any expected non-`MATCH` case that
emits a trusted route or safe-edit path. Production write attempts, final
edits, wrong-edit counts, and boundary violations remain live-run metrics and
must be measured with the benchmark worktree audit.
