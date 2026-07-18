from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from bunya_jido.cli import main
from bunya_jido.codex_run import _execute_guarded_codex_run, _safe_edit_allows


FIXED_NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _blueprint() -> dict:
    return {
        "schema_version": "bunya-jido-blueprint-v1",
        "project": {"name": "fixture", "summary": "Guarded run fixture."},
        "planes": [
            {"id": "entry", "label": "Entry", "purpose": "Commands"},
            {"id": "control", "label": "Control", "purpose": "Application"},
            {"id": "quality", "label": "Quality", "purpose": "Tests"},
        ],
        "nodes": [
            {
                "id": "component:cli",
                "label": "CLI",
                "type": "component",
                "plane": "entry",
                "importance": "core",
                "description": "Accepts application commands.",
                "evidence": [{"kind": "source", "path": "README.md"}],
            },
            {
                "id": "component:app",
                "label": "Application",
                "type": "component",
                "plane": "control",
                "importance": "core",
                "description": "Owns application behavior.",
                "evidence": [{"kind": "source", "path": "src/app.py"}],
            },
            {
                "id": "quality:tests",
                "label": "Application Tests",
                "type": "contract",
                "plane": "quality",
                "importance": "major",
                "description": "Checks application behavior.",
                "evidence": [{"kind": "test", "path": "tests/test_app.py"}],
            },
        ],
        "edges": [
            {
                "source": "component:cli",
                "target": "component:app",
                "relation": "calls",
                "confidence": "llm_grounded",
                "evidence": [{"kind": "source", "path": "src/app.py"}],
            },
            {
                "source": "component:app",
                "target": "quality:tests",
                "relation": "verified_by",
                "confidence": "llm_grounded",
                "evidence": [{"kind": "test", "path": "tests/test_app.py"}],
            },
        ],
        "workflows": [
            {
                "id": "application_flow",
                "label": "Application Flow",
                "description": "Command to application behavior.",
                "node_ids": ["component:cli", "component:app", "quality:tests"],
            }
        ],
    }


def _agent_map() -> dict:
    return {
        "schema_version": "bunya-jido-agent-map-v1",
        "project": {"name": "fixture", "summary": "Guarded run routes."},
        "repository_scope": {
            "supported_surfaces": ["application command behavior"],
            "supported_technologies": ["Python"],
            "unsupported_surfaces": [
                "native iOS application",
                "Android Gradle application",
            ],
            "unsupported_technologies": ["Terraform", "Kubernetes"],
            "repository_non_goals": ["native mobile application development"],
        },
        "task_routes": [
            {
                "task": "change application behavior",
                "intent": "Update application logic.",
                "match_terms": ["application behavior"],
                "start_nodes": ["component:app"],
                "workflows": ["application_flow"],
                "must_read": ["src/app.py"],
                "contracts": ["Application behavior contract"],
                "tests": ["tests/test_app.py"],
                "safe_edit": ["src/app.py"],
            }
        ],
    }


FAKE_CODEX = r"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


args = sys.argv[1:]
prompt = sys.stdin.read()
root = Path(args[args.index("--cd") + 1])
last_message = Path(args[args.index("--output-last-message") + 1])
mode = os.environ.get("FAKE_CODEX_MODE", "read_only")

def emit(item):
    print(json.dumps({"type": "item.completed", "item": item}), flush=True)

if mode == "timeout":
    time.sleep(30)
elif mode == "empty":
    pass
elif mode == "malformed":
    print("{malformed", flush=True)
elif mode == "partial":
    emit({"type": "agent_message", "text": "readable before malformed"})
    print("{malformed", flush=True)
