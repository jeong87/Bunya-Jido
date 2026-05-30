from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bunya_jido.blueprint import graph_from_blueprint, validate_blueprint_obj
from bunya_jido.quality import evaluate_atlas_quality_obj
from bunya_jido.render import render_html


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "fixtures" / "studio_benchmark_cases.json"


def load_cases() -> dict:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def benchmark_blueprint(case: dict) -> dict:
    evidence = [{"kind": "benchmark", "path": "README.md"}]
    families = {
        landmark["family"] for landmark in case["landmarks"]
    }
    glyphs = {
        "boundary": "hexagon",
        "gate": "octagon",
        "transform": "rounded_square",
        "record": "double_ring",
        "surface": "diamond",
    }
    nodes = []
    for index, landmark in enumerate(case["landmarks"]):
        nodes.append(
            {
                "id": f"component:{landmark['id']}",
                "label": landmark["label"],
                "type": "component",
                "family": landmark["family"],
                "plane": landmark["plane"],
                "importance": "core" if index < 2 else "major",
                "overview_visibility": "visible",
                "activation": "always",
                "description": f"{landmark['label']} is a benchmark landmark used to test this repository-specific projection.",
                "why_it_matters": f"{landmark['label']} anchors the primary reading question.",
                "inspector_summary": f"Benchmark evidence for {landmark['label']}.",
                "evidence": evidence,
            }
        )
    edges = []
    for index, (source, target) in enumerate(zip(nodes, nodes[1:]), start=1):
        edges.append(
            {
                "id": f"edge:{case['id']}:{index}",
                "source": source["id"],
                "target": target["id"],
                "relation": case["edge_relation"],
                "relation_family": "primary_reading",
                "workflow_role": "primary",
                "overview_visibility": "visible",
                "activation": "always",
                "confidence": "llm_grounded",
                "evidence": evidence,
            }
        )
    scenario_spec = case["scenario"]
    has_scenario = scenario_spec["policy"] != "none_with_reason"
    workflow = {
        "id": "workflow:primary",
        "label": case["primary_projection"]["label"],
        "description": case["primary_projection"]["question"],
        "kind": "behavioral" if scenario_spec.get("kind") == "behavioral" else "structural",
        "ordered": scenario_spec.get("kind") == "behavioral",
        "node_ids": [node["id"] for node in nodes],
        "evidence": evidence,
    }
    scenarios = []
    if has_scenario:
        scenarios.append(
            {
                "id": f"scenario:{case['id']}",
                "label": case["primary_projection"]["label"],
                "description": case["primary_projection"]["question"],
                "kind": scenario_spec["kind"],
                "basis": scenario_spec["basis"],
                "derived_from_workflow_ids": ["workflow:primary"],
                "playback_mode": scenario_spec["playback_mode"],
                "default_speed": 1.0,
                "steps": [
                    {
                        "id": f"step:{index + 1}",
                        "node_id": node["id"],
                        **({"edge_id": edges[index]["id"]} if index < len(edges) else {}),
                        "title": node["label"],
                        "narration": f"Inspect {node['label']} within the {case['primary_projection']['label']} reading.",
                        "evidence": evidence,
                    }
                    for index, node in enumerate(nodes)
                ],
            }
        )
    atlas = {
        "scenario_policy": scenario_spec["policy"],
        "vocabularies": {
            "node_families": [
                {
                    "id": family,
                    "label": family.replace("_", " ").title(),
                    "description": f"Project-local {family} landmark.",
                    "glyph": glyphs[family],
                }
                for family in sorted(families)
            ],
            "relation_families": [
                {
                    "id": "primary_reading",
                    "label": "Primary Reading",
                    "description": "Connects the selected first-read landmarks.",
                    "line_style": "solid",
                }
            ],
        },
        "projections": [
            {
                "id": f"projection:{case['primary_projection']['id']}",
                "label": case["primary_projection"]["label"],
                "description": case["thesis"],
                "question_answered": case["primary_projection"]["question"],
                "is_primary": True,
                "node_ids": [node["id"] for node in nodes],
                "plane_ids": [plane["id"] for plane in case["planes"]],
                "relation_family_ids": ["primary_reading"],
                "evidence": evidence,
            }
        ],
        "scenarios": scenarios,
        "intent": {"static_provider_overlay": "excluded"},
    }
    if scenario_spec["policy"] == "none_with_reason":
        atlas["scenario_policy_reason"] = scenario_spec["reason"]
    return {
        "schema_version": "bunya-jido-blueprint-v2",
        "project": {
            "name": case["id"],
            "summary": case["domain"],
            "thesis": case["thesis"],
            "primary_projection_id": f"projection:{case['primary_projection']['id']}",
            "ordered_behavior_assessment": case["ordered_behavior_assessment"],
        },
        "planes": case["planes"],
        "nodes": nodes,
        "edges": edges,
        "workflows": [workflow],
        "atlas": atlas,
    }


