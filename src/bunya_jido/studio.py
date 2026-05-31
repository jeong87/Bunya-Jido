from __future__ import annotations

import textwrap


def studio_components_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Studio Components - {project_name}

    This document identifies repository responsibilities before choosing a
    visual vocabulary. Use repository evidence rather than a familiar domain
    taxonomy.

    ## Project summary

    Summarize what this repository provides after reading its docs, entrypoints,
    representative source, tests, examples, configuration, and generated
    artifacts.

    ## Component inventory

    For each meaningful responsibility, record:

    ### <Component name>

    - **Responsibility:** one sentence.
    - **Primary evidence:** repository-relative files, symbols, docs, or tests.
    - **Inputs / outputs:** important calls, data, artifacts, or effects.
    - **Contracts / boundaries:** invariants and surfaces needing care.
    - **Tests / validation:** relevant verification.
    - **First-read note for coding agents:** where a task should begin.

    ## Editorial cautions

    - Do not name a plane or family merely because it appears in another map.
    - Group implementation details unless they explain a boundary.
    - Note components that must not look central in the initial atlas view.
    """).strip() + "\n"


def studio_workflows_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Studio Workflows - {project_name}

    Inventory evidenced behavior and useful reading routes before deciding
    whether playback is appropriate.

    ## Observed behaviors and routes

    For each candidate, record:

    ### <Candidate name>

    - **Question answered:** what a newcomer learns.
    - **Kind:** ordered behavior | example usage | boundary review | structural reading route.
    - **Evidence:** repository-relative docs, source, tests, traces, or examples.
    - **Sequence, if evidenced:** ordered components or transitions.
    - **What must not be implied:** especially for non-runtime routes.
    - **Potential scenario value:** strong | optional | none, with reason.

    ## Ordered behavior assessment

    State whether the repository has strong, partial, weak, or no evidenced
    ordered behavior. Do not force a runtime workflow for an API surface,
    schema collection, documentation repository, or small utility package.
    """).strip() + "\n"


def repository_thesis_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Repository Thesis - {project_name}

    ## One-sentence thesis

    What system is this repository, and what organizing idea explains it best?

    ## Audience and onboarding question

    What should a first-time reader understand first?

    ## Evidence supporting this thesis

    List repository-relative docs, entrypoints, tests, source modules, examples,
    configuration, or artifacts.

    ## What this repository is not best explained as

    Identify tempting but distorting interpretations.

    ## Ordered behavior assessment

    - Strength: strong | partial | weak | none
    - Scenario policy recommendation: required | optional | none_with_reason
    - Risks of over-narration:
    """).strip() + "\n"


def projections_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Projection Candidates - {project_name}

    Propose two to four competing ways of explaining this repository. The
    selected projection should be grounded and legible on first view.

    ## Candidate A: <name>

    - **Question answered:**
    - **Landmark nodes:**
    - **Possible planes and project-local vocabulary:**
    - **Grounding strength:**
    - **First-screen value:**
    - **Distortion risks:**
    - **Scenario potential:**

    ## Candidate B: <name>

    - **Question answered:**
    - **Landmark nodes:**
    - **Possible planes and project-local vocabulary:**
    - **Grounding strength:**
    - **First-screen value:**
    - **Distortion risks:**
    - **Scenario potential:**

    ## Editorial selection

    - **Primary projection:**
    - **Why it wins:**
    - **Secondary views to retain:**
    - **Components that must not be over-centralized:**
    - **Static overlays permitted in the primary view, if any:**

    ## Machine-readable decision record

    Carry candidate comparison and selection reasoning into optional
    `atlas.decision_record` in the Studio v2 blueprint. Set
    `selected_projection_id` to the same value as
    `project.primary_projection_id`, and use that same ID for the selected
    projection candidate. Older v2 artifacts remain compatible without a
    decision record, but newly authored maps should include it.
    """).strip() + "\n"


