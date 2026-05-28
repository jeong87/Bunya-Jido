# Bunya-Jido Contribution Plan
## Grounded Semantic Repository Maps for Humans and Coding Agents

**Status:** Implemented grounded public-alpha roadmap with agent consumption expansion in progress
**Target repository:** `jeong87/Bunya-Jido`  
**Document location:** `docs/CONTRIBUTION_PLAN.md`  
**Revision basis:** Direct review of the current repository implementation, README, package metadata, viewer, and tests.
**Implementation progress (May 28, 2026):** PR 1 through PR 8, the follow-up UI 1 through UI 3 constellation-viewer redesign, PR 9 honest agent-route matching, PR 10 agent activation, PR 11 change-aware refresh routing, and PR 11.1 portability and stale-map review gates are implemented on `main`; the original grounded public-alpha roadmap is complete and the agent consumption loop is the active extension. Python 3.10 scanner compatibility is retained through a conditional `tomli` fallback for TOML evidence.

---

## 1. Executive Decision

Bunya-Jido should continue toward this product identity:

> **Bunya-Jido is a grounded semantic repository map for humans and coding agents.**

A practical product sentence:

> **Bunya-Jido turns a codebase into an offline architecture map whose important claims can be inspected, then derives bounded coding-agent context from the same semantic model.**

This direction is already visible in the project. The roadmap is not a pivot from a generic graph renderer into an unrelated AI product. It is a plan to make the repository's existing philosophy explicit, enforceable, and demonstrable.

The center of gravity remains the semantic map:

| Consumer | Need | Product Surface |
|---|---|---|
| Human maintainer or newcomer | Understand responsibilities, workflows, boundaries, and supporting evidence | Offline interactive HTML map |
| Coding agent | Start a bounded task with relevant components, files, tests, and cautions | Context output derived from blueprint plus agent map |
| Reviewer | Know whether the map is publishable, provisional, or blocked | Validation policy, grounding status, warnings, and visible evidence |

At roadmap adoption, two corrections mattered from the outset:

1. The tool can validate the presence and consistency of evidence; it cannot automatically prove that every semantic interpretation is true.
2. The human map and agent navigation output did not yet fully share one enforced contract. PR 4 now enforces and tests that shared task-route contract.

---

## 2. Why This Direction Fits the Project

Bunya-Jido originated from the need to read complex systems through meaningful regions and flows rather than through an exhaustive import diagram. That motivation still fits repositories with orchestration, external providers, validation paths, generated artifacts, and human review boundaries.

The durable product lessons are:

- Imports, files, docs, tests, config, and runtime artifacts are evidence, not architecture by themselves.
- Planes should represent responsibilities, not simply directories.
- An opening view should show landmarks and workflows before implementation detail.
- A coding agent should receive task-oriented navigation, not an unbounded dump of repository memory.
- Uncertainty must stay visible: interpretation is useful only when its grounds and limitations can be inspected.

This positions Bunya-Jido between two poor extremes:

| Avoided Identity | Reason |
|---|---|
| Giant dependency graph renderer | Raw connections create noise without explaining responsibilities. |
| Decorative README diagram generator | The value is reviewable navigation, not appearance alone. |
| Runtime observability product | Runtime artifacts may inform a map, but this project does not own runtime truth. |
| General-purpose agent memory system | Context output is a derived task handoff, not autonomous memory. |
| Automatic architectural oracle | A coding agent authors interpretations; Bunya-Jido validates and presents their grounding. |

---

## 3. Baseline Before Roadmap Implementation

Before PR 1 was implemented, the repository already had a substantial alpha foundation:

- deterministic repository scanning in `src/bunya_jido/scanner.py`,
- blueprint and agent-map workspace preparation in `src/bunya_jido/blueprint.py`,
- blueprint and agent-map validation,
- conversion of a blueprint into viewer graph data,
- single-file offline HTML rendering,
- task-focused Markdown context generation,
- a browser viewer with planes, filters, paths, overview/detail visibility, PNG export, and JSON export,
- packaging metadata and a Python 3.10-3.12 CI matrix.

The current architecture is compact but concentrated:

| Area | Current Location | Observation |
|---|---|---|
| Scanner | `src/bunya_jido/scanner.py` | Handles Python, limited JS/TS, docs, config, runtime/data, and API hints. |
| Blueprint schema, prompt, validation, graph conversion, agent map, context | `src/bunya_jido/blueprint.py` | One large module owns most semantic behavior. |
| HTML serialization | `src/bunya_jido/render.py` | Small and deterministic. |
| Viewer | `src/bunya_jido/viewer/index.template.html` | Rich single-file UI, but trust information is not yet a first-class panel. |
| Automated tests | `tests/test_smoke.py` | Three smoke tests; no semantic regression suite yet. |

### 3.1 Confirmed strengths

These behaviors are already real and should be preserved:

