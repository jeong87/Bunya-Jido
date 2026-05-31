from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from bunya_jido.blueprint import graph_with_optional_blueprint, validate_blueprint_obj
from bunya_jido.quality import evaluate_atlas_quality_obj


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_ROOT = ROOT / "examples" / "coverage"
COVERAGE_BLUEPRINT = COVERAGE_ROOT / "studio.blueprint.json"
COVERAGE_HTML = ROOT / "docs" / "gallery" / "coverage-fixture.html"
COVERAGE_SCREENSHOT = ROOT / "docs" / "gallery" / "coverage-fixture.png"


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
    def test_coverage_fixture_publishes_a_grounded_non_runtime_reading(self) -> None:
        blueprint = json.loads(COVERAGE_BLUEPRINT.read_text(encoding="utf-8"))
        errors, warnings, metrics = validate_blueprint_obj(blueprint, root=COVERAGE_ROOT)
        quality = evaluate_atlas_quality_obj(
            blueprint, validation_errors=errors, validation_metrics=metrics
        )
        graph, _ = graph_with_optional_blueprint(
            COVERAGE_ROOT,
            blueprint=str(COVERAGE_BLUEPRINT),
            max_files=0,
        )

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["grounding_status"], "grounded")
        self.assertEqual(quality["status"], "passed")
        self.assertEqual(graph["primary_projection"], "projection:evidence_surfaces")
        self.assertEqual(graph["atlas"]["scenario_policy"], "none_with_reason")
        self.assertEqual(graph["scenario_count"], 0)
        self.assertFalse(
            any(node["type"] == "api_provider" for node in graph["nodes"])
        )

    def test_published_coverage_fixture_html_matches_curated_blueprint(self) -> None:
        published = published_graph(COVERAGE_HTML)
        rebuilt, _ = graph_with_optional_blueprint(
            COVERAGE_ROOT,
            blueprint=str(COVERAGE_BLUEPRINT),
            max_files=0,
        )

        self.assertEqual(
            stable_gallery_contract(published),
            stable_gallery_contract(rebuilt),
        )

    def test_published_coverage_fixture_has_review_capture_dimensions(self) -> None:
        image = COVERAGE_SCREENSHOT.read_bytes()

        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", image[16:24]), (1440, 900))


if __name__ == "__main__":
    unittest.main()
