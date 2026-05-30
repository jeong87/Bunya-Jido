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
