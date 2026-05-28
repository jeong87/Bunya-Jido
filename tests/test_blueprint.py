from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import (
    AGENT_ACTIVATION_END,
    AGENT_ACTIVATION_START,
    activate_agent_guides,
    generate_agent_context,
    graph_from_blueprint,
    graph_with_optional_blueprint,
    install_agent_guides,
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
        self.assertEqual(
            graph["plane_glossary"],
            [
                {"id": "control", "label": "Control", "purpose": "Workflow"},
                {"id": "entry", "label": "Entry", "purpose": "Commands"},
                {"id": "quality", "label": "Quality", "purpose": "Validation"},
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "atlas.html"
            html = render_html(graph, out).read_text(encoding="utf-8")
        self.assertIn('"blueprint_quality"', html)
        self.assertIn('"Main Flow"', html)
        self.assertIn("Trust", html)
        self.assertIn("Explore Mode", html)
        self.assertIn("Inspect Evidence", html)
        self.assertIn("Implementation Detail", html)
        self.assertIn("Node Families", html)
        self.assertIn("Relation Families", html)
        self.assertIn("Confidence", html)
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

    def test_diagnose_reports_blocked_blueprint_without_rendering_it(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][0]["evidence"] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(blueprint), encoding="utf-8"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    ["diagnose", "--root", str(root), "--require-grounded", "--json"]
                )
            report = json.loads(stdout.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(report["artifact_mode"], "semantic_blueprint")
        self.assertEqual(report["grounding_status"], "blocked")
        self.assertFalse(report["semantic_publication_allowed"])
        self.assertIn("core node component:cli has no evidence", report["publish_blockers"])


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
            node_text = generate_agent_context(root, node="component:builder")
            unmatched_text = generate_agent_context(root, task="rotate database credentials")
            catalog_text = generate_agent_context(root)
            changed_text = generate_agent_context(
                root, changed_files=["src/bunya_jido/blueprint.py"]
            )
            unrelated_changed_text = generate_agent_context(
                root, changed_files=["docs/new-guide.md"]
            )
            task_without_file_evidence_text = generate_agent_context(
                root,
                task="change builder behavior",
                changed_files=["docs/new-guide.md"],
            )
            refresh_stdout = io.StringIO()
            with redirect_stdout(refresh_stdout):
                refresh_result = main(
                    [
                        "refresh-context",
                        "--root",
                        str(root),
                        "--changed-file",
                        "src/bunya_jido/blueprint.py",
                    ]
                )
            graph, _ = graph_with_optional_blueprint(root)
            html = render_html(graph, root / "atlas.html").read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["trusted_route_count"], 1)
        self.assertIn("## Trust", text)
        self.assertIn("Grounding status: `grounded`", text)
        self.assertIn("Agent-map routes: `validated` (1 trusted route(s))", text)
        self.assertIn("Requested route match: `matched`", text)
        self.assertIn("## Recommended task routes", text)
        self.assertIn("### change builder behavior", text)
        self.assertIn("task terms match: `builder`", text)
        self.assertIn("`component:builder`", text)
        self.assertIn("`main_flow`", text)
        self.assertIn("`README.md`", text)
        self.assertIn("Requested route match: `matched`", node_text)
        self.assertIn("focus node `component:builder` starts this route", node_text)
        self.assertIn("Requested route match: `not_found`", unmatched_text)
        self.assertIn("No matching trusted route for this request.", unmatched_text)
        self.assertNotIn("### change builder behavior", unmatched_text)
        self.assertIn("Requested route match: `not_requested`", catalog_text)
        self.assertIn("## Available trusted task routes", catalog_text)
        self.assertIn("### change builder behavior", catalog_text)
        self.assertIn("Requested route match: `matched`", changed_text)
        self.assertIn("Changed-file route match: `matched`", changed_text)
        self.assertIn("changed file `src/bunya_jido/blueprint.py` matches route safe-edit path", changed_text)
        self.assertIn("### change builder behavior", changed_text)
        self.assertIn("Changed-file route match: `not_found`", unrelated_changed_text)
        self.assertIn("No matching trusted route for this request.", unrelated_changed_text)
        self.assertIn("Changed-file route match: `not_found`", task_without_file_evidence_text)
        self.assertNotIn("### change builder behavior", task_without_file_evidence_text)
        self.assertEqual(refresh_result, 0)
        self.assertIn("Changed-file route match: `matched`", refresh_stdout.getvalue())
        route = next(path for path in graph["path_presets"] if path.get("kind") == "task_route")
        self.assertEqual(route["label"], "change builder behavior")
        self.assertEqual(route["source"], "agent_map")
        self.assertIn("component:builder", route["node_ids"])
        self.assertIn("component:validator", route["node_ids"])
        self.assertEqual(graph["agent_map_quality"]["trusted_route_count"], 1)
        self.assertIn('"kind": "task_route"', html)
        self.assertIn("Task Route", html)

    def test_changed_start_node_evidence_can_select_a_route_without_path_overlap(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][1]["evidence"] = [{"kind": "source", "path": "src/builder.py"}]
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["must_read"] = ["docs/route-guide.md"]
        agent_map["task_routes"][0]["safe_edit"] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "docs").mkdir()
            (root / "src").mkdir()
            (root / "tests").mkdir()
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "docs" / "route-guide.md").write_text("route", encoding="utf-8")
            (root / "src" / "builder.py").write_text("# changed\n", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
            (outdir / "bunya-jido.agent-map.json").write_text(json.dumps(agent_map), encoding="utf-8")

            text = generate_agent_context(root, changed_files=["src/builder.py"])

        self.assertIn("Changed-file route match: `matched`", text)
        self.assertIn("### change builder behavior", text)
        self.assertIn(
            "changed file `src/builder.py` affects route start node `component:builder` through grounded evidence",
            text,
        )
        self.assertNotIn("matches route safe-edit path", text)

    def test_refresh_context_requires_changed_file_evidence(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            empty_result = main(["refresh-context"])
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "not-created.txt"
            missing_stderr = io.StringIO()
            with redirect_stderr(missing_stderr):
                missing_result = main(
                    ["refresh-context", "--changed-files-from", str(missing_file)]
                )

        self.assertEqual(empty_result, 2)
        self.assertIn("requires at least one", stderr.getvalue())
        self.assertEqual(missing_result, 2)
        self.assertIn("Changed-files input not found", missing_stderr.getvalue())

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


class AgentGuideActivationTests(unittest.TestCase):
    def test_snippet_guides_agents_to_load_task_context_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = install_agent_guides(tmpdir, agent="codex")
            text = paths["codex"].read_text(encoding="utf-8")
            snippet_bytes = paths["codex"].read_bytes()

        self.assertIn('bunya-jido context --root . --task "<user request>"', text)
        self.assertIn("No matching trusted route", text)
        self.assertIn("no semantic blueprint or agent map", text)
        self.assertIn("Must read", text)
        self.assertIn("Tests", text)
        self.assertIn("refresh-context --root . --changed-file <path>", text)
        self.assertNotIn(b"\r\n", snippet_bytes)

    def test_activation_dry_run_writes_nothing_and_lists_native_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "install-agent-guides",
                        "--root",
                        str(root),
                        "--agent",
                        "all",
                        "--activate",
                        "--dry-run",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(result, 0)
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertFalse((root / "CLAUDE.md").exists())
            self.assertFalse((root / ".cursor" / "rules" / "bunya-jido.mdc").exists())
            self.assertFalse((root / ".clinerules" / "bunya-jido.md").exists())
            self.assertIn("codex: would_create", output)
            self.assertIn("claude: would_create", output)
            self.assertIn("cursor: would_create", output)
            self.assertIn("cline: would_create", output)
            self.assertIn('bunya-jido context --root . --task "<user request>"', output)

    def test_activation_preserves_user_content_and_updates_only_managed_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agents_path = root / "AGENTS.md"
            agents_path.write_text("# Existing Rules\n\nKeep this instruction.\n", encoding="utf-8")

            first = activate_agent_guides(root, agent="all")
            first_text = agents_path.read_text(encoding="utf-8")
            second = activate_agent_guides(root, agent="all")
            second_text = agents_path.read_text(encoding="utf-8")
            cursor_path = root / ".cursor" / "rules" / "bunya-jido.mdc"
            cursor_text = cursor_path.read_text(encoding="utf-8")
            cursor_bytes = cursor_path.read_bytes()

        self.assertEqual(first["codex"]["status"], "appended")
        self.assertEqual(second["codex"]["status"], "updated")
        self.assertIn("Keep this instruction.", second_text)
        self.assertEqual(first_text, second_text)
        self.assertEqual(second_text.count(AGENT_ACTIVATION_START), 1)
        self.assertEqual(second_text.count(AGENT_ACTIVATION_END), 1)
        self.assertIn("alwaysApply: true", cursor_text)
        self.assertIn('bunya-jido context --root . --task "<user request>"', cursor_text)
        self.assertIn("refresh-context --root . --changed-file <path>", cursor_text)
        self.assertNotIn(b"\r\n", cursor_bytes)

    def test_dry_run_without_activation_is_rejected(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["install-agent-guides", "--dry-run"])

        self.assertEqual(result, 2)
        self.assertIn("--dry-run requires --activate", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
