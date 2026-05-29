from __future__ import annotations

import copy
from typing import Any


def blueprint_schema_v2(v1_schema: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(v1_schema)
    schema["title"] = "Bunya-Jido Studio Atlas Blueprint"
    schema["required"] = ["schema_version", "project", "nodes", "edges", "atlas"]
    schema["properties"]["schema_version"] = {"const": "bunya-jido-blueprint-v2"}
    project = schema["properties"]["project"]
    project["required"] = [
        "name",
        "summary",
        "thesis",
        "primary_projection_id",
        "ordered_behavior_assessment",
    ]
    project["properties"].update(
        {
            "thesis": {"type": "string"},
            "primary_projection_id": {"type": "string"},
            "ordered_behavior_assessment": {
                "enum": ["strong", "partial", "weak", "none"]
            },
        }
    )
    node = schema["properties"]["nodes"]["items"]
    node["required"] = [
        "id",
        "label",
        "type",
        "family",
        "plane",
        "importance",
        "overview_visibility",
        "activation",
        "description",
        "evidence",
    ]
    node["properties"].update(
        {
            "family": {"type": "string"},
            "importance": {"enum": ["core", "major", "support", "detail"]},
            "overview_visibility": {
                "enum": ["visible", "contextual", "hidden"]
            },
            "activation": {
                "enum": [
                    "always",
                    "conditional",
                    "failure_only",
                    "optional",
                    "external_boundary",
                ]
            },
            "why_it_matters": {"type": "string"},
            "inputs": {"type": "array", "items": {"type": "string"}},
            "outputs": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "inspector_summary": {"type": "string"},
        }
    )
    edge = schema["properties"]["edges"]["items"]
    edge["required"] = [
        "source",
        "target",
        "relation",
        "relation_family",
        "workflow_role",
        "overview_visibility",
        "activation",
        "evidence",
    ]
    edge["properties"].update(
        {
            "id": {"type": "string"},
            "relation_family": {"type": "string"},
            "workflow_role": {
                "enum": ["primary", "supporting", "failure", "boundary", "detail"]
            },
            "overview_visibility": {
                "enum": ["visible", "contextual", "hidden"]
            },
            "activation": {
                "enum": ["always", "conditional", "failure_only", "optional"]
            },
        }
    )
    workflow = schema["properties"]["workflows"]["items"]
    workflow["properties"].update(
        {
            "kind": {
                "enum": [
                    "behavioral",
                    "structural",
                    "boundary",
                    "troubleshooting",
                    "example_usage",
                ]
            },
            "ordered": {"type": "boolean"},
            "trigger": {"type": "string"},
            "outcome": {"type": "string"},
            "confidence": {
                "enum": ["deterministic", "llm_grounded", "llm_inferred", "unverified"]
            },
            "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        }
    )
    schema["properties"]["atlas"] = {
        "type": "object",
        "required": ["scenario_policy", "vocabularies", "projections", "scenarios"],
        "properties": {
            "scenario_policy": {
                "enum": ["required", "optional", "none_with_reason"]
            },
            "scenario_policy_reason": {"type": "string"},
            "vocabularies": {
                "type": "object",
                "required": ["node_families", "relation_families"],
                "properties": {
                    "node_families": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "label", "description", "glyph"],
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                                "glyph": {
                                    "enum": [
                                        "circle",
                                        "rounded_square",
                                        "hexagon",
                                        "octagon",
                                        "diamond",
                                        "double_ring",
                                        "dashed_tile",
                                    ]
                                },
                                "color_role": {"type": "string"},
                            },
                        },
                    },
                    "relation_families": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "label", "description", "line_style"],
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                                "line_style": {
                                    "enum": ["solid", "dashed", "dotted", "double"]
                                },
                                "color_role": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "projections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "id",
                        "label",
                        "description",
                        "question_answered",
                        "is_primary",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "question_answered": {"type": "string"},
                        "is_primary": {"type": "boolean"},
                        "node_ids": {"type": "array", "items": {"type": "string"}},
                        "plane_ids": {"type": "array", "items": {"type": "string"}},
                        "relation_family_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "layout_intent": {"type": "object"},
                        "evidence": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/evidence"},
                        },
                    },
                },
            },
            "scenarios": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": [
                        "id",
                        "label",
                        "description",
                        "kind",
                        "basis",
                        "playback_mode",
                        "steps",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                        "kind": {
                            "enum": [
                                "behavioral",
                                "structural_tour",
                                "example_usage",
                                "boundary",
                                "troubleshooting",
                            ]
                        },
                        "basis": {
                            "enum": [
                                "documented_workflow",
                                "deterministic_trace",
                                "grounded_inference",
                                "illustrative_tour",
                            ]
                        },
                        "derived_from_workflow_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "playback_mode": {
                            "enum": ["animated_token", "stepped_highlight"]
                        },
                        "default_speed": {"type": "number"},
                        "evidence": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/evidence"},
                        },
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "node_id", "title", "narration"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "node_id": {"type": "string"},
                                    "edge_id": {"type": "string"},
                                    "token_label": {"type": "string"},
                                    "title": {"type": "string"},
                                    "narration": {"type": "string"},
                                    "pause_ms": {"type": "integer"},
                                    "tone": {"type": "string"},
                                    "evidence": {
                                        "type": "array",
                                        "items": {"$ref": "#/$defs/evidence"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "intent": {
                "type": "object",
                "properties": {
                    "static_provider_overlay": {
                        "enum": ["excluded", "contextual"]
                    },
                    "static_provider_overlay_family": {"type": "string"},
                },
            },
            "quality_expectations": {"type": "object"},
        },
    }
    return schema


