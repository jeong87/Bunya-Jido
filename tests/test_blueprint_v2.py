from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import blueprint_schema, graph_from_blueprint, validate_blueprint_obj
from bunya_jido.cli import main


def valid_v2_blueprint() -> dict:
    evidence = [{"kind": "source", "path": "README.md"}]
    return {
        "schema_version": "bunya-jido-blueprint-v2",
        "project": {
            "name": "fixture",
            "summary": "A Studio v2 fixture.",
            "thesis": "Commands cross a grounded validation boundary.",
            "primary_projection_id": "projection:primary",
            "ordered_behavior_assessment": "strong",
        },
        "planes": [
            {"id": "entry", "label": "Entry", "purpose": "Commands"},
            {"id": "control", "label": "Control", "purpose": "Workflow"},
            {"id": "quality", "label": "Quality", "purpose": "Checks"},
        ],
        "nodes": [
            {
                "id": "component:cli",
                "label": "CLI",
                "type": "component",
                "family": "boundary",
                "plane": "entry",
                "importance": "core",
                "overview_visibility": "visible",
                "activation": "always",
                "description": "Accepts an atlas authoring command.",
                "why_it_matters": "It begins the visible authoring path.",
                "evidence": evidence,
            },
            {
                "id": "component:builder",
                "label": "Builder",
                "type": "component",
                "family": "transformer",
                "plane": "control",
                "importance": "core",
                "overview_visibility": "visible",
                "activation": "always",
                "description": "Produces a validated semantic payload.",
                "why_it_matters": "It converts authored meaning into an artifact.",
                "evidence": evidence,
            },
            {
                "id": "component:gate",
                "label": "Gate",
                "type": "contract",
                "family": "boundary",
                "plane": "quality",
                "importance": "major",
                "overview_visibility": "visible",
                "activation": "always",
                "description": "Rejects invalid atlas contracts.",
                "evidence": evidence,
            },
        ],
        "edges": [
            {
                "id": "edge:cli_builder",
                "source": "component:cli",
                "target": "component:builder",
                "relation": "submits_to",
                "relation_family": "flow",
                "workflow_role": "primary",
                "overview_visibility": "visible",
                "activation": "always",
                "confidence": "llm_grounded",
                "evidence": evidence,
            },
            {
                "id": "edge:builder_gate",
                "source": "component:builder",
                "target": "component:gate",
                "relation": "validates",
                "relation_family": "checks",
                "workflow_role": "primary",
                "overview_visibility": "visible",
                "activation": "always",
                "confidence": "llm_grounded",
                "evidence": evidence,
            },
        ],
        "workflows": [
            {
                "id": "workflow:publication",
                "label": "Publication",
                "description": "Validate an authored atlas.",
                "kind": "behavioral",
                "ordered": True,
                "node_ids": ["component:cli", "component:builder", "component:gate"],
                "evidence": evidence,
            }
        ],
        "atlas": {
            "scenario_policy": "required",
            "vocabularies": {
                "node_families": [
                    {
                        "id": "boundary",
                        "label": "Boundary",
                        "description": "Accepts or checks a transition.",
                        "glyph": "hexagon",
                    },
                    {
                        "id": "transformer",
                        "label": "Transformer",
                        "description": "Produces a new artifact.",
                        "glyph": "rounded_square",
                    },
                ],
                "relation_families": [
                    {
                        "id": "flow",
                        "label": "Flows To",
                        "description": "Advances the main path.",
                        "line_style": "solid",
                    },
                    {
                        "id": "checks",
                        "label": "Checks",
                        "description": "Applies a publication gate.",
                        "line_style": "dashed",
                    },
                ],
            },
            "projections": [
                {
                    "id": "projection:primary",
                    "label": "Authoring Flow",
                    "description": "How an atlas reaches validation.",
                    "question_answered": "How is a candidate map checked?",
                    "is_primary": True,
                    "node_ids": [
                        "component:cli",
                        "component:builder",
                        "component:gate",
                    ],
                    "plane_ids": ["entry", "control", "quality"],
                    "relation_family_ids": ["flow", "checks"],
                    "evidence": evidence,
                }
            ],
            "scenarios": [
                {
                    "id": "scenario:publication",
                    "label": "Validate an Atlas",
                    "description": "Follow a grounded validation path.",
                    "kind": "behavioral",
                    "basis": "documented_workflow",
                    "derived_from_workflow_ids": ["workflow:publication"],
                    "playback_mode": "animated_token",
                    "steps": [
                        {
                            "id": "scene:1",
                            "node_id": "component:cli",
                            "edge_id": "edge:cli_builder",
                            "title": "Submit",
                            "narration": "A command submits authored structure.",
                            "evidence": evidence,
                        },
                        {
                            "id": "scene:2",
                            "node_id": "component:builder",
                            "edge_id": "edge:builder_gate",
                            "title": "Check",
                            "narration": "The result reaches validation.",
                            "evidence": evidence,
                        },
                        {
                            "id": "scene:3",
                            "node_id": "component:gate",
                            "title": "Decide",
                            "narration": "The gate decides publication.",
                            "evidence": evidence,
                        },
                    ],
                }
            ],
            "intent": {"static_provider_overlay": "excluded"},
        },
    }