else:
    changes = []
    if mode == "safe":
        target = root / "src" / "app.py"
        target.write_text("value = 2\n", encoding="utf-8")
        changes.append({"path": str(target), "kind": "update"})
    elif mode == "unsafe":
        target = root / "docs" / "unsafe.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("unsafe\n", encoding="utf-8")
        changes.append({"path": str(target), "kind": "add"})
    elif mode == "unsafe_revert":
        target = root / "README.md"
        original = target.read_text(encoding="utf-8")
        target.write_text("temporary\n", encoding="utf-8")
        target.write_text(original, encoding="utf-8")
        changes.append({"path": str(target), "kind": "update"})
    elif mode == "rename":
        source = root / "src" / "app.py"
        target = root / "src" / "renamed.py"
        source.rename(target)
        changes.extend(
            [
                {"path": str(source), "kind": "delete"},
                {"path": str(target), "kind": "add"},
            ]
        )
    elif mode == "outside":
        target = root.parent / "outside.py"
        changes.append({"path": str(target), "kind": "add"})
    elif mode == "artifact_extra":
        target = last_message.parent / "unexpected.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("unexpected\n", encoding="utf-8")
        changes.append({"path": str(target), "kind": "add"})
    if changes:
        emit({"type": "file_change", "status": "completed", "changes": changes})
    emit({"type": "agent_message", "text": "fake completed"})

