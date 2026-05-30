from __future__ import annotations

import io
import json
import struct
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import (
    evaluate_agent_utility,
    evaluate_map_freshness,
    generate_agent_context,
    graph_with_optional_blueprint,
    validate_agent_map_obj,
    validate_blueprint_obj,
)
from bunya_jido.cli import main


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = ROOT / ".bunya-jido" / "bunya-jido.blueprint.json"
AGENT_MAP_PATH = ROOT / ".bunya-jido" / "bunya-jido.agent-map.json"
AGENT_EVALUATION_PATH = ROOT / ".bunya-jido" / "bunya-jido.agent-evaluation.json"
DEMO_PATH = ROOT / "docs" / "demo.html"
HERO_PATH = ROOT / "docs" / "assets" / "self-map-grounded.png"


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
        self.assertEqual(metrics["node_count"], 13)
        self.assertEqual(metrics["edge_count"], 22)
        self.assertEqual(metrics["grounded_core_node_ratio"], 1.0)
        self.assertEqual(metrics["grounded_critical_edge_ratio"], 1.0)

        errors, warnings, metrics = validate_agent_map_obj(
            agent_map, root=ROOT, blueprint=blueprint
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["trusted_route_count"], 4)

    def test_gallery_build_projects_expected_semantic_paths(self) -> None:
        graph, _ = graph_with_optional_blueprint(ROOT, max_files=0)

        self.assertEqual(graph["artifact_mode"], "semantic_blueprint")
        self.assertEqual(graph["grounding"]["status"], "grounded")
        self.assertTrue(graph["grounding"]["publishable"])
        self.assertEqual(graph["stats"]["nodes"], 13)
        self.assertEqual(graph["stats"]["edges"], 22)
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
                "task_route_change-atlas-quality-evaluation",
                "task_route_change-task-route-projection",
                "task_route_change-viewer-trust-presentation",
            },
        )

    def test_trusted_context_uses_committed_route(self) -> None:
        context = generate_agent_context(ROOT, task="change task route projection")

        self.assertIn("- Grounding status: `grounded`", context)
        self.assertIn("- Agent-map routes: `validated` (4 trusted route(s))", context)
        self.assertIn("- Requested route match: `matched`", context)
        self.assertIn("### change task route projection", context)
        self.assertIn("- `task_route_publication`", context)

    def test_unmatched_context_does_not_invent_self_map_route(self) -> None:
        context = generate_agent_context(ROOT, task="publish package to package registry")

        self.assertIn("- Requested route match: `not_found`", context)
        self.assertIn("No matching trusted route for this request.", context)
        self.assertNotIn("### change grounding policy", context)
        self.assertNotIn("### change atlas quality evaluation", context)
        self.assertNotIn("### change task route projection", context)
        self.assertNotIn("### change viewer trust presentation", context)

    def test_refresh_context_routes_only_from_changed_self_map_evidence(self) -> None:
        context = generate_agent_context(
            ROOT, changed_files=["src/bunya_jido/blueprint.py"]
        )
        unrelated = generate_agent_context(ROOT, changed_files=["README.ko.md"])

        self.assertIn("- Changed-file route match: `matched`", context)
        self.assertIn("### change grounding policy", context)
        self.assertIn("### change atlas quality evaluation", context)
        self.assertIn("### change task route projection", context)
        self.assertIn("### change viewer trust presentation", context)
        self.assertIn(
            "changed file `src/bunya_jido/blueprint.py` matches route safe-edit path",
            context,
        )
        self.assertIn("- Changed-file route match: `not_found`", unrelated)
        self.assertNotIn("### change grounding policy", unrelated)
        self.assertNotIn("### change atlas quality evaluation", unrelated)
        self.assertNotIn("### change task route projection", unrelated)

    def test_committed_stale_policy_requires_map_review_for_source_changes(self) -> None:
        stale = evaluate_map_freshness(ROOT, ["src/bunya_jido/cli.py"])
        reviewed = evaluate_map_freshness(
            ROOT,
            ["src/bunya_jido/cli.py", ".bunya-jido/MAP_REVIEW.md"],
        )

        self.assertEqual(stale["status"], "stale")
        self.assertIn("src/bunya_jido/cli.py", stale["triggering_files"])
        self.assertEqual(reviewed["status"], "review_recorded")

    def test_committed_agent_utility_evaluation_covers_bounded_context_contract(self) -> None:
        self.assertTrue(AGENT_EVALUATION_PATH.exists())

        report = evaluate_agent_utility(ROOT)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(
                ["evaluate-agent-utility", "--root", str(ROOT), "--require-pass", "--json"]
            )
        cli_report = json.loads(stdout.getvalue())

        self.assertEqual(result, 0)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["case_count"], 6)
        self.assertEqual(
            set(report["dimensions"]),
            {
                "first_read_accuracy",
                "test_recall",
                "boundary_discipline",
                "honest_no_match",
                "change_aware_refresh",
            },
        )
        self.assertEqual(cli_report["status"], "passed")
        self.assertIn("does not measure whether a live coding agent follows", report["limitation"])

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
            "Map Controls",
            'id="toolbarTrust"',
            'id="workflowBar"',
            "nodeRoleStyles",
            "drawNodeShape",
            "relationFamilyVisuals",
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

    def test_published_hero_is_wide_and_linked_from_both_readmes(self) -> None:
        png = HERO_PATH.read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual((width, height), (1440, 900))
        for readme in ("README.md", "README.ko.md"):
            text = (ROOT / readme).read_text(encoding="utf-8")
            self.assertIn("docs/assets/self-map-grounded.png", text)
            self.assertIn("semantic role glyphs", text)

    def test_release_diagnostics_require_the_committed_grounded_self_map(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(
                ["diagnose", "--root", str(ROOT), "--require-grounded", "--json"]
            )
        report = json.loads(stdout.getvalue())

        self.assertEqual(result, 0)
        self.assertEqual(report["artifact_mode"], "semantic_blueprint")
        self.assertEqual(report["grounding_status"], "grounded")
        self.assertTrue(report["semantic_publication_allowed"])
        self.assertEqual(report["atlas_quality_status"], "not_assessed")
        self.assertEqual(report["agent_routes"], {"status": "validated", "trusted": 4, "total": 4})


if __name__ == "__main__":
    unittest.main()
