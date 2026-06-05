<!-- BEGIN BUNYA-JIDO MANAGED AGENT ACTIVATION -->
## Bunya-Jido Task Context

For implementation, debugging, or code-review work in this repository:

1. Before editing, run `bunya-jido context --root . --task "<user request>"`.
2. Obey the returned `Execution policy`; integrations should enforce the matching sandbox when available.
3. If the decision is `MATCH`, use `workspace_write` and read its `Must read`, `Contracts`, and `Tests` guidance before changing files.
4. If the decision is `IN_SCOPE_NO_ROUTE`, use `read_only_discovery`; state that the map has `No matching trusted route`, inspect ordinary repository evidence without editing, and request a new context decision or user approval before changing files. Do not infer a route.
5. If the decision is `OUT_OF_SCOPE`, use `read_only`; do not edit files or create placeholder implementations, and explain the reviewed repository boundary.
6. If the decision is `UNCERTAIN`, use `read_only`; inspect only when useful and request clarification before editing.
7. If context generation reports that no semantic blueprint or agent map exists yet, continue with ordinary repository inspection and treat map creation as separate work.
8. After editing, run `bunya-jido refresh-context --root . --changed-file <path>` for the changed files and use only routes justified by that output.
9. If the repository defines `stale_map_policy`, run `bunya-jido check-stale --root . --git-diff --require-reviewed`; when it reports `stale`, refresh and validate the map or record a reviewed no-structure-change decision in `.bunya-jido/MAP_REVIEW.md`.
10. Run the tests named by a matched route after the change, together with any checks required by the repository.

When asked to update the Bunya-Jido map itself, run `bunya-jido prepare --root . --quiet`,
execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`, then validate the blueprint and agent map.
<!-- END BUNYA-JIDO MANAGED AGENT ACTIVATION -->
