# Bunya-Jido Workflows: Repotlas Self-Map

These paths explain the workflows encoded in
`bunya-jido.blueprint.json`. Each path uses repository evidence and is
designed to be reviewable in the generated HTML map.

## Semantic Map Publication

1. `src/bunya_jido/cli.py` accepts a build request.
2. `src/bunya_jido/blueprint.py` loads a blueprint and applies the grounding gate.
3. `src/bunya_jido/render.py` embeds a publishable graph payload.
4. `src/bunya_jido/viewer/index.template.html` exposes trust status and evidence.

## Task Route Publication

1. The CLI requests a semantic build.
2. The blueprint pipeline validates agent-map references against the grounded map.
3. Only validated task routes are projected to the HTML viewer as path presets.

## Trusted Context Generation

1. The CLI accepts a context request.
2. The context generator validates the grounded blueprint.
3. It validates task routes before emitting bounded navigation guidance.

## Continuous Contract Check

1. GitHub Actions installs the project for each supported Python version.
2. The test suite verifies semantic grounding, route parity, and representative output behavior.
