# Scenario Candidates - Bunya-Jido

## Publication policy

- **Scenario policy:** required
- **Reason:** The map publication and trusted-context commands provide
  documented ordered paths that directly explain the product.

## Selected scenarios

### Scenario 1: Publish A Trusted Map

- **Kind:** behavioral
- **Basis:** documented workflow
- **Derived from workflow/projection:** `semantic_map_publication`, Trusted Publication
- **Why playback helps:** It shows that a renderer receives only a graph which
  passed the grounding gate before the viewer presents it.
- **Steps:** CLI build request -> Blueprint Projection -> Grounding Gate ->
  HTML Renderer -> Interactive Viewer.
- **What must not be implied:** The viewer supplies new evidence.

### Scenario 2: Request Bounded Agent Context

- **Kind:** behavioral
- **Basis:** documented workflow
- **Derived from workflow/projection:** `trusted_context_generation`, Bounded Agent Navigation
- **Why playback helps:** It explains how route guidance is conditioned on
  validated blueprint and agent-map references.
- **Steps:** CLI context request -> Trusted Context Generator -> Grounding
  Gate -> Agent Route Parity.
- **What must not be implied:** Every arbitrary coding task already has a route.

## Rejected scenario ideas

- A static-scan discovery animation was rejected because observations are
  support material and are not by themselves a trusted semantic publication.
- A benchmark animation was rejected because cross-domain fixtures evaluate
  honesty; they are not a runtime user journey.
