import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reference_reader", ROOT / "skills/a-share-assistant/scripts/references.py")
READER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READER)
PRIMARY = ROOT / "skills/a-share-assistant"


class ReferenceTests(unittest.TestCase):
    def test_all_archives_and_coverage_reconcile(self):
        catalog = json.loads((PRIMARY / "references/professional-catalog.json").read_text())
        if catalog.get("distribution_profile") == "PUBLIC_SOURCE_LINKS_ONLY":
            self.skipTest("公开源不附原始参考包/私人目录；完整资料的指纹验收见私有交付")
        entries = [e for e in catalog["entries"] if e.get("archive")]
        self.assertEqual(len(entries), 34)
        with tempfile.TemporaryDirectory() as tmp:
            for e in entries:
                r = READER.unpack(e, Path(tmp) / e["name"], PRIMARY)
                self.assertEqual(r["status"], "REFERENCE_ONLY_NOT_EXECUTED")
                self.assertTrue((Path(r["directory"]) / "LICENSE").is_file())
        coverage = json.loads((PRIMARY / "references/coverage.json").read_text())
        self.assertEqual(len(coverage["entries"]), 484)
        self.assertEqual(sum(coverage["summary"].values()), 484)
        self.assertEqual(coverage["summary"]["CURATED_REFERENCE_ARCHIVE"], 34)
        self.assertEqual(coverage["summary"]["BLOCKED_KNOWN_ISSUES"], 1)
        self.assertEqual(coverage["summary"]["MISSING_SOURCE"], 7)

    def test_disabled_and_tampered_archive_refused(self):
        catalog = json.loads((PRIMARY / "references/professional-catalog.json").read_text())
        blocked = next(x for x in catalog["entries"] if x["runtime_status"] == "BLOCKED")
        with self.assertRaises(ValueError):
            READER.unpack(blocked, root=PRIMARY)
        e = dict(catalog["entries"][0], archive_sha256="0" * 64)
        with self.assertRaises(ValueError):
            READER.unpack(e, root=PRIMARY)

    def test_archive_paths_and_existing_user_directory_are_protected(self):
        catalog = json.loads((PRIMARY / "references/professional-catalog.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            existing = p / "existing"
            existing.mkdir()
            (existing / "keep.txt").write_text("user data")
            with self.assertRaises(ValueError):
                READER.unpack(catalog["entries"][0], existing, PRIMARY)
            self.assertEqual((existing / "keep.txt").read_text(), "user data")
            archive = p / "bad.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../escaped.py", "raise SystemExit('must not execute')")
            e = {"name": "bad", "archive": "bad.zip", "archive_sha256":
                 hashlib.sha256(archive.read_bytes()).hexdigest(), "instructions_sha256": "0" * 64}
            with self.assertRaises(ValueError):
                READER.unpack(e, p / "bad", p)
            self.assertFalse((p / "escaped.py").exists())
            self.assertFalse((p / "bad").exists())


if __name__ == "__main__":
    unittest.main()
