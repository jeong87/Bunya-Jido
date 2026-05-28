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

### Changed

- A canvas-first constellation viewer design with semantic role glyphs,
  streamlined workflow access, and a refreshed grounded self-map preview.
- Agent context selects only routes that match the requested task or explicit
  focus, and reports an unmatched request instead of presenting unrelated
  guidance.
- Agent guidance can be activated in Codex, Claude Code, Cursor, and Cline
  project instruction files through preserved managed blocks with dry-run
  previews.
- `refresh-context` now recommends only routes justified by supplied changed
  files, reports the matching path or grounded start-node evidence, and
  rejects refresh requests without change input.

### Fixed

- Python 3.10 static scanning now parses `pyproject.toml` through a conditional
  `tomli` fallback, matching the advertised Python support matrix.

### Existing Alpha Baseline

- Grounding gates and visible trust state for semantic blueprint maps.
- Validated agent-map task routes shared by HTML output and generated context.
- Grounded self-map gallery and semantic golden regression tests.
- Progressive disclosure viewer modes and semantic relation/node families.
- Measured deterministic scanner coverage matrix and committed fixtures.
