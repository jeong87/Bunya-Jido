from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bunya_jido import __version__
from bunya_jido.cli import main
from bunya_jido.render import render_html
from bunya_jido.scanner import build_graph


ROOT = Path(__file__).resolve().parents[1]
MINIMAL_EXAMPLE = ROOT / "examples" / "minimal"


class SmokeTests(unittest.TestCase):
    def test_version_is_set(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_static_scan_minimal_example(self) -> None:
        graph = build_graph(MINIMAL_EXAMPLE)

        self.assertEqual(graph["schema_version"], "bunya-jido-v1")
        self.assertGreaterEqual(graph["node_count"], 1)
        self.assertGreaterEqual(graph["edge_count"], 1)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertEqual(graph["artifact_mode"], "static_scan")
        self.assertEqual(graph["grounding"]["status"], "not_assessed")
        self.assertEqual(graph["path_presets"][0]["kind"], "overview")
        self.assertTrue(graph["plane_glossary"])

    def test_render_html_embeds_graph(self) -> None:
        graph = build_graph(MINIMAL_EXAMPLE)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "atlas.html"
            html_path = render_html(graph, out)
            html = html_path.read_text(encoding="utf-8")

        self.assertIn("bunya-jido-v1", html)
        self.assertNotIn("__BUNYA_JIDO_DATA__", html)
        self.assertIn("Explore Mode", html)
        self.assertIn("Relation Families", html)

    def test_diagnose_reports_static_scan_as_not_grounded(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(
                [
                    "diagnose",
                    "--root",
                    str(MINIMAL_EXAMPLE),
                    "--blueprint",
                    "none",
                    "--require-grounded",
                    "--json",
                ]
            )
        report = json.loads(stdout.getvalue())

        self.assertEqual(result, 2)
        self.assertEqual(report["artifact_mode"], "static_scan")
        self.assertEqual(report["grounding_status"], "not_assessed")
        self.assertFalse(report["semantic_publication_allowed"])


if __name__ == "__main__":
    unittest.main()