- Blueprint mode encourages responsibility-oriented documents rather than folder mirrors.
- Nodes and edges support evidence fields and confidence values.
- Secret-like strings in blueprints and agent maps are already validation errors.
- Synthetic repository-root nodes are hidden by default.
- Workflows in a blueprint can become viewer path presets.
- The final HTML artifact is portable and offline.

### 3.2 Confirmed gaps and corrections

This table records the baseline found during roadmap revision. PR 1 through PR 4 subsequently close the documentation, test, grounding, trust-panel, and agent-map parity gaps listed here.

The following are not merely speculative gaps; they follow from the current implementation and public documentation.

| Current Gap | Current Behavior | Roadmap Consequence |
|---|---|---|
| Grounding is advised more strongly than it is enforced | Missing evidence, unresolved node evidence paths, and `unverified` edges are warnings; a map can still render. | Add explicit grounding policy and build behavior. |
| There is no public quality state | Metrics are placed in graph data, but the viewer does not show a grounding status panel. | Add visible status after policy is defined. |
| Agent-map parity is incomplete | Agent-map task routes are used for context generation, while viewer paths are derived from blueprint views/workflows only. | Make task-route parity its own early milestone. |
| README overstates task-route display | README says HTML includes path presets for task routes, but that behavior is not currently wired from the agent map. | Correct docs first; implement parity later. |
| Evidence is stored but not fully inspectable in the UI | The viewer presents node source paths and relation notes, but not a full edge-confidence/evidence inspection experience. | Include evidence visibility with trust-oriented viewer work. |
| Tests do not protect semantic behavior | CI covers smoke construction/rendering only. | Add characterization tests before major validation changes. |
| JS/TS support is exploratory | JS/TS files are scanned, but relative imports are not resolved to local target modules in the same way as Python structure. | Describe JS/TS as limited support until fixtures prove more. |
| Positioning is partly aligned, not absent | README already talks about grounded human/agent maps; package metadata and a few phrases still emphasize generic graphs or working memory. | Make PR 1 an alignment/correction pass, not a product reinvention. |

At the time of this review, a deterministic scan of Bunya-Jido itself produced 105 nodes and 109 edges, dominated by implementation-level `code`, `function`, and `defines` entries. This is useful evidence for discovery, but it also demonstrates why the authored semantic blueprint must remain the product's preferred human-facing map.

---

## 4. Product Contract

### 4.1 Two output modes, named honestly

Bunya-Jido supports two meaningful output modes, and they should not be presented as if they carry the same confidence.

| Mode | Source | Proper Claim |
|---|---|---|
| **Deterministic Scan Map** | Static scanner output only | Observable repository structure and detected hints; not a semantic architecture judgment. |
| **Semantic Blueprint Map** | Agent-authored blueprint plus deterministic validation | An inspectable architectural interpretation whose grounding level can be evaluated. |

A static scan map should remain useful without being labeled as a failed or low-quality semantic blueprint. A grounding state applies to semantic blueprint maps, not automatically to every HTML generated by the tool.

### 4.2 Shared-model target contract

The intended contract is:

> Human map paths and coding-agent task routes must be traceable to the same validated semantic blueprint and must not silently contradict it.

This contract is implemented by PR 4 and covered by parity tests. Its implementation includes:

- validating task-route references against blueprint nodes and workflows,
- surfacing task routes as optional viewer path presets,
- carrying grounding status and relevant warnings into generated context,
- refusing or clearly marking context derived from blocked semantic maps.

### 4.3 Evidence before confidence

For semantic blueprint maps:

- Core nodes must have repository-relative, resolving evidence.
- Core workflow edges must have repository-relative, resolving evidence.
- Core edges must not be `unverified` in publishable outputs.
- Evidence and confidence must be visible in the HTML experience, not only retained in JSON.
- Agent routes must identify the evidence, tests, or contracts that justify their suggested reading/edit path.

### 4.4 Overview before detail

The opening semantic map should be optimized for orientation.

| Hygiene Signal | Initial Target |
|---|---:|
| Core landmarks in overview | 5 to 12 |
| Typical overview nodes for a nontrivial repository | 30 to 70 |
| One plane's share before warning | More than 40% |
| Primary relation families shown to a new viewer | Approximately 6 to 10 |
| Synthetic repository-root node | Hidden or omitted by default |

These are quality heuristics, not universal schema requirements.

### 4.5 Offline and deterministic presentation

The browser artifact remains a single offline HTML file by default. Agent-authored meaning is allowed; output generation, validation policy, and presentation of grounding status must remain deterministic for stable inputs.

---

## 5. Positioning and Supported Scope

### 5.1 Recommended public positioning

Recommended subtitle:

> **A semantic repository atlas for humans and coding agents.**

Recommended concise opening:

> Bunya-Jido creates offline repository maps from deterministic evidence and reviewable coding-agent interpretation. It shows responsibilities, workflows, and change boundaries for humans, then derives bounded task context for coding agents from the same architectural model.

The README should avoid calling the context pack `working memory`. The more accurate term is `task-oriented navigation context` or `bounded handoff context`.