def validate_blueprint_v2_atlas(
    blueprint: dict[str, Any],
) -> tuple[list[str], list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    project = (
        blueprint.get("project")
        if isinstance(blueprint.get("project"), dict)
        else {}
    )
    for key in ("thesis", "primary_projection_id", "ordered_behavior_assessment"):
        if not project.get(key):
            errors.append(f"v2 project.{key} is required")
    if project.get("ordered_behavior_assessment") not in {
        "strong",
        "partial",
        "weak",
        "none",
    }:
        errors.append(
            "v2 project.ordered_behavior_assessment must be strong, partial, weak, or none"
        )

    atlas = blueprint.get("atlas")
    if not isinstance(atlas, dict):
        errors.append("v2 atlas object is required")
        return errors, warnings, blockers, _atlas_metrics(project, {}, [], [])

    vocabularies = (
        atlas.get("vocabularies")
        if isinstance(atlas.get("vocabularies"), dict)
        else {}
    )
    if not vocabularies:
        errors.append("v2 atlas.vocabularies object is required")
    node_families = vocabularies.get("node_families")
    relation_families = vocabularies.get("relation_families")
    if not isinstance(node_families, list) or not node_families:
        errors.append("v2 atlas.vocabularies.node_families must be a non-empty list")
        node_families = []
    if not isinstance(relation_families, list) or not relation_families:
        errors.append("v2 atlas.vocabularies.relation_families must be a non-empty list")
        relation_families = []

    node_family_ids = _validate_node_families(node_families, errors, warnings)
    relation_family_ids = _validate_relation_families(relation_families, errors)
    nodes = [
        node for node in blueprint.get("nodes") or [] if isinstance(node, dict)
    ]
    edges = [
        edge for edge in blueprint.get("edges") or [] if isinstance(edge, dict)
    ]
    node_ids = {str(node.get("id")) for node in nodes if node.get("id")}
    plane_ids = {
        str(plane.get("id"))
        for plane in blueprint.get("planes") or []
        if isinstance(plane, dict) and plane.get("id")
    }
    _validate_v2_nodes(nodes, node_family_ids, errors, blockers)
    edge_ids, edge_pairs, visible_relation_families = _validate_v2_edges(
        edges, relation_family_ids, errors
    )
    if len(visible_relation_families) > 8:
        warnings.append(
            f"v2 overview exposes {len(visible_relation_families)} relation families; consider a tighter primary legend"
        )

    projections = _validate_projections(
        atlas,
        project,
        node_ids,
        plane_ids,
        relation_family_ids,
        errors,
    )
    scenarios = _validate_scenario_policy(atlas, errors, blockers)
    workflows = {
        str(workflow.get("id")): workflow
        for workflow in blueprint.get("workflows") or []
        if isinstance(workflow, dict) and workflow.get("id")
    }
    _validate_scenarios(
        scenarios,
        node_ids,
        edge_ids,
        edge_pairs,
        workflows,
        errors,
        blockers,
    )
    intent = atlas.get("intent") if isinstance(atlas.get("intent"), dict) else {}
    if intent.get("static_provider_overlay") not in {None, "excluded", "contextual"}:
        errors.append(
            "v2 atlas.intent.static_provider_overlay must be excluded or contextual"
        )
    if intent.get("static_provider_overlay") == "contextual":
        overlay_family = intent.get("static_provider_overlay_family")
        if not overlay_family or str(overlay_family) not in node_family_ids:
            errors.append(
                "v2 contextual static provider overlay requires a declared static_provider_overlay_family"
            )
    return errors, warnings, blockers, _atlas_metrics(
        project, atlas, projections, scenarios
    )


def _atlas_metrics(
    project: dict[str, Any],
    atlas: dict[str, Any],
    projections: list[Any],
    scenarios: list[Any],
) -> dict[str, Any]:
    return {
        "schema_version": "bunya-jido-blueprint-v2",
        "primary_projection": project.get("primary_projection_id"),
        "projection_count": len(projections),
        "scenario_policy": atlas.get("scenario_policy"),
        "scenario_count": len(scenarios),
    }


def _validate_node_families(
    families: list[Any], errors: list[str], warnings: list[str]
) -> set[str]:
    valid_glyphs = {
        "circle",
        "rounded_square",
        "hexagon",
        "octagon",
        "diamond",
        "double_ring",
        "dashed_tile",
    }
    ids: set[str] = set()
    for index, family in enumerate(families):
        if not isinstance(family, dict) or not family.get("id"):
            errors.append(f"v2 node_families[{index}].id is required")
            continue
        family_id = str(family["id"])
        if family_id in ids:
            errors.append(f"duplicate v2 node family id: {family_id}")
        ids.add(family_id)
        for key in ("label", "description", "glyph"):
            if not family.get(key):
                errors.append(f"v2 node family {family_id} missing {key}")
        if family.get("glyph") and family.get("glyph") not in valid_glyphs:
            errors.append(
                f"v2 node family {family_id} has invalid glyph: {family.get('glyph')}"
            )
    if len(ids) > 10:
        warnings.append(
            f"v2 atlas defines {len(ids)} node families; consider reducing the first-read vocabulary"
        )
    return ids


def _validate_relation_families(families: list[Any], errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, family in enumerate(families):
        if not isinstance(family, dict) or not family.get("id"):
            errors.append(f"v2 relation_families[{index}].id is required")
            continue
        family_id = str(family["id"])
        if family_id in ids:
            errors.append(f"duplicate v2 relation family id: {family_id}")
        ids.add(family_id)
        for key in ("label", "description", "line_style"):
            if not family.get(key):
                errors.append(f"v2 relation family {family_id} missing {key}")
        if family.get("line_style") not in {None, "solid", "dashed", "dotted", "double"}:
            errors.append(
                f"v2 relation family {family_id} has invalid line_style: {family.get('line_style')}"
            )
    return ids


def _validate_v2_nodes(
    nodes: list[dict[str, Any]],
    family_ids: set[str],
    errors: list[str],
    blockers: list[str],
) -> None:
    for node in nodes:
        node_id = str(node.get("id") or "<unknown>")
        family = node.get("family")
        if not family:
            errors.append(f"v2 node {node_id} missing family")
        elif str(family) not in family_ids:
            errors.append(f"v2 node {node_id} references unknown family: {family}")
        if node.get("importance") not in {"core", "major", "support", "detail"}:
            errors.append(f"v2 node {node_id} has invalid importance: {node.get('importance')}")
        if node.get("overview_visibility") not in {"visible", "contextual", "hidden"}:
            errors.append(
                f"v2 node {node_id} has invalid overview_visibility: {node.get('overview_visibility')}"
            )
        if node.get("activation") not in {
            "always",
            "conditional",
            "failure_only",
            "optional",
            "external_boundary",
        }:
            errors.append(f"v2 node {node_id} has invalid activation: {node.get('activation')}")
        if node.get("importance") == "core" and not node.get("why_it_matters"):
            blockers.append(f"v2 core node {node_id} has no why_it_matters")


def _validate_v2_edges(
    edges: list[dict[str, Any]], family_ids: set[str], errors: list[str]
) -> tuple[set[str], set[tuple[str, str]], set[str]]:
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    visible_families: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "<unknown>")
        target = str(edge.get("target") or "<unknown>")
        if edge.get("id"):
            edge_id = str(edge["id"])
            if edge_id in ids:
                errors.append(f"duplicate v2 edge id: {edge_id}")
            ids.add(edge_id)
        pairs.add((source, target))
        family = edge.get("relation_family")
        if not family:
            errors.append(f"v2 edge {source}->{target} missing relation_family")
        elif str(family) not in family_ids:
            errors.append(
                f"v2 edge {source}->{target} references unknown relation family: {family}"
            )
        if edge.get("workflow_role") not in {
            "primary",
            "supporting",
            "failure",
            "boundary",
            "detail",
        }:
            errors.append(
                f"v2 edge {source}->{target} has invalid workflow_role: {edge.get('workflow_role')}"
            )
        if edge.get("overview_visibility") not in {"visible", "contextual", "hidden"}:
            errors.append(
                f"v2 edge {source}->{target} has invalid overview_visibility: {edge.get('overview_visibility')}"
            )
        if edge.get("activation") not in {
            "always",
            "conditional",
            "failure_only",
            "optional",
        }:
            errors.append(
                f"v2 edge {source}->{target} has invalid activation: {edge.get('activation')}"
            )
        if edge.get("overview_visibility") == "visible" and family:
            visible_families.add(str(family))
    return ids, pairs, visible_families


def _validate_projections(
    atlas: dict[str, Any],
    project: dict[str, Any],
    node_ids: set[str],
    plane_ids: set[str],
    relation_family_ids: set[str],
    errors: list[str],
) -> list[Any]:
    projections = atlas.get("projections")
    if not isinstance(projections, list) or not projections:
        errors.append("v2 atlas.projections must contain a primary projection")
        projections = []
    ids: set[str] = set()
    primary_ids: list[str] = []
    for index, projection in enumerate(projections):
        if not isinstance(projection, dict) or not projection.get("id"):
            errors.append(f"v2 projections[{index}].id is required")
            continue
        projection_id = str(projection["id"])
        if projection_id in ids:
            errors.append(f"duplicate v2 projection id: {projection_id}")
        ids.add(projection_id)
        if projection.get("is_primary") is True:
            primary_ids.append(projection_id)
        for key in ("label", "description", "question_answered"):
            if not projection.get(key):
                errors.append(f"v2 projection {projection_id} missing {key}")
        for node_id in projection.get("node_ids") or []:
            if str(node_id) not in node_ids:
                errors.append(
                    f"v2 projection {projection_id} references missing node: {node_id}"
                )
        for plane_id in projection.get("plane_ids") or []:
            if str(plane_id) not in plane_ids:
                errors.append(
                    f"v2 projection {projection_id} references missing plane: {plane_id}"
                )
        for family_id in projection.get("relation_family_ids") or []:
            if str(family_id) not in relation_family_ids:
                errors.append(
                    f"v2 projection {projection_id} references unknown relation family: {family_id}"
                )
    if len(primary_ids) != 1:
        errors.append("v2 atlas.projections must contain exactly one primary projection")
    selected = project.get("primary_projection_id")
    if selected and selected not in ids:
        errors.append(
            f"v2 project.primary_projection_id references missing projection: {selected}"
        )
    elif selected and primary_ids and selected != primary_ids[0]:
        errors.append(
            "v2 project.primary_projection_id must identify the projection marked is_primary"
        )
    return projections


def _validate_scenario_policy(
    atlas: dict[str, Any], errors: list[str], blockers: list[str]
) -> list[Any]:
    policy = atlas.get("scenario_policy")
    if policy not in {"required", "optional", "none_with_reason"}:
        errors.append(
            "v2 atlas.scenario_policy must be required, optional, or none_with_reason"
        )
    scenarios = atlas.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("v2 atlas.scenarios must be a list")
        scenarios = []
    if policy == "required" and not scenarios:
        blockers.append("v2 scenario_policy=required requires at least one scenario")
    if policy == "none_with_reason":
        if not atlas.get("scenario_policy_reason"):
            blockers.append(
                "v2 scenario_policy=none_with_reason requires scenario_policy_reason"
            )
        if scenarios:
            blockers.append(
                "v2 scenario_policy=none_with_reason must not publish scenarios"
            )
    if len(scenarios) > 5:
        blockers.append("v2 atlas may publish at most 5 scenarios")
    return scenarios


def _validate_scenarios(
    scenarios: list[Any],
    node_ids: set[str],
    edge_ids: set[str],
    edge_pairs: set[tuple[str, str]],
    workflows: dict[str, dict[str, Any]],
    errors: list[str],
    blockers: list[str],
) -> None:
    ids: set[str] = set()
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict) or not scenario.get("id"):
            errors.append(f"v2 scenarios[{index}].id is required")
            continue
        scenario_id = str(scenario["id"])
        if scenario_id in ids:
            errors.append(f"duplicate v2 scenario id: {scenario_id}")
        ids.add(scenario_id)
        for key in ("label", "description", "kind", "basis", "playback_mode"):
            if not scenario.get(key):
                errors.append(f"v2 scenario {scenario_id} missing {key}")
        if scenario.get("kind") not in {
            "behavioral",
            "structural_tour",
            "example_usage",
            "boundary",
            "troubleshooting",
        }:
            errors.append(f"v2 scenario {scenario_id} has invalid kind: {scenario.get('kind')}")
        if scenario.get("basis") not in {
            "documented_workflow",
            "deterministic_trace",
            "grounded_inference",
            "illustrative_tour",
        }:
            errors.append(
                f"v2 scenario {scenario_id} has invalid basis: {scenario.get('basis')}"
            )
        if scenario.get("playback_mode") not in {
            "animated_token",
            "stepped_highlight",
        }:
            errors.append(
                f"v2 scenario {scenario_id} has invalid playback_mode: {scenario.get('playback_mode')}"
            )
        workflow_ids = [
            str(workflow_id)
            for workflow_id in scenario.get("derived_from_workflow_ids") or []
        ]
        for workflow_id in workflow_ids:
            if workflow_id not in workflows:
                errors.append(
                    f"v2 scenario {scenario_id} references missing workflow: {workflow_id}"
                )
        steps = scenario.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"v2 scenario {scenario_id} must contain steps")
            steps = []
        sequence: list[str] = []
        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"v2 scenario {scenario_id} step {step_index} is not an object")
                continue
            node_id = step.get("node_id")
            edge_id = step.get("edge_id")
            if node_id and str(node_id) not in node_ids:
                errors.append(
                    f"v2 scenario {scenario_id} references missing node: {node_id}"
                )
            if node_id:
                sequence.append(str(node_id))
            if edge_id and str(edge_id) not in edge_ids:
                errors.append(
                    f"v2 scenario {scenario_id} references missing edge: {edge_id}"
                )
        if scenario.get("playback_mode") == "animated_token":
            for source, target in zip(sequence, sequence[1:]):
                if (source, target) not in edge_pairs:
                    blockers.append(
                        f"v2 animated scenario {scenario_id} has disconnected transition: {source}->{target}"
                    )
        if (
            scenario.get("kind") == "structural_tour"
            and scenario.get("playback_mode") == "animated_token"
        ):
            blockers.append(
                f"v2 structural_tour scenario {scenario_id} must use stepped_highlight"
            )
        if scenario.get("basis") == "deterministic_trace" and not (
            scenario.get("evidence")
            or all(isinstance(step, dict) and step.get("evidence") for step in steps)
        ):
            blockers.append(
                f"v2 deterministic_trace scenario {scenario_id} has no evidence"
            )
        if scenario.get("kind") == "behavioral":
            has_ordered_workflow = any(
                workflows.get(workflow_id, {}).get("ordered") is True
                for workflow_id in workflow_ids
            )
            has_step_evidence = bool(steps) and all(
                isinstance(step, dict) and step.get("evidence") for step in steps
            )
            if not has_ordered_workflow and not has_step_evidence:
                blockers.append(
                    f"v2 behavioral scenario {scenario_id} requires an ordered workflow or evidence-backed steps"
                )
