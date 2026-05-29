from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ATLAS_QUALITY_LIMITATION = (
    "Deterministic atlas quality checks identify measurable contract and readability "
    "signals; they do not prove that a projection or narration is the best explanation."
)


def evaluate_atlas_quality_obj(
    blueprint: dict[str, Any],
    *,
    root: str | Path | None = None,
    validation_errors: Iterable[str] = (),
    validation_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    version = blueprint.get("schema_version")
    if version != "bunya-jido-blueprint-v2":
        return {
            "schema_version": "bunya-jido-atlas-quality-report-v1",
            "blueprint_schema_version": version,
            "status": "not_assessed",
            "reason": "Atlas quality applies to Studio v2 blueprints.",
            "limitation": ATLAS_QUALITY_LIMITATION,
            "deterministic_blockers": [],
            "deterministic_warnings": [],
            "review_required_warnings": [],
            "metrics": {},
        }

    validation_metrics = validation_metrics or {}
    blockers = [
        f"blueprint validation error: {error}" for error in validation_errors
    ]
    blockers.extend(validation_metrics.get("publish_blockers") or [])
    warnings: list[str] = []
    review_warnings: list[str] = []
    atlas = blueprint.get("atlas") if isinstance(blueprint.get("atlas"), dict) else {}
    project = (
        blueprint.get("project")
        if isinstance(blueprint.get("project"), dict)
        else {}
    )
    nodes = [
        node for node in blueprint.get("nodes") or [] if isinstance(node, dict)
    ]
    edges = [
        edge for edge in blueprint.get("edges") or [] if isinstance(edge, dict)
    ]
    node_by_id = {
        str(node.get("id")): node for node in nodes if node.get("id") is not None
    }
    projections = [
        item for item in atlas.get("projections") or [] if isinstance(item, dict)
    ]
    primary = next(
        (
            item
            for item in projections
            if item.get("id") == project.get("primary_projection_id")
            and item.get("is_primary") is True
        ),
        None,
    )
    primary_node_ids = [
        str(node_id)
        for node_id in (primary or {}).get("node_ids") or []
        if str(node_id) in node_by_id
    ]
    if not primary:
        blockers.append("Studio v2 atlas has no selected primary projection")
    elif not primary_node_ids:
        blockers.append("Studio v2 primary projection contains no visible nodes")

    visible_nodes = [
        node_by_id[node_id]
        for node_id in primary_node_ids
        if node_by_id[node_id].get("overview_visibility", "visible") == "visible"
    ]
    visible_node_ids = {str(node.get("id")) for node in visible_nodes}
    visible_edges = [
        edge
        for edge in edges
        if edge.get("overview_visibility", "visible") == "visible"
        and str(edge.get("source")) in visible_node_ids
        and str(edge.get("target")) in visible_node_ids
    ]
    visible_planes = Counter(str(node.get("plane") or "") for node in visible_nodes)
    visible_relation_families = {
        str(edge.get("relation_family"))
        for edge in visible_edges
        if edge.get("relation_family")
    }
    vocabularies = (
        atlas.get("vocabularies")
        if isinstance(atlas.get("vocabularies"), dict)
        else {}
    )
    node_family_count = len(vocabularies.get("node_families") or [])

    if len(visible_nodes) > 65:
        warnings.append(
            f"primary projection shows {len(visible_nodes)} visible nodes; consider reducing overview density"
        )
    if len(visible_planes) < 4:
        warnings.append(
            f"primary projection uses {len(visible_planes)} visible planes; confirm that responsibilities are not collapsed"
        )
    if len(visible_planes) > 10:
        warnings.append(
            f"primary projection uses {len(visible_planes)} visible planes; consider simplifying the first view"
        )
    if visible_nodes:
        dominant_plane, dominant_count = visible_planes.most_common(1)[0]
        if len(visible_nodes) >= 6 and dominant_count / len(visible_nodes) > 0.45:
            warnings.append(
                f"plane '{dominant_plane}' occupies {dominant_count}/{len(visible_nodes)} visible nodes in the primary projection"
            )
    if node_family_count < 3 or node_family_count > 8:
        warnings.append(
            f"atlas defines {node_family_count} node families; the recommended first-read range is 3 to 8"
        )
    if len(visible_relation_families) > 8:
        warnings.append(
            f"primary projection exposes {len(visible_relation_families)} visible relation families; the recommended maximum is 8"
        )
    label_chars = sum(len(str(node.get("label") or "")) for node in visible_nodes)
    average_label_length = round(label_chars / max(1, len(visible_nodes)), 2)
    if average_label_length > 28:
        warnings.append(
            f"primary projection average node label length is {average_label_length}; shorten labels or defer detail"
        )
    edge_density = round(len(visible_edges) / max(1, len(visible_nodes)), 2)
    if len(visible_nodes) >= 8 and edge_density > 3.0:
        warnings.append(
            f"primary projection edge density is {edge_density} per visible node; reduce overview crossings"
        )

    core_nodes = [
        node for node in nodes if node.get("importance") == "core"
    ]
    for node in core_nodes:
        node_id = str(node.get("id") or "<unknown>")
        if not node.get("inspector_summary"):
            warnings.append(f"core node {node_id} has no inspector_summary")
        if len(str(node.get("description") or "")) < 40:
            warnings.append(
                f"core node {node_id} has a short description for first-read inspection"
            )

    scenarios = [
        item for item in atlas.get("scenarios") or [] if isinstance(item, dict)
    ]
    for scenario in scenarios:
        scenario_id = str(scenario.get("id") or "<unknown>")
        steps = [
            step for step in scenario.get("steps") or [] if isinstance(step, dict)
        ]
        if len(steps) < 3 or len(steps) > 12:
            warnings.append(
                f"scenario {scenario_id} has {len(steps)} steps; the recommended range is 3 to 12"
            )
        for index, step in enumerate(steps):
            if not step.get("title") or not step.get("narration"):
                blockers.append(
                    f"scenario {scenario_id} step {index + 1} requires title and narration"
                )
        if scenario.get("kind") == "structural_tour":
            review_warnings.append(
                f"Review scenario {scenario_id} narration to ensure a structural tour does not imply runtime order."
            )
        if scenario.get("basis") in {"grounded_inference", "illustrative_tour"}:
            review_warnings.append(
                f"Review scenario {scenario_id} narration against its semantic relations and evidence basis."
            )

    if primary:
        review_warnings.append(
            "Review whether the selected primary projection is the clearest honest explanation of this repository."
        )
    if root is not None:
        outdir = Path(root).resolve() / ".bunya-jido"
        for filename in ("REPOSITORY_THESIS.md", "PROJECTIONS.md", "SCENARIOS.md"):
            if not (outdir / filename).exists():
                warnings.append(
                    f"Studio editorial input is not present for review: .bunya-jido/{filename}"
                )

    blockers = list(dict.fromkeys(blockers))
    warnings = list(dict.fromkeys(warnings))
    review_warnings = list(dict.fromkeys(review_warnings))
    return {
        "schema_version": "bunya-jido-atlas-quality-report-v1",
        "blueprint_schema_version": version,
        "status": "blocked" if blockers else "passed",
        "limitation": ATLAS_QUALITY_LIMITATION,
        "deterministic_blockers": blockers,
        "deterministic_warnings": warnings,
        "review_required_warnings": review_warnings,
        "metrics": {
            "primary_projection": project.get("primary_projection_id"),
            "visible_node_count": len(visible_nodes),
            "visible_edge_count": len(visible_edges),
            "visible_plane_count": len(visible_planes),
            "dominant_plane_ratio": round(
                (visible_planes.most_common(1)[0][1] / max(1, len(visible_nodes)))
                if visible_planes
                else 0.0,
                3,
            ),
            "node_family_count": node_family_count,
            "visible_relation_family_count": len(visible_relation_families),
            "average_label_length": average_label_length,
            "edge_density": edge_density,
            "scenario_policy": atlas.get("scenario_policy"),
            "scenario_count": len(scenarios),
        },
    }