### 5.2 Honest initial support statement

The strongest currently defensible public scope is:

- Python repositories, especially tooling, workflow, research, automation, and agent-oriented projects.
- Markdown documentation, common packaging/config files, selected runtime/data artifacts, and API/provider hints.
- Limited JS/TS scanning support, identified explicitly as developing until local module-resolution behavior and representative fixtures improve.

Do not claim yet:

- equivalent semantic coverage across Python and JavaScript/TypeScript,
- broad multi-language architecture inference,
- reliable infrastructure/deployment understanding,
- automatic proof of correctness,
- safe agent modification solely because a context pack exists.

---

## 6. Grounding and Review Model

The prior idea of a single `Verified` quality grade overstates what automated validation can establish. The product should instead expose separate, accurate dimensions.

### 6.1 Artifact mode

| Mode | Meaning |
|---|---|
| `Static Scan` | No semantic blueprint was used; output reflects deterministic extraction and hints. |
| `Semantic Blueprint` | Output was built from an authored blueprint and is eligible for grounding assessment. |

### 6.2 Grounding status for semantic blueprints

| Status | Meaning | Minimum Policy |
|---|---|---|
| **Grounded** | Suitable for publication as an evidence-linked architectural interpretation. | Core node and workflow-edge evidence resolves; no unverified core edge; no invalid references or secret-like content. |
| **Draft** | Useful for inspection and iteration, but not for confident publication or unqualified agent handoff. | Valid enough to display with missing/non-core weakness or explicitly allowed unresolved grounding issues. |
| **Blocked** | Must not be published or consumed as trusted semantic context. | Invalid structure, secret-like content, missing critical references, or failed required grounding checks. |

`Grounded` does not mean “architecturally proven.” It means the map satisfies the project's inspectable-evidence contract.

### 6.3 Optional review status

A separately recorded human status may be useful later:

| Review Status | Meaning |
|---|---|
| `Unreviewed` | Generated or edited map has not been explicitly assessed by a maintainer. |
| `Reviewed` | A maintainer records that the semantic map is acceptable for its documented purpose. |

This must never be inferred automatically from path existence or validation success.

### 6.4 Validation policy

Validation output should distinguish:

| Category | Examples | Default Effect |
|---|---|---|
| Errors | Invalid schema/version, dangling structural references, secret-like content, malformed route object | Fail validation and build. |
| Publish blockers | Core evidence missing or unresolved, unverified core workflow relation, agent route referencing absent required nodes/workflows | Fail semantic publication/build unless a narrowly defined draft override is used where safe. |
| Warnings | Large overview, concentrated plane, excessive leaf nodes, non-core weak evidence, taxonomy complexity | Renderable, surfaced prominently. |

Secret-like content and malformed structure must not become overrideable simply to render a draft.

### 6.5 Visible trust information

A semantic HTML map should display a compact status panel, for example:

```text
Artifact mode: Semantic Blueprint
Grounding: Grounded
Review: Unreviewed
Core landmarks: 8
Core node evidence: 100%
Core workflow evidence: 100%
Warnings: 2
```

A static-only HTML map should instead say plainly:

```text
Artifact mode: Static Scan
Semantic grounding: Not assessed
```

---

## 7. Human Viewer and Agent Context Direction

### 7.1 Human viewer

The human-facing map remains the front door. It should evolve around:

- semantic plane purposes visible in the UI,
- a small viewer-facing node taxonomy,
- relation families that simplify the primary legend while retaining detailed verbs,
- explicit Overview / Inspect Evidence / Implementation Detail experiences,
- selected-edge evidence and confidence visibility,
- workflow and, once validated, task-route path presets,
- a visible artifact-mode and grounding-status panel.

Recommended viewer-facing node families:

| Family | Meaning |
|---|---|
| Component | Subsystem responsibility |
| Agent | Decision-making or autonomous role |
| Service | Runtime process or adapter |
| Contract / Gate | Schema, invariant, policy, or validator |
| Evidence / State | Persisted artifact, result, record, or state |
| Integration | External provider, API, model lane, database, or queue |
| Human Surface | UI, docs, dashboard, or intervention point |
| Implementation Detail | Lower-level file/module detail shown on demand |

Recommended relation families:

| Family | Example Detailed Relations |
|---|---|
| Coordinates | `calls`, `dispatches`, `hands_off_to`, `schedules` |
| Reads / Requests | `reads`, `retrieves`, `queries`, `requests` |
| Writes / Emits | `writes`, `records`, `emits`, `persists` |
| Checks / Gates | `validates`, `guards`, `gates`, `uses_contract` |
| Failure / Repair | `blocks`, `routes_repair_to`, `retries`, `recovers` |
| Integrates With | `api_calls`, `uses_model_lane`, `connects_to` |
| Explains / Projects | `documents`, `shows`, `projects_to_human` |
| Structural Support | `imports`, `uses_module`, `declares_dependency` |

### 7.2 Coding-agent context

Agent context should stay a derived handoff, not become an independent architectural truth source.

