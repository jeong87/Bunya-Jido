# Bunya-Jido Gallery

This gallery promotes only maps whose artifact mode and grounding record are
explicit. The committed example below is generated from evidence paths in this
repository and is protected by semantic golden tests.

## Grounded Self-Map: Bunya-Jido

| Record | Value |
|---|---|
| Artifact | Repository self-map |
| Source inputs | `.bunya-jido/REPOSITORY_THESIS.md`, `.bunya-jido/PROJECTIONS.md`, `.bunya-jido/SCENARIOS.md`, `.bunya-jido/bunya-jido.blueprint.json`, `.bunya-jido/bunya-jido.agent-map.json` |
| Artifact mode | `semantic_blueprint` |
| Atlas contract | Studio v2, primary projection `Trusted Publication`, machine-readable decision record, two behavioral scenarios |
| Grounding status | `grounded` |
| Atlas quality status | `passed`, with projection choice and narration honesty still review-required |
| Review status | Maintainer-authored and mechanically validated on May 31, 2026 |
| Semantic coverage | 14 nodes, 25 relationships, 5 core nodes, 13 critical relationships |
| Grounding metrics | 100% core-node evidence; 100% critical-relationship evidence |
| Agent routes | 6 of 6 routes validated and projected as `Task Route` paths with optional Studio reading context |
| Viewer surface | Studio constellation with authored projection tabs, scenario playback, semantic role glyphs, workflow launcher bar, and copyable trusted route context |
| Viewer disclosure | `Overview` by default; map controls and selected-item inspector open on demand |
| Screenshot capture | Clean `Overview` state at 1440 x 900 |
| Published output | `docs/demo.html` |

**Generation command:**

```bash
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido evaluate-atlas-quality --root . --require-pass --json
python -m bunya_jido build --root . --max-files 0 --out docs/demo.html
```

![Grounded Bunya-Jido constellation map with semantic role glyphs, trust status, and workflow routes](assets/self-map-grounded.png)

**Intended lessons:**

- A semantic blueprint can publish a compact architecture view with directly inspectable repository evidence.
- The same committed artifact can expose workflows to humans and bounded task routes to coding agents.
- Grounded status is visible in the HTML output rather than being an undocumented build assumption.
- Studio projection and scenario labels are authored from this repository's thesis; playback carries a documented-workflow basis badge rather than claiming observed runtime traces.
- The blueprint retains the compared projections, scenario choices, and centrality risks in `atlas.decision_record`, while quality checks still leave editorial judgment review-required.
- Atlas-quality reporting keeps review-only narration signals separate from blockers and can write an optional local Markdown review summary.
- Validated routes may connect a coding task to a relevant projection question and qualified scenario, and the viewer copies only this projected trusted context.
- Provider hint observations now carry origin/type metadata, and generated prompt/schema example text cannot become a contextual overlay node.
- The benchmark suite exercises six different repository shapes so this promoted self-map is not the only quality target. See [`STUDIO_BENCHMARK.md`](STUDIO_BENCHMARK.md).
- The canvas-first overview keeps controls out of the initial reading surface while preserving them in an on-demand drawer.
- Zone fields, semantic role glyphs, and a restrained relation palette make the first read compact, while selected relationships retain their exact verb, confidence, and evidence in `Inspect Evidence`.

**Known limitations:**

- The published self-map uses `--max-files 0` to keep the promoted output limited to its reviewed semantic evidence. If a Studio author explicitly enables an auxiliary contextual overlay, provider nodes remain secondary and generated prompt/schema hints are filtered by provenance; source/config hints are still heuristic evidence, not verified integrations.
- This is a compact Python developer-tool repository. The cross-domain benchmark checks contract variety, but it is not equivalent to publishing independently reviewed maps for every ecosystem.
- `grounded` means the required evidence references resolve and the implemented publication policy passes; it is not automatic proof that every architectural interpretation is complete.

## Curated Miniature: Scanner Coverage Fixture

This second published item is grounded in the committed miniature repository
under `examples/coverage/`; unlike the self-map it deliberately does not claim
an ordered behavioral walkthrough.

| Record | Value |
|---|---|
| Artifact | Curated coverage-fixture Studio atlas |
| Source inputs | `examples/coverage/studio.blueprint.json` plus its referenced committed fixture files |
| Thesis | Evidence surfaces should be read without inventing an application lifecycle |
| Primary projection | `Evidence Surfaces` |
| Scenario policy | `none_with_reason` |
| Quality result | `passed`; this compact item omits a full Studio editorial workspace, so those omitted review inputs remain disclosed warnings |
| Known limitation | A compact scanner fixture demonstrates provenance handling, not a complete product architecture |
| Screenshot | [`gallery/coverage-fixture.png`](gallery/coverage-fixture.png) |
| Published HTML | [`gallery/coverage-fixture.html`](gallery/coverage-fixture.html) |

```bash
python -m bunya_jido validate-blueprint --root examples/coverage --blueprint examples/coverage/studio.blueprint.json
python -m bunya_jido evaluate-atlas-quality --root examples/coverage --blueprint examples/coverage/studio.blueprint.json --require-pass --json
python -m bunya_jido build --root examples/coverage --blueprint examples/coverage/studio.blueprint.json --max-files 0 --out docs/gallery/coverage-fixture.html
```

![Curated scanner coverage fixture atlas showing four evidence surfaces and no narrated scenario](gallery/coverage-fixture.png)

## Fixture Policy

The minimal example remains a static-scan smoke fixture for command and
rendering behavior. `examples/coverage/` is promoted only as a curated,
evidence-backed miniature for scanner/provenance behavior. Neither miniature
is evidence of broad repository support.

No sanitized complex-system map is promoted because a redistributable,
evidence-backed source has not been established. New gallery examples should
disclose their origin, review status, grounding result, and limitations before
publication.

## Publishing Workflow

`docs/demo.html` and its screenshot are reviewed, committed gallery outputs.
Before updating either file, run the validation and generation commands above,
inspect the resulting offline HTML, refresh `assets/self-map-grounded.png` from
the clean `Overview` state at 1440 x 900, and run:

```bash
python -m unittest tests.test_self_map
python -m bunya_jido diagnose --root . --require-grounded --json
python -m bunya_jido evaluate-atlas-quality --root . --require-pass --json
python -m unittest tests.test_gallery
```

After reviewed `docs/` changes merge, a maintainer can dispatch
`.github/workflows/pages.yml`. It deploys only after the committed semantic
self-map test, strict grounded diagnostic, and Studio atlas-quality gate pass. The Pages deployment
publishes the reviewed artifact already in the repository; it does not
generate a new semantic interpretation during deployment.
