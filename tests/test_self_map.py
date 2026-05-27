from __future__ import annotations

import json
import unittest
from pathlib import Path

from bunya_jido.blueprint import (
    generate_agent_context,
    graph_with_optional_blueprint,
    validate_agent_map_obj,
    validate_blueprint_obj,
)


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = ROOT / ".bunya-jido" / "bunya-jido.blueprint.json"
AGENT_MAP_PATH = ROOT / ".bunya-jido" / "bunya-jido.agent-map.json"
DEMO_PATH = ROOT / "docs" / "demo.html"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_semantic_contract(graph: dict) -> dict:
    return {
        "artifact_mode": graph["artifact_mode"],
        "grounding": graph["grounding"],
        "stats": graph["stats"],
        "plane_glossary": graph["plane_glossary"],
        "nodes": [
            (node["id"], node["label"], node["plane"], node["type"])
            for node in graph["nodes"]
        ],
        "edges": [
            (edge["source"], edge["target"], edge["relation"], edge["confidence"])
            for edge in graph["edges"]
        ],
        "paths": [
            (path["id"], path["kind"], path["source"], path["node_ids"])
            for path in graph["path_presets"]
        ],
        "blueprint_path": graph["blueprint_path"],
        "agent_map_path": graph["agent_map_path"],
        "agent_map_quality": graph["agent_map_quality"],
    }


class SemanticSelfMapGoldenTests(unittest.TestCase):
    def test_committed_self_map_and_routes_are_grounded(self) -> None:
        blueprint = load_json(BLUEPRINT_PATH)
        agent_map = load_json(AGENT_MAP_PATH)

        errors, warnings, metrics = validate_blueprint_obj(blueprint, root=ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["node_count"], 12)
        self.assertEqual(metrics["edge_count"], 19)
        self.assertEqual(metrics["grounded_core_node_ratio"], 1.0)
        self.assertEqual(metrics["grounded_critical_edge_ratio"], 1.0)

        errors, warnings, metrics = validate_agent_map_obj(
            agent_map, root=ROOT, blueprint=blueprint
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["trusted_route_count"], 3)

    def test_gallery_build_projects_expected_semantic_paths(self) -> None:
        graph, _ = graph_with_optional_blueprint(ROOT, max_files=0)

        self.assertEqual(graph["artifact_mode"], "semantic_blueprint")
        self.assertEqual(graph["grounding"]["status"], "grounded")
        self.assertTrue(graph["grounding"]["publishable"])
        self.assertEqual(graph["stats"]["nodes"], 12)
        self.assertEqual(graph["stats"]["edges"], 19)
        self.assertIn(
            {
                "id": "semantic",
                "label": "Semantic",
                "purpose": "Reviewed architecture and agent-route projection.",
            },
            graph["plane_glossary"],
        )
        self.assertEqual(
            graph["blueprint_path"], ".bunya-jido/bunya-jido.blueprint.json"
        )
        self.assertEqual(
            graph["agent_map_path"], ".bunya-jido/bunya-jido.agent-map.json"
        )
        route_ids = {
            path["id"]
            for path in graph["path_presets"]
            if path["kind"] == "task_route"
        }
        self.assertEqual(
            route_ids,
            {
                "task_route_change-grounding-policy",
                "task_route_change-task-route-projection",
                "task_route_change-viewer-trust-presentation",
            },
        )

    def test_trusted_context_uses_committed_route(self) -> None:
        context = generate_agent_context(ROOT, task="change task route projection")

        self.assertIn("- Grounding status: `grounded`", context)
        self.assertIn("- Agent-map routes: `validated` (3 trusted route(s))", context)
        self.assertIn("### change task route projection", context)
        self.assertIn("- `task_route_publication`", context)

    def test_published_demo_matches_stable_semantic_contract(self) -> None:
        html = DEMO_PATH.read_text(encoding="utf-8")
        for control in (
            "Explore Mode",
            "Inspect Evidence",
            "Implementation Detail",
            "Responsibility Areas",
            "Relation Families",
            "Confidence",
            "Validated Task Routes",
            "Selected Relationship",
        ):
            self.assertIn(control, html)
        marker = '<script id="graph-data" type="application/json">'
        data_start = html.index(marker) + len(marker)
        data_end = html.index("</script>", data_start)
        published = json.loads(html[data_start:data_end])
        rebuilt, _ = graph_with_optional_blueprint(ROOT, max_files=0)

        self.assertEqual(
            stable_semantic_contract(published),
            stable_semantic_contract(rebuilt),
        )


if __name__ == "__main__":
    unittest.main()
