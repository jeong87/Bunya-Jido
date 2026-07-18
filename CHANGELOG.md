# Changelog

Notable changes to Bunya-Jido are recorded here. The project uses semantic
versioning for its public CLI and artifact contracts while it remains in
alpha; compatibility may still change before `1.0.0`, but those changes must
be documented.

## Unreleased

### Added

- Add the public `bunya-jido codex-run` workflow with non-escalating context
  sandbox mapping, JSONL capture, post-run boundary auditing, and paired schema
  v1 JSON and Markdown reports.
- Add non-mutating preview, clean-worktree enforcement, deterministic fake-Codex
  coverage, intentional exit codes, and local run artifacts under
  `.bunya-jido/runs/`.
- Add compatible schema-v1 route and context-efficiency receipts, preserving
  actual Codex token usage only when JSONL reports it and requiring a paired
  no-map baseline before reporting savings.
- Let the offline atlas open a local `run.json` and compare the fingerprinted
  expected task route with exact evidence-linked changed paths and boundary
  violations.

### Fixed

- Make clean checkouts validate identically to development worktrees by keeping
  ignored atlas-quality output out of trusted safe-edit routes.
- Explicitly disable Codex web search independently from workspace-shell
  network access, and assert the complete guarded invocation argv.
- Ignore user and trusted-project Codex execpolicy `.rules` so the guarded
  runner's selected sandbox does not vary across local and judge environments.

## 0.5.0a2 - 2026-06-09

### Fixed

- PyPI long-description rendering now uses an absolute public URL for the
  README hero image so the package page shows the current self-map preview
  instead of a broken relative `docs/assets/` image.

## 0.5.0a1 - 2026-06-09

### Added

- A reusable `audit-worktree` API and CLI for live-agent benchmark runners
  that reports tracked, staged, deleted, renamed, untracked, and explicitly
  allowed artifact changes, plus Codex JSONL file-change attempts and
  incomplete-log evidence.
- P0 runner-correctness fixtures and a benchmark result contract covering
  clean-baseline enforcement and write-then-revert detection.
- An additive context `execution_policy` and decision-specific agent
  instruction for integrations, with `read_only_discovery` for initial
  in-scope route-free inspection.
- P1 decision confusion, false-route, safe-edit leak, and execution-policy
  metrics in deterministic agent-utility evaluation.
- Evidence-backed, capped `IN_SCOPE_NO_ROUTE` discovery with likely areas,
  first reads, likely tests, read-only search commands, and context recheck
  commands.
- Optional bounded-discovery route metadata for trigger phrases, failure
  symptoms, and domain entities without treating those hints as trusted-route
  confirmation by themselves.
- P2 trusted-route recall, bounded-discovery coverage, actionable-guidance
  coverage, and normal-bugfix hard-rejection metrics.
- Compact-by-default Markdown and JSON context output with `--verbose`
  diagnostic compatibility, plus deterministic context-size estimates in
  agent-utility evaluation.
- A `summarize-token-efficiency` API and CLI that reports context, repair,
  no-match, safe-and-resolved, map-authoring, median, and break-even token
  measures while excluding unsafe, unresolved, and infrastructure-invalid
  runs from savings claims.
- A measurement-only `summarize-time-efficiency` API and CLI with explicit
  repeated-run pairing, cumulative/median/nearest-rank-p90 timing,
  context-generation and discovery-to-first-edit visibility, per-task
  comparisons, and optional authoring-time break-even reporting.
- Benchmark audit provenance fields for the Bunya-Jido version output, git
  commit SHA, and agent-map file SHA-256 so raw runner results identify
  the exact map and package under test.
- Runtime context opt-out with `BUNYA_JIDO_CONTEXT=off` or
  `BUNYA_JIDO_DISABLE_CONTEXT=1`, returning `DISABLED` read-only context with
  no trusted routes or safe-edit paths.
- Persistent native activation deactivation via
  `install-agent-guides --deactivate`, removing only managed Bunya-Jido blocks
  while preserving user-authored project instructions.

### Fixed

- Benchmark workspace auditing no longer relies on tracked `git diff`
  output alone, preventing untracked production files from being silently
  counted as edit-free runs.
