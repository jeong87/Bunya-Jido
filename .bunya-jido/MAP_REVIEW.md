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
