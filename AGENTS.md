<!-- BEGIN BUNYA-JIDO MANAGED AGENT ACTIVATION -->
## Bunya-Jido Task Context

For implementation, debugging, or code-review work in this repository:

1. Before editing, run `bunya-jido context --root . --task "<user request>"`.
2. If the decision is `MATCH`, read its `Must read`, `Contracts`, and `Tests` guidance before changing files.
3. If the decision is `OUT_OF_SCOPE`, do not edit files; explain the reviewed repository boundary.
4. If the decision is `UNCERTAIN`, prefer read-only inspection and request clarification before editing.
5. If the decision is `IN_SCOPE_NO_ROUTE` and the output says `No matching trusted route`, state that the map has no prepared route and continue cautiously with ordinary repository inspection. Do not infer a route.
6. If context generation reports that no semantic blueprint or agent map exists yet, continue with ordinary repository inspection and treat map creation as separate work.
7. After editing, run `bunya-jido refresh-context --root . --changed-file <path>` for the changed files and use only routes justified by that output.
8. If the repository defines `stale_map_policy`, run `bunya-jido check-stale --root . --git-diff --require-reviewed`; when it reports `stale`, refresh and validate the map or record a reviewed no-structure-change decision in `.bunya-jido/MAP_REVIEW.md`.
9. Run the tests named by a matched route after the change, together with any checks required by the repository.

When asked to update the Bunya-Jido map itself, run `bunya-jido prepare --root . --quiet`,
execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`, then validate the blueprint and agent map.
<!-- END BUNYA-JIDO MANAGED AGENT ACTIVATION -->
