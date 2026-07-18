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

```bash
python -m unittest -v tests.test_codex_run
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m bunya_jido validate --root . --blueprint bunya-jido.blueprint.json
python -m bunya_jido validate-agent-map --root . --map .bunya-jido/AGENT_MAP.json
python -m bunya_jido diagnose --root . --require-grounded
python -m bunya_jido evaluate-agent-utility --root . --require-pass
python -m bunya_jido evaluate-atlas-quality --root . --require-pass
bunya-jido check-stale --root . --git-diff --require-reviewed
```

Run `bunya-jido refresh-context --root . --changed-file <path>` for every
changed file before the stale check.

## Current Results

- Focused Guarded Codex Run suite: 13 of 13 passed.
- Compileall after focused implementation: passed.
- Full unit suite: 111 of 111 passed.
- Blueprint: grounded, 15 nodes, 32 relationships, no warnings or blockers.
- Agent map: 8 of 8 routes validated.
- Agent utility: 19 of 19 cases passed.
- Atlas quality: passed; the primary-projection choice remains an explicit
  human review item rather than a deterministic claim.
- Cross-platform Windows, macOS, and Ubuntu fake-executable coverage: delegated
  to the existing CI matrix; not claimed from this single local Windows run.
- Live nested Codex validation: not run; explicit human approval is pending.
- Updated 1440 x 900 self-map capture: not produced because no browser was
  connected during this run; the regenerated `docs/demo.html` passed its
  semantic golden test and the previous capture remains preserved.
