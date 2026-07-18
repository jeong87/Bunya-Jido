# Build Week Decisions

## BW-001: Public command

- Decision: Add `bunya-jido codex-run` as a public CLI command.
- Human owner: Product owner.
- Reason: Judges and users need one explicit entry point that turns context
  policy into a reviewable Codex execution.
- Deferred: Committing, pushing, tagging, releasing, and publishing.

## BW-002: Isolated implementation

- Decision: Implement orchestration in `src/bunya_jido/codex_run.py`.
- Human owner: Product owner.
- Reason: Keep process execution, JSONL parsing, boundary evaluation, and report
  rendering separate from existing context generation and worktree audit code.
- Constraint: Reuse existing context and audit contracts; add no new public
  package-level Python API.

## BW-003: Dirty-worktree policy

- Decision: Allow preview in a dirty checkout, but block actual execution before
  Codex starts.
- Human owner: Product owner.
- Reason: A clean baseline makes post-run production changes attributable while
  still allowing safe planning in an active checkout.
- Result: A dirty execution writes a blocked report and exits `2`.

## BW-004: Compact result contract

- Decision: Use schema `bunya-jido-codex-run-v1` with JSON and Markdown reports
  plus exit codes `0`, `2`, `130`, and `1`.
- Human owner: Product owner.
- Reason: Preserve enough evidence for review without introducing an HTML report
  or a larger public artifact protocol in the MVP.

## BW-005: Enforcement versus audit

- Decision: Codex's OS sandbox enforces access. Safe-edit paths are prompt
  guidance and post-run audit criteria only.
- Human owner: Product owner.
- Mapping: Only `MATCH` receives `workspace-write`; all other context decisions,
  including `DISABLED`, receive `read-only`.
- Constraint: No CLI flag may raise a non-`MATCH` decision to writable.

## BW-006: Dependency and live-run boundary

- Decision: Add no runtime dependency, telemetry, credential flow, external
  service, Codex web-search access, or workspace-shell network permission.
- Human owner: Product owner.
- Enforcement: Set `web_search="disabled"` and independently set
  `sandbox_workspace_write.network_access=false`.
- Test policy: Use fake executables by default.
- Deferred gate: One real nested Codex run requires explicit human approval
  after the fake-executable implementation and repository validation are
  complete.

## BW-007: Existing combined-focus defect

- Decision: Do not fix the baseline `--task` plus `--workflow` `strong_match`
  error in this MVP.
- Owner: Implementation boundary accepted in the approved plan.
- Reason: Guarded Codex Run does not require the combined-focus path, and fixing
  it would broaden the change beyond the agreed feature.

## BW-008: Deterministic execpolicy rules

- Decision: Pass `--ignore-rules` so Guarded Codex Run does not load user or
  trusted-project execpolicy `.rules` files.
- Human owner: Product owner.
- Reason: Local rules can restrict commands or allow matching commands outside
  the selected sandbox, making identical guarded argv behave differently in
  development and judge environments.
- Accepted tradeoff: Project-local `.rules` conventions do not apply to this
  controlled runner.
- Boundary: This decision does not claim to bypass administrator-managed
  requirements.

## BW-009: Disposable live smoke

- Decision: Run one live nested Codex smoke from a disposable clean clone after
  focused and full fake-executable validation passed.
- Human owner: Product owner.
- Scope: Exercise only the reviewed `OUT_OF_SCOPE` path with Codex
  `read-only`, approval disabled, web search disabled, workspace-shell network
  disabled, and user/project execpolicy rules ignored.
- Stop condition: Do not push if the process fails, JSONL is incomplete, the
  final worktree is not production-clean, or any write attempt or boundary
  violation is observed.
- Limitation: One Windows read-only run is not workspace-write,
  cross-platform, exhaustive sandbox, performance, or model-identity proof.
