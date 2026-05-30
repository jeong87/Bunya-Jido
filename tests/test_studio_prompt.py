from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bunya_jido.blueprint import make_blueprint_prompt, prepare_blueprint_workspace
from bunya_jido.cli import main


class StudioPromptTests(unittest.TestCase):
    def test_classic_prepare_remains_default_v1_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")

            result = main(["prepare", "--root", str(root), "--quiet"])
            outdir = root / ".bunya-jido"
            schema = json.loads((outdir / "bunya-jido-blueprint.schema.json").read_text(encoding="utf-8"))
            prompt = (outdir / "BUNYA_JIDO_BLUEPRINT_PROMPT.md").read_text(encoding="utf-8")

            self.assertEqual(result, 0)
            self.assertEqual(schema["properties"]["schema_version"]["const"], "bunya-jido-blueprint-v1")
            self.assertFalse((outdir / "REPOSITORY_THESIS.md").exists())
            self.assertFalse((outdir / "PROJECTIONS.md").exists())
            self.assertFalse((outdir / "SCENARIOS.md").exists())
            self.assertNotIn("Studio Atlas Prompt", prompt)

    def test_studio_prepare_creates_editorial_inputs_and_v2_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")

            result = main(
                ["prepare", "--root", str(root), "--atlas-mode", "studio", "--quiet"]
            )
            outdir = root / ".bunya-jido"
            prompt = (outdir / "BUNYA_JIDO_BLUEPRINT_PROMPT.md").read_text(encoding="utf-8")
            short_prompt = (outdir / "CODEX_ONE_LINER.txt").read_text(encoding="utf-8")
            scenarios = (outdir / "SCENARIOS.md").read_text(encoding="utf-8")
            projections = (outdir / "PROJECTIONS.md").read_text(encoding="utf-8")
            schema = json.loads((outdir / "bunya-jido-blueprint.schema.json").read_text(encoding="utf-8"))

            self.assertEqual(result, 0)
            for name in ("REPOSITORY_THESIS.md", "PROJECTIONS.md", "SCENARIOS.md"):
                self.assertTrue((outdir / name).exists())
            self.assertIn("Bunya-Jido Studio Atlas Prompt", prompt)
            self.assertIn("bunya-jido-blueprint-v2", prompt)
            self.assertIn("validated projection vocabulary", prompt)
            self.assertIn("none_with_reason", prompt)
            self.assertIn("Static overlays permitted", projections)
            self.assertIn("Scenario policy", scenarios)
            self.assertIn("--atlas-mode studio", short_prompt)
            self.assertIn("Studio v2 schema", short_prompt)
            self.assertEqual(schema["properties"]["schema_version"]["const"], "bunya-jido-blueprint-v2")
            self.assertIn("atlas", schema["required"])
            self.assertIn("scenario playback", prompt)
            self.assertNotIn("arrive in later phases", prompt)

    def test_studio_prepare_preserves_existing_intermediate_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outdir = root / ".bunya-jido"
            outdir.mkdir()
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")
            (outdir / "COMPONENTS.md").write_text("authored components\n", encoding="utf-8")
            (outdir / "WORKFLOWS.md").write_text("authored workflows\n", encoding="utf-8")

            paths = prepare_blueprint_workspace(root, atlas_mode="studio", quiet=True)

            self.assertEqual(paths["components"].read_text(encoding="utf-8"), "authored components\n")
            self.assertEqual(paths["workflows"].read_text(encoding="utf-8"), "authored workflows\n")
            self.assertTrue(paths["repository_thesis"].exists())

    def test_unknown_atlas_mode_is_rejected_by_library_api(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported atlas mode"):
            make_blueprint_prompt("fixture", atlas_mode="unsupported")


if __name__ == "__main__":
    unittest.main()
