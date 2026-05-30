# Bunya-Jido Components: Repotlas Self-Map

This curated input records the architecture used by the committed grounded
self-map. The JSON blueprint is the machine-readable artifact; this document
keeps the review rationale visible beside it.

## Entry And Projection

### CLI

- **Plane:** entry
- **Role:** Parses user commands and chooses scanning, semantic rendering, validation, or context generation.
- **Evidence:** `src/bunya_jido/cli.py`
- **Boundary:** It coordinates publication, but does not define grounding policy.

### Semantic Blueprint Pipeline

- **Plane:** semantic
- **Role:** Loads semantic inputs, applies publication rules, converts them to the viewer graph, and projects task routes and Studio atlas metadata.
- **Evidence:** `src/bunya_jido/blueprint.py`
- **Boundary:** It can publish only evidence-linked core claims and trusted task routes.

### Renderer And Viewer

- **Plane:** presentation
- **Role:** Embeds the graph payload into an offline HTML viewer and presents trust, evidence, projection presets, and policy-qualified narrated scenarios.
- **Evidence:** `src/bunya_jido/render.py`, `src/bunya_jido/viewer/index.template.html`
- **Boundary:** Presentation consumes the semantic contract; it is not evidence itself.

## Analysis And Trust

### Static Scanner

- **Plane:** analysis
- **Role:** Builds deterministic scan graphs and supplies supporting repository observations to semantic generation.
- **Evidence:** `src/bunya_jido/scanner.py`
- **Boundary:** A static scan is useful context, not a grounded semantic blueprint.

### Grounding Gate And Agent Routes

- **Plane:** quality / semantic
- **Role:** Enforces core-node and critical-edge evidence, validates task route references, and blocks untrusted context.
- **Evidence:** `src/bunya_jido/blueprint.py`, `tests/test_blueprint.py`
- **Boundary:** A route is trusted only after its nodes, workflow, required reading, and tests resolve.

## Verification And Documentation

### Contract Tests And CI

- **Plane:** quality
- **Role:** Characterize the trust contract, Studio benchmark variety, and offline viewer surface for supported Python versions.
- **Evidence:** `tests/test_blueprint.py`, `tests/test_studio_benchmark.py`, `.github/workflows/ci.yml`

### Studio Benchmark

- **Plane:** quality
- **Role:** Checks that different repository shapes yield distinct projections and honest scenario policy choices.
- **Evidence:** `tests/fixtures/studio_benchmark_cases.json`, `tests/test_studio_benchmark.py`, `docs/STUDIO_BENCHMARK.md`
- **Boundary:** It measures declared contract differences; it does not prove an editorial reading is uniquely best.

### Public Narrative And Roadmap

- **Plane:** docs
- **Role:** State the product position, limitations, and implementation milestones.
- **Evidence:** `README.md`, `docs/CONTRIBUTION_PLAN.md`