last_message.parent.mkdir(parents=True, exist_ok=True)
last_message.write_text("fake final message\n", encoding="utf-8")
print("fake stderr", file=sys.stderr, flush=True)
sys.exit(int(os.environ.get("FAKE_CODEX_EXIT", "0")))
"""


class GuardedCodexRunTests(unittest.TestCase):
    def _repository(self, parent: Path) -> tuple[Path, Path]:
        root = parent / "fixture repo 한글 & ; $(noop)"
        root.mkdir()
        _write(root / "README.md", "fixture\n")
        _write(root / "src" / "app.py", "value = 1\n")
        _write(root / "tests" / "test_app.py", "def test_app():\n    assert True\n")
        _write(
            root / ".bunya-jido" / "bunya-jido.blueprint.json",
            json.dumps(_blueprint()),
        )
        _write(
            root / ".bunya-jido" / "bunya-jido.agent-map.json",
            json.dumps(_agent_map()),
        )
        fake = root / "fake_codex.py"
        _write(fake, FAKE_CODEX)
        _git(root, "init")
        _git(root, "config", "user.email", "fixture@example.com")
        _git(root, "config", "user.name", "Fixture")
        _git(root, "add", ".")
        _git(root, "commit", "-m", "fixture")
        return root, fake

    def _run(
        self,
        root: Path,
        fake: Path,
        *,
        task: str = "change application behavior",
        mode: str = "read_only",
        run_id: str = "test-run",
        timeout: float | None = None,
        extra_env: dict[str, str] | None = None,
        out_dir: str | Path | None = None,
    ) -> dict:
        environ = dict(os.environ)
        environ["FAKE_CODEX_MODE"] = mode
        environ.update(extra_env or {})
        return _execute_guarded_codex_run(
            root=root,
            task=task,
            command_prefix=[sys.executable, str(fake)],
            timeout=timeout,
            out_dir=out_dir,
            run_id=run_id,
            now_fn=lambda: FIXED_NOW,
            monotonic_fn=lambda: 10.0,
            environ=environ,
        )

    def test_preview_is_non_mutating_and_inert_to_shell_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))
            task = 'change application behavior"; New-Item injected.txt; # 한글'
            before = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout

            report = _execute_guarded_codex_run(
                root=root,
                task=task,
                preview=True,
                command_prefix=[sys.executable, str(fake)],
                run_id="preview-run",
                now_fn=lambda: FIXED_NOW,
                monotonic_fn=lambda: 10.0,
            )

            after = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertEqual(report["status"], "preview")
            self.assertEqual(report["exit_code"], 0)
            self.assertEqual(report["execution"]["shell"], False)
            self.assertNotIn(task, report["execution"]["command"])
            self.assertIn("# Bunya-Jido Agent Context", report["scoped_context"]["content"])
            self.assertIn("New-Item injected.txt", report["scoped_context"]["content"])
            self.assertIn("--ask-for-approval", report["execution"]["command"])
            self.assertIn("--ignore-user-config", report["execution"]["command"])
            self.assertIn("--ephemeral", report["execution"]["command"])
            self.assertIn("sandbox_workspace_write.network_access=false", report["execution"]["command"])
            self.assertFalse((root / "injected.txt").exists())
            self.assertFalse((root / ".bunya-jido" / "runs").exists())
            self.assertEqual(before, after)

    def test_decisions_map_to_non_escalating_sandboxes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))
            cases = [
                ("change application behavior", "MATCH", "workspace-write"),
                (
                    "Fix command option dispatch.",
                    "IN_SCOPE_NO_ROUTE",
                    "read-only",
                ),
                (
                    "Add a native iOS application with App Store signing.",
                    "OUT_OF_SCOPE",
                    "read-only",
                ),
                ("publish package to package registry", "UNCERTAIN", "read-only"),
            ]
            for index, (task, decision, sandbox) in enumerate(cases):
                with self.subTest(decision=decision):
                    report = _execute_guarded_codex_run(
                        root=root,
                        task=task,
                        preview=True,
                        command_prefix=[sys.executable, str(fake)],
                        run_id=f"decision-{index}",
                        now_fn=lambda: FIXED_NOW,
                        monotonic_fn=lambda: 10.0,
                    )
                    self.assertEqual(report["context"]["decision"], decision)
                    self.assertEqual(report["execution"]["sandbox_mode"], sandbox)
                    command = report["execution"]["command"]
                    self.assertEqual(command[command.index("--sandbox") + 1], sandbox)
                    self.assertNotIn("--search", command)
                    self.assertNotIn("danger-full-access", command)

            with patch.dict(os.environ, {"BUNYA_JIDO_CONTEXT": "off"}):
                disabled = _execute_guarded_codex_run(
                    root=root,
                    task="change application behavior",
                    preview=True,
                    command_prefix=[sys.executable, str(fake)],
                    run_id="disabled",
                    now_fn=lambda: FIXED_NOW,
                    monotonic_fn=lambda: 10.0,
                )
            self.assertEqual(disabled["context"]["decision"], "DISABLED")
            self.assertEqual(disabled["execution"]["sandbox_mode"], "read-only")

    def test_match_fake_codex_vertical_slice_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))

            report = self._run(root, fake, mode="safe")

            self.assertEqual(report["status"], "succeeded")
            self.assertEqual(report["exit_code"], 0)
            self.assertEqual(report["run_id"], "test-run")
            self.assertEqual(report["started_at"], "2026-07-18T12:00:00Z")
            self.assertEqual(report["finished_at"], "2026-07-18T12:00:00Z")
            self.assertEqual(report["duration_seconds"], 0.0)
            self.assertEqual(report["execution"]["return_code"], 0)
            self.assertTrue(report["post_run_audit"]["jsonl_complete"])
            self.assertEqual(
                report["boundary_audit"]["in_boundary_paths"],
                ["src/app.py"],
            )
            self.assertEqual(report["boundary_audit"]["boundary_violations"], [])
            self.assertFalse(report["boundary_audit"]["semantic_guidance_os_enforced"])
            run_dir = root / ".bunya-jido" / "runs" / "test-run"
            stored = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            markdown = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertEqual(stored["status"], report["status"])
            self.assertEqual(
                stored["artifacts"],
                {
                    "run_json": "run.json",
                    "report_markdown": "report.md",
                    "events_jsonl": "events.jsonl",
                    "stderr_log": "stderr.log",
                    "last_message": "last-message.txt",
                },
            )
            self.assertIn("Status: `succeeded`", markdown)
            self.assertIn("Decision: `MATCH`", markdown)
            self.assertIn("Return code: `0`", markdown)
            self.assertEqual(
                (run_dir / "last-message.txt").read_text(encoding="utf-8"),
                "fake final message\n",
            )
            self.assertIn("fake stderr", (run_dir / "stderr.log").read_text(encoding="utf-8"))

    def test_non_match_fake_runs_stay_read_only_and_succeed(self) -> None:
        tasks = [
            "Fix command option dispatch.",
            "Add a native iOS application with App Store signing.",
            "publish package to package registry",
        ]
        for index, task in enumerate(tasks):
            with self.subTest(task=task):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root, fake = self._repository(Path(temp_dir))
                    report = self._run(
                        root,
                        fake,
                        task=task,
                        mode="read_only",
                        run_id=f"read-only-{index}",
                    )
                    self.assertEqual(report["status"], "succeeded")
                    self.assertEqual(report["execution"]["sandbox_mode"], "read-only")
                    self.assertEqual(
                        report["boundary_audit"]["observed_production_activity"],
                        [],
                    )

    def test_non_match_write_attempt_is_always_a_policy_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))

            report = self._run(
                root,
                fake,
                task="Add a native iOS application with App Store signing.",
                mode="unsafe_revert",
                run_id="non-match-write",
            )

            self.assertEqual(report["context"]["decision"], "OUT_OF_SCOPE")
            self.assertEqual(report["execution"]["sandbox_mode"], "read-only")
            self.assertEqual(report["status"], "boundary_violation")
            self.assertIn(
                "production activity is forbidden for a non-MATCH decision",
                report["boundary_audit"]["boundary_violations"][0]["reason"],
            )

    def test_safe_edit_matching_is_exact_glob_or_declared_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src" / "package").mkdir(parents=True)
            _write(root / "src" / "exact.py", "")

            self.assertTrue(
                _safe_edit_allows("src/exact.py", ["src/exact.py"], root)
            )
            self.assertTrue(
                _safe_edit_allows("tests/test_app.py", ["tests/*.py"], root)
            )
            self.assertTrue(
                _safe_edit_allows(
                    "src/package/nested.py",
                    ["src/package/"],
                    root,
                )
            )
            self.assertFalse(
                _safe_edit_allows("src/other.py", ["src/exact.py"], root)
            )
            self.assertFalse(
                _safe_edit_allows(
                    "src/package_evil/nested.py",
                    ["src/package/"],
                    root,
                )
            )

    def test_dirty_worktree_blocks_launch_but_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))
            _write(root / "README.md", "dirty\n")

            report = self._run(root, fake, mode="safe", run_id="dirty-run")

            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["exit_code"], 2)
            self.assertFalse(report["execution"]["launched"])
            self.assertEqual(report["reasons"], ["dirty_worktree"])
            self.assertEqual((root / "src" / "app.py").read_text(encoding="utf-8"), "value = 1\n")
            self.assertTrue(
                (root / ".bunya-jido" / "runs" / "dirty-run" / "run.json").exists()
            )

    def test_missing_executable_is_a_controlled_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._repository(Path(temp_dir))

            report = _execute_guarded_codex_run(
                root=root,
                task="change application behavior",
                codex_executable="definitely-missing-codex-executable",
                run_id="missing-run",
                now_fn=lambda: FIXED_NOW,
                monotonic_fn=lambda: 10.0,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["exit_code"], 2)
            self.assertIn("codex_executable_not_found", report["reasons"])
            self.assertFalse(report["execution"]["launched"])

    def test_boundary_violations_cover_unsafe_rename_revert_and_outside(self) -> None:
        modes = ("unsafe", "rename", "unsafe_revert", "outside")
        for mode in modes:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root, fake = self._repository(Path(temp_dir))

                    report = self._run(root, fake, mode=mode, run_id=mode)

                    self.assertEqual(report["status"], "boundary_violation")
                    self.assertEqual(report["exit_code"], 2)
                    self.assertTrue(
                        report["boundary_audit"]["has_boundary_violation"]
                    )
                    if mode == "unsafe_revert":
                        self.assertTrue(report["baseline_audit"]["worktree_clean"])
                        self.assertNotIn(
                            "README.md",
                            report["post_run_audit"]["production_file_changes"],
                        )
                        self.assertIn(
                            "README.md",
                            report["post_run_audit"][
                                "jsonl_production_write_attempts"
                            ],
                        )
                    if mode == "outside":
                        self.assertTrue(
                            report["boundary_audit"]["outside_workspace_attempts"]
                        )

    def test_only_managed_files_are_excluded_in_a_custom_artifact_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))

            report = self._run(
                root,
                fake,
                mode="artifact_extra",
                run_id="artifact-extra",
                out_dir="guarded-output",
            )

            self.assertEqual(report["status"], "boundary_violation")
            self.assertIn(
                "guarded-output/unexpected.py",
                [
                    violation["path"]
                    for violation in report["boundary_audit"]["boundary_violations"]
                ],
            )
            markdown = (root / "guarded-output" / "report.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Return code: `0`", markdown)
            self.assertIn("guarded-output/unexpected.py", markdown)

    def test_nonzero_malformed_empty_and_timeout_have_intentional_statuses(self) -> None:
        cases = [
            ("read_only", {"FAKE_CODEX_EXIT": "7"}, None, "codex_failed", 2),
            ("malformed", {}, None, "audit_incomplete", 2),
            ("partial", {}, None, "audit_incomplete", 2),
            ("empty", {}, None, "audit_incomplete", 2),
            ("timeout", {}, 0.05, "cancelled", 130),
        ]
        for index, (mode, extra_env, timeout, status, exit_code) in enumerate(cases):
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root, fake = self._repository(Path(temp_dir))
                    report = self._run(
                        root,
                        fake,
                        mode=mode,
                        run_id=f"failure-{index}",
                        timeout=timeout,
                        extra_env=extra_env,
                    )
                    self.assertEqual(report["status"], status)
                    self.assertEqual(report["exit_code"], exit_code)
                    if mode == "malformed":
                        self.assertEqual(
                            report["post_run_audit"]["malformed_jsonl_lines"], 1
                        )
                    if mode == "partial":
                        self.assertEqual(report["post_run_audit"]["jsonl_event_count"], 1)
                        self.assertEqual(
                            report["post_run_audit"]["malformed_jsonl_lines"], 1
                        )
                        self.assertIn(
                            "readable before malformed",
                            (
                                root
                                / ".bunya-jido"
                                / "runs"
                                / f"failure-{index}"
                                / "events.jsonl"
                            ).read_text(encoding="utf-8"),
                        )
                    if mode == "timeout":
                        self.assertTrue(report["execution"]["timed_out"])

    def test_keyboard_interrupt_terminates_and_reports_cancelled(self) -> None:
        class InterruptingProcess:
            def __init__(self) -> None:
                self.returncode: int | None = None
                self.calls = 0

            def communicate(self, input=None, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    raise KeyboardInterrupt
                self.returncode = -15
                return None, None

            def terminate(self) -> None:
                self.returncode = -15

            def kill(self) -> None:
                self.returncode = -9

        with tempfile.TemporaryDirectory() as temp_dir:
            root, fake = self._repository(Path(temp_dir))
            environ = dict(os.environ)
            report = _execute_guarded_codex_run(
                root=root,
                task="change application behavior",
                command_prefix=[sys.executable, str(fake)],
                run_id="interrupt",
                now_fn=lambda: FIXED_NOW,
                monotonic_fn=lambda: 10.0,
                environ=environ,
                popen_factory=lambda *args, **kwargs: InterruptingProcess(),
            )

            self.assertEqual(report["status"], "cancelled")
            self.assertEqual(report["exit_code"], 130)
            self.assertTrue(report["execution"]["cancelled"])

    def test_cli_preview_emits_schema_v1_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._repository(Path(temp_dir))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "codex-run",
                        "--root",
                        str(root),
                        "--task",
                        "change application behavior",
                        "--preview",
                        "--codex-executable",
                        sys.executable,
                        "--json",
                    ]
                )
            report = json.loads(stdout.getvalue())

            self.assertEqual(result, 0)
            self.assertEqual(report["schema_version"], "bunya-jido-codex-run-v1")
            self.assertEqual(report["status"], "preview")
            self.assertEqual(report["context"]["decision"], "MATCH")


if __name__ == "__main__":
    unittest.main()
