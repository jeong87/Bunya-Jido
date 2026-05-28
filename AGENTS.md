<!-- BEGIN BUNYA-JIDO MANAGED AGENT ACTIVATION -->
## Bunya-Jido Task Context

For implementation, debugging, or code-review work in this repository:

1. Before editing, run `bunya-jido context --root . --task "<user request>"`.
2. If a route is matched, read its `Must read`, `Contracts`, and `Tests` guidance before changing files.
3. If the output says `No matching trusted route`, state that the map has no prepared route for the task and continue with ordinary repository inspection. Do not infer a route.
4. If context generation reports that no semantic blueprint or agent map exists yet, continue with ordinary repository inspection and treat map creation as separate work.
5. Run the tests named by a matched route after the change, together with any checks required by the repository.

When asked to update the Bunya-Jido map itself, run `bunya-jido prepare --root . --quiet`,
execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`, then validate the blueprint and agent map.
<!-- END BUNYA-JIDO MANAGED AGENT ACTIVATION -->
