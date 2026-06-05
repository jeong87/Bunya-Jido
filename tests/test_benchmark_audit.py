from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from bunya_jido.benchmark import audit_worktree
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


if __name__ == "__main__":
    unittest.main()
