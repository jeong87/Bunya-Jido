from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bunya_jido.blueprint import validate_blueprint_obj
from bunya_jido.cli import main
from bunya_jido.quality import evaluate_atlas_quality_obj
from tests.test_blueprint_v2 import valid_v2_blueprint


def quality_report(blueprint: dict) -> dict:
    errors, _, metrics = validate_blueprint_obj(blueprint)
    return evaluate_atlas_quality_obj(
        blueprint,
        validation_errors=errors,
        validation_metrics=metrics,
    )


class ProjectionQualityTests(unittest.TestCase):
    def test_quality_warns_about_weak_core_inspector_without_blocking_valid_atlas(self) -> None:
        report = quality_report(valid_v2_blueprint())

        self.assertEqual(report["status"], "passed")
        self.assertTrue(
            any("core node component:cli has no inspector_summary" in item for item in report["deterministic_warnings"])
        )
        self.assertTrue(
            any("clearest honest explanation" in item for item in report["review_required_warnings"])
        )
        self.assertIn("do not prove", report["limitation"])

    def test_structural_tour_passes_but_requests_human_narration_review(self) -> None:
        blueprint = valid_v2_blueprint()
        scenario = blueprint["atlas"]["scenarios"][0]
        blueprint["atlas"]["scenario_policy"] = "optional"
        scenario["kind"] = "structural_tour"
        scenario["basis"] = "illustrative_tour"
        scenario["playback_mode"] = "stepped_highlight"
        scenario["derived_from_workflow_ids"] = []

        report = quality_report(blueprint)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(
            any("structural tour does not imply runtime order" in item for item in report["review_required_warnings"])
        )

    def test_required_scenario_gap_blocks_quality_gate(self) -> None:
        blueprint = valid_v2_blueprint()
        blueprint["atlas"]["scenarios"] = []

        report = quality_report(blueprint)

        self.assertEqual(report["status"], "blocked")
        self.assertIn(
            "v2 scenario_policy=required requires at least one scenario",
            report["deterministic_blockers"],
        )

    def test_dense_overview_and_relation_family_burden_are_warnings(self) -> None:
        blueprint = valid_v2_blueprint()
        evidence = [{"kind": "source", "path": "README.md"}]
        projection = blueprint["atlas"]["projections"][0]
        for index in range(66):
            node_id = f"component:dense-{index}"
            blueprint["nodes"].append(
                {
                    "id": node_id,
                    "label": f"Dense Element {index}",
                    "type": "component",
                    "family": "transformer",
                    "plane": "control",
                    "importance": "support",
                    "overview_visibility": "visible",
                    "activation": "always",
                    "description": "A supporting component included to exercise overview density.",
                    "evidence": evidence,
                }
            )
            projection["node_ids"].append(node_id)
        for index in range(9):
            family_id = f"extra-{index}"
            blueprint["atlas"]["vocabularies"]["relation_families"].append(
                {
                    "id": family_id,
                    "label": f"Extra {index}",
                    "description": "Additional visible family.",
                    "line_style": "solid",
                }
            )
            blueprint["edges"].append(
                {
                    "id": f"edge:extra-{index}",
                    "source": "component:cli",
                    "target": f"component:dense-{index}",
                    "relation": f"extra_{index}",
                    "relation_family": family_id,
                    "workflow_role": "supporting",
                    "overview_visibility": "visible",
                    "activation": "always",
                    "confidence": "llm_grounded",
                    "evidence": evidence,
                }
            )
            projection["relation_family_ids"].append(family_id)

        report = quality_report(blueprint)

        self.assertEqual(report["status"], "passed")
        self.assertTrue(
            any("visible nodes" in item for item in report["deterministic_warnings"])
        )
        self.assertTrue(
            any("visible relation families" in item for item in report["deterministic_warnings"])
        )

    def test_quality_cli_requires_v2_pass_and_diagnose_includes_summary(self) -> None:
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
                    ["evaluate-atlas-quality", "--root", str(root), "--require-pass", "--json"]
                )
            report = json.loads(stdout.getvalue())
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                diagnostic_result = main(
                    ["diagnose", "--root", str(root), "--require-grounded", "--json"]
                )
            diagnostic = json.loads(stdout.getvalue())

        self.assertEqual(result, 0)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(diagnostic_result, 0)
        self.assertEqual(diagnostic["atlas_quality_status"], "passed")
        self.assertGreaterEqual(
            diagnostic["atlas_quality"]["deterministic_warning_count"], 1
        )


if __name__ == "__main__":
    unittest.main()
