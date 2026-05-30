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
- A `bunya-jido check-stale` command, committed stale-map policy, and
  `MAP_REVIEW.md` log for requiring recorded semantic-map review when mapped
  repository surfaces change.
- A `bunya-jido evaluate-agent-utility` command, committed acceptance suite,
  and documented observation protocol for bounded agent-context utility.
- An opt-in `prepare --atlas-mode studio` authoring path that creates
  repository-thesis, projection-candidate, and scenario-policy documents.
- An additive Studio `bunya-jido-blueprint-v2` contract with validated
  repository-local vocabularies, projections, scenario policies, scenario
  references, and explicit static-provider overlay handling while classic v1
  output remains compatible.
- An `evaluate-atlas-quality` command and diagnostics summary for Studio v2
  that separate deterministic readability/scenario checks from
  review-required editorial judgment.
- Studio v2 viewer projection presets with map-local node/relation styling,
  primary-projection initial focus, and contextual direct-neighbor reveal.

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
- CI now exercises the Python CLI on Ubuntu, Windows, and macOS and applies
  the stale-map review gate to push and pull-request diffs.
- English and Korean onboarding now state installation requirements and
  platform-specific setup commands.
- CI, demo publishing, and package release checks now require the committed
  agent-utility suite to pass without claiming live-agent behavioral proof.

### Fixed

- Python 3.10 static scanning now parses `pyproject.toml` through a conditional
  `tomli` fallback, matching the advertised Python support matrix.

### Existing Alpha Baseline

- Grounding gates and visible trust state for semantic blueprint maps.
- Validated agent-map task routes shared by HTML output and generated context.
- Grounded self-map gallery and semantic golden regression tests.
- Progressive disclosure viewer modes and semantic relation/node families.
- Measured deterministic scanner coverage matrix and committed fixtures.
