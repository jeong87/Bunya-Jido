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
    - **Basis:** documented | deterministic | grounded_inference | illustrative
    - **Derived from workflow/projection:**
    - **Why playback helps:**
    - **Steps:** node / transition / narration / evidence
    - **What must not be implied:**

    ## Rejected scenario ideas

    Record ideas rejected because they would overstate runtime order or add no
    useful reading path.
    """).strip() + "\n"


def make_studio_blueprint_prompt(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Studio Atlas Prompt - {project_name}

    You are preparing a grounded, repository-specific atlas interpretation.
    Do not edit application source code. Do not include secrets or raw API
    keys. Do not assume this repository is an agent system, workflow engine,
    web application, SDK, compiler, or library before inspecting evidence.

    ## Phase 2 publication boundary

    Studio authoring is opt-in. In Studio mode, the machine-readable blueprint
    contract is `bunya-jido-blueprint-v2`: write repository-local vocabulary,
    projections, scenario policy, and scenarios beneath the `atlas` object
    after drafting them in Markdown. The agent map remains grounded in the
    semantic nodes and workflows rather than depending on editorial narration.
    Advanced viewer projection styling and playback arrive in later phases.

    ## Files to create or refresh

    1. `.bunya-jido/COMPONENTS.md`
    2. `.bunya-jido/WORKFLOWS.md`
    3. `.bunya-jido/REPOSITORY_THESIS.md`
    4. `.bunya-jido/PROJECTIONS.md`
    5. `.bunya-jido/SCENARIOS.md`
    6. `.bunya-jido/bunya-jido.blueprint.json` (Studio v2 contract)
    7. `.bunya-jido/bunya-jido.agent-map.json`

    Inputs include the repository itself, the generated deterministic static
    scan, and the generated Studio v2 blueprint and agent-map schemas. Treat source,
    docs, tests, and inspectable artifacts as the evidence source.

    ## Non-negotiable rules

    - Derive the map vocabulary from this repository; do not transplant domain labels.
    - Consider two to four projection candidates before selecting a primary reading.
    - Keep grounded semantic claims distinct from future presentation or narration choices.
    - Choose `required`, `optional`, or `none_with_reason` as the scenario policy.
    - Use a behavioral scenario only for evidenced ordered behavior.
    - Use a structural tour only when it aids reading without implying runtime order.
    - If no scenario is honest or useful, explain `none_with_reason`.
    - Static/provider overlays are excluded from Studio primary projection by default.
      If a contextual overlay is justified, declare its existing map-local node family.

    ## Working sequence

    1. Read the static scan, repository docs/config, representative source,
       tests, examples, and relevant artifacts.
    2. Write `COMPONENTS.md` as a responsibility inventory without imposing
       a preselected visual taxonomy.
    3. Write `WORKFLOWS.md` as evidenced behaviors and structural reading
       routes, explicitly distinguishing ordered from non-ordered material.
    4. Write `REPOSITORY_THESIS.md` stating how this repository is best read
       and what it is not best explained as.
    5. Write `PROJECTIONS.md` comparing candidate first-screen explanations
       and selecting one primary projection.
    6. Write `SCENARIOS.md` with the scenario policy and up to five justified
       scenario candidates, or an honest no-scenario rationale.
    7. Write the Studio v2 blueprint and the agent map only with facts
       supported by the generated schemas and repository evidence. Keep the
       semantic contract separate from `atlas` presentation choices.
    8. Validate and build:

       `bunya-jido validate-blueprint --root .`

       `bunya-jido validate-agent-map --root .`

       `bunya-jido build --root . --out bunya-jido.html`

    Confirm the generated HTML path and clearly distinguish validated Studio v2
    contract data from viewer features planned for later phases.
    """).strip() + "\n"