class StudioBenchmarkTests(unittest.TestCase):
    def test_six_domain_rubrics_render_publishable_distinct_studio_atlases(self) -> None:
        fixture = load_cases()
        cases = fixture["cases"]
        theses: set[str] = set()
        projections: set[str] = set()
        policies: set[str] = set()

        self.assertGreaterEqual(len(cases), 4)
        for case in cases:
            blueprint = benchmark_blueprint(case)
            rubric = case["rubric"]
            errors, warnings, metrics = validate_blueprint_obj(blueprint)
            report = evaluate_atlas_quality_obj(
                blueprint, validation_errors=errors, validation_metrics=metrics
            )
            graph = graph_from_blueprint(blueprint)
            with tempfile.TemporaryDirectory() as tmpdir:
                html = render_html(graph, Path(tmpdir) / "benchmark.html").read_text(
                    encoding="utf-8"
                )

            self.assertEqual(errors, [], case["id"])
            self.assertEqual(metrics["publish_blockers"], [], case["id"])
            self.assertEqual(metrics["grounding_status"], "grounded", case["id"])
            self.assertEqual(report["status"], "passed", case["id"])
            self.assertEqual(graph["schema_version"], "bunya-jido-v2", case["id"])
            self.assertIn(case["primary_projection"]["label"], html)
            self.assertIn("scenarioBtn", html)
            self.assertEqual(
                len(blueprint["atlas"]["scenarios"]),
                rubric["scenario_expectation"]["min"],
            )
            node_labels = {node["label"] for node in blueprint["nodes"]}
            self.assertTrue(set(rubric["must_include_landmarks"]).issubset(node_labels))
            self.assertTrue(set(rubric["must_not_overcentralize"]).isdisjoint(node_labels))
            self.assertTrue(rubric["expected_projection_kinds"])
            self.assertTrue(rubric["human_readability_notes"])
            for trait in rubric["expected_thesis_traits"]:
                self.assertIn(trait.lower(), case["thesis"].lower())
            if blueprint["atlas"]["scenarios"]:
                self.assertIn(
                    blueprint["atlas"]["scenarios"][0]["kind"],
                    rubric["scenario_expectation"]["allowed_kinds"],
                )
            else:
                self.assertEqual(rubric["scenario_expectation"]["allowed_kinds"], [])
            theses.add(case["thesis"])
            projections.add(case["primary_projection"]["label"])
            policies.add(case["scenario"]["policy"])

        self.assertEqual(len(theses), len(cases))
        self.assertEqual(len(projections), len(cases))
        self.assertEqual(policies, {"required", "optional", "none_with_reason"})

    def test_non_runtime_surfaces_do_not_claim_animated_lifecycle(self) -> None:
        cases = {case["id"]: case for case in load_cases()["cases"]}

        sdk = benchmark_blueprint(cases["sdk_client"])
        utility = benchmark_blueprint(cases["utility_library"])

        self.assertEqual(sdk["atlas"]["scenarios"][0]["kind"], "structural_tour")
        self.assertEqual(
            sdk["atlas"]["scenarios"][0]["playback_mode"], "stepped_highlight"
        )
        self.assertEqual(utility["atlas"]["scenario_policy"], "none_with_reason")
        self.assertEqual(utility["atlas"]["scenarios"], [])

    def test_complex_system_review_policy_is_not_a_runtime_taxonomy_seed(self) -> None:
        fixture = load_cases()
        source = (
            (ROOT / "src" / "bunya_jido" / "studio.py").read_text(encoding="utf-8")
            + (ROOT / "src" / "bunya_jido" / "viewer" / "index.template.html").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("never a prompt seed", fixture["benchmark_policy"]["external_complex_system_usage"])
        self.assertNotIn("Auto-Researcher", source)
        self.assertIn("authoredPlaneOrder", source)
        self.assertIn("studioAtlas ? -90", source)


if __name__ == "__main__":
    unittest.main()
