# Bunya-Jido Components: Repotlas Self-Map

This curated input records the architecture used by the committed grounded
self-map. The JSON blueprint is the machine-readable artifact; this document
keeps the review rationale visible beside it.

## Entry And Projection

### CLI

- **Plane:** entry
- **Role:** Parses user commands and chooses scanning, semantic rendering, validation, context generation, benchmark audit, or token/time-efficiency reporting.
- **Evidence:** `src/bunya_jido/cli.py`
- **Boundary:** It coordinates publication, but does not define grounding policy.

### Semantic Blueprint Pipeline

- **Plane:** semantic
- **Role:** Loads semantic inputs, applies publication rules, preserves Studio editorial decision records, converts them to the viewer graph, and projects validated task routes with optional Studio reading context.
- **Evidence:** `src/bunya_jido/blueprint.py`
- **Boundary:** It can publish only evidence-linked core claims and trusted task routes.

### Renderer And Viewer

- **Plane:** presentation
- **Role:** Embeds the graph payload into an offline HTML viewer and presents human-first repository orientation, an accessible outline, semantic inspector context, trust, evidence, projection presets, policy-qualified narrated scenarios, and copyable validated agent-route context.
- **Evidence:** `src/bunya_jido/render.py`, `src/bunya_jido/viewer/index.template.html`
- **Boundary:** Presentation consumes the semantic contract and may clarify direction or reading order, but it is not evidence itself and must not reinterpret authored meaning.

## Analysis And Trust

### Static Scanner

- **Plane:** analysis
- **Role:** Builds deterministic scan graphs, marks provider-hint origin and type, excludes generated prompt/schema/template example pollution, and supplies supporting observations to semantic generation.
- **Evidence:** `src/bunya_jido/scanner.py`
- **Boundary:** A static scan is useful context, not a grounded semantic blueprint; source/config hints remain contextual evidence, not primary authored landmarks.

### Grounding Gate And Agent Routes

- **Plane:** quality / semantic
- **Role:** Enforces core-node and critical-edge evidence, checks Studio decision-record consistency, validates task route references including optional projection and scenario context, and blocks untrusted context.
- **Evidence:** `src/bunya_jido/blueprint.py`, `tests/test_blueprint.py`
- **Boundary:** A route is trusted only after its nodes, workflow, required reading, tests, and any published Studio context references resolve.

### Trusted Context Decision Router

- **Plane:** semantic
- **Role:** Classifies context requests as `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, or `UNCERTAIN`, recovers routes only from independent positive evidence, and emits compact selected-route guidance or capped evidence-backed discovery.
- **Evidence:** `src/bunya_jido/blueprint.py`, `src/bunya_jido/cli.py`, `tests/test_blueprint.py`, `.bunya-jido/bunya-jido.agent-evaluation.json`
- **Boundary:** Non-`MATCH` decisions do not expose trusted routes or safe-edit paths; only `IN_SCOPE_NO_ROUTE` may expose bounded read-only discovery, while `OUT_OF_SCOPE` and `UNCERTAIN` remain route-free.

### Atlas Quality Evaluator

- **Plane:** quality
- **Role:** Measures first-read burden and scenario narration honesty, exposes review-required signals separately from blockers, and optionally writes a maintainer-readable quality report.
- **Evidence:** `src/bunya_jido/quality.py`, `src/bunya_jido/cli.py`, `tests/test_projection_quality.py`
- **Boundary:** It may detect narration that deserves review, but it does not prove the best editorial explanation or block solely on that judgment.

## Verification And Documentation

### Contract Tests And CI

- **Plane:** quality
- **Role:** Characterize the trust contract, benchmark evidence reporting, Studio benchmark variety, and offline viewer surface for supported Python versions.
- **Evidence:** `tests/test_blueprint.py`, `tests/test_benchmark_audit.py`, `tests/test_studio_benchmark.py`, `.github/workflows/ci.yml`

### Benchmark Evidence Suite

- **Plane:** quality
- **Role:** Checks that different repository shapes yield distinct projections and that live benchmark token/time claims use auditable workspace truth and explicitly paired safe-and-resolved runs.
- **Evidence:** `src/bunya_jido/benchmark.py`, `tests/test_benchmark_audit.py`, `tests/fixtures/studio_benchmark_cases.json`, `tests/test_studio_benchmark.py`, `docs/BENCHMARK_RESULT_CONTRACT.md`, `docs/STUDIO_BENCHMARK.md`
- **Boundary:** It keeps unsafe, unresolved, and infrastructure-invalid runs visible but excludes them from savings claims; timing reports measure supplied evidence without tuning routing from synthetic scenarios, and Studio fixtures still do not prove an editorial reading is uniquely best.

### Public Narrative And Roadmap

- **Plane:** docs
- **Role:** State the product position, limitations, and implementation milestones.
- **Evidence:** `README.md`, `docs/CONTRIBUTION_PLAN.md`