def scenarios_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Scenario Candidates - {project_name}

    Scenarios are optional unless the repository has an evidenced, useful
    playback path. Never invent ordered behavior to satisfy a visual feature.

    ## Publication policy

    - **Scenario policy:** required | optional | none_with_reason
    - **Reason:**

    ## Workflow and tour inventory

    List grounded behavioral paths, example-usage tours, boundary tours, or
    structural reading routes that might help a newcomer.

    ## Selected scenarios (0-5 according to policy)

    ### Scenario 1: <name>

    - **Kind:** behavioral | structural_tour | example_usage | boundary | troubleshooting
    - **Basis:** documented_workflow | deterministic_trace | grounded_inference | illustrative_tour
    - **Derived from workflow/projection:**
    - **Why playback helps:**
    - **Steps:** node / transition / narration / evidence
    - **What must not be implied:**

    ## Rejected scenario ideas

    Record ideas rejected because they would overstate runtime order or add no
    useful reading path. Preserve selected and rejected scenario reasoning in
    optional `atlas.decision_record.scenario_candidates` for newly authored
    Studio v2 maps; selected candidate IDs must match published scenario IDs.
    """).strip() + "\n"


def atlas_interview_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Atlas Interview - {project_name}

    This is an internal checklist for the coding agent composing a Studio atlas.
    Use it while writing the authored Studio documents and blueprint. It is not
    a required publication artifact and need not be filled in separately unless
    a maintainer asks for a recorded interview.

    ## Public face

    - What does a user or integrator encounter first: CLI, API, UI route,
      generated output, configuration, or another surface?

    ## Central organizing idea

    - What does this repository transform, coordinate, expose, or preserve?
    - Which tempting explanation would distort it?

    ## Responsibility regions

    - What responsibilities matter independently of folder layout?
    - What belongs in the first 30 seconds of reading?
    - What should remain contextual or hidden until selected?

    ## Boundaries

    - Where are external calls, persistence, plugins, policy/security,
      compatibility, and generated-output boundaries?

    ## Ordered behavior

    - Is there evidenced execution or user-action order?
    - If not, what structural reading tour would help without implying runtime?
    - What scenario claims must not be made?

    ## Centrality risk

    - Which optional, conditional, detail, or failure-only components would
      mislead a reader if over-centralized?

    ## Agent tasks

    - Which task routes, must-read files, contracts, and tests help a coding
      agent safely begin likely maintenance work?
    """).strip() + "\n"


