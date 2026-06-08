# Bunya-Jido Map Review Log

This file records reviewed map-maintenance decisions when policy-covered
repository changes do not require rewriting the semantic structure itself.
An entry records review work; it does not prove architectural completeness.

## 2026-06-05 - P2 Normal Bugfix Recovery And Bounded Discovery

- Change: Added independent-evidence route recovery, capped evidence-backed
  `IN_SCOPE_NO_ROUTE` discovery, and deterministic normal-bugfix recovery
  metrics while preserving P1 non-MATCH route and safe-edit isolation.
- Decision: Updated the existing Trusted Context Generator, bounded-agent
  projection, workflow, scenario, and task-route contract. The change extends
  an existing context boundary and does not add a new top-level subsystem or
  alter the human-facing viewer design.
- Validation: Focused recovery/safety fixtures, external Realistic Large and
  Enterprise XLarge deterministic context replay, strict map/utility/quality
  gates, stale-map review, regenerated demo, and the full unit suite are
  required before commit.

## 2026-06-05 - Decision-Aware No-Match Rejection

- Change: Replaced permissive task substring matching with conservative
  decision-aware routing, optional reviewed repository/route boundaries,
  route-free non-MATCH output, `context --json`, and adversarial no-match
  utility cases.
- Decision: Updated the existing Trusted Context Generator, Agent Route
  Parity, bounded-navigation workflow, and scenario rather than adding a new
  top-level product subsystem. Context decisions remain part of the semantic
  agent-handoff boundary.
- Validation: Blueprint and agent-map validation, strict grounded diagnostics,
  strict agent-utility and atlas-quality evaluation, the full unit suite,
  refresh-context, and stale-map review are required.

## 2026-05-28 - PR 11.1 Portability And Stale-Map Gate

- Change: Added `check-stale`, cross-platform CI coverage, and OS-specific
  onboarding guidance.
- Decision: Added `stale_map_policy` to the agent map. Existing semantic
  nodes, workflows, and task routes remain adequate for this maintenance gate.
- Validation: `validate-blueprint`, `validate-agent-map`, strict `diagnose`,
  `check-stale --require-reviewed`, and the unit test suite passed.

## 2026-05-28 - PR 12 Agent Utility Evaluation

- Change: Added committed bounded-context evaluation cases, a strict
  `evaluate-agent-utility` command, and CI/release/documentation integration.
- Decision: This tests the existing `semantic:context` and
  `semantic:agent_map` contracts; it does not introduce a new semantic
  component or workflow, so the existing self-map structure remains adequate.
- Validation: Strict agent-utility evaluation, blueprint and agent-map
  validation, grounded diagnostics, stale-map review, and the unit test suite
  are required before commit.

## 2026-05-29 - Studio Atlas Phase 0 And Phase 1

- Change: Recorded the v1 baseline and added opt-in
  `prepare --atlas-mode studio` editorial templates and prompting while
  retaining the current v1 schema and rendering.
- Decision: This phase prepares future authored inputs but does not add a
  published semantic component, viewer path, or trusted context route.
  Existing CLI and blueprint-publication nodes remain the correct self-map
  structure until v2 publication is implemented.
- Validation: Blueprint and agent-map validation, grounded diagnostics,
  strict agent-utility evaluation, stale-map review, and the unit test suite
  are required before commit.

## 2026-05-29 - Studio Atlas Phase 2 Additive V2 Contract

- Change: Added the opt-in Studio v2 blueprint schema, deterministic atlas
  reference and scenario-policy validation, v2 graph metadata, and explicit
  provider-overlay handling.
- Decision: Updated the existing Grounding Gate and Semantic Contract Tests
  evidence plus the grounding-policy agent route because `schema.py` and
  `test_blueprint_v2.py` are now part of that published trust contract. No new
  product node is needed because v2 validation remains the same gate's
  responsibility.
- Validation: Blueprint and agent-map validation, grounded diagnostics,
  strict agent-utility evaluation, stale-map review, and the full unit test
  suite are required before commit.

## 2026-05-29 - Studio Atlas Phase 3 Quality Evaluator

- Change: Added `evaluate-atlas-quality`, Studio v2 quality metrics and
  diagnostics, and tests for density, inspector weakness, scenario gaps, and
  review-required narration judgments.
