# Bunya-Jido Map Review Log

This file records reviewed map-maintenance decisions when policy-covered
repository changes do not require rewriting the semantic structure itself.
An entry records review work; it does not prove architectural completeness.

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