A useful task route identifies:

- where to begin reading,
- what evidence, contract, or invariant matters,
- which tests are relevant,
- which files are plausible edit locations,
- which boundary needs deliberate review,
- what grounding status and warnings apply to the source map.

Potential context modes remain useful after parity is established:

| Mode | Purpose |
|---|---|
| `orientation` | Small map summary before planning. |
| `task` | Files, contracts, tests, and boundaries for a planned change. |
| `debug` | Failure paths and runtime evidence relevant to diagnosis. |
| `review` | Responsibilities and checks likely affected by an existing diff. |

---

## 8. Contribution Roadmap by Pull Request

Each pull request should remain independently reviewable. The revised order deliberately establishes accurate public claims and regression coverage before enforcing larger trust behavior.

---

### PR 1: Documentation and Capability Alignment

**Goal:** Make public claims precise before changing behavior.

**Suggested branch:** `docs/align-product-contract`

**Scope:**

- Update README opening/subtitle and package metadata to emphasize semantic maps and bounded agent context.
- Replace `working memory` phrasing with task-oriented navigation context.
- Distinguish Deterministic Scan Map from Semantic Blueprint Map.
- Correct the statement that HTML already displays agent-map task routes, or clearly mark it as planned until implemented.
- Describe Python as the strongest current scanning surface and JS/TS as limited/developing support.
- Link to this roadmap.

**Acceptance criteria:**

- A new visitor can tell what is deterministic extraction versus authored interpretation.
- Documentation does not claim behavior that the current HTML or agent-map integration does not provide.
- Unsupported language/generalization claims are absent.

**Non-goals:**

- No validation behavior change.
- No viewer redesign.
- No scanner expansion.

**Suggested commit message:**  
`docs: align public claims with grounded map capabilities`

---

### PR 2: Characterization Tests and Focused Semantic Boundaries

**Goal:** Protect current behavior and prepare the semantic code path for trust-policy changes.

**Suggested branch:** `test/characterize-semantic-pipeline`

**Scope:**

- Add blueprint validation fixtures for missing evidence, unresolved evidence path, unverified edge, secret-like content, and hidden root behavior.
- Add agent-map fixtures for missing start-node references and context output.
- Add viewer-data/render tests covering workflows, evidence payload retention, and existing blueprint-quality metrics.
- Add a deterministic-output assertion after excluding or normalizing generated timestamps.
- Extract only the smallest helpful internal boundaries, such as validation/quality helpers or context handling, if needed to keep tests and the next PR focused.

**Acceptance criteria:**

- CI exposes the current warning-versus-error behavior before it is intentionally changed.
- Future trust-policy changes fail tests when they accidentally alter unrelated rendering or context behavior.
- Any refactor is behavior-preserving and keeps CLI commands compatible.

**Non-goals:**

- No full package restructuring for its own sake.
- No new quality status yet.

**Suggested commit message:**  
`test: characterize blueprint validation rendering and agent context behavior`

---

### PR 3: Grounding Status, Publication Gate, and Trust Panel

**Goal:** Make inspectable grounding a visible and enforceable product contract.

**Suggested branch:** `feat/grounding-status-and-gates`

**Scope:**

- Implement artifact-mode reporting: `Static Scan` versus `Semantic Blueprint`.
- Add semantic grounding statuses: `Grounded`, `Draft`, and `Blocked`.
- Promote critical missing/unresolved core evidence and unverified core workflow relationships to publish blockers.
- Retain current secret-like-content failure behavior and cover it in tests.
- Define draft-render behavior only for non-secret, structurally valid semantic maps, for example `--allow-draft`.
- Pass mode, status, metrics, and warnings to rendered HTML.
- Add an always-visible trust/status panel to the viewer.
- Expose confidence and evidence for selected semantic nodes/edges.

**Acceptance criteria:**

- A semantic blueprint with missing core evidence cannot silently appear publishable.
- A static scan render is identified as static rather than unfairly graded as a weak blueprint.
- Secret-like content is blocked and cannot be bypassed through draft rendering.
- Status and critical warnings are visible in HTML and covered by tests.

**Suggested commit message:**  
`feat: enforce semantic grounding status and expose trust in the viewer`

---

### PR 4: Agent-Map Parity and Task-Route Projection

**Goal:** Turn “one model for humans and agents” into a tested product contract.

**Suggested branch:** `feat/agent-map-parity`

**Implementation status:** Implemented on `main` on May 27, 2026.

**Scope:**

- Treat missing required blueprint node/workflow references in agent routes as blockers for trusted context.
- Validate task-route links to blueprint nodes, workflows, tests, and must-read evidence where applicable.
- Carry artifact mode, grounding status, and relevant warnings into context output.
- Project valid task routes into optional HTML path presets.
- Clearly label paths derived from workflows versus task routes in the viewer.
- Add parity tests ensuring human paths and generated context refer to valid shared semantic nodes.

**Acceptance criteria:**