def make_studio_blueprint_prompt(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Studio Atlas Prompt - {project_name}

    You are preparing a grounded, repository-specific atlas interpretation.
    Do not edit application source code. Do not include secrets or raw API
    keys. Do not assume this repository is an agent system, workflow engine,
    web application, SDK, compiler, or library before inspecting evidence.

    ## Studio publication boundary

    Studio authoring is opt-in. In Studio mode, the machine-readable blueprint
    contract is `bunya-jido-blueprint-v2`: write repository-local vocabulary,
    projections, scenario policy, and scenarios beneath the `atlas` object
    after drafting them in Markdown. The agent map remains grounded in the
    semantic nodes and workflows rather than depending on editorial narration.
    A task route may optionally name one validated `projection_context` and
    validated `scenario_context` IDs so an agent can read the authored Studio
    orientation relevant to the task; omit them when no bounded context helps.
    The offline viewer presents validated projection vocabulary and published
    scenario playback without turning narration into evidence.

    ## Files to create or refresh

    1. `.bunya-jido/COMPONENTS.md`
    2. `.bunya-jido/WORKFLOWS.md`
    3. `.bunya-jido/REPOSITORY_THESIS.md`
    4. `.bunya-jido/PROJECTIONS.md`
    5. `.bunya-jido/SCENARIOS.md`
    6. `.bunya-jido/bunya-jido.blueprint.json` (Studio v2 contract)
    7. `.bunya-jido/bunya-jido.agent-map.json`

    Before writing those outputs, use `.bunya-jido/ATLAS_INTERVIEW.md` as an
    internal checklist. It is generated to improve your editorial reasoning,
    not as a required authored or publication artifact.

    Inputs include the repository itself, the generated deterministic static
    scan, and the generated Studio v2 blueprint and agent-map schemas. Treat source,
    docs, tests, and inspectable artifacts as the evidence source.

    ## Non-negotiable rules

    - Derive the map vocabulary from this repository; do not transplant domain labels.
    - Consider two to four projection candidates before selecting a primary reading.
    - For newly authored Studio maps, write optional `atlas.decision_record`
      so candidate comparisons, selected scenarios, and over-centralization
      risks remain machine-readable. Set its `selected_projection_id` equal
      to `project.primary_projection_id`; legacy v2 maps without it remain valid.
    - Do not assume a workflow is the primary projection. An API surface, state
      loop, transformation pipeline, plugin topology, data lineage, deployment
      boundary, component composition, or structural library tour may explain
      the repository more honestly.
    - Keep grounded semantic claims distinct from future presentation or narration choices.
    - Choose `required`, `optional`, or `none_with_reason` as the scenario policy.
    - Use a behavioral scenario only for evidenced ordered behavior.
    - A scenario is a reading aid, not a required runtime claim. Use a structural
      tour only when it aids reading without implying runtime order.
    - If no scenario is honest or useful, explain `none_with_reason`.
    - Static/provider overlays are excluded from Studio primary projection by default.
      If a contextual overlay is justified, declare its existing map-local node family.

    ## Role-pass working sequence

    1. **Cartographer:** Read the static scan, repository docs/config,
       representative source, tests, examples, relevant artifacts, and
       `ATLAS_INTERVIEW.md`; write `COMPONENTS.md` without imposing a
       preselected visual taxonomy.
    2. **Behavior and Route Analyst:** Write `WORKFLOWS.md` as evidenced
       behaviors and structural reading routes, explicitly distinguishing
       ordered from non-ordered material.
    3. **Repository Thesis Author:** Write `REPOSITORY_THESIS.md` stating how
       this repository is best read and what it is not best explained as.
    4. **Projection Critic:** Write `PROJECTIONS.md`, comparing two to four
       candidate first-screen explanations, recording distortion risks, and
       selecting one primary projection. Prepare the same rationale for
       `atlas.decision_record`.
    5. **Scenario Editor:** Write `SCENARIOS.md` with the scenario policy and
       up to five justified scenario candidates, or an honest no-scenario
       rationale. A structural tour must describe a reading path rather than
       execution order.
    6. **Vocabulary Designer:** Define map-local node and relation families
       whose meanings fit repository evidence instead of imported examples.
    7. **Atlas Composer:** Write the Studio v2 blueprint using grounded
       projection, visibility, scenario, and vocabulary choices, including
       `atlas.decision_record` for this newly authored map.
    8. **Evidence Auditor:** Verify core nodes, critical edges, and scenario
       steps against evidence paths and confidence before publication.
    9. **Visual Editor:** Check first-read density, label burden, centrality,
       projections, and scenario pacing; revise authored atlas choices where
       the first screen would mislead.
    10. **Agent Context Designer:** Write the agent map from validated
        semantic nodes and workflows so task routes remain bounded and
        grounded rather than depending on narration alone. When useful, add
        `projection_context` and `scenario_context` using only IDs published
        in `atlas.projections` and `atlas.scenarios`.
    11. **Validator:** Validate, evaluate, and build:

       `bunya-jido validate-blueprint --root .`

       `bunya-jido validate-agent-map --root .`

       `bunya-jido evaluate-atlas-quality --root . --require-pass --json`

       `bunya-jido build --root . --out bunya-jido.html`

    Confirm the generated HTML path and clearly distinguish validated Studio v2
    contract data, deterministic quality signals, and review-required editorial
    judgments.
    """).strip() + "\n"
