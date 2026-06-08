from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from bunya_jido.benchmark import (
    audit_worktree,
    summarize_time_efficiency,
    summarize_token_efficiency,
)
from bunya_jido.cli import main


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _committed_repo(root: Path, files: dict[str, str]) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "benchmark@example.com")
    _git(root, "config", "user.name", "Benchmark Fixture")
    for relative_path, content in files.items():
        _write(root / relative_path, content)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")


class BenchmarkAuditTests(unittest.TestCase):
    def test_clean_baseline_and_untracked_production_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _committed_repo(root, {"src/app.py": "value = 1\n"})

            clean = audit_worktree(root)
            self.assertTrue(clean["worktree_clean"])
            self.assertFalse(clean["has_production_changes"])

            _write(root / "ios/App.swift", "let value = 1\n")
            changed = audit_worktree(root)
            self.assertEqual(changed["untracked_files"], ["ios/App.swift"])
            self.assertEqual(changed["production_file_changes"], ["ios/App.swift"])
            self.assertTrue(changed["has_production_changes"])

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "audit-worktree",
                        "--root",
                        str(root),
                        "--require-no-production-activity",
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertEqual(json.loads(stdout.getvalue())["untracked_files"], ["ios/App.swift"])

            with redirect_stdout(StringIO()):
                self.assertEqual(main(["audit-worktree", "--root", str(root), "--require-clean"]), 2)

    def test_tracks_modified_staged_deleted_and_renamed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _committed_repo(
                root,
                {
                    "src/modified.py": "value = 1\n",
                    "src/staged.py": "value = 1\n",
                    "src/deleted.py": "value = 1\n",
                    "src/old.py": "value = 1\n",
                },
            )

            _write(root / "src/modified.py", "value = 2\n")
            _write(root / "src/staged.py", "value = 2\n")
            _git(root, "add", "src/staged.py")
            (root / "src/deleted.py").unlink()
            _git(root, "mv", "src/old.py", "src/new.py")

            report = audit_worktree(root)
            self.assertEqual(
                report["changed_files_tracked"],
                ["src/deleted.py", "src/modified.py", "src/new.py", "src/old.py", "src/staged.py"],
            )
            self.assertEqual(report["staged_files"], ["src/new.py", "src/old.py", "src/staged.py"])
            self.assertEqual(report["deleted_files"], ["src/deleted.py"])
            self.assertEqual(report["renamed_files"], [{"from": "src/old.py", "to": "src/new.py"}])
            self.assertGreater(report["changed_lines_tracked"], 0)

    def test_separates_allowed_artifacts_from_production_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _committed_repo(root, {"src/app.py": "value = 1\n"})
            _write(root / "results/run.json", "{}\n")
            _write(root / "infra/terraform/main.tf", "resource \"example\" \"test\" {}\n")
            _write(root / "src/orders/infrastructure/adapter.py", "value = 1\n")

            report = audit_worktree(root, allowed_artifacts=["results/**"])
            self.assertEqual(report["allowed_artifact_changes"], ["results/run.json"])
            self.assertEqual(
                report["production_file_changes"],
                ["infra/terraform/main.tf", "src/orders/infrastructure/adapter.py"],
            )

    def test_generated_noise_does_not_count_as_production_activity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _committed_repo(root, {"src/app.py": "value = 1\n"})
            _write(root / "__pycache__/app.cpython-312.pyc", "cache\n")
            _write(root / "src/__pycache__/worker.cpython-312.pyc", "cache\n")
            _write(root / ".pytest_cache/v/cache/nodeids", "[]\n")
            _write(root / "htmlcov/index.html", "<html></html>\n")
            _write(root / ".coverage", "coverage\n")
            _write(root / "results/run.json", "{}\n")
            events = [
                {
                    "type": "item.completed",
                    "item": {
                        "type": "file_change",
                        "status": "completed",
                        "changes": [
                            {"path": str(root / "src/__pycache__/worker.cpython-312.pyc"), "kind": "add"},
                            {"path": str(root / ".pytest_cache/v/cache/nodeids"), "kind": "add"},
                            {"path": str(root / "results/run.json"), "kind": "add"},
                        ],
                    },
                },
            ]
            jsonl = root / "results" / "codex.jsonl"
            jsonl.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )

            report = audit_worktree(
                root,
                jsonl_paths=[jsonl],
                allowed_artifacts=["results/**"],
            )

            self.assertFalse(report["worktree_clean"])
            self.assertTrue(report["production_clean"])
            self.assertEqual(report["production_file_changes"], [])
            self.assertEqual(report["jsonl_production_write_attempts"], [])
            self.assertEqual(report["allowed_artifact_changes"], ["results/codex.jsonl", "results/run.json"])
            self.assertEqual(report["jsonl_allowed_artifact_attempts"], ["results/run.json"])
            self.assertEqual(
                report["generated_noise_changes"],
                [
                    ".coverage",
                    ".pytest_cache/v/cache/nodeids",
                    "__pycache__/app.cpython-312.pyc",
                    "htmlcov/index.html",
                    "src/__pycache__/worker.cpython-312.pyc",
                ],
            )
            self.assertEqual(
                report["jsonl_generated_noise_attempts"],
                [
                    ".pytest_cache/v/cache/nodeids",
                    "src/__pycache__/worker.cpython-312.pyc",
                ],
            )
            classifications = {
                item["path"]: item["classification"]
                for item in report["file_change_classification"]
            }
            self.assertEqual(classifications["src/__pycache__/worker.cpython-312.pyc"], "generated_noise")
            self.assertEqual(classifications["results/run.json"], "allowed_artifact")

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "audit-worktree",
                        "--root",
                        str(root),
                        "--jsonl",
                        str(jsonl),
                        "--allow-artifact",
                        "results/**",
                        "--require-no-production-activity",
                        "--json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            cli_report = json.loads(stdout.getvalue())
            self.assertEqual(cli_report["generated_noise_changes"], report["generated_noise_changes"])

            strict = audit_worktree(
                root,
                allowed_artifacts=["results/**"],
                include_default_noise=False,
            )
            self.assertIn("src/__pycache__/worker.cpython-312.pyc", strict["production_file_changes"])

    def test_jsonl_detects_write_then_revert_and_deduplicates_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            root = fixture_root / "workspace"
            root.mkdir()
            _committed_repo(root, {"src/app.py": "value = 1\n"})
            outside = fixture_root / "outside.py"
            events = [
                {
                    "type": "item.started",
                    "item": {
                        "type": "file_change",
                        "status": "in_progress",
                        "changes": [{"path": str(root / "src/app.py"), "kind": "update"}],
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "file_change",
                        "status": "completed",
                        "changes": [
                            {"path": str(root / "src/app.py"), "kind": "update"},
                            {"path": str(root / "results/run.json"), "kind": "add"},
                            {"path": str(outside), "kind": "add"},
                        ],
                    },
                },
            ]
            jsonl = fixture_root / "codex.jsonl"
            valid_jsonl = "\n".join(json.dumps(event) for event in events) + "\n"
            jsonl.write_text("", encoding="utf-8")
            self.assertFalse(audit_worktree(root, jsonl_paths=[jsonl])["jsonl_complete"])
            jsonl.write_text(valid_jsonl, encoding="utf-8")

            report = audit_worktree(root, jsonl_paths=[jsonl], allowed_artifacts=["results/**"])
            self.assertTrue(report["worktree_clean"])
            self.assertEqual(report["production_file_changes"], [])
            self.assertEqual(report["jsonl_production_write_attempts"], ["src/app.py"])
            self.assertEqual(report["jsonl_allowed_artifact_attempts"], ["results/run.json"])
            self.assertEqual(len(report["jsonl_file_change_events"]), 2)
            self.assertEqual(len(report["jsonl_outside_workspace_changes"]), 1)
            self.assertEqual(report["jsonl_event_count"], 2)
            self.assertEqual(report["malformed_jsonl_lines"], 0)
            self.assertTrue(report["jsonl_complete"])

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(["audit-worktree", "--root", str(root), "--jsonl", str(jsonl), "--require-jsonl"]),
                    0,
                )

            jsonl.write_text(valid_jsonl + "{malformed\n[]\n", encoding="utf-8")
            malformed_report = audit_worktree(root, jsonl_paths=[jsonl])
            self.assertEqual(malformed_report["malformed_jsonl_lines"], 1)
            self.assertEqual(malformed_report["invalid_jsonl_lines"], 1)
            self.assertFalse(malformed_report["jsonl_complete"])

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(["audit-worktree", "--root", str(root), "--jsonl", str(jsonl), "--require-jsonl"]),
                    2,
                )

    def test_token_efficiency_uses_only_paired_safe_and_resolved_runs(self) -> None:
        runs = [
            {
                "condition": "no-map",
                "task_id": "repair-1",
                "task_kind": "bugfix",
                "task_tokens": 1000,
                "context_output_tokens": 100,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            },
            {
                "condition": "0.5-map",
                "task_id": "repair-1",
                "task_kind": "bugfix",
                "task_tokens": 600,
                "context_output_tokens": 60,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            },
            {
                "condition": "no-map",
                "task_id": "repair-rejected",
                "task_kind": "bugfix",
                "task_tokens": 1200,
                "context_output_tokens": 90,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            },
            {
                "condition": "0.5-map",
                "task_id": "repair-rejected",
                "task_kind": "bugfix",
                "task_tokens": 50,
                "context_output_tokens": 30,
                "resolved": False,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": False,
            },
            {
                "condition": "no-map",
                "task_id": "no-match-1",
                "task_kind": "no_match",
                "task_tokens": 300,
                "context_output_tokens": 40,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": False,
            },
            {
                "condition": "0.5-map",
                "task_id": "no-match-1",
                "task_kind": "no_match",
                "task_tokens": 250,
                "context_output_tokens": 30,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": False,
            },
            {
                "condition": "0.5-map",
                "task_id": "no-match-write",
                "task_kind": "no_match",
                "task_tokens": 10,
                "context_output_tokens": 20,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            },
        ]

        report = summarize_token_efficiency(
            runs,
            baseline_condition="no-map",
            candidate_condition="0.5-map",
            map_authoring_tokens={"no-map": 0, "0.5-map": 800},
        )

        self.assertEqual(report["status"], "comparable")
        self.assertEqual(report["paired_safe_and_resolved_task_count"], 2)
        self.assertEqual(report["comparisons"]["all"]["task_token_saving"], 450)
        self.assertEqual(report["comparisons"]["repair"]["task_token_saving"], 400)
        self.assertEqual(report["comparisons"]["no_match"]["task_token_saving"], 50)
        self.assertEqual(
            report["comparisons"]["no_match"]["candidate_median_task_tokens"], 250
        )
        self.assertEqual(report["break_even_task_count"]["all"], 3.56)
        self.assertEqual(report["break_even_task_count"]["repair"], 2.0)
        self.assertEqual(
            report["conditions"]["0.5-map"]["excluded_run_reasons"],
            {"no_match_production_write": 1, "unresolved_bugfix": 1},
        )
        self.assertEqual(
            report["conditions"]["0.5-map"][
                "safe_and_resolved_no_match_median_task_tokens"
            ],
            250,
        )
        self.assertIn(
            {
                "condition": "0.5-map",
                "task_id": "repair-rejected",
                "task_kind": "bugfix",
                "reasons": ["unresolved_bugfix"],
            },
            report["excluded_runs"],
        )

    def test_token_efficiency_cli_and_validation(self) -> None:
        runs = [
            {
                "condition": condition,
                "task_id": "repair-1",
                "task_kind": "bugfix",
                "task_tokens": tokens,
                "context_output_tokens": context_tokens,
                "resolved": resolved,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            }
            for condition, tokens, context_tokens, resolved in (
                ("no-map", 1000, 100, True),
                ("0.5-map", 600, 60, True),
            )
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            results = Path(temp_dir) / "tokens.json"
            results.write_text(
                json.dumps(
                    {
                        "runs": runs,
                        "map_authoring_tokens": {"no-map": 0, "0.5-map": 400},
                    }
                ),
                encoding="utf-8",
            )
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "summarize-token-efficiency",
                        "--results",
                        str(results),
                        "--baseline",
                        "no-map",
                        "--candidate",
                        "0.5-map",
                        "--require-comparable",
                        "--json",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["paired_safe_and_resolved_task_count"],
            1,
        )
        invalid = [dict(runs[0], task_tokens=-1), runs[1]]
        with self.assertRaisesRegex(ValueError, "task_tokens"):
            summarize_token_efficiency(
                invalid,
                baseline_condition="no-map",
                candidate_condition="0.5-map",
            )

        missing_authoring = summarize_token_efficiency(
            runs,
            baseline_condition="no-map",
            candidate_condition="0.5-map",
        )
        self.assertEqual(
            missing_authoring["map_authoring_tokens"],
            {
                "baseline": None,
                "candidate": None,
                "incremental": None,
                "complete": False,
            },
        )
        self.assertIsNone(
            missing_authoring["conditions"]["0.5-map"]["map_authoring_tokens"]
        )
        self.assertIsNone(missing_authoring["break_even_task_count"]["repair"])

    def test_time_efficiency_uses_repeated_safe_and_resolved_pairs(self) -> None:
        def run(
            condition: str,
            pair_id: str,
            task_id: str,
            task_kind: str,
            total: float,
            context: float,
            first_edit: float | None,
            *,
            resolved: bool = True,
            boundary_violation: bool = False,
            production_write_attempt: bool = True,
        ) -> dict[str, object]:
            return {
                "condition": condition,
                "pair_id": pair_id,
                "task_id": task_id,
                "task_kind": task_kind,
                "total_resolution_seconds": total,
                "context_generation_seconds": context,
                "discovery_to_first_edit_seconds": first_edit,
                "resolved": resolved,
                "infrastructure_valid": True,
                "boundary_violation": boundary_violation,
                "production_write_attempt": production_write_attempt,
            }

        runs = [
            run("no-map", "repair-a/r1", "repair-a", "bugfix", 100, 5, 20),
            run("0.5-map", "repair-a/r1", "repair-a", "bugfix", 80, 4, 15),
            run("no-map", "repair-a/r2", "repair-a", "bugfix", 120, 6, 30),
            run("0.5-map", "repair-a/r2", "repair-a", "bugfix", 90, 4, 18),
            run("no-map", "repair-a/r3", "repair-a", "bugfix", 140, 7, 40),
            run("0.5-map", "repair-a/r3", "repair-a", "bugfix", 100, 5, None),
            run(
                "no-map",
                "no-match/r1",
                "no-match",
                "no_match",
                20,
                0,
                None,
                production_write_attempt=False,
            ),
            run(
                "0.5-map",
                "no-match/r1",
                "no-match",
                "no_match",
                25,
                2,
                None,
                production_write_attempt=False,
            ),
            run("no-map", "unsafe/r1", "unsafe", "bugfix", 200, 5, 50),
            run(
                "0.5-map",
                "unsafe/r1",
                "unsafe",
                "bugfix",
                10,
                1,
                2,
                boundary_violation=True,
            ),
            run("no-map", "unresolved/r1", "unresolved", "bugfix", 160, 5, 40),
            run(
                "0.5-map",
                "unresolved/r1",
                "unresolved",
                "bugfix",
                20,
                1,
                None,
                resolved=False,
                production_write_attempt=False,
            ),
        ]

        report = summarize_time_efficiency(
            runs,
            baseline_condition="no-map",
            candidate_condition="0.5-map",
            map_authoring_seconds={"no-map": 0, "0.5-map": 300},
        )

        self.assertEqual(report["status"], "comparable")
        self.assertEqual(report["measurement_scope"], "reporting_only_no_routing_optimization")
        self.assertEqual(report["paired_safe_and_resolved_run_count"], 4)
        all_time = report["comparisons"]["all"]["total_resolution"]
        self.assertEqual(all_time["saving_seconds"], 85)
        self.assertEqual(all_time["saving_rate"], 0.2237)
        self.assertEqual(all_time["baseline"]["median_seconds"], 110)
        self.assertEqual(all_time["baseline"]["p90_seconds"], 140.0)
        self.assertEqual(all_time["candidate"]["p90_seconds"], 100.0)
        first_edit = report["comparisons"]["all"]["discovery_to_first_edit"]
        self.assertEqual(first_edit["paired_run_count"], 2)
        self.assertEqual(first_edit["saving_seconds"], 17)
        self.assertEqual(report["break_even_task_count"]["repair"], 10.0)
        repair_task = next(
            task for task in report["per_task"] if task["task_id"] == "repair-a"
        )
        self.assertEqual(repair_task["paired_run_count"], 3)
        self.assertEqual(
            repair_task["total_resolution"]["baseline"]["median_seconds"], 120.0
        )
        self.assertEqual(
            report["conditions"]["0.5-map"]["excluded_run_reasons"],
            {"boundary_violation": 1, "unresolved_bugfix": 1},
        )

    def test_time_efficiency_cli_and_validation(self) -> None:
        runs = [
            {
                "condition": condition,
                "task_id": "repair-1",
                "task_kind": "bugfix",
                "total_resolution_seconds": total,
                "context_generation_seconds": context,
                "discovery_to_first_edit_seconds": first_edit,
                "resolved": True,
                "infrastructure_valid": True,
                "boundary_violation": False,
                "production_write_attempt": True,
            }
            for condition, total, context, first_edit in (
                ("no-map", 100, 0, 25),
                ("0.5-map", 70, 3, 15),
            )
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            results = Path(temp_dir) / "time.json"
            results.write_text(json.dumps({"runs": runs}), encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "summarize-time-efficiency",
                        "--results",
                        str(results),
                        "--baseline",
                        "no-map",
                        "--candidate",
                        "0.5-map",
                        "--require-comparable",
                        "--json",
                    ]
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["paired_safe_and_resolved_run_count"], 1)
        self.assertEqual(
            report["map_authoring_seconds"],
            {
                "baseline": None,
                "candidate": None,
                "incremental": None,
                "complete": False,
            },
        )
        self.assertIsNone(report["break_even_task_count"]["repair"])
        invalid = [
            dict(runs[0], context_generation_seconds=101),
            runs[1],
        ]
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            summarize_time_efficiency(
                invalid,
                baseline_condition="no-map",
                candidate_condition="0.5-map",
            )
        duplicate = [runs[0], dict(runs[0]), runs[1]]
        with self.assertRaisesRegex(ValueError, "duplicate time run"):
            summarize_time_efficiency(
                duplicate,
                baseline_condition="no-map",
                candidate_condition="0.5-map",
            )


if __name__ == "__main__":
    unittest.main()
