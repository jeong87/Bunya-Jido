from __future__ import annotations

import json
import re
import textwrap
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from .quality import evaluate_atlas_quality_obj
from .scanner import build_graph, infer_project_name, slug
from .schema import (
    blueprint_schema_v2 as studio_blueprint_schema_v2,
    validate_blueprint_v2_atlas,
)
from .studio import (
    make_studio_blueprint_prompt,
    projections_template,
    repository_thesis_template,
    scenarios_template,
    studio_components_template,
    studio_workflows_template,
)

BLUEPRINT_DIR = ".bunya-jido"
BLUEPRINT_FILE = "bunya-jido.blueprint.json"
AGENT_MAP_FILE = "bunya-jido.agent-map.json"
AGENT_EVALUATION_FILE = "bunya-jido.agent-evaluation.json"
COMPONENTS_FILE = "COMPONENTS.md"
WORKFLOWS_FILE = "WORKFLOWS.md"
REPOSITORY_THESIS_FILE = "REPOSITORY_THESIS.md"
PROJECTIONS_FILE = "PROJECTIONS.md"
SCENARIOS_FILE = "SCENARIOS.md"
MAP_REVIEW_FILE = "MAP_REVIEW.md"
AGENT_HANDOFF_FILE = "AGENT_HANDOFF.md"
PROMPT_FILE = "BUNYA_JIDO_BLUEPRINT_PROMPT.md"
SHORT_PROMPT_FILE = "CODEX_ONE_LINER.txt"
SCHEMA_FILE = "bunya-jido-blueprint.schema.json"
AGENT_MAP_SCHEMA_FILE = "bunya-jido-agent-map.schema.json"
STATIC_SCAN_FILE = "bunya-jido-static-scan.json"
MAP_REVIEW_ARTIFACTS = {
    f"{BLUEPRINT_DIR}/{BLUEPRINT_FILE}",
    f"{BLUEPRINT_DIR}/{AGENT_MAP_FILE}",
    f"{BLUEPRINT_DIR}/{MAP_REVIEW_FILE}",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-./]{12,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-./]{20,}"),
]

RELATION_LENS = {
    "calls": "call", "feeds": "call", "hands_off_to": "call", "receives": "call",
    "imports": "dependency", "uses_module": "dependency", "declares_dependency": "dependency",
    "api_calls": "api", "uses_model_lane": "api", "fallbacks_to": "api",
    "reads": "runtime", "queries": "runtime", "requests": "runtime", "requests_memory_via": "runtime",
    "writes": "runtime", "writes_to": "runtime", "updates": "runtime", "records": "runtime", "stored_in": "runtime",
    "emits": "runtime", "emitted_by": "runtime", "projects_from": "runtime", "projects_to": "runtime", "alerts": "runtime", "shows": "runtime",
    "guards": "contract", "gates": "contract", "validates": "contract", "checks": "contract", "checked_by": "contract",
    "uses_contract": "contract", "governs": "contract", "gates_claims_for": "contract",
    "blocks": "failure", "blocks_on": "failure", "routes_to": "failure", "routes_repair_to": "failure",
    "may_route_to": "failure", "routes": "failure", "risk": "failure", "affected_by": "failure", "guards_against": "failure",
    "submits_to": "run", "runs": "run", "enables": "run", "allows": "run", "can_hold": "run", "can_be_overridden_by": "run",
    "contains": "structure", "defines": "structure", "documents": "docs", "references": "docs", "links_to": "docs",
    "explains": "docs", "summarizes": "docs",
}

NODE_TYPE_DEFAULT_PLANE = {
    "agent": "reasoning",
    "component": "code",
    "service": "execution",
    "module": "code",
    "package": "repo",
    "contract": "governance",
    "artifact": "runtime",
    "event": "runtime",
    "failure": "validation",
    "llm_endpoint": "llm",
    "api_provider": "external",
    "database": "data",
    "queue": "runtime",
    "ui": "hitl",
    "document": "docs",
    "config": "config",
    "test": "tests",
    "repo": "repo",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def blueprint_dir(root: str | Path) -> Path:
    return Path(root).resolve() / BLUEPRINT_DIR


def default_blueprint_path(root: str | Path) -> Path:
    return blueprint_dir(root) / BLUEPRINT_FILE


def _read_json_relaxed(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Agents sometimes leave a fenced JSON blob. Recover the first object.
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _safe_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def blueprint_schema_v1() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Bunya-Jido Blueprint",
        "type": "object",
        "required": ["schema_version", "project", "nodes", "edges"],
        "additionalProperties": True,
        "properties": {
            "schema_version": {"const": "bunya-jido-blueprint-v1"},
            "project": {
                "type": "object",
                "required": ["name", "summary"],
                "properties": {
                    "name": {"type": "string"},
                    "summary": {"type": "string"},
                    "architecture_style": {"type": "string"},
                    "entrypoints": {"type": "array", "items": {"type": "string"}},
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
            },
            "planes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "label", "purpose"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "purpose": {"type": "string"},
                    },
                },
            },
            "nodes": {
                "type": "array",
                "minItems": 5,
                "items": {
                    "type": "object",
                    "required": ["id", "label", "type", "plane", "description", "evidence"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {"type": "string"},
                        "plane": {"type": "string"},
                        "description": {"type": "string"},
                        "importance": {"enum": ["core", "major", "support", "minor"]},
                        "source_path": {"type": "string"},
                        "llm_lane": {"type": "string"},
                        "llm_env": {"type": "string"},
                        "aliases": {"type": "array", "items": {"type": "string"}},
                        "parent": {"type": "string"},
                        "detail_level": {"enum": ["overview", "detail"]},
                        "evidence": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/evidence"},
                        },
                    },
                },
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["source", "target", "relation", "evidence"],
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "relation": {"type": "string"},
                        "lens": {"type": "string"},
                        "note": {"type": "string"},
                        "confidence": {"enum": ["deterministic", "llm_grounded", "llm_inferred", "unverified"]},
                        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
                    },
                },
            },
            "views": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "label", "description"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "node_ids": {"type": "array", "items": {"type": "string"}},
                        "include_planes": {"type": "array", "items": {"type": "string"}},
                        "include_relations": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "label", "children"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "children": {"type": "array", "items": {"type": "string"}},
                        "default_collapsed": {"type": "boolean"}
                    }
                }
            },
            "workflows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "label", "description"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "node_ids": {"type": "array", "items": {"type": "string"}},
                        "steps": {"type": "array"}
                    }
                }
            },
        },
        "$defs": {
            "evidence": {
                "type": "object",
                "required": ["kind", "path"],
                "properties": {
                    "kind": {"type": "string"},
                    "path": {"type": "string"},
                    "line": {"type": ["integer", "string"]},
                    "symbol": {"type": "string"},
                    "note": {"type": "string"},
                },
                "additionalProperties": True,
            }
        },

    }


def blueprint_schema_v2() -> dict[str, Any]:
    return studio_blueprint_schema_v2(blueprint_schema_v1())


def blueprint_schema(atlas_mode: str = "classic") -> dict[str, Any]:
    if atlas_mode == "classic":
        return blueprint_schema_v1()
    if atlas_mode == "studio":
        return blueprint_schema_v2()
    raise ValueError(f"Unsupported atlas mode: {atlas_mode}")