- Decision: Added the Atlas Quality Evaluator contract node, its CLI/validation
  workflow, and a bounded agent route because this is a new maintained
  publication boundary rather than an implementation detail of validation.
- Validation: Blueprint and agent-map validation, strict diagnostics and
  agent-utility evaluation, stale-map review, and the full unit test suite are
  required before commit.

## 2026-05-30 - Studio Atlas Phase 4 Viewer Projection Upgrade

- Change: Added Studio v2 projection presets, map-local node and relation
  styling, primary-projection initial focus, and contextual direct-neighbor
  reveal in the offline viewer.
- Decision: Updated the existing Blueprint Projection and Interactive Viewer
  evidence and viewer route rather than adding a new component: authored
  atlas data remains the source, while the viewer presents that data without
  asserting new evidence.
- Validation: V2/viewer regression tests, blueprint and agent-map validation,
  grounded diagnostics, agent-utility evaluation, and the stale-map review
  gate are required before commit. Visual browser inspection is attempted when
  a connected in-app browser session is available.

## 2026-05-30 - Studio Atlas Phase 5 Scenario Playback Engine

- Change: Added Studio-only scenario launching and narrated playback controls,
  animated behavioral tokens, non-directional structural highlighting, basis
  badges, and restoration of the pre-playback view state.
- Decision: Kept playback inside the existing Interactive Viewer node and
  expanded its route contract: validated atlas data remains the source of
  narration and basis claims, while the viewer only presents it.
- Validation: V2/viewer regression tests, blueprint and agent-map validation,
  grounded diagnostics, agent-utility evaluation, stale-map review, and
  available visual inspection are required before commit.

## 2026-05-30 - Studio Atlas Phase 6 Generality And Self-Map Publication

- Change: Added a six-shape Studio benchmark rubric and executable rendering
  suite, a visible label-burden diagnostic, domain-neutral Studio plane layout,
  and public documentation/release gates for atlas quality.
- Decision: Upgraded the committed Bunya-Jido self-map to Studio v2 with
  authored thesis, projections, two evidence-badged behavioral scenarios, and
  a new benchmark component and trusted rubric-maintenance route. External
  complex-workflow review remains evaluation input only, never prompt or
  viewer vocabulary.
- Validation: Blueprint and agent-map validation, strict atlas-quality and
  agent-utility evaluation, full unit tests, regenerated demo/screenshot,
  stale-map review, and visual inspection are required before commit.

## 2026-05-30 - Official Actions Node 24 Runtime Maintenance

- Change: Upgraded maintained workflow uses of checkout, Python setup, and
  release artifact transport actions to official Node.js 24-backed majors.
- Decision: This is CI and publishing runtime maintenance only. The committed
  Studio self-map structure, projections, scenarios, and trusted routes remain
  accurate, so no blueprint or agent-map rewrite is required.
- Validation: Full tests, strict semantic and atlas gates, agent-utility
  evaluation, stale-map review, and the resulting GitHub CI run are required.

## 2026-05-31 - Quick Start Studio Onboarding Placement

- Change: Moved the two-step Quick Start above the product-output description
  and embedded the full recommended Studio atlas agent prompt in both READMEs.
- Decision: This is onboarding presentation for the already published Studio
  workflow. It does not change the semantic self-map, scenarios, or routes.
- Validation: Self-map tests, strict semantic and atlas gates, agent-utility
  evaluation, and stale-map review are required before publication.

## 2026-05-31 - Coding-Agent-Native Atlas N1 Prompt Contract

- Change: Fixed the Studio scenario basis template drift, added a generated
  `ATLAS_INTERVIEW.md` internal checklist, strengthened Studio prompting with
  role passes and the atlas-quality gate, and aligned both READMEs.
- Decision: This expands authoring guidance within the existing Semantic
  Blueprint Pipeline; it does not introduce a new published node, viewer path,
  scenario, or trusted task route, so the current self-map remains accurate.
- Validation: Blueprint and agent-map validation, grounded diagnostics, strict
  atlas-quality and agent-utility evaluation, and all 65 unit tests passed.

## 2026-05-31 - Coding-Agent-Native Atlas N2 Decision Record

