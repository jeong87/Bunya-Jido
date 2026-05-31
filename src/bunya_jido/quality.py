from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ATLAS_QUALITY_LIMITATION = (
    "Deterministic atlas quality checks identify measurable contract and readability "
    "signals; they do not prove that a projection or narration is the best explanation."
)
ATLAS_QUALITY_REPORT_FILE = "ATLAS_QUALITY_REPORT.md"
_RUNTIME_ACTION_RE = re.compile(r"\b(executes?|runs?|triggers?|emits?)\b", re.IGNORECASE)
_TRACE_CLAIM_RE = re.compile(
    r"\b(deterministic(?:ally)?|recorded|observed|execution\s+trace|runtime\s+trace|actual\s+runtime)\b",
    re.IGNORECASE,
)
_GENERIC_SCENARIO_TITLE_RE = re.compile(
    r"^(scenario|flow|tour)(?:\s+\d+)?$", re.IGNORECASE
)


def _quality_summary(
    blockers: list[str], warnings: list[str], review_warnings: list[str]
) -> dict[str, Any]:
    return {
        "review_required": bool(review_warnings),
        "blocker_count": len(blockers),
        "warning_count": len(warnings) + len(review_warnings),
        "deterministic_warning_count": len(warnings),
        "review_required_warning_count": len(review_warnings),
    }


def _scenario_review_warnings(
    scenario: dict[str, Any],
    steps: list[dict[str, Any]],
    *,
    primary_landmark_ids: set[str],
) -> list[str]:
    scenario_id = str(scenario.get("id") or "<unknown>")
    findings: list[str] = []
    narration_text = " ".join(str(step.get("narration") or "") for step in steps)
    if scenario.get("kind") == "structural_tour" and _RUNTIME_ACTION_RE.search(
        narration_text
    ):
        findings.append(
            f"Review scenario {scenario_id}: structural_tour narration uses runtime-action language; present it as a reading path."
        )
    if scenario.get("basis") == "illustrative_tour" and _TRACE_CLAIM_RE.search(
        narration_text
    ):
        findings.append(
            f"Review scenario {scenario_id}: illustrative_tour narration sounds like recorded or deterministic runtime evidence."
        )
    label = str(scenario.get("label") or "").strip()
    if _GENERIC_SCENARIO_TITLE_RE.fullmatch(label):
        findings.append(
            f"Review scenario {scenario_id}: its title '{label}' is too generic to explain the reading path."
        )
    narrations = [
        str(step.get("narration") or "").strip()
        for step in steps
        if str(step.get("narration") or "").strip()
    ]
    if narrations:
        short_count = sum(len(narration) < 28 for narration in narrations)
        long_count = sum(len(narration) > 180 for narration in narrations)
        if short_count > len(narrations) / 2:
            findings.append(
                f"Review scenario {scenario_id}: most step narration is too brief to explain its landmarks."
            )
        if long_count > len(narrations) / 2:
            findings.append(
                f"Review scenario {scenario_id}: most step narration is too long for readable playback."
            )
    visited_node_ids = {
        str(step.get("node_id"))
        for step in steps
        if step.get("node_id") is not None
    }
    if (
        visited_node_ids
        and primary_landmark_ids
        and not visited_node_ids.intersection(primary_landmark_ids)
    ):
        findings.append(
            f"Review scenario {scenario_id}: it does not visit a primary landmark from the selected projection."
        )
    return findings


def render_atlas_quality_markdown(report: dict[str, Any]) -> str:
    def bullet_lines(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- None."

    lines = [
        "# Atlas Quality Report",
        "",
        f"- Status: `{report.get('status', 'not_assessed')}`",
        f"- Blueprint schema: `{report.get('blueprint_schema_version') or 'not provided'}`",
        f"- Deterministic blockers: `{report.get('blocker_count', 0)}`",
        f"- Deterministic warnings: `{report.get('deterministic_warning_count', 0)}`",
        f"- Review required: `{'yes' if report.get('review_required') else 'no'}`",
        f"- Review-required warnings: `{report.get('review_required_warning_count', 0)}`",
        "",
        "## Scope",
        "",
        str(report.get("limitation") or ATLAS_QUALITY_LIMITATION),
        "",
    ]
    if report.get("status") == "not_assessed":
        lines.extend(["## Assessment", "", str(report.get("reason") or "Not assessed."), ""])
        return "\n".join(lines)
    lines.extend(["## Metrics", ""])
    for key, value in (report.get("metrics") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Deterministic Blockers",
            "",
            bullet_lines(report.get("deterministic_blockers") or []),
            "",
            "## Deterministic Warnings",
            "",
            bullet_lines(report.get("deterministic_warnings") or []),
            "",
            "## Review Required",
            "",
            bullet_lines(report.get("review_required_warnings") or []),
            "",
        ]
    )
    return "\n".join(lines)


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
            **_quality_summary([], [], []),
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
    primary_landmark_ids = {
        node_id
        for node_id in primary_node_ids
        if node_by_id[node_id].get("importance") in {"core", "major"}
    }
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
    if len(visible_nodes) >= 12 and label_chars > 420:
        warnings.append(
            f"primary projection exposes {label_chars} visible label characters; defer labels or reduce the first-screen set"
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
        review_warnings.extend(
            _scenario_review_warnings(
                scenario,
                steps,
                primary_landmark_ids=primary_landmark_ids,
            )
        )

    decision_record_present = isinstance(atlas.get("decision_record"), dict)
    if not decision_record_present:
        review_warnings.append(
            "Review Studio editorial choices because atlas.decision_record is not present."
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
            "visible_label_character_count": label_chars,
            "edge_density": edge_density,
            "scenario_policy": atlas.get("scenario_policy"),
            "scenario_count": len(scenarios),
            "decision_record_present": decision_record_present,
        },
        **_quality_summary(blockers, warnings, review_warnings),
    }