- README's human/agent shared-map promise is implemented, not merely aspirational.
- Invalid agent routes cannot be emitted as trusted navigation context.
- Valid routes are inspectable in both context output and HTML.

**Suggested commit message:**  
`feat: validate and project agent task routes from the semantic map`

---

### PR 5: Self-Map, Gallery, and Semantic Golden Fixtures

**Goal:** Demonstrate usefulness with real output and lock in baseline map quality.

**Suggested branch:** `docs/add-grounded-gallery-and-goldens`

**Implemented (May 27, 2026):** The repository now carries a grounded self-map in `.bunya-jido/`, a generated HTML demo and screenshot documented in `docs/gallery.md`, and semantic golden tests. The gallery also records the current provider-hint overlay limitation instead of treating heuristic additions as part of the promoted example.

**Scope:**

- Generate and commit a Bunya-Jido self-map after the grounding/status contract exists.
- Add a sanitized complex-system example only if its evidence and redistribution are appropriate.
- Keep the existing minimal example as a smoke fixture, not proof of broad generality.
- Create `docs/gallery.md` with generation records, intended lessons, and screenshots.
- Use committed semantic examples as bounded golden fixtures for status, path presets, key metadata, and deterministic rendering expectations.

**Acceptance criteria:**

- At least one real self-map is `Grounded` under the implemented policy.
- Gallery examples disclose artifact mode, grounding status, review status if recorded, and known limitations.
- CI protects representative semantic output from quiet regression.

**Suggested commit message:**  
`docs: add grounded self-map gallery and semantic golden fixtures`

---

### PR 6: Viewer Semantics and Progressive Disclosure

**Goal:** Improve first-read comprehension once trust and examples provide a stable baseline.

**Suggested branch:** `feat/semantic-viewer-disclosure`

**Implemented (May 27, 2026):** Semantic graphs now preserve authored plane-purpose glossary data for the viewer; static scans expose bounded default plane descriptions. The viewer provides explicit Overview, Inspect Evidence, and Implementation Detail modes, node/relation family filters, confidence filtering, grouped task-route/workflow paths, and selected-relationship evidence while preserving exact relation verbs.

**Scope:**

- Display plane purpose/glossary information.
- Fold detailed node types into viewer-facing families.
- Fold relation verbs into primary semantic relation families while preserving original detail.
- Make Overview / Inspect Evidence / Implementation Detail explicit UI modes.
- Add confidence filters and improve workflow/task-route discoverability.
- Verify readability using the committed self-map and gallery fixtures.

**Acceptance criteria:**

- Default view is legible without hiding trust information.
- Detailed relation verbs and evidence remain accessible.
- Golden/gallery fixtures demonstrate a meaningful usability improvement without untested semantic changes.

**Suggested commit message:**  
`feat: add progressive disclosure and semantic viewer taxonomy`

---

### PR 7: Scanner Coverage Matrix and Measured Extension

**Goal:** Expand repository support from evidence rather than aspiration.

**Suggested branch:** `docs/scanner-coverage-and-adapters`

**Scope:**

- Publish a coverage matrix describing exact current behavior for Python, JS/TS, Markdown, config, runtime/data artifacts, and provider hints.
- Add representative fixtures for supported behavior.
- Decide whether JS/TS local import resolution should be improved next or documented as intentionally limited.
- Define requirements for future language or artifact adapters: fixtures, evidence semantics, output hygiene, and regression tests.

**Example matrix:**

| Area | Baseline Position | Next Evidence Required |
|---|---|---|
| Python module/import and symbol scan | Current primary scanner surface | Real fixtures and semantic map examples |
| JS/TS module scan | Limited/developing | Local resolution tests and example map before stronger claim |
| Markdown/docs | Supported as evidence discovery | Contract/document linkage fixtures |
| Config/package metadata | Supported selected formats | Exact format coverage documentation |
| Runtime/data artifacts | Policy-controlled discovery | Privacy and scale fixtures |
| Provider/API hints | Heuristic discovery only | Privacy/false-positive tests |
| Other languages | Not claimed | Adapter proposal plus fixtures |

**Acceptance criteria:**

- Users can judge fit before installation.
- A new support claim requires fixtures and quality expectations.

**Suggested commit message:**  
`docs: publish scanner coverage matrix and measured extension policy`

**Implemented (May 28, 2026):** `docs/SCANNER_COVERAGE.md` publishes the exact deterministic scanner claims and extension gate. The committed `examples/coverage/` fixture and `tests/test_scanner_coverage.py` cover Python/config/provider evidence, Markdown linkage, bounded runtime/data behavior, and the intentional JS/TS local-import resolution limitation.

---

### PR 8: Public Alpha Release Readiness

**Goal:** Release only after the product's trust signals and examples are real.

**Suggested branch:** `release/public-alpha-readiness`

**Scope:**

- PyPI publication workflow and release documentation.
- Changelog and semantic version policy.
- Contribution guide and issue templates.
- Demo/gallery publishing workflow.
- Clear compatibility and limitation statements.
- Optional diagnostics command only if it reports actual artifact mode and grounding behavior.

