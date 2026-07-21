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
from bunya_jido.render import _render_html_with_sample_run, render_html
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
        self.assertIn('id="openRunBtn"', html)
        self.assertIn('id="loadSampleRunBtn"', html)
        self.assertIn('id="bunya-jido-sample-run"', html)
        self.assertIn('id="runEvidencePanel"', html)
        self.assertIn("new FileReader()", html)
        self.assertIn("importRunObject", html)
        self.assertIn(
            "function loadEmbeddedSampleRun(){if(!embeddedSampleRun)return;importRunObject(embeddedSampleRun);}",
            html,
        )
        self.assertIn("loadSampleRunBtn.hidden=!embeddedSampleRun", html)
        self.assertIn(
            "if(!run||run.schema_version!=='bunya-jido-codex-run-v1')",
            html,
        )
        self.assertIn("route_fingerprint", html)
        self.assertIn(
            "expectedRoute.route_fingerprint===route.route_fingerprint",
            html,
        )
        self.assertIn(
            "state.runExpectedNodeIds=compatible?new Set(expectedRoute.node_ids||[]):new Set()",
            html,
        )
        self.assertIn("const actualIds=compatible?", html)
        self.assertIn("expected route", html)
        self.assertIn("actual evidence", html)
        self.assertIn("openRouteFromHash", html)
        self.assertIn("5*1024*1024", html)
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
        self.assertNotIn("fetch(", html)
        self.assertNotIn("localStorage", html)

        marker = '<script id="bunya-jido-sample-run" type="application/json">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        self.assertIsNone(json.loads(html[start:end]))

    def test_render_html_can_embed_an_offline_sample_without_changing_generic_output(self) -> None:
        graph = build_graph(MINIMAL_EXAMPLE)
        sample = {
            "schema_version": "bunya-jido-codex-run-v1",
            "evidence_provenance": {
                "kind": "sanitized_demonstration_fixture",
                "note": "UI fixture </script> remains inert.",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "atlas.html"
            html = _render_html_with_sample_run(graph, sample, out).read_text(
                encoding="utf-8"
            )

        marker = '<script id="bunya-jido-sample-run" type="application/json">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        self.assertEqual(json.loads(html[start:end]), sample)
        self.assertNotIn("UI fixture </script>", html)
        self.assertIn("UI fixture <\\/script>", html)
        self.assertIn("Loads a sanitized demonstration receipt into this browser.", html)
        self.assertIn("No credentials or live Codex account required.", html)

    def test_custom_templates_without_a_sample_placeholder_remain_compatible(self) -> None:
        graph = build_graph(MINIMAL_EXAMPLE)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            template = root / "custom.html"
            template.write_text("<script>__BUNYA_JIDO_DATA__</script>", encoding="utf-8")
            html = render_html(graph, root / "atlas.html", template=template).read_text(
                encoding="utf-8"
            )

        self.assertIn("bunya-jido-v1", html)
        self.assertNotIn("__BUNYA_JIDO_DATA__", html)

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
