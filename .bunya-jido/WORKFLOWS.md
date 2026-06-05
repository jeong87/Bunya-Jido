# Bunya-Jido Workflows: Repotlas Self-Map

These paths explain the workflows encoded in
`bunya-jido.blueprint.json`. Each path uses repository evidence and is
designed to be reviewable in the generated HTML map.

## Static Evidence Discovery

1. `src/bunya_jido/scanner.py` collects source, configuration, artifact, and limited client-surface evidence.
2. Provider/API hints receive `hint_origin` and `hint_type` metadata, while generated prompt/schema/template example text is not emitted as provider evidence.
3. `src/bunya_jido/blueprint.py` may carry only admissible contextual overlay nodes into a Studio atlas; authored projections remain primary.

## Semantic Map Publication

1. `src/bunya_jido/cli.py` accepts a build request.
2. `src/bunya_jido/blueprint.py` loads a blueprint and applies the grounding gate.
3. `src/bunya_jido/render.py` embeds a publishable Studio graph payload.
4. `src/bunya_jido/viewer/index.template.html` exposes a human-first repository summary and outline, semantic inspector context, trust status, evidence, projection selection, directional path cues, and qualified scenario playback.

## Task Route Publication

1. The CLI requests a semantic build.
2. The blueprint pipeline validates agent-map references, including optional Studio projection and scenario context, against the grounded map.
3. Only validated task routes are projected to the HTML viewer as path presets and copyable coding-agent context.

## Trusted Context Generation

1. The CLI accepts a context request.
2. The context generator validates the grounded blueprint and agent-map routes.
3. It checks reviewed repository scope and route negative boundaries before candidate retrieval.
4. Conservative exact-term matching and route separation produce `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, or `UNCERTAIN`.
5. Only `MATCH` emits bounded navigation guidance and safe-edit paths; other decisions remain route-free, with `OUT_OF_SCOPE` and `UNCERTAIN` marked read-only.
6. The CLI can emit either the human-readable Markdown handoff or a machine-readable `context --json` decision report.

## Continuous Contract Check

1. GitHub Actions installs the project for each supported Python version.
2. The test suite verifies semantic grounding, route parity, multi-domain Studio variety, and representative output behavior.

## Atlas Quality Evaluation

1. The CLI validates a Studio v2 blueprint and gathers objective overview metrics.
2. `src/bunya_jido/quality.py` reports density, label burden, and misleading scenario-narration signals separately from human editorial review.
3. On request, the CLI writes `.bunya-jido/ATLAS_QUALITY_REPORT.md` as a local review summary without changing the publication gate.

## Studio Benchmark Review

1. `tests/fixtures/studio_benchmark_cases.json` declares differing repository-shape rubrics.
2. `tests/test_studio_benchmark.py` builds compact v2 atlas outputs, validates them, and renders each through the offline viewer.
3. `docs/STUDIO_BENCHMARK.md` records that complex external repositories are review targets rather than taxonomy seeds.
