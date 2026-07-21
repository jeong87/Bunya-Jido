from __future__ import annotations

import fnmatch
import io
import json
import struct
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import (
    evaluate_agent_utility,
    evaluate_map_freshness,
    generate_agent_context,
    generate_agent_context_report,
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
PAGES_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "pages.yml"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_semantic_contract(graph: dict) -> dict:
    return {
        "schema_version": graph["schema_version"],
        "artifact_mode": graph["artifact_mode"],
        "grounding": graph["grounding"],
        "stats": graph["stats"],
        "primary_projection": graph["primary_projection"],
        "scenario_policy": graph["atlas"]["scenario_policy"],
        "scenario_count": graph["scenario_count"],
        "atlas": graph["atlas"],
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
    def test_pages_deploys_reviewed_docs_changes_from_main(self) -> None:
        workflow = PAGES_WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("push:", workflow)
        self.assertIn("- main", workflow)
        self.assertIn('- "docs/**"', workflow)
        self.assertIn("workflow_dispatch:", workflow)

    def test_committed_self_map_and_routes_are_grounded(self) -> None:
        blueprint = load_json(BLUEPRINT_PATH)
        agent_map = load_json(AGENT_MAP_PATH)

        errors, warnings, metrics = validate_blueprint_obj(blueprint, root=ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(blueprint["schema_version"], "bunya-jido-blueprint-v2")
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["node_count"], 15)
        self.assertEqual(metrics["edge_count"], 32)
        self.assertEqual(metrics["primary_projection"], "projection:trusted_publication")
        self.assertEqual(metrics["scenario_count"], 2)
        self.assertTrue(metrics["decision_record_present"])
        self.assertEqual(
            blueprint["atlas"]["decision_record"]["selected_projection_id"],
            "projection:trusted_publication",
        )
        self.assertEqual(metrics["grounded_core_node_ratio"], 1.0)
        self.assertEqual(metrics["grounded_critical_edge_ratio"], 1.0)

        errors, warnings, metrics = validate_agent_map_obj(
            agent_map, root=ROOT, blueprint=blueprint
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(metrics["trusted_route_count"], 8)

    def test_agent_map_safe_edit_paths_resolve_to_git_tracked_content(self) -> None:
        agent_map = load_json(AGENT_MAP_PATH)
        tracked = {
            item
            for item in subprocess.run(
                ["git", "ls-files", "-z"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout.decode("utf-8").split("\0")
            if item
        }

        for route in agent_map["task_routes"]:
            for safe_edit in route.get("safe_edit", []):
                normalized = safe_edit.replace("\\", "/").removeprefix("./")
                if any(character in normalized for character in "*?["):
                    resolved = any(
                        fnmatch.fnmatchcase(path, normalized) for path in tracked
                    )
                elif normalized.endswith("/"):
                    resolved = any(path.startswith(normalized) for path in tracked)
                else:
                    resolved = normalized in tracked
                self.assertTrue(
                    resolved,
                    f"safe-edit path is not Git-tracked: {safe_edit} "
                    f"in route {route['task']}",
                )

    def test_gallery_build_projects_expected_semantic_paths(self) -> None:
        graph, _ = graph_with_optional_blueprint(ROOT, max_files=0)

        self.assertEqual(graph["artifact_mode"], "semantic_blueprint")
        self.assertEqual(graph["schema_version"], "bunya-jido-v2")
        self.assertEqual(graph["grounding"]["status"], "grounded")
        self.assertTrue(graph["grounding"]["publishable"])
        self.assertEqual(graph["stats"]["nodes"], 15)
        self.assertEqual(graph["stats"]["edges"], 32)
        self.assertEqual(graph["primary_projection"], "projection:trusted_publication")
        self.assertEqual(graph["scenario_count"], 2)
        self.assertEqual(
            graph["atlas"]["decision_record"]["selected_projection_id"],
            "projection:trusted_publication",
        )
        self.assertIn(
            {
                "id": "semantic",
                "label": "Semantic Contract",
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
                "task_route_change-scanner-hint-provenance",
                "task_route_change-grounding-policy",
                "task_route_change-atlas-quality-evaluation",
                "task_route_change-benchmark-evidence-reporting",
                "task_route_change-multi-domain-rubric-coverage",
                "task_route_change-guarded-Codex-run-orchestration",
                "task_route_change-task-route-projection",
                "task_route_change-viewer-trust-presentation",
            },
        )

    def test_trusted_context_uses_committed_route(self) -> None:
        context = generate_agent_context(ROOT, task="change task route projection")
        verbose_context = generate_agent_context(
            ROOT, task="change task route projection", verbose=True
        )

        self.assertIn("- Grounding status: `grounded`", context)
        self.assertNotIn("- Agent-map routes: `validated` (8 trusted route(s))", context)
        self.assertIn(
            "- Agent-map routes: `validated` (8 trusted route(s))", verbose_context
        )
        self.assertIn("- Requested route match: `matched`", context)
        self.assertIn("- Execution policy: `workspace_write`", context)
        self.assertIn("- Codex sandbox mode: `workspace-write`", context)
        self.assertIn("### change task route projection", context)
        self.assertIn("- `task_route_publication`", context)
        self.assertIn("**Start-node responsibility:**", context)
        self.assertIn("`projection:agent_navigation` - Bounded Agent Navigation", context)
        self.assertIn("`scenario:agent_context` - Request Bounded Agent Context", context)

    def test_agent_context_scenario_keeps_authored_route_and_step_evidence(self) -> None:
        blueprint = load_json(BLUEPRINT_PATH)
        scenario = next(
            item
            for item in blueprint["atlas"]["scenarios"]
            if item["id"] == "scenario:agent_context"
        )

        self.assertEqual(scenario["label"], "Request Bounded Agent Context")
        self.assertEqual(
            [step["node_id"] for step in scenario["steps"]],
            [
                "entry:cli",
                "semantic:context",
                "semantic:validation",
                "semantic:agent_map",
            ],
        )
        self.assertEqual(
            [step.get("edge_id") for step in scenario["steps"]],
            [
                "edge:cli_context",
                "edge:context_validation",
                "edge:validation_agent_map",
                None,
            ],
        )
        self.assertTrue(
            all(step.get("title") and step.get("narration") for step in scenario["steps"])
        )
        self.assertTrue(all(step.get("evidence") for step in scenario["steps"]))

    def test_scanner_provenance_has_a_bounded_quality_route(self) -> None:
        context = generate_agent_context(ROOT, task="change scanner hint provenance")

        self.assertIn("### change scanner hint provenance", context)
        self.assertIn("- `src/bunya_jido/scanner.py`", context)
        self.assertIn(
            "Provider hints from generated prompts, schemas, or viewer templates",
            context,
        )
        self.assertIn("`projection:quality_contract` - Quality Contract", context)

    def test_benchmark_reporting_has_a_safe_and_resolved_route(self) -> None:
        token_context = generate_agent_context(
            ROOT, task="change benchmark token reporting"
        )
        time_context = generate_agent_context(
            ROOT, task="change benchmark time reporting"
        )

        for context in (token_context, time_context):
            self.assertIn("### change benchmark evidence reporting", context)
            self.assertIn("- `src/bunya_jido/benchmark.py`", context)
            self.assertIn("- `tests/test_benchmark_audit.py`", context)
            self.assertNotIn("### change multi-domain rubric coverage", context)
        self.assertIn("paired safe-and-resolved runs", token_context)
        self.assertIn("explicitly paired safe-and-resolved runs", time_context)
        self.assertIn("must not tune route vocabulary", time_context)

    def test_guarded_codex_run_has_an_independent_non_escalating_route(self) -> None:
        report = generate_agent_context_report(
            ROOT, task="Implement guarded Codex run orchestration and boundary reporting."
        )

        self.assertEqual(report["decision"], "MATCH")
        self.assertEqual(report["execution_policy"], "workspace_write")
        self.assertEqual(
            report["matched_routes"],
            ["change guarded Codex run orchestration"],
        )
        self.assertIn("src/bunya_jido/codex_run.py", report["safe_edit_paths"])
        self.assertIn("tests/test_codex_run.py", report["safe_edit_paths"])
        self.assertNotIn(
            "change benchmark evidence reporting",
            report["matched_routes"],
        )

    def test_unmatched_context_does_not_invent_self_map_route(self) -> None:
        context = generate_agent_context(ROOT, task="publish package to package registry")

        self.assertIn("- Requested route match: `not_found`", context)
        self.assertIn("No matching trusted route for this request.", context)
        self.assertNotIn("### change grounding policy", context)
        self.assertNotIn("### change scanner hint provenance", context)
        self.assertNotIn("### change atlas quality evaluation", context)
        self.assertNotIn("### change multi-domain rubric coverage", context)
        self.assertNotIn("### change task route projection", context)
        self.assertNotIn("### change viewer trust presentation", context)

    def test_reviewed_out_of_scope_context_is_read_only_and_route_free(self) -> None:
        report = generate_agent_context_report(
            ROOT, task="Add a native iOS app with App Store signing."
        )

        self.assertEqual(report["decision"], "OUT_OF_SCOPE")
        self.assertEqual(report["route_status"], "not_found")
        self.assertEqual(report["edit_policy"], "read_only")
        self.assertEqual(report["execution_policy"], "read_only")
        self.assertEqual(report["codex_sandbox_mode"], "read-only")
        self.assertEqual(report["matched_routes"], [])
        self.assertEqual(report["safe_edit_paths"], [])
        self.assertIn("native iOS application", report["scope_evidence"]["unsupported_matches"])

    def test_in_scope_no_route_is_read_only_discovery_and_route_free(self) -> None:
        report = generate_agent_context_report(
            ROOT, task="Change context decision calibration."
        )

        self.assertEqual(report["decision"], "IN_SCOPE_NO_ROUTE")
        self.assertEqual(report["route_status"], "not_found")
        self.assertEqual(report["execution_policy"], "read_only_discovery")
        self.assertEqual(report["codex_sandbox_mode"], "read-only")
        self.assertEqual(report["matched_routes"], [])
        self.assertEqual(report["safe_edit_paths"], [])
        self.assertEqual(report["discovery_context"]["mode"], "bounded_read_only")
        self.assertIn(
            "src/bunya_jido/blueprint.py",
            [item["path"] for item in report["discovery_context"]["read_first"]],
        )
        self.assertIn("Do not modify files during initial discovery", report["agent_instruction"])

    def test_refresh_context_routes_only_from_changed_self_map_evidence(self) -> None:
        context = generate_agent_context(
            ROOT, changed_files=["src/bunya_jido/blueprint.py"]
        )
        unrelated = generate_agent_context(ROOT, changed_files=["LICENSE"])

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
        self.assertEqual(report["case_count"], 20)
        self.assertEqual(report["dimensions"]["honest_no_match"]["passed"], 7)
        self.assertEqual(report["dimensions"]["normal_bugfix_recovery"]["passed"], 2)
        self.assertEqual(report["safety_metrics"]["expected_decision_accuracy"], 1.0)
        self.assertEqual(report["safety_metrics"]["false_route_rate"], 0.0)
        self.assertEqual(report["safety_metrics"]["safe_edit_leak_rate"], 0.0)
        self.assertEqual(report["safety_metrics"]["execution_policy_accuracy"], 1.0)
        self.assertEqual(report["recovery_metrics"]["normal_bugfix_case_count"], 2)
        self.assertEqual(report["recovery_metrics"]["trusted_route_recall"], 0.5)
        self.assertEqual(report["recovery_metrics"]["bounded_discovery_coverage"], 0.5)
        self.assertEqual(report["recovery_metrics"]["actionable_guidance_coverage"], 1.0)
        self.assertEqual(
            report["recovery_metrics"]["normal_bugfix_hard_rejection_rate"], 0.0
        )
        self.assertEqual(
            set(report["dimensions"]),
            {
                "first_read_accuracy",
                "test_recall",
                "boundary_discipline",
                "honest_no_match",
                "change_aware_refresh",
                "normal_bugfix_recovery",
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
            "Related Trusted Routes",
            "Copy coding-agent context",
            "Selected Relationship",
            "Studio Projections",
            "Scenario",
            "Map Controls",
            "Repository Outline",
            "Start guided tour",
            'id="toolbarTrust"',
            'id="workflowBar"',
            'id="repositorySummary"',
            "nodeRoleStyles",
            "drawNodeShape",
            "relationFamilyVisuals",
            "semanticOverviewHtml",
            "pathStepIndex",
            "e.directed!==false",
            "--layer-scenario:18",
            "z-index:var(--layer-scenario)",
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
            self.assertIn(
                "https://jeong87.github.io/Bunya-Jido/assets/self-map-grounded.png",
                text,
            )
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
        self.assertEqual(report["atlas_quality_status"], "passed")
        self.assertTrue(report["atlas_quality"]["review_required"])
        self.assertEqual(report["agent_routes"], {"status": "validated", "trusted": 8, "total": 8})


if __name__ == "__main__":
    unittest.main()