**Release gate:**

- PRs 1 through 5 are merged.
- Public documentation matches actual behavior.
- Grounding status is visible in semantic outputs.
- Agent-map parity is covered by tests.
- At least one real grounded self-map is available.
- Semantic regression tests run in CI.
- Coverage claims are documented conservatively.

**Suggested commit message:**  
`release: prepare grounded semantic map public alpha`

**Implemented (May 28, 2026):** Release readiness now includes `bunya-jido diagnose --require-grounded` as an executable semantic publication gate, CI coverage for that gate, PyPI Trusted Publishing and Pages workflows, release/version guidance, contribution and issue templates, and explicit public compatibility and limitation documentation.

---

### Follow-up UI 1 through UI 3: Constellation Viewer Design Pass

**Goal:** Give the grounded semantic map a calmer, constellation-first reading
surface without weakening its evidence and task-route contracts.

**Implemented (May 28, 2026):** The offline viewer now opens on a canvas-first
constellation overview with semantic role glyphs, restrained visible relation
families, and a workflow launcher bar. Controls and selected-item inspection
remain available on demand. The committed demo, grounded self-map screenshot,
gallery explanation, and both README hero presentations have been refreshed to
show this viewer.

**Verification:** Focused viewer tests protect the new presentation hooks, and
the committed grounded self-map remains subject to the semantic diagnostic gate.

---

### PR 9: Honest Agent Route Matching

**Goal:** Ensure coding-agent context recommends a prepared route only when it
actually matches the requested task or explicit semantic focus.

**Scope:**

- Treat explicit node and workflow selection as precise route matches.
- Match natural-language task requests only through meaningful route terms,
  excluding generic action and product words.
- Emit match reasons for recommended routes.
- Emit `No matching trusted route` rather than unrelated routes when a request
  is outside the authored agent map.
- Preserve an unfiltered route catalog only when no task or focus was requested.

**Acceptance criteria:**

- Known fixture and self-map tasks select their intended validated route.
- An unrelated requested task emits no prepared route.
- Explicit focus and no-match behavior are covered by tests.
- README guidance describes the honest no-match contract.

**Implemented (May 28, 2026):** Agent context now distinguishes validated
routes from routes relevant to the current request. Task or focus selection
reports `matched` or `not_found`, includes match reasons when a route is
recommended, and avoids fabricating guidance for an uncovered task.

**Suggested commit message:**
`feat: report unmatched agent tasks without invented routes`

---

### PR 10: Agent Activation

**Goal:** Make validated context discoverable in the instructions that coding
agents actually load when they begin repository work.

**Scope:**

- Expand generated guidance from map-authoring help into a context-first rule
  for implementation, debugging, and code review.
- Add `install-agent-guides --activate` to write managed project-instruction
  blocks for Codex, Claude Code, Cursor, and Cline.
- Add `--dry-run` previews before native project instruction files change.
- Preserve existing user-authored instructions and update only the marked
  Bunya-Jido block on repeated activation.
- Dogfood Codex activation in this repository through `AGENTS.md`.

**Acceptance criteria:**

- Activated guidance directs agents to request task context before editing.
- Guidance explains matched-route, no-match, and not-yet-mapped repository
  behavior without overclaiming.
- Native activation targets are covered by tests and documented in both
  READMEs.
- Repeated activation is idempotent and does not erase existing instructions.

**Implemented (May 28, 2026):** The CLI now previews or activates managed
task-context guidance in `AGENTS.md`, `CLAUDE.md`,
`.cursor/rules/bunya-jido.mdc`, and `.clinerules/bunya-jido.md`. Generated
snippets carry the same context-first instruction, while tests protect
dry-run behavior, preservation of existing content, and idempotent updates.

**Suggested commit message:**
`feat: activate bounded context guidance for coding agents`

---

### PR 11: Change-Aware Refresh Routing

**Goal:** Route post-edit context through the files and grounded evidence that
were actually affected.

**Scope:**

- Treat `--changed-file` and `--changed-files-from` inputs as the evidence
  gate for `refresh-context` route recommendations.
- Match changed files against route reading, test, safe-edit, and guarded
  paths, as well as grounded evidence for route start nodes.
- Explain the file-level reason for every recommended route.
- Preserve honest no-match behavior when changes are unrelated to prepared
  routes, even when task text sounds related.
- Reject refresh requests that do not supply changed-file evidence.
- Extend activated agent guidance so agents request evidence-based refresh
  context after editing.

**Acceptance criteria:**

- `refresh-context` recommends no route unless a supplied changed file
  justifies it.
- Both path-based and grounded start-node matching are covered by tests.
- A matching task description cannot override unrelated changed files.
- Native Windows console output remains usable for affected-node reporting.
- English and Korean READMEs describe the bounded refresh behavior.
- Activated project guidance includes the post-edit refresh step.

