from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import (
    generate_agent_context,
    graph_from_blueprint,
    graph_with_optional_blueprint,
    validate_agent_map_obj,
    validate_blueprint_obj,
)
from bunya_jido.cli import main
from bunya_jido.render import render_html


def example_blueprint() -> dict:
    return {
        "schema_version": "bunya-jido-blueprint-v1",
        "project": {"name": "fixture", "summary": "A semantic fixture."},
        "planes": [
            {"id": "entry", "label": "Entry", "purpose": "Commands"},
            {"id": "control", "label": "Control", "purpose": "Workflow"},
            {"id": "quality", "label": "Quality", "purpose": "Validation"},
        ],
        "nodes": [
            {
                "id": "component:cli",
                "label": "CLI",
                "type": "component",
                "plane": "entry",
                "importance": "core",
                "description": "Accepts commands.",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
            {
                "id": "component:builder",
                "label": "Builder",
                "type": "component",
                "plane": "control",
                "importance": "core",
                "description": "Builds a map.",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
            {
                "id": "component:validator",
                "label": "Validator",
                "type": "contract",
                "plane": "quality",
                "importance": "major",
                "description": "Checks blueprint structure.",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
        ],
        "edges": [
            {
                "source": "component:cli",
                "target": "component:builder",
                "relation": "calls",
                "confidence": "llm_grounded",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
            {
                "source": "component:builder",
                "target": "component:validator",
                "relation": "validates",
                "confidence": "llm_grounded",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
        ],
        "workflows": [
            {
                "id": "main_flow",
                "label": "Main Flow",
                "description": "Command to validation.",
                "node_ids": ["component:cli", "component:builder", "component:validator"],
            }
        ],
    }


def example_agent_map() -> dict:
    return {
        "schema_version": "bunya-jido-agent-map-v1",
        "project": {"name": "fixture", "summary": "Agent routes."},
        "task_routes": [
            {
                "task": "change builder behavior",
                "intent": "Update builder logic.",
                "start_nodes": ["component:builder"],
                "workflows": ["main_flow"],
                "must_read": ["README.md"],
                "contracts": ["Blueprint contract"],
                "tests": ["tests/test_smoke.py"],
                "safe_edit": ["src/bunya_jido/blueprint.py"],
            }
        ],
    }


class BlueprintCharacterizationTests(unittest.TestCase):
    def test_missing_core_evidence_and_unverified_edge_block_publication(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][0]["evidence"] = []
        blueprint["edges"][0]["evidence"] = []
        blueprint["edges"][0]["confidence"] = "unverified"

        errors, warnings, metrics = validate_blueprint_obj(blueprint)

        self.assertEqual(errors, [])
        self.assertIn("node component:cli has no evidence", warnings)
        self.assertIn("edge component:cli->component:builder has no evidence", warnings)
        self.assertIn("edge component:cli->component:builder is unverified", warnings)
        self.assertEqual(metrics["grounded_node_ratio"], 0.667)
        self.assertEqual(metrics["grounded_edge_ratio"], 0.5)
        self.assertEqual(metrics["grounding_status"], "blocked")
        self.assertEqual(metrics["publish_blocker_count"], 3)
        with self.assertRaisesRegex(ValueError, "Blueprint publication blocked"):
            graph_from_blueprint(blueprint)
        draft = graph_from_blueprint(blueprint, allow_draft=True)
        self.assertEqual(draft["grounding"]["status"], "draft")
        self.assertTrue(draft["grounding"]["draft_override"])

    def test_unresolved_core_evidence_path_blocks_publication(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][0]["evidence"] = [{"kind": "source", "path": "src/missing.py"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("fixture", encoding="utf-8")

            errors, warnings, metrics = validate_blueprint_obj(blueprint, root=root)

        self.assertEqual(errors, [])
        self.assertIn("evidence path not found: src/missing.py for node component:cli", warnings)
        self.assertIn(
            "core node component:cli has unresolved evidence path: src/missing.py",
            metrics["publish_blockers"],
        )

    def test_blueprint_without_core_landmarks_is_blocked(self) -> None:
        blueprint = example_blueprint()
        for node in blueprint["nodes"]:
            node.pop("importance", None)

        errors, _, metrics = validate_blueprint_obj(blueprint)

        self.assertEqual(errors, [])
        self.assertIn(
            "semantic blueprint has no core nodes; mark architectural landmarks with importance=core",
            metrics["publish_blockers"],
        )
        with self.assertRaisesRegex(ValueError, "Blueprint publication blocked"):
            graph_from_blueprint(blueprint)

    def test_secret_like_blueprint_content_is_an_error(self) -> None:
        blueprint = example_blueprint()
        blueprint["project"]["summary"] = "token=abcdefghijklmnopqrstuv"

        errors, _, _ = validate_blueprint_obj(blueprint)

        self.assertTrue(any("secret-like text" in error for error in errors))
        with self.assertRaisesRegex(ValueError, "Blueprint validation failed"):
            graph_from_blueprint(blueprint, allow_draft=True)

    def test_graph_hides_repo_node_and_preserves_workflow_and_quality_data(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"].append(
            {
                "id": "repo:fixture",
                "label": "fixture",
                "type": "repo",
                "plane": "repo",
                "description": "Synthetic root.",
                "evidence": [{"kind": "root", "path": "."}],
            }
        )

        graph = graph_from_blueprint(blueprint, show_root=False)

        self.assertFalse(any(node["type"] == "repo" for node in graph["nodes"]))
        self.assertTrue(any(path["label"] == "Main Flow" for path in graph["path_presets"]))
        self.assertEqual(graph["artifact_mode"], "semantic_blueprint")
        self.assertEqual(graph["grounding"]["status"], "grounded")
        self.assertEqual(graph["blueprint_quality"]["grounded_node_ratio"], 1.0)
        self.assertEqual(graph["nodes"][0].get("evidence"), [{"kind": "source", "path": "README.md"}])

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "atlas.html"
            html = render_html(graph, out).read_text(encoding="utf-8")
        self.assertIn('"blueprint_quality"', html)
        self.assertIn('"Main Flow"', html)
        self.assertIn("Trust", html)
        self.assertIn("confidence:", html)

    def test_graph_conversion_is_stable_after_generated_timestamp_is_removed(self) -> None:
        first = graph_from_blueprint(example_blueprint())
        second = graph_from_blueprint(example_blueprint())
        first.pop("generated_at", None)
        second.pop("generated_at", None)

        self.assertEqual(first, second)

    def test_cli_requires_explicit_draft_override_for_grounding_blockers(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][0]["evidence"] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
            html_path = root / "atlas.html"
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                blocked = main(["validate-blueprint", "--root", str(root)])
                blocked_build = main(["build", "--root", str(root), "--out", str(html_path)])
                draft = main(["build", "--root", str(root), "--allow-draft", "--out", str(html_path)])
            html = html_path.read_text(encoding="utf-8")

        self.assertEqual(blocked, 2)
        self.assertIn("Blueprint publication blocked", stderr.getvalue())
        self.assertEqual(blocked_build, 1)
        self.assertEqual(draft, 0)
        self.assertIn("grounding=draft", stdout.getvalue())
        self.assertIn('"status": "draft"', html)


class AgentMapCharacterizationTests(unittest.TestCase):
    def test_missing_blueprint_start_node_blocks_trusted_context(self) -> None:
        agent_map = {
            "schema_version": "bunya-jido-agent-map-v1",
            "project": {"name": "fixture", "summary": "Agent routes."},
            "task_routes": [
                {
                    "task": "change provider behavior",
                    "intent": "Update routing.",
                    "start_nodes": ["component:missing"],
                    "must_read": ["README.md"],
                    "tests": ["tests/test_smoke.py"],
                }
            ],
        }

        errors, warnings, metrics = validate_agent_map_obj(agent_map, blueprint=example_blueprint())

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertTrue(any("references nodes not in blueprint" in blocker for blocker in metrics["publish_blockers"]))
        self.assertEqual(metrics["grounded_route_ratio"], 0.0)
        self.assertEqual(metrics["trusted_route_count"], 0)

    def test_missing_workflow_and_required_files_block_trusted_context(self) -> None:
        blueprint = example_blueprint()
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["workflows"] = ["missing_flow"]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            errors, _, metrics = validate_agent_map_obj(agent_map, root=root, blueprint=blueprint)

        self.assertEqual(errors, [])
        self.assertTrue(any("workflows not in blueprint" in blocker for blocker in metrics["publish_blockers"]))
        self.assertTrue(any("must-read path not found" in blocker for blocker in metrics["publish_blockers"]))
        self.assertTrue(any("test path not found" in blocker for blocker in metrics["publish_blockers"]))

    def test_malformed_route_link_fields_are_validation_errors(self) -> None:
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["must_read"] = "README.md"

        errors, _, _ = validate_agent_map_obj(agent_map, blueprint=example_blueprint())

        self.assertIn("task_routes[0].must_read must be a list", errors)

    def test_hidden_root_start_and_remote_test_cannot_be_trusted_route(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"].append(
            {
                "id": "repo:fixture",
                "label": "fixture",
                "type": "repo",
                "plane": "repo",
                "description": "Synthetic root.",
                "evidence": [{"kind": "root", "path": "."}],
            }
        )
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["start_nodes"] = ["repo:fixture"]
        agent_map["task_routes"][0]["must_read"] = ["../outside.md"]
        agent_map["task_routes"][0]["tests"] = ["https://example.test/remote-test"]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (Path(tmpdir) / "outside.md").write_text("outside", encoding="utf-8")

            _, _, metrics = validate_agent_map_obj(agent_map, root=root, blueprint=blueprint)

        self.assertTrue(any("starts at hidden repo/root node" in blocker for blocker in metrics["publish_blockers"]))
        self.assertTrue(any("must-read path not found" in blocker for blocker in metrics["publish_blockers"]))
        self.assertTrue(any("test path not found" in blocker for blocker in metrics["publish_blockers"]))

    def test_validated_task_route_is_shared_by_context_and_html(self) -> None:
        blueprint = example_blueprint()
        agent_map = example_agent_map()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "tests").mkdir()
            (root / "src" / "bunya_jido").mkdir(parents=True)
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (root / "src" / "bunya_jido" / "blueprint.py").write_text("# fixture\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
            (outdir / "bunya-jido.agent-map.json").write_text(json.dumps(agent_map), encoding="utf-8")

            errors, warnings, metrics = validate_agent_map_obj(agent_map, root=root, blueprint=blueprint)
            text = generate_agent_context(root, task="change builder behavior")
            graph, _ = graph_with_optional_blueprint(root)
            html = render_html(graph, root / "atlas.html").read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["trusted_route_count"], 1)
        self.assertIn("## Trust", text)
        self.assertIn("Grounding status: `grounded`", text)
        self.assertIn("Agent-map routes: `validated` (1 trusted route(s))", text)
        self.assertIn("## Recommended task routes", text)
        self.assertIn("### change builder behavior", text)
        self.assertIn("`component:builder`", text)
        self.assertIn("`main_flow`", text)
        self.assertIn("`README.md`", text)
        route = next(path for path in graph["path_presets"] if path.get("kind") == "task_route")
        self.assertEqual(route["label"], "change builder behavior")
        self.assertEqual(route["source"], "agent_map")
        self.assertIn("component:builder", route["node_ids"])
        self.assertIn("component:validator", route["node_ids"])
        self.assertEqual(graph["agent_map_quality"]["trusted_route_count"], 1)
        self.assertIn('"kind": "task_route"', html)
        self.assertIn("Task Route", html)

    def test_context_refuses_blocked_task_route(self) -> None:
        blueprint = example_blueprint()
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["start_nodes"] = ["component:missing"]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "tests").mkdir()
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
            (outdir / "bunya-jido.agent-map.json").write_text(json.dumps(agent_map), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Trusted context blocked by agent-map routes"):
                generate_agent_context(root, task="change builder behavior")

    def test_invalid_task_route_blocks_publication_but_draft_omits_it(self) -> None:
        blueprint = example_blueprint()
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["start_nodes"] = ["component:missing"]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "tests").mkdir()
            (root / "src" / "bunya_jido").mkdir(parents=True)
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (root / "src" / "bunya_jido" / "blueprint.py").write_text("# fixture\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
            (outdir / "bunya-jido.agent-map.json").write_text(json.dumps(agent_map), encoding="utf-8")
            html_path = root / "atlas.html"
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                blocked = main(["build", "--root", str(root), "--out", str(html_path)])
                draft = main(["build", "--root", str(root), "--allow-draft", "--out", str(html_path)])
            html = html_path.read_text(encoding="utf-8")

        self.assertEqual(blocked, 1)
        self.assertIn("Blueprint publication blocked", stderr.getvalue())
        self.assertEqual(draft, 0)
        self.assertIn("grounding=draft", stdout.getvalue())
        self.assertIn("agent map: task route change builder behavior references nodes not in blueprint", html)
        self.assertNotIn('"kind": "task_route"', html)


if __name__ == "__main__":
    unittest.main()
