# Build Week Testing

## Baseline

At commit `a01d26bb9843252856f7fd2b952943c687d17641`, before Guarded Codex
Run implementation:

- 97 unit tests passed.
- `python -m compileall -q src tests` passed.
- Blueprint validation passed.
- Agent-map validation passed.
- Grounded diagnostics passed.
- Agent utility passed 18 of 18 cases.
- Atlas quality validation passed.

## Focused Fake-Codex Coverage

`tests/test_codex_run.py` covers:

- `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, `UNCERTAIN`, and `DISABLED`
  sandbox mapping.
- Inability to raise a non-`MATCH` decision to writable.
- Dirty preview success and dirty actual-run blocking.
- Unicode, spaces, quotes, and command-injection-shaped task/root values.
- Successful `MATCH` writes within exact safe-edit boundaries.
- Read-only success for every non-`MATCH` decision.
- Unsafe paths, untracked files, renames, outside-workspace events, and
  write-then-revert attempts.
- Codex non-zero, missing executable, timeout, keyboard cancellation, malformed
  JSONL, empty JSONL, partial readable events, stderr, and last-message
  preservation.
- Schema v1 fields, status and exit-code priority, relative artifact paths, and
  deterministic injected run IDs and clocks.
- Shared route ID/fingerprint parity between run artifacts and HTML task-route
  presets.
- Context byte counts, exact single-event Codex token usage, unavailable and
  partial usage, rejection of negative token counts, and refusal to sum
  multiple usage events.
- Combined malformed JSONL and boundary violations preserve both reasons while
  failing with the contractually stronger `audit_incomplete` status.
- Single-run `tokens_saved` unavailability and the paired no-map requirement.

The viewer smoke coverage verifies the offline local-file import surface,
schema gate, route fingerprint gate, exact evidence-path mapping, overlay
legend, 5 MiB limit, and route-fragment support. Generated HTML also passes a
JavaScript syntax check. Interactive browser QA remains pending because no
controllable browser was connected during this work; no live Codex process is
needed for that future check.

The fake executable verifies Bunya-Jido's command construction, capture, policy,
and audit logic. It does not prove the behavior of a live Codex OS sandbox.

## Required Local Validation

The current CLI help was inspected on July 18, 2026. All commands and options
below are supported as written; no compatibility substitution is required.

```bash
python -m unittest -v tests.test_codex_run
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido diagnose --root . --require-grounded --json
python -m bunya_jido evaluate-agent-utility --root . --require-pass --json
python -m bunya_jido evaluate-atlas-quality --root . --require-pass --json
python -m bunya_jido check-stale --root . --git-diff "origin/main...HEAD" --require-reviewed
```

Run `bunya-jido refresh-context --root . --changed-file <path>` for every
changed file before the stale check.

## Shared Route And Receipt Slice

The strong visual submission slice was validated locally on July 19, 2026:

- A fresh Python 3.12 virtual environment installed the worktree with
  `python -m pip install -e .`.
- Focused fake-Codex suite: 15 of 15 passed.
- Full unit suite: 114 of 114 passed.
- `python -m compileall -q src tests`: passed.
- Blueprint: grounded, 15 nodes, 32 relationships, no warning or blocker.
- Agent map: 8 of 8 routes validated.
- Grounded diagnostics: passed.
- Agent utility: 20 of 20 cases passed.
- Atlas quality: passed with one explicit human-review warning and no
  deterministic warning or blocker.
- The committed demo was rebuilt; its semantic golden test and generated
  JavaScript syntax check passed.
- All 21 implementation, test, map, demo, and documentation files owned by
  this slice received a matched `refresh-context` result.
- Both the required `origin/main...HEAD` stale check and the supplemental
  working-diff stale check reported `review_recorded`.

No new CI run, live Codex run, cross-platform live behavior, or token-savings
claim is attached to this uncommitted slice. Interactive browser QA remains
pending for the reason recorded above.

## CI Incident at `b03f510`

GitHub Actions run `29635239405` failed at the `Run tests` step on Ubuntu
Python 3.10, 3.11, and 3.12, macOS Python 3.12, and Windows Python 3.12. All
five jobs reported the same two failures:

- `test_committed_self_map_and_routes_are_grounded`: the Guarded Codex Run
  route referenced ignored file `.bunya-jido/ATLAS_QUALITY_REPORT.md`.
- `test_published_demo_matches_stable_semantic_contract`: a clean rebuild
  included that missing-path warning while the committed demo, generated in a
  development worktree where the ignored file existed, did not.

A clean Python 3.12 virtual environment at `b03f510` reproduced 2 failures out
of 111 tests. A separate clean Python 3.12 environment at baseline
`a01d26bb9843252856f7fd2b952943c687d17641` passed 97 of 97 tests. This is a
Build Week regression, not a baseline failure.

The earlier local 111-of-111 result was valid only for the development
worktree state in which the ignored report existed. It was not clean-checkout
or cross-platform evidence. The corrective change removes that ignored path
from the route and adds a regression requiring safe-edit entries to resolve to
Git-tracked content.

## Stabilization Results

- A fresh Python 3.12 virtual environment installed the corrective worktree
  with `python -m pip install -e .`.
- Focused Guarded Codex Run suite: 13 of 13 passed in that environment.
- Full unit suite: 112 of 112 passed in that environment.
- `python -m compileall -q src tests`: passed.
- Blueprint: grounded, 15 nodes, 32 relationships, no warnings or blockers.
- Agent map: 8 of 8 routes validated with no warning or error.
- Grounded diagnostics: passed.
- Agent utility: 19 of 19 cases passed.
- Atlas quality: passed with one explicit human-review warning about primary
  projection choice and no deterministic warning or blocker.
- The self-map demo was rebuilt and its semantic golden test passed.
- Guarded preview reported `MATCH`, `workspace-write`,
  `execpolicy_rules_ignored=true`, `web_search_mode=disabled`, workspace
  network `false`, and `launched=false`.
- Every changed implementation, test, map, and documentation file received a
  matched `refresh-context` route after normalizing the Build Week
  documentation scope to the declared directory `docs/build-week/`.
- The required `origin/main...HEAD` stale-map check and a supplemental
  working-diff stale-map check both reported `review_recorded`.
- Corrective cross-platform CI:
  [run `29641266678`](https://github.com/jeong87/Bunya-Jido/actions/runs/29641266678)
  completed successfully at
  `f10182c97d5f139703063ad60876c3ccb9d64547`.
- Successful jobs: Ubuntu Python 3.10, 3.11, and 3.12; macOS Python 3.12;
  Windows Python 3.12; and semantic-map review.
- A disposable clean clone at corrective commit
  `3544c198f7c1279fb96084790f109cd5ac38b34b` passed the documented preview and
  live read-only smoke.
- Cross-platform success is limited to the fake-executable and repository
  validation exercised by that CI matrix. It is not cross-platform live Codex
  sandbox evidence.
- Live nested Codex validation: one explicitly approved read-only smoke
  succeeded; details and limitations are recorded below.
- The fake executable verifies Bunya-Jido's command construction, capture,
  policy, and audit logic. It does not prove the behavior of a live Codex OS
  sandbox.

## Disposable Live Smoke Protocol

This protocol was approved and run once on July 18, 2026. Future live runs
still require a new product-owner approval. Use a disposable clean clone, a
separately installed and authenticated Codex CLI, and the exact corrective
commit selected for submission.

1. Clone the approved `build-week-2026` revision into a temporary directory,
   install it with `python -m pip install -e .`, and confirm
   `git status --porcelain` is empty.
2. Run preview with the bounded out-of-scope task below and confirm the decision
   is `OUT_OF_SCOPE`, the sandbox is `read-only`, and execution is not launched:

   ```bash
   python -m bunya_jido codex-run --root . --task "Add a native iOS app with App Store signing." --preview --json
   ```

3. Only after immediate human approval, run the same command without
   `--preview`. Do not add a sandbox override, network flag, dirty-worktree
   bypass, or arbitrary Codex argument.
4. Confirm the final Git audit reports no production changes or write attempts.
   Remove the disposable clone after preserving the reviewed run artifacts.

Expected `.bunya-jido/runs/<run-id>/` artifacts are `run.json`, `report.md`,
`events.jsonl`, `stderr.log`, and `last-message.txt`. For a successful smoke,
`run.json` should record schema `bunya-jido-codex-run-v1`, decision
`OUT_OF_SCOPE`, sandbox `read-only`, `web_search_mode` `disabled`,
`execpolicy_rules_ignored` `true`, `workspace_network_access` `false`, a
launched process with return code `0`, complete JSONL, no production boundary
violation, status `succeeded`, and exit code `0`.

One successful smoke is evidence for the observed installed Codex version and
that disposable environment only. It is not an exhaustive safety,
cross-platform, or workspace-write proof.

## Approved Live Smoke Result

- Date: July 18, 2026.
- Source commit: `3544c198f7c1279fb96084790f109cd5ac38b34b`.
- Environment: disposable clean Windows clone, Python 3.12, Codex CLI
  `0.144.5`.
- Run ID: `20260718T103801Z-8885b3dd`.
- Task decision: `OUT_OF_SCOPE`.
- Codex sandbox: `read-only`.
- Invocation controls: approval `never`, user config ignored, user/project
  execpolicy rules ignored, web search `disabled`, workspace-shell network
  `false`, ephemeral JSONL execution.
- Process: launched, return code `0`, no timeout or cancellation.
- Audit: four valid JSONL events, complete stream, production-clean worktree,
  no production write attempts, outside-workspace attempts, or boundary
  violations.
- Result: schema `bunya-jido-codex-run-v1`, status `succeeded`, exit code `0`,
  and all five expected artifacts present.
- Artifact hashes:
  - `run.json`:
    `ca8f9826ff19a8807e2a99b4baec9b8817373560c0931154b0559f60f729f3e3`
  - `events.jsonl`:
    `992f3027e4efa261d44f753f51bd32e0fea9761ec3d55c45c293dfe66c9e1245`
  - `last-message.txt`:
    `fb7329f9552e81e859166b18f21cfbf41d07d928b118f14fe0cca000e7e52425`
- Stderr contained one non-fatal Codex warning that PowerShell shell snapshots
  are not yet supported. It did not change the return code, JSONL
  completeness, worktree audit, or boundary result.

The live process returned the reviewed repository-boundary explanation and
made no file changes. This result validates only the observed read-only path
for the versions and environment above. It does not prove `workspace-write`
enforcement, other operating systems, other Codex versions, performance, or
the model identity used by the provider.
