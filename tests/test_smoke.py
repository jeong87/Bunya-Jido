from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

from bunya_jido import __version__
from bunya_jido.cli import main
from bunya_jido.render import render_html
from bunya_jido.scanner import build_graph


ROOT = Path(__file__).resolve().parents[1]
MINIMAL_EXAMPLE = ROOT / "examples" / "minimal"


class SmokeTests(unittest.TestCase):
    def test_version_is_set(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?$")
        with (ROOT / "pyproject.toml").open("rb") as handle:
            package_version = tomllib.load(handle)["project"]["version"]
        self.assertEqual(__version__, package_version)

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
        self.assertIn("Map Controls", html)
        self.assertIn('id="toolbarTrust"', html)
        self.assertIn('id="workflowBar"', html)
        self.assertIn('id="scenarioBtn"', html)
        self.assertIn("studioScenarios", html)
        self.assertIn("renderScenarioUI", html)
        self.assertIn("Related Trusted Routes", html)
        self.assertIn("Copy coding-agent context", html)
        self.assertIn("codingAgentContextText", html)
        self.assertIn("nodeRoleStyles", html)
        self.assertIn("drawNodeShape", html)
        self.assertIn("relationFamilyVisuals", html)
        self.assertIn("Repository Outline", html)
        self.assertIn('id="repositorySummary"', html)
        self.assertIn("semanticOverviewHtml", html)
        self.assertIn("pathStepIndex", html)
        self.assertIn("e.directed!==false", html)
        self.assertIn('role="img"', html)
        layers = {
            name: int(value)
            for name, value in re.findall(
                r"--layer-(drawer|scenario|toolbar):(\d+)", html
            )
        }
        self.assertGreater(layers["scenario"], layers["drawer"])
        self.assertGreater(layers["toolbar"], layers["scenario"])
        self.assertEqual(html.count("z-index:var(--layer-scenario)"), 3)

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