- Change: Added optional Studio v2 `atlas.decision_record`, consistency checks
  for published projection and scenario selections, an editorial-review signal
  for older maps that omit it, and aligned prompts, benchmarks, docs, and the
  committed self-map.
- Decision: This extends the existing Blueprint Projection, Grounding Gate,
  and Atlas Quality Evaluator contracts; no new map node or trusted route is
  introduced. The self-map now records its own primary projection and scenario
  rationale.
- Validation: Blueprint and agent-map validation, grounded diagnostics, strict
  atlas-quality and agent-utility evaluation, rebuilt committed demo,
  stale-map review, and the full unit suite are required before commit.

## 2026-05-31 - Coding-Agent-Native Atlas N3 Quality Reporting

- Change: Added narration-honesty and readability review diagnostics, additive
  atlas-quality review summary fields, and optional local
  `ATLAS_QUALITY_REPORT.md` output.
- Decision: This extends the existing Atlas Quality Evaluator contract rather
  than creating a new semantic component or route. Review-only findings remain
  separate from deterministic blockers and do not change `--require-pass`.
- Validation: Blueprint and agent-map validation, grounded diagnostics, strict
  atlas-quality and agent-utility evaluation, rebuilt committed demo,
  stale-map review, and the full unit suite are required before commit.

## 2026-05-31 - Coding-Agent-Native Atlas N4 Agent Reading Context

- Change: Added optional validated `projection_context` and
  `scenario_context` task-route references, bounded CLI context that explains
  route reading context and start-node responsibility, and viewer actions for
  related trusted routes and copyable coding-agent context.
- Decision: This extends the existing Agent Route Parity, Trusted Context
  Generator, and Interactive Viewer contracts. Only references already
  validated against the published Studio atlas can reach either output.
- Validation: Blueprint and agent-map validation, grounded diagnostics, strict
  atlas-quality and agent-utility evaluation, rebuilt committed demo,
  stale-map review, and the full unit suite are required before commit.

## 2026-05-31 - Coding-Agent-Native Atlas N5 Provenance And Gallery

- Change: Added provider-hint provenance metadata and generated-example
  suppression, a trusted scanner-provenance route, and an evidence-backed
  curated coverage-fixture Studio gallery item with published HTML and screenshot review.
- Decision: Provider/API hints remain contextual scanner observations. They
  cannot become authored primary landmarks merely because prompt, schema, or
  template text mentions a provider. The curated miniature demonstrates an
  honest `none_with_reason` reading distinct from this repository's behavioral
  self-map.
- Validation: Scanner coverage, Studio and gallery regression tests, blueprint
  and agent-map validation, grounded diagnostics, strict atlas-quality and
  agent-utility evaluation, rebuilt gallery/demo outputs, and stale-map review
  are required before commit.

## 2026-06-01 - README Hero Self-Map Capture Refresh

- Change: Regenerated `docs/assets/self-map-grounded.png` from the committed
  `docs/demo.html` overview after the N3-N5 self-map upgrades.
- Decision: This corrects a stale published screenshot that still displayed
  `5/5 routes`; it does not change the semantic blueprint, agent routes, or
  atlas interpretation. The refreshed image now shows the validated `6/6`
  trusted routes and current workflow surface.
- Validation: Confirm the demo remains generated from the committed grounded
  self-map, visually inspect the refreshed 1440 x 900 overview capture, and
  rerun blueprint, agent-map, utility, quality, stale-map, and unit checks.

## 2026-06-01 - Coding-Agent-Native Atlas N5 Published Domain Gallery

- Change: Added evidence-backed Studio miniatures for SDK/client, web-state,
  compiler/parser, and utility-library readings with generated HTML outputs
  and reviewed 1440 x 900 captures.
- Decision: These examples complete the roadmap's real-gallery proof without
  changing Bunya-Jido's self-map structure. They preserve distinct scenario
  choices: structural SDK reading, grounded behavioral UI/compiler paths, and
  utility output with no invented lifecycle.
- Validation: Each miniature must pass blueprint and atlas-quality validation,
  published HTML and PNG contracts are checked by `tests/test_gallery.py`, and
  the repository's full trust and stale-map gates remain required.

