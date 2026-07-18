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
- Corrective cross-platform CI: pending commit approval, push approval, and a
  new GitHub Actions run.
- A clean checkout of the corrective revision remains pending because that
  revision cannot exist until the commit Decision Gate is approved.
- Cross-platform success is not claimed while the latest published CI run is
  red.
- Live nested Codex validation: not run; explicit human approval is pending.
- The fake executable verifies Bunya-Jido's command construction, capture,
  policy, and audit logic. It does not prove the behavior of a live Codex OS
  sandbox.

## Disposable Live Smoke Protocol

Do not run this protocol until the product owner approves the live nested
Codex Decision Gate. Use a disposable clean clone, a separately installed and
authenticated Codex CLI, and the exact corrective commit selected for
submission.

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
