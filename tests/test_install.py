import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_installed_runtime_works_without_source_tree_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            destination = Path(d)
            (destination / "unrelated-skill").mkdir()
            result = installer.install(destination)
            self.assertEqual(result["skills"], 12)
            self.assertEqual(installer.install(destination)["changed"], 0)
            p = subprocess.run([sys.executable, str(destination / "a-share-assistant/scripts/astock.py"),
                                "doctor"], capture_output=True, text=True, cwd=d, check=False)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn('"core": "READY"', p.stdout)
            self.assertTrue((destination / "unrelated-skill").exists())

    def test_local_edits_and_unknown_skill_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            destination = Path(d)
            installer.install(destination)
            p = destination / "a-share-assistant/SKILL.md"
            p.write_text("my edits", encoding="utf-8")
            with self.assertRaises(ValueError):
                installer.install(destination, replace=True)
            self.assertEqual(p.read_text(), "my edits")
        with tempfile.TemporaryDirectory() as d:
            destination = Path(d)
            (destination / "a-share-assistant").mkdir()
            with self.assertRaises(ValueError):
                installer.install(destination)
            self.assertEqual(list(destination.iterdir()), [destination / "a-share-assistant"])