**Implemented (May 28, 2026):** Context generation now normalizes changed
paths, selects routes only from matching route paths or grounded start-node
evidence, and prints each match reason. `refresh-context` fails early without
changed-file input or when its input list file is missing. Fixture and
committed self-map tests cover matched, unrelated, and task-without-file-
evidence cases, and activated guidance now directs agents through this
post-edit refresh step.

**Suggested commit message:**
`feat: route refreshed agent context from changed evidence`

---

### PR 11.1: Portability And Stale-Map Review Gate

**Goal:** Make the agent-consumption loop easier to adopt across operating
systems and prevent mapped repositories from silently drifting after code
changes.

**Scope:**

- Add a deterministic `check-stale` command driven by an authored
  `stale_map_policy`.
- Distinguish `stale` changes from `review_recorded` changes without claiming
  automatic semantic correctness.
- Apply the stale-map review gate in CI for push and pull-request diffs.
- Expand CI execution coverage from Ubuntu to Windows and macOS.
- Document Python, Git, coding-agent, and optional browser requirements with
  OS-specific installation commands in both READMEs.
- Extend activated agent guidance with the post-edit stale-map check.

**Acceptance criteria:**

- A policy-covered source change without a blueprint, agent-map, or map-review
  note update
  fails `check-stale --require-reviewed`.
- A changed semantic-map artifact or `MAP_REVIEW.md` note records review while
  retaining the explicit limitation that validation does not prove completeness.
- CI executes tests on Ubuntu, Windows, and macOS and runs the freshness gate.
- English and Korean onboarding gives usable Windows PowerShell and
  macOS/Linux command sequences.
- The committed self-map defines and tests its own stale-map policy.

**Implemented (May 28, 2026):** `check-stale` accepts explicit changed files,
files-from input, or tracked `git diff` input, and reports `current`,
`review_recorded`, or `stale` from the agent-map policy. The repository
self-map now carries that policy, CI exercises three operating systems and
enforces map-review detection, a tracked `MAP_REVIEW.md` avoids meaningless
map churn for reviewed no-structure-change cases, and onboarding documents
installation and maintenance steps for each supported operating-system family.

**Suggested commit message:**
`feat: add portable stale-map review gate`

---

### PR 12: Agent Utility Evaluation

**Goal:** Measure whether the bounded agent-context output supports the tasks
it claims to cover, without treating deterministic output as proof of live
agent behavior.

**Scope:**

- Add a committed `bunya-jido.agent-evaluation.json` acceptance suite for a
  mapped repository.
- Add `evaluate-agent-utility` with a strict CI mode and machine-readable
  report.
- Measure first-read accuracy, test recall, boundary discipline, honest
  no-match handling, and change-aware refresh behavior against the committed
  self-map.
- Document a separate live-agent observation protocol for any later
  behavioral claim.
- Apply the deterministic gate in CI, demo publishing, and package release
  verification.

**Acceptance criteria:**

- The committed self-map suite passes in strict mode and is protected by tests.
- Broken expected reading, tests, boundaries, or route selection cause strict
  evaluation to fail.
- Both READMEs show how to run the evaluation and state its limitation.
- Release documentation does not confuse context-output validation with proof
  that a live agent followed the map.

**Implemented (May 28, 2026):** A tracked five-case self-map suite now
exercises the bounded context contract through `evaluate-agent-utility`.
Fixture and self-map tests protect pass and failure reporting; CI, Pages, and
publish workflows run the strict evaluation gate. The dedicated evaluation
protocol separates deterministic handoff validation from optional recorded
live-agent observation.

**Suggested commit message:**
`feat: evaluate bounded agent context utility`

---

## 9. Completed Delivery Sequence

The roadmap was delivered in this order to prioritize truthfulness, testability, and trust:

| Order | Pull Request | Reason |
|---:|---|---|
| 1 | Documentation and Capability Alignment | Correct current overstatements and clarify output modes immediately. |
| 2 | Characterization Tests and Focused Semantic Boundaries | Establish protection before validation behavior changes. |
| 3 | Grounding Status, Publication Gate, and Trust Panel | Make the central product promise enforceable and visible. |
| 4 | Agent-Map Parity and Task-Route Projection | Close the largest mismatch in the human/agent shared-map thesis. |
| 5 | Self-Map, Gallery, and Semantic Golden Fixtures | Prove the product against its own real workflow and preserve the result. |
| 6 | Viewer Semantics and Progressive Disclosure | Improve comprehension against stable, trusted fixtures. |
| 7 | Scanner Coverage Matrix and Measured Extension | Expand honestly after current strengths are demonstrated. |
| 8 | Public Alpha Release Readiness | Publish with trust signals rather than promises. |
| 9 | Honest Agent Route Matching | Avoid presenting unrelated prepared routes for uncovered agent tasks. |
| 10 | Agent Activation | Place context-first guidance in agent-native project instruction surfaces. |
| 11 | Change-Aware Refresh Routing | Recommend post-edit routes only from affected files or grounded start-node evidence. |
| 11.1 | Portability And Stale-Map Review Gate | Verify OS adoption paths and require reviewed map updates after covered changes. |
| 12 | Agent Utility Evaluation | Gate bounded context claims with committed cases and keep live-agent claims evidence-based. |

