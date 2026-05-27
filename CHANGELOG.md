# Changelog

Notable changes to Bunya-Jido are recorded here. The project uses semantic
versioning for its public CLI and artifact contracts while it remains in
alpha; compatibility may still change before `1.0.0`, but those changes must
be documented.

## Unreleased

### Added

- Public-alpha release preparation with PyPI Trusted Publishing and GitHub
  Pages deployment workflows.
- A `bunya-jido diagnose` command that reports actual artifact mode,
  grounding status, and validated task-route readiness, with a strict
  `--require-grounded` release gate.
- Contribution guidance and structured issue templates for changes to scanner,
  grounding, viewer, agent-context, and release contracts.
- Distribution metadata prepared for current SPDX license expression support.

### Existing Alpha Baseline

- Grounding gates and visible trust state for semantic blueprint maps.
- Validated agent-map task routes shared by HTML output and generated context.
- Grounded self-map gallery and semantic golden regression tests.
- Progressive disclosure viewer modes and semantic relation/node families.
- Measured deterministic scanner coverage matrix and committed fixtures.