def agent_map_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Bunya-Jido Agent Navigation Map",
        "type": "object",
        "required": ["schema_version", "project", "task_routes"],
        "additionalProperties": True,
        "properties": {
            "schema_version": {"const": "bunya-jido-agent-map-v1"},
            "project": {"type": "object", "required": ["name", "summary"]},
            "task_routes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["task", "intent", "start_nodes", "must_read", "tests"],
                    "properties": {
                        "task": {"type": "string"},
                        "intent": {"type": "string"},
                        "start_nodes": {"type": "array", "items": {"type": "string"}},
                        "must_read": {"type": "array", "items": {"type": "string"}},
                        "contracts": {"type": "array", "items": {"type": "string"}},
                        "tests": {"type": "array", "items": {"type": "string"}},
                        "workflows": {"type": "array", "items": {"type": "string"}},
                        "safe_edit": {"type": "array", "items": {"type": "string"}},
                        "do_not_touch_without_reason": {"type": "array", "items": {"type": "string"}},
                        "common_failure_modes": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": "string"}
                    }
                }
            },
            "workflow_routes": {"type": "array", "items": {"type": "object"}},
            "stale_map_policy": {
                "type": "object",
                "required": ["rerun_when_changed", "ignore_when_changed"],
                "properties": {
                    "rerun_when_changed": {"type": "array", "items": {"type": "string"}},
                    "ignore_when_changed": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    }


def components_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Components · {project_name}

    This file is generated or refreshed by a coding agent during `bunya-jido prepare`.
    It is an intermediate architecture document for humans and future coding agents.

    ## Project summary

    Fill this in after reading README, docs, configuration, entrypoints, source modules, tests, and runtime artifacts.

    ## Component inventory

    For each component, use this shape:

    ### <Component name>

    - **Plane:** control | entry | domain | reasoning | execution | data/storage | runtime | validation/governance | llm | external | frontend/hitl | tests | docs
    - **Role:** one sentence responsibility.
    - **Primary evidence:** relative files, symbols, docs.
    - **Inputs:** important calls, data, events, artifacts, config.
    - **Outputs:** important calls, artifacts, events, side effects.
    - **Contracts / invariants:** schemas, interfaces, safety rules.
    - **Tests / validation:** relevant tests or manual checks.
    - **Notes for coding agents:** what to read first, what not to touch casually.

    ## Classification notes

    - Planes are responsibility regions, not folder names.
    - Group leaf files unless they are architectural boundaries.
    - Do not create a central repo/root node unless the repository itself acts as a runtime component.
    """).strip() + "\n"


def workflows_template(project_name: str) -> str:
    return textwrap.dedent(f"""
    # Bunya-Jido Workflows · {project_name}

    This file explains how components cooperate. It should become the source material for
    `bunya-jido.blueprint.json`, `bunya-jido.agent-map.json`, and future coding-agent context.

    ## Workflow inventory

    For each workflow, use this shape:

    ### <Workflow name>

    - **Trigger / entrypoint:** command, API route, scheduler, event, user action.
    - **Goal:** what the workflow accomplishes.
    - **Steps:** ordered component path.
    - **Reads:** configs, stores, artifacts, DBs, inputs.
    - **Writes / emits:** outputs, traces, DB updates, reports, side effects.
    - **Guards / validators:** budget, policy, safety, schema, capability, tests.
    - **External/LLM/API calls:** provider lanes, commands, network boundaries.
    - **Failure / repair path:** what happens when it blocks or fails.
    - **Agent handoff notes:** what Codex/Claude should inspect for modifications.

    ## Suggested workflows

    - Startup / initialization
    - Main happy path
    - LLM/API/provider path, if applicable
    - Data/storage/artifact path
    - Validation/safety/contract path
    - Failure/debug/repair path
    - Reporting/output path
    """).strip() + "\n"


def compact_static_scan(graph: dict[str, Any], limit_nodes: int = 180, limit_edges: int = 260) -> dict[str, Any]:
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))
    degree = Counter()
    for e in edges:
        degree[e.get("source")] += 1
        degree[e.get("target")] += 1
    nodes = sorted(nodes, key=lambda n: (bool(n.get("major")), degree[n.get("id")], n.get("size", 0)), reverse=True)[:limit_nodes]
    keep = {n.get("id") for n in nodes}
    edges = [e for e in edges if e.get("source") in keep and e.get("target") in keep]
    edges = sorted(edges, key=lambda e: (e.get("relation") not in {"contains", "defines"}, degree[e.get("source")] + degree[e.get("target")]), reverse=True)[:limit_edges]
    return {
        "schema_version": graph.get("schema_version", "bunya-jido-v1"),
        "generated_at": graph.get("generated_at"),
        "title": graph.get("title"),
        "description": "Compact deterministic scan. Use as evidence/hints, not as final architecture.",
        "stats": graph.get("stats", {}),
        "nodes": [
            {
                "id": n.get("id"), "label": n.get("label"), "type": n.get("type"), "plane": n.get("plane"),
                "description": n.get("description", ""), "source_path": n.get("source_path", ""),
                "major": n.get("major", False), "degree": degree[n.get("id")],
            }
            for n in nodes
        ],
        "edges": [
            {
                "source": e.get("source"), "target": e.get("target"), "relation": e.get("relation"),
                "lens": e.get("lens"), "note": e.get("note", ""), "confidence": e.get("confidence", "deterministic"),
                "evidence": e.get("evidence", [])[:2],
            }
            for e in edges
        ],
    }


def make_blueprint_prompt(project_name: str, atlas_mode: str = "classic") -> str:
    if atlas_mode not in {"classic", "studio"}:
        raise ValueError(f"Unsupported atlas mode: {atlas_mode}")
    if atlas_mode == "studio":
        return make_studio_blueprint_prompt(project_name)
    return textwrap.dedent(f"""
    # Bunya-Jido Blueprint Prompt

    You are helping Bunya-Jido create an **AI-first, human-auditable architecture context pack** for this repository.
    Do not edit application source code. Do not generate HTML. Do not include secrets or raw API keys.

    Your output files are:

    1. `.bunya-jido/COMPONENTS.md`
    2. `.bunya-jido/WORKFLOWS.md`
    3. `.bunya-jido/bunya-jido.blueprint.json`
    4. `.bunya-jido/bunya-jido.agent-map.json`

    The two Markdown files are not optional scratchpads. They are the intermediate design documents that make the blueprint good.
    Write them first, then derive the JSON files from them.

    ## Inputs available to you

    - `.bunya-jido/bunya-jido-static-scan.json`: deterministic scan of files, modules, docs, config, runtime artifacts, dependencies, and API hints.
    - `.bunya-jido/bunya-jido-blueprint.schema.json`: schema for the visual architecture blueprint.
    - `.bunya-jido/bunya-jido-agent-map.schema.json`: schema for the coding-agent navigation map.
    - `.bunya-jido/COMPONENTS.md`: template you must fill or rewrite.
    - `.bunya-jido/WORKFLOWS.md`: template you must fill or rewrite.
    - The repository itself is the source of truth. Read README/docs/config/source/tests/runtime artifacts directly when the static scan is shallow.

    ## Product goal

    Bunya-Jido is not asking for a file tree. It is asking for a useful map for future coding agents.
    A good result lets Codex, Claude Code, Cline, Cursor, or another coding agent answer:

    - What are the main components and responsibility boundaries?
    - What workflows move through those components?
    - Which files/contracts/tests should an agent read before editing a subsystem?
    - Which boundaries should an agent avoid touching casually?
    - Which LLM/API/model/provider routes, if any, shape behavior?
    - Which generated artifacts or runtime traces are useful for debugging?

    ## Required working method

    ### Step 1 — deterministic scan review

    Read `.bunya-jido/bunya-jido-static-scan.json`. Use it as a discovery aid, not as the final architecture.
    Static scan nodes may overrepresent low-level functions/classes. Group them unless they are architectural boundaries.

    ### Step 2 — write `.bunya-jido/COMPONENTS.md`

    Create a concise but substantive component document.
    Include:

    - project summary
    - entrypoints
    - planes / responsibility regions
    - components with role, evidence, inputs, outputs, contracts, tests
    - LLM/API/provider lanes if present
    - storage/data/runtime artifacts if present
    - human-facing or external surfaces if present
    - notes for future coding agents

    ### Step 3 — write `.bunya-jido/WORKFLOWS.md`

    Create a workflow document explaining component relationships.
    Include 3-8 important workflows when possible:

    - startup / initialization
    - main happy path
    - data/artifact flow
    - validation/safety/contract flow
    - LLM/API/provider flow if applicable
    - failure/debug/repair flow
    - reporting/output flow

    For each workflow, list trigger, ordered steps, reads, writes, guards, external calls, failure/repair path, and coding-agent notes.

    ### Step 4 — write `.bunya-jido/bunya-jido.blueprint.json`

    Derive the visual graph from the two Markdown docs. The blueprint should be compact and semantic.
    Target 30-70 visible nodes for most repos. Small repos may use 15-30. Large repos may use 70-120 only when truly necessary.

    ### Step 5 — write `.bunya-jido/bunya-jido.agent-map.json`

    Create a machine-readable handoff map for coding agents. It should answer:

    - For a task, where should the agent start?
    - Which files/docs/tests/contracts must it read?
    - What is safe to edit?
    - What should not be touched without a strong reason?
    - Which workflow or component context should be loaded?

    Every task route must reference node IDs and workflow IDs that exist in the semantic blueprint.
    Files in `must_read` and `tests` must resolve in the repository; otherwise trusted context and normal semantic publication are blocked.

    ### Step 6 — validate

    Run:

    `bunya-jido validate-blueprint --root .`

    and:

    `bunya-jido validate-agent-map --root .`

    Fix errors and grounding blockers. Classification warnings are acceptable only if they are honest and hard to avoid.
    Use `--allow-draft` only when a human explicitly wants to inspect an incomplete draft map.

    ## Plane classification guidance

    Pick 5-10 semantic planes. Planes are responsibility regions, not folder categories.
    Every plane you use must appear in `planes[]` with a clear purpose.

    Suggested planes:

    1. `control` — workflow, lifecycle, orchestration, scheduling, routing, retries, queueing, supervision.
    2. `entry` — CLI, HTTP API, UI route, command, package script.
    3. `domain` — project-specific business/research/application logic, algorithms, domain transforms.
    4. `reasoning` — agents, evaluators, planners, reviewers, debate, recommendation loops.
    5. `execution` — workers, runners, backends, job executors, subprocess/deployment adapters.
    6. `data` or `storage` — databases, artifact stores, schemas, datasets, caches, persistence.
    7. `runtime` — generated outputs, traces, event streams, status files, logs, queues.
    8. `validation` or `governance` — safety guards, policy gates, validators, budgets, permission enforcement.
    9. `llm` — model routers, prompt builders, provider protocols, embedding/model-server lanes.
    10. `external` — third-party APIs, cloud services, external CLIs, remote systems.
    11. `frontend` or `hitl` — UI, dashboards, reporting surfaces, notifications, manual approval.
    12. `tests` — grouped test surfaces that verify contracts or flows.
    13. `docs` — grouped architecture docs only when they materially explain the system.

    Calibration rules:

    - Avoid a central repo/root/blueprint node. Bunya-Jido hides synthetic roots by default; your blueprint should usually omit them.
    - Do not let a generic `code` plane swallow the architecture.
    - If one plane has more than about 40% of all nodes, split by responsibility.
    - Docs/tests should usually be grouped into 1-5 nodes, not one node per file.

    ## Node classification guidance

    Use `importance` carefully:

    - `core`: 5-12 landmarks maximum.
    - `major`: important subsystem nodes.
    - `support`: useful but not central.
    - `minor`: include only when it clarifies a boundary or detail view.

    Suggested node types:

    - `component`: subsystem or service responsibility.
    - `agent`: role-based autonomous/LLM/decision actor.
    - `service`: independent server/worker/process.
    - `module`: source module only when the module itself is the architecture unit.
    - `entrypoint`: CLI/API/UI route/package script.
    - `interface` or `protocol`: adapter interface or public API boundary.
    - `contract`: schema, typed contract, invariant, API envelope.
    - `validator` or `guard`: policy/safety/budget/contract gate.
    - `storage`: database, artifact store, filesystem store.
    - `artifact` or `runtime`: generated output, trace, status, log, queue message.
    - `llm_endpoint`: model router, provider lane, embedding lane, model server.
    - `external_api`: external service boundary.
    - `document`: grouped documentation surface.
    - `test`: grouped test surface.
    - `config`: configuration surface that materially shapes architecture.

    Grouping examples:

    - Many JSON schema files → one `contract` node such as "Published JSON Schemas".
    - Many workflow tests → one `test` node such as "Lifecycle and Resume Tests".
    - Many safety/release docs → one `document` node such as "Governance and Safety Docs".
    - Many classes serving one role → one `component` node, not many class nodes.
    - A function/class gets its own node only if it is an entrypoint, protocol, guard, router, state machine, executor, datastore, external boundary, or central agent.

    ## Collapse / expand guidance

    Use optional `groups` and node `parent` / `detail_level` when the repo has both overview and detail layers.

    - Overview nodes should have `detail_level: "overview"` or omit it.
    - Detail nodes should have `detail_level: "detail"` and `parent` set to the overview node or group id.
    - Groups should list child node ids and may use `default_collapsed: true`.
    - Default graph should be readable at overview level; detail nodes should help coding agents when expanded.

    ## LLM/API/model-provider guidance

    If the repo uses LLMs, model servers, embeddings, or provider APIs, make them visible:

    - Add `llm_lane` and/or `llm_env` to components that call models.
    - Add `type: "llm_endpoint"` for model routers, model servers, provider protocols, embedding lanes.
    - Use `external_api` nodes for external providers or external commands.
    - Use relation `uses_model_lane`, `api_calls`, or `fallbacks_to` for provider routes.
    - Env var names are okay. Actual secret values are forbidden.

    ## Relation guidance

    Prefer relation names the viewer styles well:

    - `calls`, `feeds`, `hands_off_to`
    - `reads`, `writes`, `records`, `emits`
    - `guards`, `gates`, `validates`, `uses_contract`
    - `blocks`, `routes_to`, `routes_repair_to`, `risk`
    - `api_calls`, `uses_model_lane`, `fallbacks_to`
    - `imports`, `uses_module`, `declares_dependency`
    - `documents`, `references`, `explains`, `contains`, `defines`

    Use `contains` sparingly. Prefer operational relations when evidence supports them.

    ## Evidence and confidence rules

    - Every node must have evidence.
    - Every edge must have evidence.
    - Evidence paths should be relative to repo root.
    - `deterministic`: directly visible from source/config/static scan.
    - `llm_grounded`: inferred by you but grounded in specific files/docs.
    - `llm_inferred`: plausible but weaker. Use sparingly and explain in `note`.
    - `unverified`: avoid unless the project truly lacks evidence and add a warning.

    ## Blueprint JSON shape

    ```json
    {{
      "schema_version": "bunya-jido-blueprint-v1",
      "project": {{
        "name": "{project_name}",
        "summary": "1-3 sentence system summary",
        "architecture_style": "short phrase",
        "entrypoints": ["path or command"],
        "warnings": []
      }},
      "planes": [
        {{"id": "control", "label": "Control", "purpose": "Orchestration and state"}}
      ],
      "nodes": [
        {{
          "id": "component:orchestrator",
          "label": "Orchestrator",
          "type": "component",
          "plane": "control",
          "importance": "core",
          "detail_level": "overview",
          "description": "What this node is responsible for.",
          "source_path": "src/example/orchestrator.py",
          "aliases": ["optional"],
          "evidence": [{{"kind": "source", "path": "src/example/orchestrator.py", "symbol": "Orchestrator"}}]
        }}
      ],
      "edges": [
        {{
          "source": "component:orchestrator",
          "target": "component:planner",
          "relation": "calls",
          "lens": "runtime",
          "confidence": "llm_grounded",
          "note": "Why this relation exists.",
          "evidence": [{{"kind": "source", "path": "src/example/orchestrator.py"}}]
        }}
      ],
      "groups": [
        {{
          "id": "group:provider_layer",
          "label": "Provider Layer",
          "description": "Overview/detail grouping for provider components.",
          "children": ["component:llm_router", "component:provider_protocols"],
          "default_collapsed": true
        }}
      ],
      "workflows": [
        {{
          "id": "main_flow",
          "label": "Main Flow",
          "description": "Primary successful workflow.",
          "node_ids": ["component:orchestrator", "component:runner"]
        }}
      ],
      "views": [
        {{
          "id": "architecture",
          "label": "Architecture",
          "description": "Core subsystem map",
          "node_ids": ["component:orchestrator", "component:planner"]
        }}
      ]
    }}
    ```

    ## Agent map JSON shape

    ```json
    {{
      "schema_version": "bunya-jido-agent-map-v1",
      "project": {{"name": "{project_name}", "summary": "same project summary"}},
      "task_routes": [
        {{
          "task": "modify provider behavior",
          "intent": "Change how model/API calls are routed or sanitized.",
          "start_nodes": ["component:llm_router"],
          "must_read": ["src/example/llm.py", ".bunya-jido/COMPONENTS.md#llm-router"],
          "contracts": ["ProviderRequest", "ProviderResponse"],
          "tests": ["tests/test_provider.py"],
          "workflows": ["llm_api_flow"],
          "safe_edit": ["src/example/provider_*.py"],
          "do_not_touch_without_reason": ["src/example/orchestrator.py"],
          "common_failure_modes": ["provider schema drift", "secret leakage"],
          "notes": "Short guidance for a coding agent."
        }}
      ],
      "workflow_routes": [],
      "stale_map_policy": {{
        "rerun_when_changed": ["pyproject.toml", "src/**", "docs/**"],
        "ignore_when_changed": [".git/**", "node_modules/**", "__pycache__/**"]
      }}
    }}
    ```

    ## Final self-check

    - COMPONENTS.md and WORKFLOWS.md exist and are useful.
    - The blueprint is not a file tree.
    - Planes are responsibility regions.
    - Core nodes are few and recognizable.
    - Leaf files are grouped unless architecturally important.
    - LLM/API/provider routes are visible if the repo uses them.
    - Edges say what actually happens.
    - The agent map contains useful task routes for future coding agents.
    - Every task route references existing blueprint nodes/workflows and resolving required files/tests.
    - Evidence supports every important node and edge.

    ## Final step

    Run:

    `bunya-jido validate-blueprint --root .`

    and:

    `bunya-jido validate-agent-map --root .`

    Fix errors and grounding blockers. When done, say only:

    `준비완료: .bunya-jido/COMPONENTS.md .bunya-jido/WORKFLOWS.md .bunya-jido/bunya-jido.blueprint.json .bunya-jido/bunya-jido.agent-map.json`
    """).strip() + "\n"


def prepare_blueprint_workspace(
    root: str | Path,
    *,
    mode: str = "auto",
    max_files: int = 5000,
    max_nodes: int = 700,
    max_edges: int = 1800,
    include_hidden: bool = False,
    quiet: bool = False,
    show_root: bool = False,
    data_policy: str = "summary",
    max_data_files: int = 25,
    atlas_mode: str = "classic",
) -> dict[str, Path]:
    if atlas_mode not in {"classic", "studio"}:
        raise ValueError(f"Unsupported atlas mode: {atlas_mode}")
    root_path = Path(root).resolve()
    outdir = blueprint_dir(root_path)
    outdir.mkdir(parents=True, exist_ok=True)
    graph = build_graph(root_path, mode=mode, max_files=max_files, max_nodes=max_nodes, max_edges=max_edges, include_hidden=include_hidden, show_root=show_root, data_policy=data_policy, max_data_files=max_data_files)
    compact = compact_static_scan(graph)
    project_name = infer_project_name(root_path)
    paths = {
        "dir": outdir,
        "static_scan": outdir / STATIC_SCAN_FILE,
        "schema": outdir / SCHEMA_FILE,
        "agent_map_schema": outdir / AGENT_MAP_SCHEMA_FILE,
        "components": outdir / COMPONENTS_FILE,
        "workflows": outdir / WORKFLOWS_FILE,
        "repository_thesis": outdir / REPOSITORY_THESIS_FILE,
        "projections": outdir / PROJECTIONS_FILE,
        "scenarios": outdir / SCENARIOS_FILE,
        "agent_map": outdir / AGENT_MAP_FILE,
        "handoff": outdir / AGENT_HANDOFF_FILE,
        "prompt": outdir / PROMPT_FILE,
        "short_prompt": outdir / SHORT_PROMPT_FILE,
        "blueprint": outdir / BLUEPRINT_FILE,
    }
    _safe_write_json(paths["static_scan"], compact)
    _safe_write_json(paths["schema"], blueprint_schema(atlas_mode))
    _safe_write_json(paths["agent_map_schema"], agent_map_schema())
    if not paths["components"].exists():
        component_text = studio_components_template(project_name) if atlas_mode == "studio" else components_template(project_name)
        paths["components"].write_text(component_text, encoding="utf-8")
    if not paths["workflows"].exists():
        workflow_text = studio_workflows_template(project_name) if atlas_mode == "studio" else workflows_template(project_name)
        paths["workflows"].write_text(workflow_text, encoding="utf-8")
    if atlas_mode == "studio":
        for key, template in (
            ("repository_thesis", repository_thesis_template),
            ("projections", projections_template),
            ("scenarios", scenarios_template),
        ):
            if not paths[key].exists():
                paths[key].write_text(template(project_name), encoding="utf-8")
    paths["prompt"].write_text(make_blueprint_prompt(project_name, atlas_mode=atlas_mode), encoding="utf-8")
    if atlas_mode == "studio":
        short_prompt = (
            "Run `bunya-jido prepare --root . --atlas-mode studio --quiet` if needed, then read and execute "
            "`.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Refresh the five Studio Markdown inputs, keep "
            "the blueprint compatible with the Studio v2 schema and the agent map grounded in its semantic layer, validate them, "
            "then run `bunya-jido build --root . --out bunya-jido.html` and report the HTML path.\n"
        )
    else:
        short_prompt = (
            "Run `bunya-jido prepare --root . --quiet` if needed, then read and execute "
            "`.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Create or refresh "
            "`.bunya-jido/COMPONENTS.md`, `.bunya-jido/WORKFLOWS.md`, "
            "`.bunya-jido/bunya-jido.blueprint.json`, and `.bunya-jido/bunya-jido.agent-map.json`; "
            "run `bunya-jido validate-blueprint --root .` and `bunya-jido validate-agent-map --root .`; "
            "fix errors and grounding blockers and reduce classification warnings when practical; then say `준비완료`.\n"
        )
    paths["short_prompt"].write_text(short_prompt, encoding="utf-8")
    if not quiet:
        print(f"Bunya-Jido blueprint workspace prepared: {outdir}")
        print(f"Prompt: {paths['prompt']}")
        print("Tell Codex/Claude Code:")
        print("  Read and execute .bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md")
        print("Expected outputs:")
        print(f"  {paths['components']}")
        print(f"  {paths['workflows']}")
        if atlas_mode == "studio":
            print(f"  {paths['repository_thesis']}")
            print(f"  {paths['projections']}")
            print(f"  {paths['scenarios']}")
        print(f"  {paths['blueprint']}")
        print(f"  {paths['agent_map']}")
    return paths


def _string_has_secret(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(p.search(value) for p in SECRET_PATTERNS)


def _walk_strings(obj: Any):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def _workflow_edge_pairs(bp: dict[str, Any]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for workflow in bp.get("workflows") or []:
        if not isinstance(workflow, dict):
            continue
        sequence = [str(node_id) for node_id in workflow.get("node_ids") or [] if node_id]
        if not sequence:
            for step in workflow.get("steps") or []:
                if isinstance(step, str) and step:
                    sequence.append(step)
                elif isinstance(step, dict):
                    node_id = step.get("node") or step.get("node_id")
                    if node_id:
                        sequence.append(str(node_id))
        pairs.update((source, target) for source, target in zip(sequence, sequence[1:]))
    return pairs


def _evidence_path_missing(path: Any, root_path: Path) -> bool:
    if not path or re.match(r"^[a-z]+://", str(path)):
        return False
    value = str(path).split("#", 1)[0]
    if re.match(r"^[A-Za-z]:\\", value):
        candidate = Path(value)
    else:
        value = re.sub(r":\d+(?::\d+)?$", "", value)
        candidate = root_path / value
    return bool(value) and not candidate.exists()


def _route_path_resolves(path: Any, root_path: Path) -> bool:
    if not isinstance(path, str) or not path:
        return False
    if re.match(r"^[a-z]+://", path):
        return False
    value = path.split("#", 1)[0]
    value = re.sub(r":\d+(?::\d+)?$", "", value)
    route_path = Path(value)
    if route_path.is_absolute() or re.match(r"^[A-Za-z]:\\", value):
        return False
    if any(char in value for char in "*?["):
        return any(candidate.resolve().is_relative_to(root_path) for candidate in root_path.glob(value))
    candidate = (root_path / value).resolve()
    return candidate.is_relative_to(root_path) and candidate.exists()


def validate_blueprint_obj(bp: dict[str, Any], root: str | Path | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    publish_blockers: list[str] = []
    schema_version = bp.get("schema_version")
    if schema_version not in {"bunya-jido-blueprint-v1", "bunya-jido-blueprint-v2"}:
        errors.append(
            "schema_version must be bunya-jido-blueprint-v1 or bunya-jido-blueprint-v2"
        )
    project = bp.get("project")
    if not isinstance(project, dict) or not project.get("name") or not project.get("summary"):
        errors.append("project.name and project.summary are required")
    nodes = bp.get("nodes")
    edges = bp.get("edges")
    if not isinstance(nodes, list) or len(nodes) < 3:
        errors.append("nodes must be a list with at least 3 items")
        nodes = []
    if not isinstance(edges, list):
        errors.append("edges must be a list")
        edges = []
    core_node_ids = {
        str(n.get("id"))
        for n in nodes
        if isinstance(n, dict) and n.get("id") and str(n.get("importance") or "").lower() == "core"
    }
    if nodes and not core_node_ids:
        publish_blockers.append(
            "semantic blueprint has no core nodes; mark architectural landmarks with importance=core"
        )
    workflow_pairs = _workflow_edge_pairs(bp)
    critical_edges: list[dict[str, Any]] = []
    ids: set[str] = set()
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append(f"nodes[{i}] is not an object")
            continue
        nid = n.get("id")
        if not nid:
            errors.append(f"nodes[{i}].id is required")
            continue
        if nid in ids:
            errors.append(f"duplicate node id: {nid}")
        ids.add(str(nid))
        for key in ("label", "type", "plane", "description"):
            if not n.get(key):
                warnings.append(f"node {nid} missing {key}")
        ev = n.get("evidence")
        if not isinstance(ev, list) or not ev:
            warnings.append(f"node {nid} has no evidence")
            if str(nid) in core_node_ids:
                publish_blockers.append(f"core node {nid} has no evidence")
        if str(nid).startswith("repo:") or str(n.get("type", "")).lower() == "repo":
            warnings.append(f"node {nid} is a repo/root node; usually omit it because build hides synthetic roots by default")
    # Semantic classification hygiene checks. These are warnings, not hard failures.
    used_planes = Counter(str(n.get("plane") or "") for n in nodes if isinstance(n, dict))
    used_types = Counter(str(n.get("type") or "") for n in nodes if isinstance(n, dict))
    declared_planes = {str(p.get("id")) for p in (bp.get("planes") or []) if isinstance(p, dict) and p.get("id")}
    for plane in sorted(k for k in used_planes if k and k not in declared_planes):
        warnings.append(f"plane '{plane}' is used by nodes but not declared in planes[]")
    node_count_for_hygiene = max(1, len(nodes))
    for plane, count in used_planes.items():
        if plane and len(nodes) >= 20 and count / node_count_for_hygiene > 0.40 and plane not in {"repo"}:
            warnings.append(f"plane '{plane}' contains {count}/{len(nodes)} nodes; consider splitting by responsibility")
    leaf_count = sum(used_types.get(t, 0) for t in ("function", "class"))
    if len(nodes) >= 25 and leaf_count / node_count_for_hygiene > 0.25:
        warnings.append(f"{leaf_count} function/class nodes detected; consider grouping leaf implementation details into component nodes")
    doc_count = used_types.get("document", 0)
    if doc_count > 8:
        warnings.append(f"{doc_count} document nodes detected; consider grouping documentation into architecture/governance/API doc nodes")
    test_count = used_types.get("test", 0)
    if test_count > 8:
        warnings.append(f"{test_count} test nodes detected; consider grouping tests by contract/workflow")
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append(f"edges[{i}] is not an object")
            continue
        s, t = e.get("source"), e.get("target")
        if not s or not t:
            errors.append(f"edges[{i}] source/target required")
            continue
        if s not in ids:
            errors.append(f"edge {i} source not found: {s}")
        if t not in ids:
            errors.append(f"edge {i} target not found: {t}")
        is_critical = (s in core_node_ids and t in core_node_ids) or (
            (str(s), str(t)) in workflow_pairs and (s in core_node_ids or t in core_node_ids)
        )
        if is_critical:
            critical_edges.append(e)
        if not e.get("relation"):
            warnings.append(f"edge {s}->{t} missing relation")
        if not e.get("evidence"):
            warnings.append(f"edge {s}->{t} has no evidence")
            if is_critical:
                publish_blockers.append(f"critical edge {s}->{t} has no evidence")
        if e.get("confidence") == "unverified":
            warnings.append(f"edge {s}->{t} is unverified")
            if is_critical:
                publish_blockers.append(f"critical edge {s}->{t} is unverified")
    if any(_string_has_secret(s) for s in _walk_strings(bp)):
        errors.append("blueprint appears to contain secret-like text; remove raw tokens/API keys/passwords")
    unresolved_core_nodes: set[str] = set()
    unresolved_critical_edges: set[tuple[str, str]] = set()
    if root is not None:
        root_path = Path(root).resolve()
        for n in nodes:
            evs = list(n.get("evidence") or [])
            sp = n.get("source_path")
            if sp:
                evs.append({"path": sp, "kind": "source_path"})
            for ev in evs[:8]:
                path = ev.get("path") if isinstance(ev, dict) else None
                if _evidence_path_missing(path, root_path):
                    warnings.append(f"evidence path not found: {path} for node {n.get('id')}")
                    if str(n.get("id")) in core_node_ids:
                        unresolved_core_nodes.add(str(n.get("id")))
                        publish_blockers.append(f"core node {n.get('id')} has unresolved evidence path: {path}")
                    break
        critical_ids = {id(edge) for edge in critical_edges}
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            for ev in (edge.get("evidence") or [])[:8]:
                path = ev.get("path") if isinstance(ev, dict) else None
                if _evidence_path_missing(path, root_path):
                    s, t = str(edge.get("source")), str(edge.get("target"))
                    warnings.append(f"evidence path not found: {path} for edge {s}->{t}")
                    if id(edge) in critical_ids:
                        unresolved_critical_edges.add((s, t))
                        publish_blockers.append(f"critical edge {s}->{t} has unresolved evidence path: {path}")
                    break
    grounded_nodes = sum(1 for n in nodes if n.get("evidence"))
    grounded_edges = sum(1 for e in edges if e.get("evidence") and e.get("confidence") != "unverified")
    grounded_core_nodes = sum(
        1 for n in nodes if str(n.get("id")) in core_node_ids and n.get("evidence") and str(n.get("id")) not in unresolved_core_nodes
    )
    grounded_critical_edges = sum(
        1
        for e in critical_edges
        if e.get("evidence")
        and e.get("confidence") != "unverified"
        and (str(e.get("source")), str(e.get("target"))) not in unresolved_critical_edges
    )
    atlas_metrics: dict[str, Any] = {}
    if schema_version == "bunya-jido-blueprint-v2":
        atlas_errors, atlas_warnings, atlas_blockers, atlas_metrics = (
            validate_blueprint_v2_atlas(bp)
        )
        errors.extend(atlas_errors)
        warnings.extend(atlas_warnings)
        publish_blockers.extend(atlas_blockers)
    publish_blockers = list(dict.fromkeys(publish_blockers))
    grounding_status = "blocked" if errors or publish_blockers else "grounded"
    metrics = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "grounded_node_ratio": round(grounded_nodes / max(1, len(nodes)), 3),
        "grounded_edge_ratio": round(grounded_edges / max(1, len(edges)), 3),
        "core_node_count": len(core_node_ids),
        "critical_edge_count": len(critical_edges),
        "grounded_core_node_ratio": round(grounded_core_nodes / max(1, len(core_node_ids)), 3),
        "grounded_critical_edge_ratio": round(grounded_critical_edges / max(1, len(critical_edges)), 3),
        "grounding_status": grounding_status,
        "publish_blocker_count": len(publish_blockers),
        "publish_blockers": publish_blockers[:40],
        "warning_count": len(warnings),
        "error_count": len(errors),
        **atlas_metrics,
    }
    return errors, warnings, metrics


def validate_blueprint_file(path: str | Path, root: str | Path | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    bp = _read_json_relaxed(Path(path))
    return validate_blueprint_obj(bp, root=root)


def evaluate_atlas_quality(
    root: str | Path,
    blueprint_path: str | Path | None = None,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = Path(blueprint_path).resolve() if blueprint_path else default_blueprint_path(root_path)
    if not path.exists():
        raise ValueError(f"Atlas quality requires a semantic blueprint: {path}")
    blueprint = _read_json_relaxed(path)
    errors, _, metrics = validate_blueprint_obj(blueprint, root=root_path)
    return evaluate_atlas_quality_obj(
        blueprint,
        root=root_path,
        validation_errors=errors,
        validation_metrics=metrics,
    )



def default_agent_map_path(root: str | Path) -> Path:
    return blueprint_dir(root) / AGENT_MAP_FILE


def default_agent_evaluation_path(root: str | Path) -> Path:
    return blueprint_dir(root) / AGENT_EVALUATION_FILE


def validate_agent_map_obj(agent_map: dict[str, Any], root: str | Path | None = None, blueprint: dict[str, Any] | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    publish_blockers: list[str] = []
    blocked_route_indexes: set[int] = set()
    if agent_map.get("schema_version") != "bunya-jido-agent-map-v1":
        errors.append("schema_version must be bunya-jido-agent-map-v1")
    project = agent_map.get("project")
    if not isinstance(project, dict) or not project.get("name") or not project.get("summary"):
        errors.append("project.name and project.summary are required")
    routes = agent_map.get("task_routes")
    if not isinstance(routes, list):
        errors.append("task_routes must be a list")
        routes = []
    bp_node_by_id: dict[str, dict[str, Any]] = {}
    bp_workflow_by_id: dict[str, dict[str, Any]] = {}
    if blueprint:
        bp_node_by_id = {str(n.get("id")): n for n in blueprint.get("nodes", []) if isinstance(n, dict) and n.get("id")}
        bp_workflow_by_id = {
            str(workflow.get("id")): workflow
            for workflow in blueprint.get("workflows", [])
            if isinstance(workflow, dict) and workflow.get("id")
        }
    root_path = Path(root).resolve() if root is not None else None
    for i, route in enumerate(routes):
        if not isinstance(route, dict):
            errors.append(f"task_routes[{i}] is not an object")
            continue
        task = str(route.get("task") or i)
        route_blockers: list[str] = []
        if not route.get("task"):
            errors.append(f"task_routes[{i}].task is required")
        if not route.get("intent"):
            errors.append(f"task_routes[{i}].intent is required")
        route_lists: dict[str, list[Any]] = {}
        for key in ("start_nodes", "must_read", "tests", "workflows", "safe_edit"):
            value = route.get(key) or []
            if not isinstance(value, list):
                errors.append(f"task_routes[{i}].{key} must be a list")
                value = []
            route_lists[key] = value
        start_nodes = route_lists["start_nodes"]
        if not start_nodes:
            route_blockers.append(f"task route {task} has no start_nodes")
        elif not blueprint:
            route_blockers.append(f"task route {task} cannot be trusted without a semantic blueprint")
        else:
            missing = [n for n in start_nodes if str(n) not in bp_node_by_id]
            if missing:
                route_blockers.append(f"task route {task} references nodes not in blueprint: {missing[:5]}")
            for node_id in [str(n) for n in start_nodes if str(n) in bp_node_by_id]:
                node = bp_node_by_id[node_id]
                if node_id.startswith("repo:") or str(node.get("type") or "").lower() == "repo":
                    route_blockers.append(f"task route {task} starts at hidden repo/root node: {node_id}")
                evidence = node.get("evidence") or []
                if not evidence:
                    route_blockers.append(f"task route {task} starts at ungrounded node: {node_id}")
                elif root_path and not any(
                    isinstance(ev, dict) and _route_path_resolves(ev.get("path"), root_path)
                    for ev in evidence
                ):
                    route_blockers.append(f"task route {task} starts at node with unresolved evidence: {node_id}")
        workflows = route_lists["workflows"]
        if workflows and not blueprint:
            route_blockers.append(f"task route {task} references workflows without a semantic blueprint")
        elif workflows:
            missing_workflows = [workflow for workflow in workflows if str(workflow) not in bp_workflow_by_id]
            if missing_workflows:
                route_blockers.append(f"task route {task} references workflows not in blueprint: {missing_workflows[:5]}")
            for workflow_id in [str(w) for w in workflows if str(w) in bp_workflow_by_id]:
                workflow_nodes: list[str] = []
                workflow = bp_workflow_by_id[workflow_id]
                workflow_nodes.extend(str(node_id) for node_id in workflow.get("node_ids") or [] if node_id)
                for step in workflow.get("steps") or []:
                    if isinstance(step, str) and step:
                        workflow_nodes.append(step)
                    elif isinstance(step, dict) and (step.get("node") or step.get("node_id")):
                        workflow_nodes.append(str(step.get("node") or step.get("node_id")))
                missing_nodes = [node_id for node_id in workflow_nodes if node_id not in bp_node_by_id]
                if missing_nodes:
                    route_blockers.append(
                        f"task route {task} references workflow {workflow_id} with missing nodes: {missing_nodes[:5]}"
                    )
                hidden_nodes = [
                    node_id
                    for node_id in workflow_nodes
                    if node_id in bp_node_by_id
                    and (
                        node_id.startswith("repo:")
                        or str(bp_node_by_id[node_id].get("type") or "").lower() == "repo"
                    )
                ]
                if hidden_nodes:
                    route_blockers.append(
                        f"task route {task} references workflow {workflow_id} with hidden repo/root nodes: {hidden_nodes[:5]}"
                    )
        must_read = route_lists["must_read"]
        tests = route_lists["tests"]
        if not must_read:
            route_blockers.append(f"task route {task} has empty must_read")
        if not tests:
            route_blockers.append(f"task route {task} has empty tests")
        if root_path:
            for path in list(must_read)[:20]:
                if not _route_path_resolves(path, root_path):
                    route_blockers.append(f"task route {task} must-read path not found: {path}")
            for path in list(tests)[:20]:
                if not _route_path_resolves(path, root_path):
                    route_blockers.append(f"task route {task} test path not found: {path}")
            for path in route_lists["safe_edit"][:20]:
                if isinstance(path, str) and path and not _route_path_resolves(path, root_path):
                    warnings.append(f"agent-map safe-edit path not found: {path} in route {task}")
        if route_blockers:
            blocked_route_indexes.add(i)
            publish_blockers.extend(route_blockers)
    if any(_string_has_secret(s) for s in _walk_strings(agent_map)):
        errors.append("agent map appears to contain secret-like text; remove raw tokens/API keys/passwords")
    stale_policy = agent_map.get("stale_map_policy")
    if stale_policy is not None:
        if not isinstance(stale_policy, dict):
            errors.append("stale_map_policy must be an object")
        else:
            for key in ("rerun_when_changed", "ignore_when_changed"):
                patterns = stale_policy.get(key)
                if not isinstance(patterns, list) or not all(
                    isinstance(pattern, str) and pattern.strip() for pattern in patterns
                ):
                    errors.append(f"stale_map_policy.{key} must be a list of non-empty strings")
    publish_blockers = list(dict.fromkeys(publish_blockers))
    projectable_route_indexes = [i for i, route in enumerate(routes) if isinstance(route, dict) and i not in blocked_route_indexes]
    grounding_status = "blocked" if errors or publish_blockers else "grounded"
    metrics = {
        "task_route_count": len(routes),
        "trusted_route_count": len(projectable_route_indexes),
        "grounded_route_ratio": round(len(projectable_route_indexes) / max(1, len(routes)), 3),
        "grounding_status": grounding_status,
        "publish_blocker_count": len(publish_blockers),
        "publish_blockers": publish_blockers[:40],
        "projectable_route_indexes": projectable_route_indexes,
        "warning_count": len(warnings),
        "error_count": len(errors),
    }
    return errors, warnings, metrics


def validate_agent_map_file(path: str | Path, root: str | Path | None = None, blueprint_path: str | Path | None = None) -> tuple[list[str], list[str], dict[str, Any]]:
    agent_map = _read_json_relaxed(Path(path))
    bp = None
    if blueprint_path and Path(blueprint_path).exists():
        bp = _read_json_relaxed(Path(blueprint_path))
    elif root is not None and default_blueprint_path(root).exists():
        bp = _read_json_relaxed(default_blueprint_path(root))
    return validate_agent_map_obj(agent_map, root=root, blueprint=bp)


def _load_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


GENERIC_ROUTE_TERMS = {
    "add", "change", "changed", "debug", "edit", "fix", "implement", "improve",
    "modify", "review", "update", "behavior", "context", "feature", "issue", "map",
    "repository", "route", "task", "work", "working",
}


def _task_match_terms(task: str | None) -> list[str]:
    if not task:
        return []
    return list(
        dict.fromkeys(
            word
            for word in re.findall(r"\w+", task.lower())
            if len(word) >= 3 and word not in GENERIC_ROUTE_TERMS
        )
    )


def _normalize_context_path(path: str) -> str:
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _context_paths_overlap(left: str, right: str) -> bool:
    left_path = _normalize_context_path(left)
    right_path = _normalize_context_path(right)
    if not left_path or not right_path:
        return False
    return (
        left_path == right_path
        or left_path.startswith(right_path + "/")
        or right_path.startswith(left_path + "/")
    )


def _matches_policy_path(path: str, patterns: list[str]) -> bool:
    normalized = _normalize_context_path(path)
    return any(fnmatchcase(normalized, _normalize_context_path(pattern)) for pattern in patterns)


def evaluate_map_freshness(root: str | Path, changed_files: list[str]) -> dict[str, Any]:
    root_path = Path(root).resolve()
    agent_map_path = default_agent_map_path(root_path)
    changed = list(
        dict.fromkeys(
            _normalize_context_path(path) for path in changed_files if str(path).strip()
        )
    )
    if not agent_map_path.exists():
        return {
            "status": "not_configured",
            "reason": "agent map not found",
            "changed_files": changed,
            "triggering_files": [],
            "ignored_files": [],
            "review_artifacts": [],
        }
    agent_map = _read_json_relaxed(agent_map_path)
    policy = agent_map.get("stale_map_policy")
    if not isinstance(policy, dict):
        return {
            "status": "not_configured",
            "reason": "agent map has no stale_map_policy",
            "changed_files": changed,
            "triggering_files": [],
            "ignored_files": [],
            "review_artifacts": [],
        }
    rerun_patterns = policy.get("rerun_when_changed")
    ignore_patterns = policy.get("ignore_when_changed")
    if not isinstance(rerun_patterns, list) or not all(
        isinstance(pattern, str) and pattern.strip() for pattern in rerun_patterns
    ) or not isinstance(ignore_patterns, list) or not all(
        isinstance(pattern, str) and pattern.strip() for pattern in ignore_patterns
    ):
        return {
            "status": "invalid_policy",
            "reason": "stale_map_policy lists are invalid",
            "changed_files": changed,
            "triggering_files": [],
            "ignored_files": [],
            "review_artifacts": [],
        }
    ignored = [path for path in changed if _matches_policy_path(path, ignore_patterns)]
    triggering = [
        path
        for path in changed
        if path not in ignored and _matches_policy_path(path, rerun_patterns)
    ]
    review_artifacts = [path for path in changed if path in MAP_REVIEW_ARTIFACTS]
    if not triggering:
        status = "current"
        reason = "no changed file matches stale-map review policy"
    elif review_artifacts:
        status = "review_recorded"
        reason = "triggering changes include a map review artifact update"
    else:
        status = "stale"
        reason = "triggering changes require a semantic map review"
    return {
        "status": status,
        "reason": reason,
        "changed_files": changed,
        "triggering_files": triggering,
        "ignored_files": ignored,
        "review_artifacts": review_artifacts,
        "rerun_when_changed": rerun_patterns,
        "ignore_when_changed": ignore_patterns,
    }


def _affected_nodes_for_changes(changed_files: list[str], node_by_id: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    affected: dict[str, list[str]] = {}
    for node_id, node in node_by_id.items():
        evidence_paths: list[str] = []
        if node.get("source_path"):
            evidence_paths.append(str(node.get("source_path")).split(":", 1)[0])
        for evidence in node.get("evidence") or []:
            if isinstance(evidence, dict) and evidence.get("path"):
                evidence_paths.append(str(evidence["path"]).split(":", 1)[0])
        matched = [
            changed_file
            for changed_file in changed_files
            if any(_context_paths_overlap(changed_file, evidence_path) for evidence_path in evidence_paths)
        ]
        if matched:
            affected[node_id] = list(dict.fromkeys(matched))
    return affected


def _match_changed_files(
    route: dict[str, Any],
    *,
    changed_files: list[str],
    affected_node_files: dict[str, list[str]],
) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0
    route_path_fields = (
        ("must_read", "must-read"),
        ("tests", "test"),
        ("safe_edit", "safe-edit"),
        ("do_not_touch_without_reason", "guarded"),
    )
    for field, label in route_path_fields:
        for route_path in route.get(field) or []:
            for changed_file in changed_files:
                if _context_paths_overlap(changed_file, str(route_path)):
                    reasons.append(
                        f"changed file `{changed_file}` matches route {label} path `{route_path}`"
                    )
                    score += 3
    for node_id in route.get("start_nodes") or []:
        for changed_file in affected_node_files.get(str(node_id), []):
            reasons.append(
                f"changed file `{changed_file}` affects route start node `{node_id}` through grounded evidence"
            )
            score += 2
    reasons = list(dict.fromkeys(reasons))
    return {
        "status": "matched" if reasons else "unmatched",
        "score": score,
        "reasons": reasons,
    }


def _match_route(
    route: dict[str, Any],
    *,
    task: str | None = None,
    node: str | None = None,
    workflow: str | None = None,
    changed_files: list[str] | None = None,
    affected_node_files: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0
    if node is not None or workflow is not None:
        if node is not None:
            if node not in (route.get("start_nodes") or []):
                return {"status": "unmatched", "score": 0, "reasons": []}
            reasons.append(f"focus node `{node}` starts this route")
        if workflow is not None:
            if workflow not in (route.get("workflows") or []):
                return {"status": "unmatched", "score": 0, "reasons": []}
            reasons.append(f"focus workflow `{workflow}` belongs to this route")
        score = 100 + (10 * len(reasons))
    elif task:
        hay = " ".join(str(route.get(k, "")) for k in ("task", "intent", "notes")).lower()
        matched_terms = [word for word in _task_match_terms(task) if word in hay]
        if matched_terms:
            reasons.append("task terms match: " + ", ".join(f"`{word}`" for word in matched_terms))
            score += len(matched_terms) * 2
        elif not changed_files:
            return {"status": "unmatched", "score": 0, "reasons": []}

    if changed_files:
        changed_match = _match_changed_files(
            route,
            changed_files=changed_files,
            affected_node_files=affected_node_files or {},
        )
        if changed_match["status"] != "matched":
            return {"status": "unmatched", "score": 0, "reasons": []}
        reasons.extend(changed_match["reasons"])
        return {"status": "matched", "score": score + changed_match["score"], "reasons": reasons}

    if reasons:
        return {"status": "matched", "score": score, "reasons": reasons}
    return {"status": "available", "score": 0, "reasons": []}


def generate_agent_context(root: str | Path, *, node: str | None = None, workflow: str | None = None, task: str | None = None, changed_files: list[str] | None = None) -> str:
    root_path = Path(root).resolve()
    bp_path = default_blueprint_path(root_path)
    am_path = default_agent_map_path(root_path)
    comp_path = blueprint_dir(root_path) / COMPONENTS_FILE
    wf_path = blueprint_dir(root_path) / WORKFLOWS_FILE
    if not bp_path.exists():
        raise ValueError(f"Trusted context requires a semantic blueprint: {bp_path}")
    if not am_path.exists():
        raise ValueError(f"Trusted context requires an agent map: {am_path}")
    bp = _read_json_relaxed(bp_path)
    agent_map = _read_json_relaxed(am_path)
    bp_errors, bp_warnings, bp_metrics = validate_blueprint_obj(bp, root=root_path)
    if bp_errors:
        raise ValueError("Trusted context blocked by invalid semantic blueprint: " + "; ".join(bp_errors[:8]))
    bp_blockers = list(bp_metrics.get("publish_blockers") or [])
    if bp_blockers:
        raise ValueError("Trusted context blocked by semantic blueprint grounding: " + "; ".join(bp_blockers[:8]))
    agent_errors, agent_warnings, agent_metrics = validate_agent_map_obj(agent_map, root=root_path, blueprint=bp)
    if agent_errors:
        raise ValueError("Trusted context blocked by invalid agent map: " + "; ".join(agent_errors[:8]))
    agent_blockers = list(agent_metrics.get("publish_blockers") or [])
    if agent_blockers:
        raise ValueError("Trusted context blocked by agent-map routes: " + "; ".join(agent_blockers[:8]))
    node_by_id = {str(n.get("id")): n for n in bp.get("nodes", []) if isinstance(n, dict) and n.get("id")}
    trusted_indexes = set(agent_metrics.get("projectable_route_indexes") or [])
    routes = [r for i, r in enumerate(agent_map.get("task_routes", [])) if isinstance(r, dict) and i in trusted_indexes]
    changed = [_normalize_context_path(path) for path in (changed_files or []) if str(path).strip()]
    affected_node_files = _affected_nodes_for_changes(changed, node_by_id)
    affected_nodes = list(affected_node_files)
    selection_requested = bool(task or node or workflow or changed)
    scored = sorted(
        [
            (
                _match_route(
                    route,
                    task=task,
                    node=node,
                    workflow=workflow,
                    changed_files=changed,
                    affected_node_files=affected_node_files,
                ),
                route,
            )
            for route in routes
        ],
        key=lambda item: item[0]["score"],
        reverse=True,
    )
    if selection_requested:
        chosen = [(match, route) for match, route in scored if match["status"] == "matched"][:5]
    else:
        chosen = [({"status": "available", "score": 0, "reasons": []}, route) for route in routes[:3]]
    lines = []
    lines.append("# Bunya-Jido Agent Context\n")
    if task: lines.append(f"**Task:** {task}")
    if node: lines.append(f"**Focus node:** `{node}`")
    if workflow: lines.append(f"**Focus workflow:** `{workflow}`")
    if changed: lines.append(f"**Changed files:** {', '.join(changed)}")
    lines.append("")
    lines.append("## Trust")
    lines.append("- Artifact mode: `semantic_blueprint`")
    lines.append("- Grounding status: `grounded`")
    lines.append(f"- Agent-map routes: `validated` ({agent_metrics.get('trusted_route_count', 0)} trusted route(s))")
    if selection_requested:
        lines.append(f"- Requested route match: `{'matched' if chosen else 'not_found'}`")
    else:
        lines.append("- Requested route match: `not_requested`")
    if changed:
        lines.append(f"- Changed-file route match: `{'matched' if chosen else 'not_found'}`")
    trust_warnings = list(bp_warnings) + list(agent_warnings)
    lines.append(f"- Warnings: `{len(trust_warnings)}`")
    for warning in trust_warnings[:10]:
        lines.append(f"  - {warning}")
    lines.append("")
    if node and node in node_by_id:
        n = node_by_id[node]
        lines.append(f"## Focus node: {n.get('label', node)}")
        lines.append(str(n.get("description", "")))
        lines.append("")
        lines.append("Evidence:")
        for ev in (n.get("evidence") or [])[:10]:
            if isinstance(ev, dict): lines.append(f"- {ev.get('kind','evidence')}: `{ev.get('path','')}` {ev.get('symbol','')}")
        lines.append("")
    if affected_nodes:
        lines.append("## Affected nodes from changed files")
        for nid in affected_nodes[:20]:
            n = node_by_id.get(nid, {})
            lines.append(f"- `{nid}` - {n.get('label','')} | {n.get('plane','')} | {n.get('type','')}")
        lines.append("")
    lines.append("## Recommended task routes" if selection_requested else "## Available trusted task routes")
    if not chosen:
        if selection_requested:
            lines.append("No matching trusted route for this request. The grounded map does not claim a prepared path for this task.")
        else:
            lines.append("No trusted task routes are available. Run the Bunya-Jido blueprint prompt to author routes.")
        lines.append("")
    for match, r in chosen:
        lines.append(f"### {r.get('task','Unnamed route')}")
        if r.get("intent"): lines.append(str(r.get("intent")))
        if match["reasons"]:
            lines.append("\n**Matched because:**")
            for reason in match["reasons"]:
                lines.append(f"- {reason}")
        def emit_list(title, vals):
            vals = [v for v in (vals or []) if v]
            if vals:
                lines.append(f"\n**{title}:**")
                for v in vals[:30]: lines.append(f"- `{v}`")
        emit_list("Start nodes", r.get("start_nodes"))
        emit_list("Workflows", r.get("workflows"))
        emit_list("Must read", r.get("must_read"))
        emit_list("Contracts", r.get("contracts"))
        emit_list("Tests", r.get("tests"))
        emit_list("Safe edit", r.get("safe_edit"))
        emit_list("Do not touch casually", r.get("do_not_touch_without_reason"))
        if r.get("notes"): lines.append(f"\n**Notes:** {r.get('notes')}")
        lines.append("")
    lines.append("## Generated docs")
    lines.append(f"- Components doc: `{comp_path.relative_to(root_path) if comp_path.exists() else comp_path}`")
    lines.append(f"- Workflows doc: `{wf_path.relative_to(root_path) if wf_path.exists() else wf_path}`")
    lines.append(f"- Blueprint: `{bp_path.relative_to(root_path) if bp_path.exists() else bp_path}`")
    lines.append(f"- Agent map: `{am_path.relative_to(root_path) if am_path.exists() else am_path}`")
    return "\n".join(lines).rstrip() + "\n"


AGENT_UTILITY_DIMENSIONS = {
    "first_read_accuracy",
    "test_recall",
    "boundary_discipline",
    "honest_no_match",
    "change_aware_refresh",
}
AGENT_UTILITY_LIMITATION = (
    "This deterministic suite verifies generated bounded context against authored "
    "expectations; it does not measure whether a live coding agent follows that context."
)


def validate_agent_evaluation_obj(evaluation: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(evaluation, dict):
        return ["evaluation suite must be an object"]
    if evaluation.get("schema_version") != "bunya-jido-agent-evaluation-v1":
        errors.append("schema_version must be bunya-jido-agent-evaluation-v1")
    project = evaluation.get("project")
    if not isinstance(project, dict) or not project.get("name") or not project.get("summary"):
        errors.append("project.name and project.summary are required")
    cases = evaluation.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []
    seen_ids: set[str] = set()
    expected_list_fields = (
        "routes",
        "forbid_routes",
        "must_read",
        "contracts",
        "tests",
        "safe_edit",
    )
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{i}] is not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"cases[{i}].id is required")
        elif case_id in seen_ids:
            errors.append(f"cases[{i}].id must be unique: {case_id}")
        else:
            seen_ids.add(case_id)
        dimension = case.get("dimension")
        if dimension not in AGENT_UTILITY_DIMENSIONS:
            errors.append(f"cases[{i}].dimension is not supported: {dimension}")
        query = case.get("query")
        if not isinstance(query, dict):
            errors.append(f"cases[{i}].query must be an object")
            query = {}
        has_query = False
        for key in ("task", "node", "workflow"):
            if key in query:
                if not isinstance(query[key], str) or not query[key].strip():
                    errors.append(f"cases[{i}].query.{key} must be a non-empty string")
                else:
                    has_query = True
        if "changed_files" in query:
            changed_files = query["changed_files"]
            if not isinstance(changed_files, list) or not all(
                isinstance(path, str) and path.strip() for path in changed_files
            ):
                errors.append(f"cases[{i}].query.changed_files must be a list of non-empty strings")
            elif changed_files:
                has_query = True
        if not has_query:
            errors.append(f"cases[{i}].query must request task, node, workflow, or changed_files")
        expect = case.get("expect")
        if not isinstance(expect, dict):
            errors.append(f"cases[{i}].expect must be an object")
            continue
        if expect.get("route_status") not in {"matched", "not_found"}:
            errors.append(f"cases[{i}].expect.route_status must be matched or not_found")
        for field in expected_list_fields:
            value = expect.get(field, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                errors.append(f"cases[{i}].expect.{field} must be a list of non-empty strings")
        if expect.get("route_status") == "not_found" and expect.get("routes"):
            errors.append(f"cases[{i}].expect.routes must be empty for not_found")
    if any(_string_has_secret(value) for value in _walk_strings(evaluation)):
        errors.append("evaluation suite appears to contain secret-like text; remove raw tokens/API keys/passwords")
    return errors


def _context_route_status(context: str) -> str:
    match = re.search(r"^- Requested route match: `([^`]+)`", context, re.MULTILINE)
    return match.group(1) if match else "missing"


def _context_route_titles(context: str) -> list[str]:
    return re.findall(r"^### (.+?)\s*$", context, re.MULTILINE)


def _context_list_values(context: str, title: str) -> list[str]:
    values: list[str] = []
    collecting = False
    marker = f"**{title}:**"
    for line in context.splitlines():
        if line == marker:
            collecting = True
            continue
        if collecting and line.startswith("- `") and line.endswith("`"):
            values.append(line[3:-1])
            continue
        if collecting:
            collecting = False
    return values


def evaluate_agent_utility(root: str | Path, evaluation_path: str | Path | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = Path(evaluation_path).resolve() if evaluation_path else default_agent_evaluation_path(root_path)
    if not path.exists():
        raise ValueError(f"Agent utility evaluation suite not found: {path}")
    evaluation = _read_json_relaxed(path)
    errors = validate_agent_evaluation_obj(evaluation)
    if errors:
        raise ValueError("Invalid agent utility evaluation suite: " + "; ".join(errors[:12]))
    case_reports: list[dict[str, Any]] = []
    dimension_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "total": 0})
    list_titles = {
        "must_read": "Must read",
        "contracts": "Contracts",
        "tests": "Tests",
        "safe_edit": "Safe edit",
    }
    for case in evaluation["cases"]:
        query = case["query"]
        expected = case["expect"]
        context = generate_agent_context(
            root_path,
            task=query.get("task"),
            node=query.get("node"),
            workflow=query.get("workflow"),
            changed_files=query.get("changed_files"),
        )
        actual_status = _context_route_status(context)
        actual_routes = _context_route_titles(context)
        failures: list[str] = []
        if actual_status != expected["route_status"]:
            failures.append(
                f"route status expected {expected['route_status']}, got {actual_status}"
            )
        expected_routes = expected.get("routes", [])
        if actual_routes != expected_routes:
            failures.append(f"routes expected {expected_routes}, got {actual_routes}")
        forbidden = [
            route for route in expected.get("forbid_routes", []) if route in actual_routes
        ]
        if forbidden:
            failures.append(f"forbidden routes emitted: {forbidden}")
        actual_lists: dict[str, list[str]] = {}
        for field, title in list_titles.items():
            actual_lists[field] = _context_list_values(context, title)
            missing = [
                value for value in expected.get(field, []) if value not in actual_lists[field]
            ]
            if missing:
                failures.append(f"{field} missing from context: {missing}")
        passed = not failures
        dimension = str(case["dimension"])
        dimension_counts[dimension]["total"] += 1
        if passed:
            dimension_counts[dimension]["passed"] += 1
        case_reports.append(
            {
                "id": case["id"],
                "dimension": dimension,
                "status": "passed" if passed else "failed",
                "expected_route_status": expected["route_status"],
                "actual_route_status": actual_status,
                "expected_routes": expected_routes,
                "actual_routes": actual_routes,
                "failures": failures,
            }
        )
    passed_count = sum(1 for report in case_reports if report["status"] == "passed")
    try:
        suite_path = path.relative_to(root_path).as_posix()
    except ValueError:
        suite_path = str(path)
    dimensions = {
        dimension: {
            **counts,
            "status": "passed" if counts["passed"] == counts["total"] else "failed",
        }
        for dimension, counts in dimension_counts.items()
    }
    return {
        "schema_version": "bunya-jido-agent-utility-report-v1",
        "suite_path": suite_path,
        "status": "passed" if passed_count == len(case_reports) else "failed",
        "limitation": evaluation.get("limitation") or AGENT_UTILITY_LIMITATION,
        "case_count": len(case_reports),
        "passed_case_count": passed_count,
        "dimensions": dimensions,
        "cases": case_reports,
    }


AGENT_ACTIVATION_START = "<!-- BEGIN BUNYA-JIDO MANAGED AGENT ACTIVATION -->"
AGENT_ACTIVATION_END = "<!-- END BUNYA-JIDO MANAGED AGENT ACTIVATION -->"


def _agent_activation_instructions() -> str:
    return textwrap.dedent("""
    ## Bunya-Jido Task Context

    For implementation, debugging, or code-review work in this repository:

    1. Before editing, run `bunya-jido context --root . --task "<user request>"`.
    2. If a route is matched, read its `Must read`, `Contracts`, and `Tests` guidance before changing files.
    3. If the output says `No matching trusted route`, state that the map has no prepared route for the task and continue with ordinary repository inspection. Do not infer a route.
    4. If context generation reports that no semantic blueprint or agent map exists yet, continue with ordinary repository inspection and treat map creation as separate work.
    5. After editing, run `bunya-jido refresh-context --root . --changed-file <path>` for the changed files and use only routes justified by that output.
    6. If the repository defines `stale_map_policy`, run `bunya-jido check-stale --root . --git-diff --require-reviewed`; when it reports `stale`, refresh and validate the map or record a reviewed no-structure-change decision in `.bunya-jido/MAP_REVIEW.md`.
    7. Run the tests named by a matched route after the change, together with any checks required by the repository.

    When asked to update the Bunya-Jido map itself, run `bunya-jido prepare --root . --quiet`,
    execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`, then validate the blueprint and agent map.
    """).strip()


def _agent_activation_block() -> str:
    return "\n".join(
        [AGENT_ACTIVATION_START, _agent_activation_instructions(), AGENT_ACTIVATION_END]
    )


def _active_agent_targets(root_path: Path) -> dict[str, Path]:
    return {
        "codex": root_path / "AGENTS.md",
        "claude": root_path / "CLAUDE.md",
        "cursor": root_path / ".cursor" / "rules" / "bunya-jido.mdc",
        "cline": root_path / ".clinerules" / "bunya-jido.md",
    }


def _new_activation_document(name: str, block: str) -> str:
    if name == "cursor":
        return (
            "---\n"
            "description: Use Bunya-Jido validated context before repository work\n"
            "alwaysApply: true\n"
            "---\n\n"
            + block
            + "\n"
        )
    return block + "\n"


def _merge_activation_block(existing: str, block: str) -> tuple[str, str]:
    pattern = re.compile(
        re.escape(AGENT_ACTIVATION_START)
        + r".*?"
        + re.escape(AGENT_ACTIVATION_END),
        re.DOTALL,
    )
    if pattern.search(existing):
        return pattern.sub(block, existing), "updated"
    prefix = existing.rstrip()
    return (prefix + "\n\n" if prefix else "") + block + "\n", "appended"


def activate_agent_guides(root: str | Path, agent: str = "all", *, dry_run: bool = False) -> dict[str, dict[str, Any]]:
    root_path = Path(root).resolve()
    targets = _active_agent_targets(root_path)
    selected = targets if agent == "all" else {agent: targets[agent]}
    block = _agent_activation_block()
    actions: dict[str, dict[str, Any]] = {}
    planned_actions = {"created": "would_create", "updated": "would_update", "appended": "would_append"}
    for name, path in selected.items():
        if path.exists():
            rendered, action = _merge_activation_block(path.read_text(encoding="utf-8"), block)
        else:
            rendered, action = _new_activation_document(name, block), "created"
        status = planned_actions[action] if dry_run else action
        actions[name] = {"path": path, "status": status, "content": rendered}
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8", newline="\n")
    return actions


def install_agent_guides(root: str | Path, agent: str = "all", *, overwrite: bool = False) -> dict[str, Path]:
    root_path = Path(root).resolve()
    outdir = blueprint_dir(root_path) / "agent-guides"
    outdir.mkdir(parents=True, exist_ok=True)
    base = "# Bunya-Jido Agent Guide\n\n" + _agent_activation_instructions() + "\n"
    targets = {
        "codex": outdir / "AGENTS.bunya-jido.md",
        "claude": outdir / "CLAUDE.bunya-jido.md",
        "cursor": outdir / "cursor-bunya-jido.mdc",
        "cline": outdir / "clinerules-bunya-jido.md",
    }
    selected = targets if agent == "all" else {agent: targets[agent]}
    for name, path in selected.items():
        if path.exists() and not overwrite:
            continue
        path.write_text(
            base.replace("Bunya-Jido Agent Guide", f"Bunya-Jido Agent Guide · {name}"),
            encoding="utf-8",
            newline="\n",
        )
    return selected


def _first_evidence_path(n: dict[str, Any]) -> str:
    if n.get("source_path"):
        return str(n.get("source_path"))
    evs = n.get("evidence") or []
    if isinstance(evs, list):
        for ev in evs:
            if isinstance(ev, dict) and ev.get("path"):
                return str(ev["path"])
    return ""


def _importance_size(importance: str, type_: str) -> tuple[bool, float]:
    imp = (importance or "support").lower()
    if imp == "core":
        return True, 22.0
    if imp == "major":
        return True, 17.0
    if type_ in {"plane", "repo"}:
        return True, 18.0
    if imp == "minor":
        return False, 7.5
    return False, 10.0


def _normalize_node_id(raw: str) -> str:
    # Preserve the semantic prefix while making it viewer-safe.
    return slug(raw, 120)


def _plane_glossary_from_blueprint(bp: dict[str, Any], planes: list[str]) -> list[dict[str, str]]:
    declared: dict[str, dict[str, str]] = {}
    for raw in bp.get("planes") or []:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        plane_id = str(raw["id"])
        declared[plane_id] = {
            "id": plane_id,
            "label": str(raw.get("label") or plane_id.replace("_", " ").title()),
            "purpose": str(raw.get("purpose") or "No authored purpose recorded."),
        }
    return [
        declared.get(
            plane,
            {
                "id": plane,
                "label": plane.replace("_", " ").title(),
                "purpose": "Supporting region included by rendered graph projection.",
            },
        )
        for plane in planes
    ]


def graph_from_blueprint(
    bp: dict[str, Any],
    *,
    root: str | Path | None = None,
    static_graph: dict[str, Any] | None = None,
    agent_map: dict[str, Any] | None = None,
    show_root: bool = False,
    allow_draft: bool = False,
) -> dict[str, Any]:
    errors, warnings, metrics = validate_blueprint_obj(bp, root=root)
    if errors:
        raise ValueError("Blueprint validation failed: " + "; ".join(errors[:8]))
    publish_blockers = list(metrics.get("publish_blockers") or [])
    agent_metrics: dict[str, Any] | None = None
    if agent_map is not None:
        agent_errors, agent_warnings, agent_metrics = validate_agent_map_obj(agent_map, root=root, blueprint=bp)
        if agent_errors:
            raise ValueError("Agent map validation failed: " + "; ".join(agent_errors[:8]))
        warnings.extend(f"agent map: {warning}" for warning in agent_warnings)
        publish_blockers.extend(f"agent map: {blocker}" for blocker in agent_metrics.get("publish_blockers") or [])
    publish_blockers = list(dict.fromkeys(publish_blockers))
    if publish_blockers and not allow_draft:
        raise ValueError(
            "Blueprint publication blocked: "
            + "; ".join(publish_blockers[:8])
            + ". Use allow_draft=True or `--allow-draft` to render an explicitly marked draft."
        )
    grounding_status = "draft" if publish_blockers else "grounded"
    quality_metrics = {
        **metrics,
        "grounding_status": grounding_status,
        "publish_blocker_count": len(publish_blockers),
        "publish_blockers": publish_blockers[:40],
        "warning_count": len(warnings),
    }
    project = bp.get("project") or {}
    is_v2 = bp.get("schema_version") == "bunya-jido-blueprint-v2"
    atlas = bp.get("atlas") if is_v2 and isinstance(bp.get("atlas"), dict) else {}
    atlas_intent = atlas.get("intent") if isinstance(atlas.get("intent"), dict) else {}
    static_provider_overlay = (
        str(atlas_intent.get("static_provider_overlay") or "excluded")
        if is_v2
        else "legacy"
    )
    static_provider_overlay_family = str(
        atlas_intent.get("static_provider_overlay_family") or ""
    )
    project_name = str(project.get("name") or (infer_project_name(Path(root)) if root else "repository"))
    id_map: dict[str, str] = {}
    raw_group_children: dict[str, str] = {}
    for g in bp.get("groups") or []:
        if isinstance(g, dict):
            gid = str(g.get("id") or "")
            for child in g.get("children") or []:
                raw_group_children[str(child)] = gid
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    repo_id = _normalize_node_id(f"repo:{project_name}")
    hidden_repo_ids: set[str] = set()
    explicit_repo = any(str(n.get("id", "")).startswith("repo:") or str(n.get("type", "")).lower() == "repo" for n in bp.get("nodes", []))
    if show_root and not explicit_repo:
        nodes.append({
            "id": repo_id,
            "label": project_name,
            "type": "repo",
            "plane": "repo",
            "description": str(project.get("summary") or "Repository root."),
            "source_path": ".",
            "tags": ["repo", "root", "type/repo", "plane/repo", "blueprint"],
            "status": "",
            "major": True,
            "degree": 0,
            "size": 21,
            "evidence": [{"kind": "root", "path": "."}],
        })

    for raw in bp.get("nodes", []):
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        raw_id = str(raw["id"])
        nid = _normalize_node_id(raw_id)
        id_map[raw_id] = nid
        type_ = str(raw.get("type") or "component")
        if not show_root and (type_.lower() == "repo" or raw_id.startswith("repo:")):
            hidden_repo_ids.add(raw_id)
            id_map[raw_id] = ""
            continue
        plane = str(raw.get("plane") or NODE_TYPE_DEFAULT_PLANE.get(type_, "code"))
        major, size = _importance_size(str(raw.get("importance") or "support"), type_)
        tags = [f"type/{type_}", f"plane/{plane}", "blueprint"]
        if raw.get("importance"):
            tags.append(f"importance/{raw.get('importance')}")
        node = {
            "id": nid,
            "label": str(raw.get("label") or raw_id),
            "type": type_,
            "plane": plane,
            "description": str(raw.get("description") or ""),
            "source_path": _first_evidence_path(raw),
            "tags": sorted(set(tags + [f"alias/{a}" for a in raw.get("aliases", [])[:4] if isinstance(a, str)])),
            "status": str(raw.get("status") or ""),
            "major": bool(raw.get("major", major)),
            "degree": 0,
            "size": float(raw.get("size") or size),
            "parent": str(raw.get("parent") or raw_group_children.get(raw_id) or ""),
            "detail_level": str(raw.get("detail_level") or ("detail" if (raw.get("parent") or raw_group_children.get(raw_id)) else "overview")),
            "evidence": raw.get("evidence") or [],
        }
        if raw.get("llm_lane"):
            node["llm_lane"] = str(raw.get("llm_lane"))
        if raw.get("llm_env"):
            node["llm_env"] = str(raw.get("llm_env"))
        if is_v2:
            for key in (
                "family",
                "overview_visibility",
                "activation",
                "why_it_matters",
                "inputs",
                "outputs",
                "constraints",
                "inspector_summary",
            ):
                if raw.get(key) is not None:
                    node[key] = raw[key]
        nodes.append(node)
        if show_root and not explicit_repo and type_ not in {"repo", "plane"}:
            edges.append({
                "id": f"e{len(edges):05d}",
                "source": repo_id,
                "target": nid,
                "source_label": project_name,
                "target_label": node["label"],
                "relation": "contains",
                "lens": "structure",
                "note": "Blueprint component belongs to repository.",
                "confidence": "llm_grounded",
                "directed": True,
                "evidence": [{"kind": "blueprint", "path": BLUEPRINT_FILE}],
            })

    node_labels = {n["id"]: n["label"] for n in nodes}
    for raw in bp.get("edges", []):
        if not isinstance(raw, dict):
            continue
        s_raw, t_raw = str(raw.get("source") or ""), str(raw.get("target") or "")
        if (not show_root) and (s_raw in hidden_repo_ids or t_raw in hidden_repo_ids or s_raw.startswith("repo:") or t_raw.startswith("repo:")):
            continue
        s, t = id_map.get(s_raw, _normalize_node_id(s_raw)), id_map.get(t_raw, _normalize_node_id(t_raw))
        if not s or not t or s not in node_labels or t not in node_labels or s == t:
            continue
        rel = str(raw.get("relation") or "references")
        lens = str(raw.get("lens") or RELATION_LENS.get(rel, "architecture"))
        edge = {
            "id": str(raw.get("id") or f"e{len(edges):05d}"),
            "source": s,
            "target": t,
            "source_label": node_labels.get(s, s),
            "target_label": node_labels.get(t, t),
            "relation": rel,
            "lens": lens,
            "note": str(raw.get("note") or ""),
            "confidence": str(raw.get("confidence") or "llm_grounded"),
            "directed": bool(raw.get("directed", True)),
            "evidence": raw.get("evidence") or [],
        }
        if is_v2:
            for key in ("relation_family", "workflow_role", "overview_visibility", "activation"):
                if raw.get(key) is not None:
                    edge[key] = raw[key]
        edges.append(edge)

    # Add selected static API/provider nodes that the blueprint did not name, so LLM/API routes remain visible in generic repos.
    existing_labels = {n["label"].lower() for n in nodes}
    if static_graph and (not is_v2 or static_provider_overlay == "contextual"):
        for sn in static_graph.get("nodes", []):
            if sn.get("type") not in {"api_provider"}:
                continue
            if str(sn.get("label", "")).lower() in existing_labels:
                continue
            sid = _normalize_node_id(sn.get("id", ""))
            overlay_node = {
                "id": sid, "label": sn.get("label", sid), "type": "api_provider", "plane": "external",
                "description": sn.get("description", "Detected API/model provider from static scan."),
                "source_path": sn.get("source_path", ""), "tags": ["type/api_provider", "plane/external", "static-overlay"],
                "status": "", "major": not is_v2, "degree": 0, "size": 16,
                "evidence": [{"kind": "static_scan", "path": f".bunya-jido/{STATIC_SCAN_FILE}"}],
            }
            if is_v2:
                overlay_node.update(
                    {
                        "family": static_provider_overlay_family,
                        "overview_visibility": "contextual",
                        "activation": "external_boundary",
                        "detail_level": "detail",
                    }
                )
            nodes.append(overlay_node)
            existing_labels.add(str(sn.get("label", "")).lower())

    # Recompute degree and labels after optional overlay.
    node_by_id = {n["id"]: n for n in nodes}
    deg = Counter()
    for e in edges:
        if e["source"] in node_by_id and e["target"] in node_by_id:
            deg[e["source"]] += 1
            deg[e["target"]] += 1
    for n in nodes:
        n["degree"] = int(deg[n["id"]])
        if n.get("major"):
            n["size"] = max(float(n.get("size", 0)), min(28, 15 + deg[n["id"]] ** 0.5))
        else:
            n["size"] = max(float(n.get("size", 0)), min(18, 7 + deg[n["id"]] ** 0.55))
    labels = {n["id"]: n["label"] for n in nodes}
    for e in edges:
        e["source_label"] = labels.get(e["source"], e["source"])
        e["target_label"] = labels.get(e["target"], e["target"])

    path_presets = _path_presets_from_blueprint(
        bp,
        nodes,
        edges,
        id_map,
        agent_map=agent_map,
        projectable_route_indexes=set((agent_metrics or {}).get("projectable_route_indexes") or []),
    )
    lenses = _lenses_from_blueprint(bp, edges)
    groups = _groups_from_blueprint(bp, id_map, nodes)
    relations = sorted({e["relation"] for e in edges})
    planes = sorted({n["plane"] for n in nodes})
    types = sorted({n["type"] for n in nodes})
    plane_glossary = _plane_glossary_from_blueprint(bp, planes)
    source_docs = []
    seen_paths = set()
    for n in nodes:
        for ev in n.get("evidence", [])[:4]:
            if isinstance(ev, dict) and ev.get("path") and ev.get("path") not in seen_paths:
                source_docs.append(ev)
                seen_paths.add(ev.get("path"))
            if len(source_docs) >= 80:
                break
    graph = {
        "schema_version": "bunya-jido-v2" if is_v2 else "bunya-jido-v1",
        "generated_at": now_iso(),
        "title": f"Bunya-Jido · {project_name}",
        "description": str(project.get("summary") or "Blueprint-assisted repository graph."),
        "artifact_mode": "semantic_blueprint",
        "grounding": {
            "status": grounding_status,
            "publishable": not publish_blockers,
            "draft_override": bool(publish_blockers and allow_draft),
            "publish_blockers": publish_blockers[:40],
            "warnings": warnings[:40],
            "metrics": quality_metrics,
        },
        "stats": {"nodes": len(nodes), "edges": len(edges), "relations": relations, "planes": planes, "types": types},
        "plane_glossary": plane_glossary,
        "nodes": sorted(nodes, key=lambda n: (n["plane"], not n.get("major"), n["type"], n["label"].lower())),
        "edges": edges,
        "path_presets": path_presets,
        "lenses": lenses,
        "groups": groups,
        "source_documents": source_docs,
        "blueprint_quality": {**quality_metrics, "warnings": warnings[:40]},
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    if is_v2:
        graph["blueprint_schema_version"] = str(bp.get("schema_version") or "")
        graph["atlas"] = atlas
        graph["primary_projection"] = project.get("primary_projection_id")
        graph["scenario_count"] = len(atlas.get("scenarios") or [])
        graph["static_provider_overlay"] = static_provider_overlay
    if agent_metrics is not None:
        graph["agent_map_quality"] = {**agent_metrics, "warnings": [warning.removeprefix("agent map: ") for warning in warnings if warning.startswith("agent map: ")]}
    return graph


def _groups_from_blueprint(bp: dict[str, Any], id_map: dict[str, str], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    node_ids = {n["id"] for n in nodes}
    groups: list[dict[str, Any]] = []
    for g in bp.get("groups") or []:
        if not isinstance(g, dict) or not g.get("id"):
            continue
        children = []
        for raw_id in g.get("children") or []:
            nid = id_map.get(str(raw_id), _normalize_node_id(str(raw_id)))
            if nid in node_ids:
                children.append(nid)
        if not children:
            continue
        groups.append({
            "id": _normalize_node_id(str(g.get("id"))),
            "label": str(g.get("label") or g.get("id")),
            "description": str(g.get("description") or ""),
            "children": children,
            "default_collapsed": bool(g.get("default_collapsed", True)),
        })
    return groups


def _path_presets_from_blueprint(
    bp: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    id_map: dict[str, str],
    *,
    agent_map: dict[str, Any] | None = None,
    projectable_route_indexes: set[int] | None = None,
) -> list[dict[str, Any]]:
    node_by_id = {n["id"]: n for n in nodes}
    edge_by_rel = defaultdict(list)
    for e in edges:
        edge_by_rel[e["relation"]].append(e)
    presets: list[dict[str, Any]] = []
    if bp.get("schema_version") == "bunya-jido-blueprint-v2":
        atlas = bp.get("atlas") if isinstance(bp.get("atlas"), dict) else {}
        project = bp.get("project") if isinstance(bp.get("project"), dict) else {}
        primary_projection_id = str(project.get("primary_projection_id") or "")
        for projection in atlas.get("projections") or []:
            if not isinstance(projection, dict):
                continue
            projection_id = str(projection.get("id") or "")
            ordered_ids: list[str] = []
            for raw_id in projection.get("node_ids") or []:
                nid = id_map.get(str(raw_id), _normalize_node_id(str(raw_id)))
                if nid in node_by_id and nid not in ordered_ids:
                    ordered_ids.append(nid)
            if not ordered_ids:
                continue
            arr = ordered_ids[:60]
            presets.append({
                "id": slug("projection_" + (projection_id or str(len(presets))), 70),
                "projection_id": projection_id,
                "label": str(projection.get("label") or projection_id or "Atlas Projection"),
                "description": str(projection.get("description") or "Studio atlas projection."),
                "question_answered": str(projection.get("question_answered") or ""),
                "kind": "projection",
                "source": "atlas",
                "is_primary": bool(
                    projection.get("is_primary") is True
                    and projection_id == primary_projection_id
                ),
                "node_ids": arr,
                "nodes": [node_by_id[node_id]["label"] for node_id in arr],
                "plane_ids": list(projection.get("plane_ids") or []),
                "relation_family_ids": list(
                    projection.get("relation_family_ids") or []
                ),
            })
    for view in bp.get("views") or []:
        if not isinstance(view, dict):
            continue
        ids: set[str] = set()
        for raw_id in view.get("node_ids") or []:
            nid = id_map.get(str(raw_id), _normalize_node_id(str(raw_id)))
            if nid in node_by_id:
                ids.add(nid)
        for plane in view.get("include_planes") or []:
            ids.update(n["id"] for n in nodes if n.get("plane") == plane)
        for rel in view.get("include_relations") or []:
            for e in edge_by_rel.get(rel, []):
                ids.add(e["source"]); ids.add(e["target"])
        if ids:
            arr = sorted(
                ids,
                key=lambda i: (
                    not node_by_id[i].get("major", False),
                    -node_by_id[i].get("degree", 0),
                    -node_by_id[i].get("size", 0),
                    i,
                ),
            )[:48]
            presets.append({
                "id": slug(view.get("id") or view.get("label") or f"view-{len(presets)}", 60),
                "label": str(view.get("label") or view.get("id") or "Blueprint View"),
                "description": str(view.get("description") or "Blueprint-selected view"),
                "kind": "view",
                "source": "blueprint",
                "node_ids": arr,
                "nodes": [node_by_id[i]["label"] for i in arr],
            })
    workflow_node_ids: dict[str, list[str]] = {}
    for wf in bp.get("workflows") or []:
        if not isinstance(wf, dict):
            continue
        ordered_ids: list[str] = []
        for raw_id in wf.get("node_ids") or []:
            nid = id_map.get(str(raw_id), _normalize_node_id(str(raw_id)))
            if nid in node_by_id and nid not in ordered_ids:
                ordered_ids.append(nid)
        for step in wf.get("steps") or []:
            if isinstance(step, str):
                nid = id_map.get(step, _normalize_node_id(step))
                if nid in node_by_id and nid not in ordered_ids:
                    ordered_ids.append(nid)
            elif isinstance(step, dict):
                raw_id = str(step.get("node") or step.get("node_id") or "")
                nid = id_map.get(raw_id, _normalize_node_id(raw_id))
                if nid in node_by_id and nid not in ordered_ids:
                    ordered_ids.append(nid)
        workflow_id = str(wf.get("id") or "")
        if workflow_id:
            workflow_node_ids[workflow_id] = ordered_ids
        if ordered_ids:
            arr = ordered_ids[:60]
            presets.append({
                "id": slug("workflow_" + str(wf.get("id") or wf.get("label") or len(presets)), 70),
                "label": str(wf.get("label") or wf.get("id") or "Workflow"),
                "description": str(wf.get("description") or "Blueprint workflow"),
                "kind": "workflow",
                "source": "blueprint",
                "node_ids": arr,
                "nodes": [node_by_id[i]["label"] for i in arr],
            })
    valid_route_indexes = projectable_route_indexes or set()
    if agent_map is not None:
        for index, route in enumerate(agent_map.get("task_routes") or []):
            if index not in valid_route_indexes or not isinstance(route, dict):
                continue
            route_ids: list[str] = []
            for raw_id in route.get("start_nodes") or []:
                node_id = id_map.get(str(raw_id), _normalize_node_id(str(raw_id)))
                if node_id in node_by_id and node_id not in route_ids:
                    route_ids.append(node_id)
            for workflow_id in route.get("workflows") or []:
                for node_id in workflow_node_ids.get(str(workflow_id), []):
                    if node_id not in route_ids:
                        route_ids.append(node_id)
            if route_ids:
                task = str(route.get("task") or f"Task {index + 1}")
                presets.append({
                    "id": slug("task_route_" + task, 70),
                    "label": task,
                    "description": str(route.get("intent") or "Validated coding-agent task route."),
                    "kind": "task_route",
                    "source": "agent_map",
                    "node_ids": route_ids[:60],
                    "nodes": [node_by_id[node_id]["label"] for node_id in route_ids[:60]],
                    "workflows": list(route.get("workflows") or []),
                    "must_read": list(route.get("must_read") or []),
                    "tests": list(route.get("tests") or []),
                })
    core = sorted(
        nodes,
        key=lambda n: (
            not n.get("major", False),
            -n.get("degree", 0),
            -n.get("size", 0),
            n["id"],
        ),
    )[:36]
    presets.insert(0, {"id": "blueprint_core", "label": "Blueprint Core", "description": "Core architecture nodes selected from the LLM-authored blueprint.", "kind": "overview", "source": "blueprint", "node_ids": [n["id"] for n in core], "nodes": [n["label"] for n in core]})
    llm = [n for n in nodes if n.get("plane") in {"llm", "external"} or n.get("type") in {"llm_endpoint", "api_provider"} or n.get("llm_lane")]
    if llm:
        arr = sorted(
            llm,
            key=lambda n: (
                not n.get("major", False),
                -n.get("degree", 0),
                n["id"],
            ),
        )[:36]
        presets.append({"id": "llm_api", "label": "LLM / API", "description": "Model, API, and external provider routes.", "kind": "view", "source": "blueprint", "node_ids": [n["id"] for n in arr], "nodes": [n["label"] for n in arr]})
    return presets


def _lenses_from_blueprint(bp: dict[str, Any], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lens_names = sorted({e.get("lens") for e in edges if e.get("lens")})
    lenses = [{"id": str(l), "label": str(l).replace("_", " ").title(), "lenses": [str(l)]} for l in lens_names[:12]]
    # Add relation-driven lenses for common semantic families.
    relation_sets = {
        "Architecture": ["calls", "feeds", "guards", "uses_contract", "api_calls", "reads", "writes", "emits"],
        "Runtime": ["reads", "writes", "records", "emits", "routes_to", "submits_to", "runs"],
        "Contracts": ["guards", "gates", "validates", "uses_contract", "blocks", "risk"],
        "LLM/API": ["api_calls", "uses_model_lane", "fallbacks_to"],
    }
    rels = {e.get("relation") for e in edges}
    for label, rs in relation_sets.items():
        present = [r for r in rs if r in rels]
        if present:
            lenses.append({"id": slug(label.lower(), 40), "label": label, "relations": present})
    return lenses


def load_blueprint(path: str | Path) -> dict[str, Any]:
    return _read_json_relaxed(Path(path))


def _published_artifact_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def graph_with_optional_blueprint(
    root: str | Path,
    *,
    blueprint: str | Path | None | bool = "auto",
    mode: str = "auto",
    max_files: int = 5000,
    max_nodes: int = 700,
    max_edges: int = 1800,
    include_hidden: bool = False,
    show_root: bool = False,
    data_policy: str = "summary",
    max_data_files: int = 25,
    allow_draft: bool = False,
) -> tuple[dict[str, Any], Path | None]:
    root_path = Path(root).resolve()
    static_graph = build_graph(root_path, mode=mode, max_files=max_files, max_nodes=max_nodes, max_edges=max_edges, include_hidden=include_hidden, show_root=show_root, data_policy=data_policy, max_data_files=max_data_files)
    bp_path: Path | None = None
    if blueprint is False or blueprint == "none":
        return static_graph, None
    if blueprint == "auto" or blueprint is True or blueprint is None:
        cand = default_blueprint_path(root_path)
        if cand.exists():
            bp_path = cand
    else:
        cand = Path(str(blueprint)).resolve()
        if cand.exists():
            bp_path = cand
        else:
            raise FileNotFoundError(f"blueprint file not found: {cand}")
    if not bp_path:
        return static_graph, None
    bp = load_blueprint(bp_path)
    agent_map_path = default_agent_map_path(root_path)
    agent_map = _read_json_relaxed(agent_map_path) if agent_map_path.exists() else None
    graph = graph_from_blueprint(
        bp,
        root=root_path,
        static_graph=static_graph,
        agent_map=agent_map,
        show_root=show_root,
        allow_draft=allow_draft,
    )
    graph["blueprint_path"] = _published_artifact_path(bp_path, root_path)
    if agent_map is not None:
        graph["agent_map_path"] = _published_artifact_path(agent_map_path, root_path)
    return graph, bp_path
