from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from bunya_jido.blueprint import (
    AGENT_ACTIVATION_END,
    AGENT_ACTIVATION_START,
    activate_agent_guides,
    deactivate_agent_guides,
    evaluate_agent_utility,
    evaluate_map_freshness,
    _generate_agent_route_receipt,
    generate_agent_context,
    generate_agent_context_report,
    graph_from_blueprint,
    graph_with_optional_blueprint,
    install_agent_guides,
    validate_agent_evaluation_obj,
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
        "repository_scope": {
            "supported_surfaces": ["semantic map builder"],
            "supported_technologies": ["Python"],
            "unsupported_surfaces": [
                "native iOS application",
                "Android Gradle application",
                "Electron desktop application",
            ],
            "unsupported_technologies": ["Terraform", "Kubernetes"],
            "repository_non_goals": ["native mobile application development"],
        },
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
        agent_map["task_routes"][0]["when_not_to_use"] = "mobile work"
        agent_map["task_routes"][0]["common_failure_modes"] = "cursor drift"
        agent_map["task_routes"][0]["domain_entities"] = "BuilderState"
        agent_map["repository_scope"]["unsupported_surfaces"] = "native iOS application"

        errors, _, _ = validate_agent_map_obj(agent_map, blueprint=example_blueprint())

        self.assertIn("task_routes[0].must_read must be a list", errors)
        self.assertIn("task_routes[0].when_not_to_use must be a list of non-empty strings", errors)
        self.assertIn(
            "task_routes[0].common_failure_modes must be a list of non-empty strings",
            errors,
        )
        self.assertIn(
            "task_routes[0].domain_entities must be a list of non-empty strings",
            errors,
        )
        self.assertIn(
            "repository_scope.unsupported_surfaces must be a list of non-empty strings",
            errors,
        )

    def test_context_decision_rejects_out_of_scope_and_weak_lexical_matches(self) -> None:
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

            ios = generate_agent_context_report(
                root, task="Add a native iOS app with App Store signing."
            )
            weak = generate_agent_context_report(
                root, task="Add an audit event for a workflow state not yet represented in the map."
            )
            matched = generate_agent_context_report(root, task="change builder behavior")
            broad_match_map = example_agent_map()
            broad_match_map["task_routes"][0]["match_terms"] = ["builder"]
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(broad_match_map), encoding="utf-8"
            )
            broad_match = generate_agent_context_report(
                root, task="Add external builder deployment support."
            )
            route_boundary_map = example_agent_map()
            route_boundary_map["repository_scope"]["supported_technologies"].append("iOS")
            route_boundary_map["repository_scope"]["unsupported_surfaces"] = [
                "Android Gradle application",
                "Electron desktop application",
            ]
            route_boundary_map["repository_scope"]["repository_non_goals"] = []
            route_boundary_map["task_routes"][0]["when_not_to_use"] = [
                "native iOS application"
            ]
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(route_boundary_map), encoding="utf-8"
            )
            route_boundary = generate_agent_context_report(
                root, task="change builder behavior for a native iOS application"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                cli_result = main(
                    [
                        "context",
                        "--root",
                        str(root),
                        "--task",
                        "Add Terraform Kubernetes deployment manifests.",
                        "--json",
                    ]
                )
            cli_report = json.loads(stdout.getvalue())

        self.assertEqual(ios["decision"], "OUT_OF_SCOPE")
        self.assertEqual(ios["route_status"], "not_found")
        self.assertEqual(ios["edit_policy"], "read_only")
        self.assertEqual(ios["execution_policy"], "read_only")
        self.assertEqual(ios["safe_edit_paths"], [])
        self.assertIn("Do not modify files", ios["agent_instruction"])
        self.assertEqual(weak["decision"], "UNCERTAIN")
        self.assertEqual(weak["execution_policy"], "read_only")
        self.assertEqual(weak["matched_routes"], [])
        self.assertEqual(matched["decision"], "MATCH")
        self.assertEqual(matched["execution_policy"], "workspace_write")
        self.assertEqual(matched["matched_routes"], ["change builder behavior"])
        self.assertNotEqual(broad_match["decision"], "MATCH")
        self.assertEqual(broad_match["matched_routes"], [])
        self.assertEqual(route_boundary["decision"], "IN_SCOPE_NO_ROUTE")
        self.assertEqual(route_boundary["execution_policy"], "read_only_discovery")
        self.assertTrue(
            any("task conflicts with route boundary" in basis for basis in route_boundary["decision_basis"])
        )
        self.assertEqual(cli_result, 0)
        self.assertEqual(cli_report["decision"], "OUT_OF_SCOPE")
        self.assertEqual(cli_report["output_profile"], "compact")
        self.assertEqual(cli_report["execution_policy"], "read_only")
        self.assertEqual(cli_report["safe_edit_paths"], [])

    def test_failure_mode_needs_independent_grounded_evidence_to_match(self) -> None:
        blueprint = example_blueprint()
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["common_failure_modes"] = [
            "report cursor drift"
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "tests").mkdir()
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(agent_map), encoding="utf-8"
            )
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(blueprint), encoding="utf-8"
            )

            symptom_only = generate_agent_context_report(
                root, task="Fix report cursor drift."
            )
            blueprint["nodes"][1]["description"] = (
                "Builder owns report cursor behavior and drift correction."
            )
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(blueprint), encoding="utf-8"
            )
            corroborated = generate_agent_context_report(
                root, task="Fix report cursor drift."
            )

        self.assertNotEqual(symptom_only["decision"], "MATCH")
        self.assertEqual(symptom_only["matched_routes"], [])
        self.assertEqual(corroborated["decision"], "MATCH")
        self.assertEqual(corroborated["matched_routes"], ["change builder behavior"])

    def test_bounded_discovery_is_grounded_capped_and_non_match_only(self) -> None:
        blueprint = example_blueprint()
        blueprint["nodes"][0]["description"] = "Dispatches command options."
        blueprint["nodes"][0]["source_path"] = "src/cli.py"
        blueprint["nodes"][0]["evidence"] = [{"kind": "source", "path": "src/cli.py"}]
        agent_map = example_agent_map()
        agent_map["task_routes"][0]["domain_entities"] = [
            "queue lease owner",
            "QueueLease",
        ]
        agent_map["task_routes"][0]["failure_symptoms"] = [
            "lease ownership does not transfer",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "src" / "fixture" / "queueing").mkdir(parents=True)
            (root / "tests").mkdir()
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "src" / "cli.py").write_text("# command option dispatch\n", encoding="utf-8")
            (root / "src" / "fixture" / "queueing" / "component_001.py").write_text(
                "# lease holder\n", encoding="utf-8"
            )
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(blueprint), encoding="utf-8"
            )
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(agent_map), encoding="utf-8"
            )

            semantic = generate_agent_context_report(
                root, task="Fix command option dispatch."
            )
            semantic_verbose = generate_agent_context_report(
                root, task="Fix command option dispatch.", verbose=True
            )
            repository_path = generate_agent_context_report(
                root, task="Fix queue lease ownership."
            )
            unsupported = generate_agent_context_report(
                root, task="Add a native iOS application."
            )
            unknown = generate_agent_context_report(
                root, task="publish package to package registry"
            )
            ambiguous_map = example_agent_map()
            ambiguous_map["task_routes"][0]["match_terms"] = ["cursor repair"]
            ambiguous_route = json.loads(json.dumps(ambiguous_map["task_routes"][0]))
            ambiguous_route["task"] = "change validator behavior"
            ambiguous_route["intent"] = "Update validator logic."
            ambiguous_route["start_nodes"] = ["component:validator"]
            ambiguous_route["match_terms"] = ["cursor repair"]
            ambiguous_map["task_routes"].append(ambiguous_route)
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(ambiguous_map), encoding="utf-8"
            )
            ambiguous = generate_agent_context_report(
                root, task="Fix cursor repair."
            )

        discovery = semantic["discovery_context"]
        self.assertEqual(semantic["decision"], "IN_SCOPE_NO_ROUTE")
        self.assertEqual(semantic["safe_edit_paths"], [])
        self.assertIn(
            "component:cli",
            [candidate.get("id") for candidate in discovery["likely_areas"]],
        )
        self.assertIn("src/cli.py", [item["path"] for item in discovery["read_first"]])
        self.assertNotIn("evidence_paths", discovery["likely_areas"][0])
        self.assertIn("evidence_path", discovery["likely_areas"][0])
        self.assertIn(
            "evidence_paths",
            semantic_verbose["discovery_context"]["likely_areas"][0],
        )
        self.assertLessEqual(len(discovery["likely_areas"]), 3)
        self.assertLessEqual(len(discovery["likely_workflows"]), 2)
        self.assertLessEqual(len(discovery["read_first"]), 5)
        self.assertLessEqual(len(discovery["likely_tests"]), 3)
        self.assertEqual(repository_path["decision"], "IN_SCOPE_NO_ROUTE")
        self.assertEqual(repository_path["matched_routes"], [])
        self.assertEqual(repository_path["safe_edit_paths"], [])
        self.assertIn(
            "src/fixture/queueing",
            [candidate.get("path") for candidate in repository_path["discovery_context"]["likely_areas"]],
        )
        self.assertIn(
            "queue lease owner",
            [candidate.get("value") for candidate in repository_path["discovery_context"]["domain_entities"]],
        )
        self.assertIn(
            "lease ownership does not transfer",
            [candidate.get("value") for candidate in repository_path["discovery_context"]["route_signals"]],
        )
        self.assertFalse(
            any(
                "source_route" in candidate
                for field in ("domain_entities", "route_signals")
                for candidate in repository_path["discovery_context"][field]
            )
        )
        self.assertTrue(repository_path["discovery_context"]["search_commands"])
        self.assertNotIn("discovery_context", unsupported)
        self.assertNotIn("discovery_context", unknown)
        self.assertEqual(ambiguous["decision"], "UNCERTAIN")
        self.assertEqual(ambiguous["matched_routes"], [])
        self.assertNotIn("discovery_context", ambiguous)

    def test_malformed_stale_map_policy_is_a_validation_error(self) -> None:
        agent_map = example_agent_map()
        agent_map["stale_map_policy"] = {
            "rerun_when_changed": "src/**",
            "ignore_when_changed": [""],
        }

        errors, _, _ = validate_agent_map_obj(agent_map, blueprint=example_blueprint())

        self.assertIn(
            "stale_map_policy.rerun_when_changed must be a list of non-empty strings",
            errors,
        )
        self.assertIn(
            "stale_map_policy.ignore_when_changed must be a list of non-empty strings",
            errors,
        )

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
            verbose_text = generate_agent_context(
                root, task="change builder behavior", verbose=True
            )
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
            route_receipt = _generate_agent_route_receipt(
                root,
                task="change builder behavior",
            )
            html = render_html(graph, root / "atlas.html").read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["trusted_route_count"], 1)
        self.assertIn("## Trust", text)
        self.assertIn("Grounding status: `grounded`", text)
        self.assertNotIn("Agent-map routes: `validated` (1 trusted route(s))", text)
        self.assertIn(
            "Agent-map routes: `validated` (1 trusted route(s))", verbose_text
        )
        self.assertIn("Requested route match: `matched`", text)
        self.assertIn("## Recommended task routes", text)
        self.assertIn("### change builder behavior", text)
        self.assertIn("task terms match: `builder`", text)
        self.assertIn("`component:builder`", text)
        self.assertIn("`main_flow`", text)
        self.assertIn("`README.md`", text)
        self.assertLess(len(text), len(verbose_text))
        self.assertNotIn("## Generated docs", text)
        self.assertNotIn("- Route score:", text)
        self.assertNotIn("**Start nodes:**", text)
        self.assertIn("## Generated docs", verbose_text)
        self.assertIn("- Route score:", verbose_text)
        self.assertIn("**Start nodes:**", verbose_text)
        self.assertIn("Requested route match: `matched`", node_text)
        self.assertIn("focus node `component:builder` starts this route", node_text)
        self.assertIn("Requested route match: `not_found`", unmatched_text)
        self.assertIn("No matching trusted route for this request.", unmatched_text)
        self.assertNotIn("### change builder behavior", unmatched_text)
        self.assertIn("Requested route match: `not_requested`", catalog_text)
        self.assertIn("## Available trusted task routes", catalog_text)
        self.assertIn("### change builder behavior", catalog_text)
        self.assertNotIn("**Safe edit:**", catalog_text)
        self.assertNotIn("`src/bunya_jido/blueprint.py`", catalog_text)
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
        self.assertEqual(
            route["route_fingerprint"],
            route_receipt["route_fingerprint"],
        )
        self.assertEqual(route["id"], route_receipt["route_id"])
        self.assertEqual(
            route["route_fingerprint_algorithm"],
            "bunya-jido-route-fingerprint-v1",
        )
        self.assertEqual(graph["agent_map_quality"]["trusted_route_count"], 1)
        self.assertIn('"kind": "task_route"', html)
        self.assertIn("Task Route", html)
        self.assertIn("Related Trusted Routes", html)
        self.assertIn("Copy coding-agent context", html)

    def test_environment_can_disable_agent_context_without_map_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict("os.environ", {"BUNYA_JIDO_CONTEXT": "off"}):
                text = generate_agent_context(root, task="change builder behavior")
                report = generate_agent_context_report(
                    root,
                    task="change builder behavior",
                )
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    context_result = main(
                        [
                            "context",
                            "--root",
                            str(root),
                            "--task",
                            "change builder behavior",
                            "--json",
                        ]
                    )
            with patch.dict("os.environ", {"BUNYA_JIDO_DISABLE_CONTEXT": "1"}):
                refresh_stdout = io.StringIO()
                with redirect_stdout(refresh_stdout):
                    refresh_result = main(
                        [
                            "refresh-context",
                            "--root",
                            str(root),
                            "--changed-file",
                            "src/example.py",
                        ]
                    )

        cli_report = json.loads(stdout.getvalue())
        self.assertIn("Decision: `DISABLED`", text)
        self.assertIn("Bunya-Jido context: `disabled`", text)
        self.assertNotIn("### change builder behavior", text)
        self.assertEqual(report["decision"], "DISABLED")
        self.assertTrue(report["context_disabled"])
        self.assertEqual(report["execution_policy"], "read_only")
        self.assertEqual(report["codex_sandbox_mode"], "read-only")
        self.assertEqual(report["matched_routes"], [])
        self.assertEqual(report["safe_edit_paths"], [])
        self.assertNotIn("discovery_context", report)
        self.assertEqual(context_result, 0)
        self.assertEqual(cli_report["decision"], "DISABLED")
        self.assertEqual(cli_report["matched_routes"], [])
        self.assertEqual(cli_report["safe_edit_paths"], [])
        self.assertEqual(refresh_result, 0)
        self.assertIn("Decision: `DISABLED`", refresh_stdout.getvalue())
        self.assertIn("**Changed files:** src/example.py", refresh_stdout.getvalue())

    def test_validated_optional_studio_route_context_is_projected_but_missing_references_block(self) -> None:
        blueprint = example_blueprint()
        blueprint["atlas"] = {
            "projections": [
                {
                    "id": "projection:agent",
                    "label": "Agent Reading",
                    "description": "A bounded task orientation.",
                    "question_answered": "Where should an agent begin?",
                }
            ],
            "scenarios": [
                {
                    "id": "scenario:change",
                    "label": "Change Safely",
                    "description": "Follow validated guidance.",
                    "kind": "behavioral",
                    "basis": "documented_workflow",
                    "playback_mode": "animated_token",
                }
            ],
        }
        agent_map = example_agent_map()
        route = agent_map["task_routes"][0]
        route["projection_context"] = "projection:agent"
        route["scenario_context"] = ["scenario:change"]
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
            context = generate_agent_context(root, task="change builder behavior")
            graph, _ = graph_with_optional_blueprint(root)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["trusted_route_count"], 1)
        self.assertIn("**Start-node responsibility:**", context)
        self.assertIn("**Projection context:**", context)
        self.assertIn("`projection:agent` - Agent Reading", context)
        self.assertIn("**Scenario context:**", context)
        self.assertIn("`scenario:change` - Change Safely", context)
        projected = next(path for path in graph["path_presets"] if path["kind"] == "task_route")
        self.assertEqual(projected["start_nodes"], ["component:builder"])
        self.assertEqual(projected["projection_context"]["id"], "projection:agent")
        self.assertEqual(projected["scenario_context"][0]["id"], "scenario:change")

        blocked_map = json.loads(json.dumps(agent_map))
        blocked_map["task_routes"][0]["projection_context"] = "projection:missing"
        _, _, blocked_metrics = validate_agent_map_obj(blocked_map, blueprint=blueprint)
        self.assertTrue(
            any("references projection not in blueprint" in blocker for blocker in blocked_metrics["publish_blockers"])
        )

        malformed_map = json.loads(json.dumps(agent_map))
        malformed_map["task_routes"][0]["scenario_context"] = "scenario:change"
        malformed_errors, _, _ = validate_agent_map_obj(malformed_map, blueprint=blueprint)
        _, _, malformed_metrics = validate_agent_map_obj(malformed_map, blueprint=blueprint)
        self.assertIn(
            "task_routes[0].scenario_context must be a list of non-empty strings",
            malformed_errors,
        )
        self.assertEqual(malformed_metrics["trusted_route_count"], 0)

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

    def test_stale_map_policy_requires_review_artifact_for_triggering_changes(self) -> None:
        agent_map = example_agent_map()
        agent_map["stale_map_policy"] = {
            "rerun_when_changed": ["src/**", "docs/**"],
            "ignore_when_changed": ["docs/generated/**"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(agent_map), encoding="utf-8"
            )

            stale = evaluate_map_freshness(root, ["src/builder.py"])
            reviewed = evaluate_map_freshness(
                root, ["src/builder.py", ".bunya-jido/bunya-jido.agent-map.json"]
            )
            acknowledged = evaluate_map_freshness(
                root, ["src/builder.py", ".bunya-jido/MAP_REVIEW.md"]
            )
            ignored = evaluate_map_freshness(root, ["docs/generated/report.md"])

        self.assertEqual(stale["status"], "stale")
        self.assertEqual(stale["triggering_files"], ["src/builder.py"])
        self.assertEqual(reviewed["status"], "review_recorded")
        self.assertEqual(
            reviewed["review_artifacts"], [".bunya-jido/bunya-jido.agent-map.json"]
        )
        self.assertEqual(acknowledged["status"], "review_recorded")
        self.assertEqual(acknowledged["review_artifacts"], [".bunya-jido/MAP_REVIEW.md"])
        self.assertEqual(ignored["status"], "current")
        self.assertEqual(ignored["ignored_files"], ["docs/generated/report.md"])

    def test_check_stale_strict_mode_blocks_unreviewed_changes(self) -> None:
        agent_map = example_agent_map()
        agent_map["stale_map_policy"] = {
            "rerun_when_changed": ["src/**"],
            "ignore_when_changed": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(agent_map), encoding="utf-8"
            )
            stale_stdout = io.StringIO()
            reviewed_stdout = io.StringIO()
            with redirect_stdout(stale_stdout):
                stale_result = main(
                    [
                        "check-stale",
                        "--root",
                        str(root),
                        "--changed-file",
                        "src/builder.py",
                        "--require-reviewed",
                    ]
                )
            with redirect_stdout(reviewed_stdout):
                reviewed_result = main(
                    [
                        "check-stale",
                        "--root",
                        str(root),
                        "--changed-file",
                        "src/builder.py",
                        "--changed-file",
                        ".bunya-jido/bunya-jido.agent-map.json",
                        "--require-reviewed",
                    ]
                )

        self.assertEqual(stale_result, 2)
        self.assertIn("Map freshness status: stale", stale_stdout.getvalue())
        self.assertEqual(reviewed_result, 0)
        self.assertIn("Map freshness status: review_recorded", reviewed_stdout.getvalue())

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

    def test_agent_utility_evaluation_checks_context_contract_and_strict_cli(self) -> None:
        evaluation = {
            "schema_version": "bunya-jido-agent-evaluation-v1",
            "project": {"name": "fixture", "summary": "Agent utility cases."},
            "cases": [
                {
                    "id": "builder-reading",
                    "dimension": "first_read_accuracy",
                    "query": {"task": "change builder behavior"},
                    "expect": {
                        "route_status": "matched",
                        "decision": "MATCH",
                        "execution_policy": "workspace_write",
                        "routes": ["change builder behavior"],
                        "must_read": ["README.md"],
                        "tests": ["tests/test_smoke.py"],
                    },
                },
                {
                    "id": "honest-gap",
                    "dimension": "honest_no_match",
                    "query": {"task": "rotate database credentials"},
                    "expect": {
                        "route_status": "not_found",
                        "decision": "UNCERTAIN",
                        "execution_policy": "read_only",
                        "routes": [],
                        "forbid_routes": ["change builder behavior"],
                    },
                },
                {
                    "id": "bounded-recovery",
                    "dimension": "normal_bugfix_recovery",
                    "query": {"task": "Fix CLI command behavior."},
                    "expect": {
                        "route_status": "not_found",
                        "decision": "IN_SCOPE_NO_ROUTE",
                        "execution_policy": "read_only_discovery",
                        "routes": [],
                        "discovery_nodes": ["component:cli"],
                        "read_first": ["README.md"],
                    },
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            (root / "tests").mkdir()
            (root / "src" / "bunya_jido").mkdir(parents=True)
            outdir.mkdir()
            (root / "README.md").write_text("fixture", encoding="utf-8")
            (root / "tests" / "test_smoke.py").write_text("pass\n", encoding="utf-8")
            (root / "src" / "bunya_jido" / "blueprint.py").write_text("# fixture\n", encoding="utf-8")
            (outdir / "bunya-jido.blueprint.json").write_text(
                json.dumps(example_blueprint()), encoding="utf-8"
            )
            (outdir / "bunya-jido.agent-map.json").write_text(
                json.dumps(example_agent_map()), encoding="utf-8"
            )
            suite_path = outdir / "bunya-jido.agent-evaluation.json"
            suite_path.write_text(json.dumps(evaluation), encoding="utf-8")

            passed = evaluate_agent_utility(root)
            evaluation["cases"][0]["expect"]["must_read"] = ["src/missing.py"]
            suite_path.write_text(json.dumps(evaluation), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                strict_result = main(
                    [
                        "evaluate-agent-utility",
                        "--root",
                        str(root),
                        "--require-pass",
                        "--json",
                    ]
                )
            failed = json.loads(stdout.getvalue())

        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["passed_case_count"], 3)
        self.assertEqual(passed["cases"][0]["actual_decision"], "MATCH")
        self.assertEqual(passed["cases"][0]["actual_execution_policy"], "workspace_write")
        self.assertEqual(passed["cases"][1]["actual_decision"], "UNCERTAIN")
        self.assertEqual(passed["cases"][1]["actual_execution_policy"], "read_only")
        self.assertEqual(passed["safety_metrics"]["expected_decision_accuracy"], 1.0)
        self.assertEqual(passed["safety_metrics"]["false_route_rate"], 0.0)
        self.assertEqual(passed["safety_metrics"]["safe_edit_leak_rate"], 0.0)
        self.assertEqual(passed["safety_metrics"]["execution_policy_accuracy"], 1.0)
        self.assertEqual(passed["decision_confusion_matrix"]["MATCH"]["MATCH"], 1)
        self.assertEqual(passed["decision_confusion_matrix"]["UNCERTAIN"]["UNCERTAIN"], 1)
        self.assertEqual(passed["recovery_metrics"]["normal_bugfix_case_count"], 1)
        self.assertEqual(passed["recovery_metrics"]["trusted_route_recall"], 0.0)
        self.assertEqual(passed["recovery_metrics"]["bounded_discovery_coverage"], 1.0)
        self.assertEqual(passed["recovery_metrics"]["actionable_guidance_coverage"], 1.0)
        self.assertEqual(
            passed["recovery_metrics"]["normal_bugfix_hard_rejection_rate"], 0.0
        )
        self.assertGreater(
            passed["context_efficiency_metrics"]["estimated_token_saving_rate"],
            0,
        )
        self.assertEqual(
            passed["context_efficiency_metrics"]["passing_context_case_count"],
            3,
        )
        self.assertGreater(
            passed["cases"][0]["context_output"]["verbose_reference"][
                "estimated_tokens"
            ],
            passed["cases"][0]["context_output"]["compact"]["estimated_tokens"],
        )
        self.assertEqual(strict_result, 2)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("must_read missing from context", failed["cases"][0]["failures"][0])

    def test_agent_utility_evaluation_rejects_unsupported_dimension(self) -> None:
        errors = validate_agent_evaluation_obj(
            {
                "schema_version": "bunya-jido-agent-evaluation-v1",
                "project": {"name": "fixture", "summary": "Agent utility cases."},
                "cases": [
                    {
                        "id": "unsupported",
                        "dimension": "agent_magic",
                        "query": {"task": "change builder behavior"},
                        "expect": {"route_status": "matched", "routes": ["change builder behavior"]},
                    }
                ],
            }
        )

        self.assertIn("cases[0].dimension is not supported: agent_magic", errors)
        invalid_decision = {
            "schema_version": "bunya-jido-agent-evaluation-v1",
            "project": {"name": "fixture", "summary": "Agent utility cases."},
            "cases": [
                {
                    "id": "invalid-decision",
                    "dimension": "honest_no_match",
                    "query": {"task": "rotate database credentials"},
                    "expect": {
                        "route_status": "not_found",
                        "decision": "MAYBE",
                        "routes": [],
                    },
                }
            ],
        }
        self.assertIn(
            "cases[0].expect.decision must be MATCH, IN_SCOPE_NO_ROUTE, OUT_OF_SCOPE, UNCERTAIN, or DISABLED",
            validate_agent_evaluation_obj(invalid_decision),
        )
        invalid_non_match_contract = {
            "schema_version": "bunya-jido-agent-evaluation-v1",
            "project": {"name": "fixture", "summary": "Agent utility cases."},
            "cases": [
                {
                    "id": "invalid-non-match-contract",
                    "dimension": "honest_no_match",
                    "query": {"task": "rotate database credentials"},
                    "expect": {
                        "route_status": "not_found",
                        "decision": "OUT_OF_SCOPE",
                        "execution_policy": "workspace_write",
                        "routes": ["change builder behavior"],
                        "safe_edit": ["src/bunya_jido/blueprint.py"],
                    },
                }
            ],
        }
        invalid_non_match_errors = validate_agent_evaluation_obj(invalid_non_match_contract)
        self.assertIn(
            "cases[0].expect.routes must be empty for non-MATCH decision",
            invalid_non_match_errors,
        )
        self.assertIn(
            "cases[0].expect.safe_edit must be empty for non-MATCH decision",
            invalid_non_match_errors,
        )
        self.assertIn(
            "cases[0].expect.execution_policy must be read_only for OUT_OF_SCOPE",
            invalid_non_match_errors,
        )
        self.assertEqual(
            validate_agent_evaluation_obj([]),
            ["evaluation suite must be an object"],
        )

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
        self.assertIn("read_only_discovery", text)
        self.assertIn("workspace_write", text)
        self.assertIn("no semantic blueprint or agent map", text)
        self.assertIn("Must read", text)
        self.assertIn("Tests", text)
        self.assertIn("refresh-context --root . --changed-file <path>", text)
        self.assertIn("check-stale --root . --git-diff --require-reviewed", text)
        self.assertIn(".bunya-jido/MAP_REVIEW.md", text)
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
        self.assertIn("check-stale --root . --git-diff --require-reviewed", cursor_text)
        self.assertIn(".bunya-jido/MAP_REVIEW.md", cursor_text)
        self.assertNotIn(b"\r\n", cursor_bytes)

    def test_deactivation_removes_only_managed_blocks_and_preserves_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agents_path = root / "AGENTS.md"
            agents_path.write_text("# Existing Rules\n\nKeep this instruction.\n", encoding="utf-8")
            activate_agent_guides(root, agent="all")
            cursor_path = root / ".cursor" / "rules" / "bunya-jido.mdc"

            dry_run = deactivate_agent_guides(root, agent="codex", dry_run=True)
            dry_run_text = agents_path.read_text(encoding="utf-8")
            codex = deactivate_agent_guides(root, agent="codex")
            codex_text = agents_path.read_text(encoding="utf-8")
            remaining = deactivate_agent_guides(root, agent="all")
            cursor_exists_after_deactivation = cursor_path.exists()
            missing = deactivate_agent_guides(root, agent="all")

        self.assertEqual(dry_run["codex"]["status"], "would_remove")
        self.assertIn(AGENT_ACTIVATION_START, dry_run_text)
        self.assertEqual(codex["codex"]["status"], "removed")
        self.assertIn("Keep this instruction.", codex_text)
        self.assertNotIn(AGENT_ACTIVATION_START, codex_text)
        self.assertNotIn(AGENT_ACTIVATION_END, codex_text)
        self.assertEqual(remaining["cursor"]["status"], "deleted")
        self.assertFalse(cursor_exists_after_deactivation)
        self.assertEqual(missing["cursor"]["status"], "not_found")
        self.assertEqual(missing["codex"]["status"], "unchanged")

    def test_deactivation_cli_dry_run_lists_native_targets_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            activate_agent_guides(root, agent="all")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "install-agent-guides",
                        "--root",
                        str(root),
                        "--agent",
                        "all",
                        "--deactivate",
                        "--dry-run",
                    ]
                )

            output = stdout.getvalue()
            agents_exists = (root / "AGENTS.md").exists()
            claude_exists = (root / "CLAUDE.md").exists()
            cursor_exists = (root / ".cursor" / "rules" / "bunya-jido.mdc").exists()
            cline_exists = (root / ".clinerules" / "bunya-jido.md").exists()

        self.assertEqual(result, 0)
        self.assertIn("codex: would_delete", output)
        self.assertIn("claude: would_delete", output)
        self.assertIn("cursor: would_delete", output)
        self.assertIn("cline: would_delete", output)
        self.assertTrue(agents_exists)
        self.assertTrue(claude_exists)
        self.assertTrue(cursor_exists)
        self.assertTrue(cline_exists)

    def test_dry_run_without_activation_is_rejected(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["install-agent-guides", "--dry-run"])

        self.assertEqual(result, 2)
        self.assertIn("--dry-run requires --activate or --deactivate", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
