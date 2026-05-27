# Bunya-Jido Gallery

This gallery promotes only maps whose artifact mode and grounding record are
explicit. The committed example below is generated from evidence paths in this
repository and is protected by semantic golden tests.

## Grounded Self-Map: Bunya-Jido

| Record | Value |
|---|---|
| Artifact | Repository self-map |
| Source inputs | `.bunya-jido/bunya-jido.blueprint.json`, `.bunya-jido/bunya-jido.agent-map.json` |
| Artifact mode | `semantic_blueprint` |
| Grounding status | `grounded` |
| Review status | Maintainer-authored and mechanically validated on May 27, 2026 |
| Semantic coverage | 12 nodes, 19 relationships, 5 core nodes, 11 critical relationships |
| Grounding metrics | 100% core-node evidence; 100% critical-relationship evidence |
| Agent routes | 3 of 3 routes validated and projected as `Task Route` paths |
| Published output | `docs/demo.html` |

**Generation command:**

```bash
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido build --root . --max-files 0 --out docs/demo.html
```

![Grounded Bunya-Jido self-map with trust status and validated task routes](assets/self-map-grounded.png)

**Intended lessons:**

- A semantic blueprint can publish a compact architecture view with directly inspectable repository evidence.
- The same committed artifact can expose workflows to humans and bounded task routes to coding agents.
- Grounded status is visible in the HTML output rather than being an undocumented build assumption.

**Known limitations:**

- The published self-map uses `--max-files 0` to keep the promoted output limited to its reviewed semantic evidence. With the auxiliary static overlay enabled, current provider-hint heuristics also detect provider names in the blueprint prompt source and add irrelevant external API nodes. That heuristic behavior is not claimed as self-map evidence.
- This is a compact Python developer-tool repository. It demonstrates the grounding and route contracts, not broad language or large-system coverage.
- `grounded` means the required evidence references resolve and the implemented publication policy passes; it is not automatic proof that every architectural interpretation is complete.

## Fixture Policy

The minimal example remains a static-scan smoke fixture for command and
rendering behavior. It is not presented as a semantic gallery map or evidence
of broad repository support.

No second sanitized complex-system map is promoted in this milestone because a
redistributable, evidence-backed source has not been established. New gallery
examples should disclose their origin, review status, grounding result, and
limitations before publication.