## 2026-06-05 - Human-First Viewer Orientation

- Change: Preserved the existing canvas-first constellation design while
  adding a repository summary and guided-tour entry, a keyboard-accessible
  outline, semantic inspector cards, directional relation cues, numbered
  workflow landmarks, and narrow-screen overflow handling.
- Decision: This extends the existing Interactive Viewer and Semantic Map
  Publication contracts. It does not add a new semantic component or allow the
  presentation layer to reinterpret evidence; every new human-facing detail is
  projected from existing published graph data.
- Validation: Viewer and Studio regression tests, blueprint and agent-map
  validation, grounded diagnostics, strict atlas-quality and agent-utility
  evaluation, rebuilt committed demo and hero capture, stale-map review, and
  the full unit suite are required before commit.

## 2026-06-05 - Scenario Surface Layer Ordering

- Change: Moved the scenario menu, narration, and playback controls above the
  selected-node Inspector while keeping them below the main toolbar.
- Decision: This is a presentation-layer bug fix within the existing
  Interactive Viewer contract. It does not change self-map structure,
  scenario meaning, or evidence.
- Validation: The viewer regression test asserts `drawer < scenario <
  toolbar`, and the committed self-map demo and hero capture are regenerated
  before the full repository checks.

## 2026-06-05 - Published Demo Delivery And Version Alignment

- Change: Advanced the compatible viewer release to `0.4.0`, added a regression
  check that package version declarations stay aligned, and made reviewed
  `docs/` changes deploy to GitHub Pages automatically when they reach `main`.
- Decision: This changes delivery of the existing reviewed Semantic Map
  Publication artifact, not its structure or evidence. Pages still publishes
  only the committed `docs/` artifact after the existing trust gates pass.
- Validation: Version alignment and Pages trigger regression tests, rebuilt
  committed demo, stale-map review, release gates, and the full unit suite are
  required before merge to `main`.

## 2026-06-05 - 0.5 Trust-Preserving Recall Recovery Plan

- Change: Added the proposed `0.5` update plan with ordered runner-correctness,
  no-match safety, normal-bugfix recovery, token-efficiency, and resolution-time
  gates.
- Decision: This is a planning and acceptance-contract document only. It does
  not change the current semantic map, context decision behavior, trusted
  routes, or viewer output.
- Validation: Review the plan against the current context-decision
  implementation and updated-map revalidation report, then run stale-map
  review to record that no current structure changed.

## 2026-06-05 - P0 Benchmark Worktree Truth

- Change: Added a reusable benchmark worktree audit API and CLI, fixture tests,
  and a runner integration contract that detect tracked, staged, deleted,
  renamed, untracked, and JSONL-observed write activity.
- Decision: This extends quality evaluation support around live-agent
  benchmarks. It does not change the semantic blueprint, trusted task routes,
  context decisions, or human-facing map, so no self-map structure update is
  required.
- Validation: Run the benchmark-audit fixtures, CLI smoke checks, full unit
  suite, blueprint and agent-map validation, strict utility and atlas-quality
  evaluation, stale-map review, and local Realistic Large/Enterprise XLarge
  runner mock smoke runs before commit.

## 2026-06-05 - P1 No-Match Safety Lock

- Change: Added machine-readable context execution policies, decision-specific
  agent instructions, non-MATCH safe-edit suppression, deterministic decision
  confusion and safety metrics, and a mixed-boundary acceptance case.
- Decision: This strengthens the existing Agent Route Parity and bounded
  context safety contract without changing matcher thresholds, trusted route
  definitions, semantic blueprint structure, or human-facing HTML output.
- Validation: Regenerate the managed Codex activation block, run context and
  utility P1 fixtures, validate the blueprint and agent map, pass grounded,
  atlas-quality, utility, stale-map, and full unit-suite gates, then locally
  smoke-test sandbox policy integration in the external benchmark runners.

## 2026-06-08 - P0 Generated Noise Classifier

- Change: Hardened benchmark worktree auditing so common generated/cache noise
  is classified separately from production changes and JSONL production write
  attempts.
- Decision: This is a Benchmark Evidence Suite contract refinement. It keeps
  the existing benchmark route, semantic blueprint structure, context decision
  behavior, and viewer output unchanged. Runner artifacts still require
  explicit allowlist globs, and `.gitignore` is not used as a blanket
  exemption.