class BlueprintV2Tests(unittest.TestCase):
    def test_studio_schema_and_valid_v2_payload_build(self) -> None:
        schema = blueprint_schema("studio")
        blueprint = valid_v2_blueprint()

        errors, warnings, metrics = validate_blueprint_obj(blueprint)
        graph = graph_from_blueprint(
            blueprint,
            static_graph={
                "nodes": [
                    {"id": "api:provider", "label": "Provider", "type": "api_provider"}
                ]
            },
        )

        self.assertEqual(schema["properties"]["schema_version"]["const"], "bunya-jido-blueprint-v2")
        self.assertIn(
            "steps",
            schema["properties"]["atlas"]["properties"]["scenarios"]["items"]["properties"],
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["primary_projection"], "projection:primary")
        self.assertEqual(metrics["scenario_count"], 1)
        self.assertEqual(graph["schema_version"], "bunya-jido-v2")
        self.assertEqual(graph["atlas"]["scenario_policy"], "required")
        self.assertEqual(graph["primary_projection"], "projection:primary")
        self.assertEqual(graph["static_provider_overlay"], "excluded")
        self.assertNotIn("Provider", {node["label"] for node in graph["nodes"]})
        projection = next(
            path for path in graph["path_presets"] if path["kind"] == "projection"
        )
        self.assertEqual(projection["projection_id"], "projection:primary")
        self.assertTrue(projection["is_primary"])
        self.assertEqual(projection["label"], "Authoring Flow")
        self.assertEqual(projection["relation_family_ids"], ["flow", "checks"])

    def test_v2_family_and_projection_references_are_checked(self) -> None:
        blueprint = valid_v2_blueprint()
        blueprint["nodes"][0]["family"] = "unknown"
        blueprint["edges"][0]["relation_family"] = "unknown"
        blueprint["atlas"]["projections"][0]["node_ids"].append("component:missing")

        errors, _, _ = validate_blueprint_obj(blueprint)

        self.assertIn("v2 node component:cli references unknown family: unknown", errors)
        self.assertIn(
            "v2 edge component:cli->component:builder references unknown relation family: unknown",
            errors,
        )
        self.assertIn(
            "v2 projection projection:primary references missing node: component:missing",
            errors,
        )

    def test_v2_requires_one_selected_primary_projection(self) -> None:
        blueprint = valid_v2_blueprint()
        blueprint["atlas"]["projections"][0]["is_primary"] = False

        errors, _, _ = validate_blueprint_obj(blueprint)

        self.assertIn(
            "v2 atlas.projections must contain exactly one primary projection",
            errors,
        )

    def test_v2_scenario_policy_supports_honest_no_scenario_and_blocks_contradictions(self) -> None:
        no_scenario = valid_v2_blueprint()
        no_scenario["atlas"]["scenario_policy"] = "none_with_reason"
        no_scenario["atlas"]["scenario_policy_reason"] = "No honest ordered tour is needed."
        no_scenario["atlas"]["scenarios"] = []

        errors, _, metrics = validate_blueprint_obj(no_scenario)
        self.assertEqual(errors, [])
        self.assertEqual(metrics["publish_blockers"], [])

        required = copy.deepcopy(no_scenario)
        required["atlas"]["scenario_policy"] = "required"
        _, _, required_metrics = validate_blueprint_obj(required)
        self.assertIn(
            "v2 scenario_policy=required requires at least one scenario",
            required_metrics["publish_blockers"],
        )

        too_many = valid_v2_blueprint()
        too_many["atlas"]["scenarios"] = too_many["atlas"]["scenarios"] * 6
        _, _, too_many_metrics = validate_blueprint_obj(too_many)
        self.assertIn(
            "v2 atlas may publish at most 5 scenarios",
            too_many_metrics["publish_blockers"],
        )

    def test_v2_scenario_reference_and_behavioral_grounding_are_checked(self) -> None:
        blueprint = valid_v2_blueprint()
        scenario = blueprint["atlas"]["scenarios"][0]
        scenario["derived_from_workflow_ids"] = ["workflow:missing"]
        scenario["steps"][0]["node_id"] = "component:missing"
        scenario["steps"][0]["edge_id"] = "edge:missing"
        for step in scenario["steps"]:
            step.pop("evidence", None)

        errors, _, metrics = validate_blueprint_obj(blueprint)

        self.assertIn(
            "v2 scenario scenario:publication references missing workflow: workflow:missing",
            errors,
        )
        self.assertIn(
            "v2 scenario scenario:publication references missing node: component:missing",
            errors,
        )
        self.assertIn(
            "v2 scenario scenario:publication references missing edge: edge:missing",
            errors,
        )
        self.assertIn(
            "v2 behavioral scenario scenario:publication requires an ordered workflow or evidence-backed steps",
            metrics["publish_blockers"],
        )

    def test_v2_contextual_overlay_is_explicit_and_non_primary(self) -> None:
        blueprint = valid_v2_blueprint()
        blueprint["atlas"]["intent"]["static_provider_overlay"] = "contextual"
        blueprint["atlas"]["intent"]["static_provider_overlay_family"] = "boundary"

        graph = graph_from_blueprint(
            blueprint,
            static_graph={
                "nodes": [
                    {"id": "api:provider", "label": "Provider", "type": "api_provider"}
                ]
            },
        )
        provider = next(node for node in graph["nodes"] if node["label"] == "Provider")

        self.assertEqual(provider["overview_visibility"], "contextual")
        self.assertEqual(provider["family"], "boundary")
        self.assertEqual(provider["detail_level"], "detail")
        self.assertFalse(provider["major"])

        missing_family = valid_v2_blueprint()
        missing_family["atlas"]["intent"]["static_provider_overlay"] = "contextual"
        errors, _, _ = validate_blueprint_obj(missing_family)
        self.assertIn(
            "v2 contextual static provider overlay requires a declared static_provider_overlay_family",
            errors,
        )

    def test_v2_viewer_presets_preserve_secondary_projection_and_contextual_neighbors(self) -> None:
        blueprint = valid_v2_blueprint()
        evidence = [{"kind": "source", "path": "README.md"}]
        blueprint["nodes"].append(
            {
                "id": "component:detail",
                "label": "Direct Context",
                "type": "component",
                "family": "transformer",
                "plane": "control",
                "importance": "detail",
                "overview_visibility": "contextual",
                "activation": "optional",
                "description": "A contextual neighbor revealed from a selected core node.",
                "evidence": evidence,
            }
        )
        blueprint["edges"].append(
            {
                "id": "edge:builder_detail",
                "source": "component:builder",
                "target": "component:detail",
                "relation": "documents",
                "relation_family": "flow",
                "workflow_role": "detail",
                "overview_visibility": "contextual",
                "activation": "optional",
                "confidence": "llm_grounded",
                "evidence": evidence,
            }
        )
        secondary = copy.deepcopy(blueprint["atlas"]["projections"][0])
        secondary.update(
            {
                "id": "projection:detail",
                "label": "Context View",
                "description": "A supporting context projection.",
                "question_answered": "What supporting context is available?",
                "is_primary": False,
                "node_ids": ["component:builder", "component:detail"],
            }
        )
        blueprint["atlas"]["projections"].append(secondary)

        errors, _, _ = validate_blueprint_obj(blueprint)
        graph = graph_from_blueprint(blueprint)
        projections = [
            path for path in graph["path_presets"] if path["kind"] == "projection"
        ]

        self.assertEqual(errors, [])
        self.assertEqual([path["label"] for path in projections], ["Authoring Flow", "Context View"])
        self.assertEqual([path["is_primary"] for path in projections], [True, False])
        self.assertEqual(projections[1]["node_ids"], ["component:builder", "component:detail"])
        contextual = next(node for node in graph["nodes"] if node["id"] == "component:detail")
        self.assertEqual(contextual["overview_visibility"], "contextual")

    def test_v2_structural_tour_is_allowed_without_inventing_runtime_order(self) -> None:
        blueprint = valid_v2_blueprint()
        blueprint["atlas"]["scenario_policy"] = "optional"
        scenario = blueprint["atlas"]["scenarios"][0]
        scenario["kind"] = "structural_tour"
        scenario["basis"] = "illustrative_tour"
        scenario["playback_mode"] = "stepped_highlight"
        scenario["derived_from_workflow_ids"] = []

        errors, _, metrics = validate_blueprint_obj(blueprint)

        self.assertEqual(errors, [])
        self.assertEqual(metrics["publish_blockers"], [])

    def test_v2_diagnostics_and_build_report_atlas_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(valid_v2_blueprint()), encoding="utf-8"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    ["diagnose", "--root", str(root), "--require-grounded", "--json"]
                )
            report = json.loads(stdout.getvalue())
            html_path = root / "studio.html"
            with redirect_stdout(io.StringIO()):
                build_result = main(
                    ["build", "--root", str(root), "--out", str(html_path)]
                )
            html = html_path.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(build_result, 0)
        self.assertEqual(report["schema_version"], "bunya-jido-blueprint-v2")
        self.assertEqual(report["primary_projection"], "projection:primary")
        self.assertEqual(report["scenario_policy"], "required")
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(report["atlas_quality_status"], "passed")
        self.assertIn('"schema_version": "bunya-jido-v2"', html)
        self.assertIn('"primary_projection": "projection:primary"', html)
        self.assertIn('"kind": "projection"', html)
        self.assertIn("Studio Projections", html)
        self.assertIn("contextualDirectContext", html)


if __name__ == "__main__":
    unittest.main()
