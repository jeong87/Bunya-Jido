from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from bunya_jido.blueprint import graph_with_optional_blueprint, validate_blueprint_obj
from bunya_jido.quality import evaluate_atlas_quality_obj


ROOT = Path(__file__).resolve().parents[1]
GALLERY_CASES = {
    "coverage-fixture": {
        "root": ROOT / "examples" / "coverage",
        "blueprint": ROOT / "examples" / "coverage" / "studio.blueprint.json",
        "html": ROOT / "docs" / "gallery" / "coverage-fixture.html",
        "screenshot": ROOT / "docs" / "gallery" / "coverage-fixture.png",
        "projection": "projection:evidence_surfaces",
        "policy": "none_with_reason",
        "scenario_kind": None,
        "deterministic_warning_count": 3,
        "forbid_api_provider": True,
    },
    "sdk-client": {
        "root": ROOT / "examples" / "gallery" / "sdk_client",
        "blueprint": ROOT / "examples" / "gallery" / "sdk_client" / ".bunya-jido" / "bunya-jido.blueprint.json",
        "html": ROOT / "docs" / "gallery" / "sdk-client.html",
        "screenshot": ROOT / "docs" / "gallery" / "sdk-client.png",
        "projection": "projection:client_contract",
        "policy": "optional",
        "scenario_kind": "structural_tour",
        "deterministic_warning_count": 0,
    },
    "web-state-app": {
        "root": ROOT / "examples" / "gallery" / "web_state_app",
        "blueprint": ROOT / "examples" / "gallery" / "web_state_app" / ".bunya-jido" / "bunya-jido.blueprint.json",
        "html": ROOT / "docs" / "gallery" / "web-state-app.html",
        "screenshot": ROOT / "docs" / "gallery" / "web-state-app.png",
        "projection": "projection:interaction_loop",
        "policy": "required",
        "scenario_kind": "behavioral",
        "deterministic_warning_count": 0,
    },
    "compiler-parser": {
        "root": ROOT / "examples" / "gallery" / "compiler_parser",
        "blueprint": ROOT / "examples" / "gallery" / "compiler_parser" / ".bunya-jido" / "bunya-jido.blueprint.json",
        "html": ROOT / "docs" / "gallery" / "compiler-parser.html",
        "screenshot": ROOT / "docs" / "gallery" / "compiler-parser.png",
        "projection": "projection:transformation_stages",
        "policy": "required",
        "scenario_kind": "behavioral",
        "deterministic_warning_count": 0,
    },
    "utility-library": {
        "root": ROOT / "examples" / "gallery" / "utility_library",
        "blueprint": ROOT / "examples" / "gallery" / "utility_library" / ".bunya-jido" / "bunya-jido.blueprint.json",
        "html": ROOT / "docs" / "gallery" / "utility-library.html",
        "screenshot": ROOT / "docs" / "gallery" / "utility-library.png",
        "projection": "projection:api_reading_route",
        "policy": "none_with_reason",
        "scenario_kind": None,
        "deterministic_warning_count": 0,
    },
}


def published_graph(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    marker = '<script id="graph-data" type="application/json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    return json.loads(html[start:end])


def stable_gallery_contract(graph: dict) -> dict:
    return {
        "schema_version": graph["schema_version"],
        "artifact_mode": graph["artifact_mode"],
        "grounding": graph["grounding"],
        "primary_projection": graph["primary_projection"],
        "scenario_count": graph["scenario_count"],
        "atlas": graph["atlas"],
        "nodes": [
            (node["id"], node["label"], node["plane"], node["type"])
            for node in graph["nodes"]
        ],
        "edges": [
            (edge["source"], edge["target"], edge["relation"], edge["confidence"])
            for edge in graph["edges"]
        ],
    }


class CuratedStudioGalleryTests(unittest.TestCase):
    def test_curated_gallery_publishes_distinct_grounded_readings(self) -> None:
        projections: set[str] = set()
        policies: set[str] = set()

        for name, case in GALLERY_CASES.items():
            blueprint = json.loads(case["blueprint"].read_text(encoding="utf-8"))
            errors, warnings, metrics = validate_blueprint_obj(
                blueprint, root=case["root"]
            )
            quality = evaluate_atlas_quality_obj(
                blueprint,
                root=case["root"],
                validation_errors=errors,
                validation_metrics=metrics,
            )
            graph, _ = graph_with_optional_blueprint(
                case["root"],
                blueprint=str(case["blueprint"]),
                max_files=0,
            )

            self.assertEqual(errors, [], name)
            self.assertEqual(warnings, [], name)
            self.assertEqual(metrics["grounding_status"], "grounded", name)
            self.assertEqual(quality["status"], "passed", name)
            self.assertEqual(
                len(quality["deterministic_warnings"]),
                case["deterministic_warning_count"],
                name,
            )
            self.assertEqual(graph["primary_projection"], case["projection"], name)
            self.assertEqual(graph["atlas"]["scenario_policy"], case["policy"], name)
            scenarios = graph["atlas"]["scenarios"]
            if case["scenario_kind"] is None:
                self.assertEqual(scenarios, [], name)
            else:
                self.assertEqual(scenarios[0]["kind"], case["scenario_kind"], name)
            if case.get("forbid_api_provider"):
                self.assertFalse(
                    any(node["type"] == "api_provider" for node in graph["nodes"]),
                    name,
                )
            projections.add(case["projection"])
            policies.add(case["policy"])

        self.assertEqual(len(projections), len(GALLERY_CASES))
        self.assertEqual(policies, {"required", "optional", "none_with_reason"})

    def test_published_gallery_html_matches_curated_blueprints(self) -> None:
        for name, case in GALLERY_CASES.items():
            published = published_graph(case["html"])
            rebuilt, _ = graph_with_optional_blueprint(
                case["root"],
                blueprint=str(case["blueprint"]),
                max_files=0,
            )

            self.assertEqual(
                stable_gallery_contract(published),
                stable_gallery_contract(rebuilt),
                name,
            )

    def test_published_gallery_has_review_capture_dimensions(self) -> None:
        for name, case in GALLERY_CASES.items():
            image = case["screenshot"].read_bytes()

            self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n", name)
            self.assertEqual(struct.unpack(">II", image[16:24]), (1440, 900), name)


if __name__ == "__main__":
    unittest.main()
