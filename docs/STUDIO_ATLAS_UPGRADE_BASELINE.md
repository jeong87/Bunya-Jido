# Studio Atlas Upgrade Baseline

This baseline locks the public `main` behavior before the opt-in Studio prompt
pipeline is introduced. It is intentionally about existing v1 behavior; it
does not claim Studio blueprint or viewer support yet.

## Baseline Commit

- Date: 2026-05-29
- Commit: `c7468d3` (`feat: evaluate bounded agent context utility`)
- Package version: `0.3.1`
- Authored blueprint schema: `bunya-jido-blueprint-v1`

## Verification Run

The following checks passed before Phase 1 source edits:

```bash
python -m unittest discover -s tests
python -m compileall -q src tests
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido diagnose --root . --require-grounded --json
python -m bunya_jido evaluate-agent-utility --root . --require-pass --json
python -m bunya_jido build --root . --out <temporary-html> --write-json <temporary-json>
```

Results:

| Contract | Baseline result |
|---|---|
| Unit tests | 43 passed |
| Semantic blueprint | grounded, 12 authored nodes, 19 authored edges |
| Core/critical grounding | 100% / 100% |
| Agent routes | 3 / 3 validated |
| Agent utility suite | 5 / 5 passed |
| Render payload | `bunya-jido-v1`, semantic blueprint, grounded |
| Render payload size | 24 nodes, 19 edges, 12 path presets |
| Rendered task-route presets | 3 |

The difference between authored and rendered node counts is existing behavior:
the semantic render currently permits detected API/provider overlay nodes from
the static scan. Studio design must decide explicitly whether those overlays
belong in its primary projection.

## Regression Contract

Until a later phase deliberately changes these contracts:

- Default `bunya-jido prepare` remains the classic v1 authoring path.
- Existing v1 blueprint build, validation, context output, and viewer output
  continue to work without requiring Studio artifacts.
- Studio preparation is opt-in and must not imply v2 publication support until
  v2 validation and rendering are implemented.
- Agent utility and stale-map review gates remain part of release readiness.