The sequencing constraints used during implementation were:

- Documentation corrections could proceed while characterization fixtures were prepared.
- Gallery authoring could start during parity work, but examples were not promoted as grounded until the status policy existed.
- Viewer experimentation could happen early, but semantic taxonomy changes landed with fixtures and trust behavior in place.

---

## 10. Success Metrics

### 10.1 Public accuracy

- README distinguishes deterministic scan output from semantic blueprint output.
- README does not call task routes visible in HTML until that integration exists.
- Supported-language statements match measured fixtures.
- Context output is described as bounded navigation context, not memory or guaranteed safe action.

### 10.2 Grounding and trust

- Semantic maps expose `Grounded`, `Draft`, or `Blocked`, while static maps expose `Static Scan`.
- 100% of core nodes in a `Grounded` map have resolving repository-relative evidence.
- 100% of core workflow edges in a `Grounded` map have resolving evidence.
- Zero `unverified` core workflow relationships are publishable as `Grounded`.
- Secret-like content remains non-renderable as trusted semantic output.
- Critical grounding decisions are protected by CI tests.

### 10.3 Human comprehension

- A newcomer can identify the purpose and several responsibility areas from Overview.
- Workflow or task-route paths visibly answer how work moves or where an agent should start.
- Evidence and confidence are reachable from selected important relationships.
- Default examples remain legible at an ordinary laptop viewport.

### 10.4 Coding-agent utility

- Trusted context records source artifact mode, grounding status, and relevant warnings.
- Every published task route validates against shared semantic nodes/workflows.
- Every real gallery map includes at least one bounded task route once parity ships.
- Maintainer review can distinguish suggested edit areas from boundaries that require care.
- Requests without a matching validated route receive an explicit no-match result rather than arbitrary route guidance.
- Maintainers can activate context-first agent instructions without losing existing project guidance.
- Post-edit context recommends routes only when changed-file evidence supports them and states why.
- Mapped repositories can fail CI when covered changes lack a reviewed map artifact or review-note update.
- Installation guidance and CI verification explicitly cover Windows, macOS, and Linux usage.
- Committed agent-utility cases gate first-read, test, boundary, no-match, and refresh-context claims without implying live-agent compliance.

---

## 11. Contribution Workflow

Each substantial contribution should be evaluated as both software behavior and map behavior.

### Before editing

1. Read this roadmap, current README, impacted source modules, and existing tests.
2. State which product contract is being changed: documentation, grounding, parity, viewer comprehension, scanning coverage, or release.
3. Identify compatibility impact on CLI output, schema, generated HTML, or existing context packs.

### During implementation

- Add focused tests proportional to the semantic risk.
- Preserve offline rendering and deterministic output for stable inputs.
- Keep static scan and semantic blueprint behavior distinguishable.
- Do not introduce stronger claims than the fixtures and validation policy support.

### Before merge

- Run tests.
- Validate and render a representative semantic fixture whenever quality, paths, or viewer output changes.
- Inspect the resulting HTML when the user experience changes.
- Record grounding/status changes and known limitations in the PR description.

### Review checklist

- Does the change improve human comprehension or coding-agent navigation in a measurable way?
- Does it expose rather than hide uncertainty?
- Does it preserve one reviewable semantic model across outputs?
- Does it incorrectly treat deterministic detection as architectural proof?
- Is a test or real example protecting the claimed improvement?

---

## 12. Decisions to Keep Explicit

### Adopt

- A grounded semantic repository map for humans and coding agents as the top-level direction.
- The semantic HTML map as the primary product artifact.
- Agent context as bounded, map-derived navigation output.
- Separate identification of static-scan output and semantic-blueprint output.
- Grounding status that expresses inspectable support without claiming proof.
- Tests and real examples as prerequisites for stronger public claims.

### Avoid

- A `Verified` badge that implies automated proof of architecture.
- Treating every file or import as a first-class semantic landmark.
- Presenting task routes as part of the map without validated parity.
- Calling generated context long-term memory or safe autonomous guidance.
- Claiming broad JS/TS or multi-language equivalence without fixtures.
- Adding scanners or decorative UI before closing trust and parity gaps.

---

## 13. Final Product Statement

Bunya-Jido should become a tool through which a maintainer, a new contributor, and a coding agent can inspect the same architectural interpretation of a repository:

- its major responsibility areas,
- its important workflows,
- its evidence-linked boundaries,
- its uncertainty and grounding status,
- and its bounded route into a particular task.

The advantage is not maximal graph coverage. The advantage is a smaller, reviewable semantic map whose claims can be inspected and whose agent handoffs do not drift away from what humans see.

That is a credible extension of the existing codebase, a disciplined roadmap for the alpha product, and a standard against which future contributions can be reviewed.