- Benchmark workspace auditing now classifies common generated/cache noise
  separately from production changes, so files such as Python bytecode caches,
  test caches, coverage output, and OS/editor temp files do not create false
  no-match production-edit failures.
- Non-`MATCH` context and read-only route catalogs no longer expose safe-edit
  paths, and committed no-match acceptance cases fail on any trusted-route or
  safe-edit leak.
- Normal bugfix routing now recovers from independent explicit, failure-mode,
  route-specific node, and workflow evidence without allowing a failure mode
  or shared-workflow term to select a route alone.
- `IN_SCOPE_NO_ROUTE` can surface weak-route domain and symptom hints for
  read-only discovery while keeping trusted route and safe-edit output
  suppressed.
- Default task context no longer repeats diagnostic scores, route evidence,
  start-node identifiers, generated-doc references, or full discovery
  evidence when the compact handoff already carries the actionable contract.

## 0.4.0 - 2026-06-05

### Added

- Human-first map orientation with a repository summary, guided-tour entry,
  keyboard-accessible repository outline, and semantic inspector cards for
  authored purpose, inputs, outputs, and constraints.
- Decision-aware context routing with `MATCH`, `IN_SCOPE_NO_ROUTE`,
  `OUT_OF_SCOPE`, and `UNCERTAIN`, optional reviewed repository/route
  boundaries, and machine-readable `bunya-jido context --json` output.
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
- Studio v2 narrated scenario playback with basis badges, animated behavioral
  paths, non-directional structural tours, and restored pre-playback view state.
- A multi-domain Studio benchmark rubric and executable rendering suite that
  distinguishes behavioral, structural-tour, and no-scenario repositories
  without seeding prompts from an external complex-system example.
- An optional Studio v2 `atlas.decision_record` contract that retains
  projection/scenario alternatives and over-centralization risks while
  detecting contradictions with the published primary projection.
- Additive Studio atlas-quality review reporting for misleading narration,
  weak playback readability, and missing primary landmarks, plus opt-in
  `.bunya-jido/ATLAS_QUALITY_REPORT.md` output without changing the
  deterministic `--require-pass` gate.
- Optional validated Studio `projection_context` and `scenario_context`
  references on task routes, with bounded CLI orientation and viewer-side
  copying of related trusted coding-agent context.
- Provenance-tagged provider/API hints that suppress generated prompt/schema
  example pollution from Studio overlays, plus a published evidence-backed
  coverage-fixture gallery atlas with an honest `none_with_reason` policy.
- Evidence-backed gallery miniatures for SDK/client, web-state,
  compiler/parser, and utility-library readings, each with a reviewed Studio
  HTML output and screenshot regression surface.

### Changed

- The existing constellation viewer now adds subtle relationship direction,
  numbered workflow landmarks, current-path HUD context, and narrow-screen
  overflow handling without replacing its visual design.
- Natural-language task matching now uses conservative exact meaningful terms,
  explicit route-use phrases, route separation, and scope-sensitive rejection;
  non-`MATCH` decisions expose neither trusted routes nor safe-edit paths.
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
- Maintained workflows use current official Node.js 24-backed checkout,
  Python setup, and release artifact actions where supported.
- GitHub Pages now deploys validated committed `docs/` changes automatically
  when they reach `main`, while retaining manual workflow dispatch.
- The committed Bunya-Jido self-map now publishes a grounded Studio v2 atlas
  with authored projections and evidence-badged scenarios; Studio layout
  derives its planes from authored data rather than domain-specific defaults.

### Fixed

- Scenario menus, narration, and playback controls now remain visible above an
  open selected-node Inspector while staying below the main toolbar.
- Python 3.10 static scanning now parses `pyproject.toml` through a conditional
  `tomli` fallback, matching the advertised Python support matrix.

### Existing Alpha Baseline

- Grounding gates and visible trust state for semantic blueprint maps.
- Validated agent-map task routes shared by HTML output and generated context.
- Grounded self-map gallery and semantic golden regression tests.
- Progressive disclosure viewer modes and semantic relation/node families.
- Measured deterministic scanner coverage matrix and committed fixtures.