- Validation: Run benchmark-audit fixtures, refresh-context, stale-map review,
  blueprint and agent-map validation, utility and atlas-quality gates, and the
  full unit suite before commit.

## 2026-06-08 - Runner Sandbox Policy Field

- Change: Added a machine-readable `codex_sandbox_mode` to context selection,
  JSON context reports, and Markdown context output.
- Decision: This hardens runner integration against Markdown backtick parsing
  errors without changing trusted route definitions, route matching,
  publication structure, or viewer output. `MATCH` maps to `workspace-write`;
  every non-MATCH decision maps to `read-only`.
- Validation: Run context/report focused tests, refresh-context, stale-map
  review, blueprint and agent-map validation, utility and atlas-quality gates,
  and the full unit suite before commit.

## 2026-06-08 - Bounded Discovery Route Metadata

- Change: Added validated route metadata fields for trigger phrases, failure
  symptoms, and domain entities, and exposed matching weak-route hints in
  capped `IN_SCOPE_NO_ROUTE` discovery output.
- Decision: This strengthens the existing bounded agent-context projection. It
  does not change semantic map structure, viewer output, or safe-edit
  boundaries; metadata hints remain read-only discovery signals and cannot
  confirm a trusted route without independent route evidence.
- Validation: Run focused route-selection/discovery tests, refresh-context,
  stale-map review, blueprint and agent-map validation, utility and
  atlas-quality gates, and the full unit suite before commit.

## 2026-06-08 - Benchmark Provenance Fields

- Change: Added benchmark audit provenance for Bunya-Jido version output, git
  commit SHA, and the agent-map file SHA-256 when present.
- Decision: This strengthens the Benchmark Evidence Suite contract and raw
  runner result traceability. It does not change route selection, semantic map
  structure, viewer output, or benchmark scoring.
- Validation: Run benchmark audit fixtures, version-alignment smoke test,
  refresh-context, stale-map review, blueprint and agent-map validation,
  utility and atlas-quality gates, and the full unit suite before commit.

## 2026-06-05 - P3 Compact Context And Token Evidence

- Change: Made task-selected Markdown and JSON context compact by default,
  retained full diagnostics behind `--verbose`, added deterministic
  context-size estimates, and added safe-and-resolved benchmark token
  reporting with medians and break-even counts.
- Decision: Broadened the existing Benchmark Evidence Suite responsibility,
  added the `benchmark_evidence_reporting` workflow and trusted maintenance
  route, and kept the existing canvas-first viewer design and node layout.
  Unsafe, unresolved, no-match-writing, and infrastructure-invalid runs remain
  visible but cannot improve token-saving claims.
- Validation: Validate the refreshed blueprint and agent map, pass compact
  context, benchmark audit, self-map, utility, atlas-quality, stale-map, and
  full unit tests, rebuild the committed demo, inspect the 1440 x 900 overview
  capture, and replay the current local XHigh-authored benchmark maps. The
  replay records compact-output reductions separately from live task tokens
  and corrects the Realistic P2 route result to 7/8 MATCH plus 1/8 bounded
  discovery. Compatible live benchmarks remain required before claiming P3
  release thresholds.

## 2026-06-06 - P4 Measurement-Only Time Evidence

- Change: Added safe-and-resolved repeated-run time reporting with explicit
  pair IDs, cumulative/median/nearest-rank-p90 metrics, context-generation and
  discovery-to-first-edit visibility, per-task comparisons, and optional
  authoring-time break-even.
- Decision: Broadened the existing Benchmark Evidence Suite and maintenance
  route to cover time evidence while explicitly forbidding synthetic benchmark
  timing from becoming route-vocabulary or matcher tuning. No context decision,
  route threshold, viewer layout, node count, or edge count changed.
- Validation: Run benchmark audit/time fixtures, the committed agent-utility
  suite, blueprint and agent-map validation, grounded/atlas/stale gates, full
  unit tests, rebuild the committed demo and clean overview capture, replay the
  current local XHigh-authored maps to verify unchanged routing decisions, and
  keep live P4 speed claims open until compatible diverse-repository and
  holdout results exist.
