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
- Interpretation: The owner's numbered response `4. 간결한 계약` was treated as
  the third decision question's compact result-contract option.
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
  service, web-search enablement, or workspace-shell network permission.
- Human owner: Product owner.
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
