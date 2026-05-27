from __future__ import annotations

import unittest
from pathlib import Path

from bunya_jido.scanner import build_graph


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_EXAMPLE = ROOT / "examples" / "coverage"


def node_id_for_path(graph: dict, source_path: str, type_: str | None = None) -> str:
    return next(
        node["id"]
        for node in graph["nodes"]
        if node.get("source_path") == source_path
        and (type_ is None or node["type"] == type_)
    )


def edges_from(graph: dict, source: str, relation: str) -> list[dict]:
    return [
        edge
        for edge in graph["edges"]
        if edge["source"] == source and edge["relation"] == relation
    ]


class ScannerCoverageFixtureTests(unittest.TestCase):
    def test_python_config_and_provider_evidence_are_projected(self) -> None:
        graph = build_graph(COVERAGE_EXAMPLE)
        worker = node_id_for_path(graph, "src/coverage_app/worker.py")
        core = node_id_for_path(graph, "src/coverage_app/core.py")
        pyproject = node_id_for_path(graph, "pyproject.toml", "config")
        requirements = node_id_for_path(graph, "requirements.txt", "config")

        imports = edges_from(graph, worker, "uses_module")
        self.assertTrue(any(edge["target"] == core for edge in imports))
        self.assertTrue(
            any(
                edge["target"] == core
                and edge["evidence"][0]["kind"] == "python_import"
                for edge in imports
            )
        )
        self.assertTrue(
            any(
                edge["source"] == pyproject
                and edge["relation"] == "uses_module"
                and edge["target_label"] == "httpx"
                for edge in graph["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["source"] == requirements
                and edge["relation"] == "uses_module"
                and edge["target_label"] == "rich"
                and edge["evidence"][0]["kind"] == "requirements"
                for edge in graph["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["source"] == worker
                and edge["relation"] == "api_calls"
                and edge["target_label"] == "External OpenAI API"
                and edge["evidence"][0]["kind"] == "python_import"
                for edge in graph["edges"]
            )
        )

        hint_text = node_id_for_path(graph, "src/coverage_app/hint_text.py")
        self.assertTrue(
            any(
                edge["source"] == hint_text
                and edge["relation"] == "api_calls"
                and edge["confidence"] == "inferred"
                and edge["evidence"][0]["kind"] == "api_text_hint"
                for edge in graph["edges"]
            )
        )

    def test_markdown_runtime_and_data_policy_outputs_are_bounded(self) -> None:
        graph = build_graph(COVERAGE_EXAMPLE)
        readme = node_id_for_path(graph, "README.md")
        contract = node_id_for_path(graph, "docs/contract.md")

        self.assertTrue(
            any(
                edge["source"] == readme
                and edge["target"] == contract
                and edge["relation"] == "documents"
                and edge["evidence"][0]["kind"] == "markdown_link"
                for edge in graph["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["relation"] == "emits"
                and edge["target_label"] == "queued"
                for edge in graph["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["relation"] == "records"
                and edge["target_label"] == "status: ready"
                for edge in graph["edges"]
            )
        )
        self.assertFalse(
            any(node.get("source_path") == "data/sample.csv" for node in graph["nodes"])
        )

        sampled = build_graph(COVERAGE_EXAMPLE, data_policy="sample")
        self.assertTrue(
            any(
                node.get("source_path") == "data/sample.csv"
                and node["type"] == "data"
                for node in sampled["nodes"]
            )
        )

    def test_javascript_relative_import_is_detected_but_not_locally_resolved(self) -> None:
        graph = build_graph(COVERAGE_EXAMPLE, show_root=True)
        main = node_id_for_path(graph, "web/main.ts", "module")
        local = node_id_for_path(graph, "web/local.ts", "module")
        relative_edges = [
            edge
            for edge in edges_from(graph, main, "uses_module")
            if edge["evidence"][0]["kind"] == "js_relative_import"
        ]

        self.assertEqual(len(relative_edges), 1)
        self.assertEqual(relative_edges[0]["confidence"], "inferred")
        self.assertNotEqual(relative_edges[0]["target"], local)
        self.assertTrue(
            any(
                edge["source"] == main
                and edge["relation"] == "uses_module"
                and edge["target_label"] == "react"
                for edge in graph["edges"]
            )
        )

        default_graph = build_graph(COVERAGE_EXAMPLE)
        default_main = node_id_for_path(default_graph, "web/main.ts", "module")
        self.assertFalse(
            any(
                edge["source"] == default_main
                and edge["evidence"][0]["kind"] == "js_relative_import"
                for edge in default_graph["edges"]
            )
        )


if __name__ == "__main__":
    unittest.main()
