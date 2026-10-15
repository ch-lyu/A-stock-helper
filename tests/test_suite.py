import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


EXPORT = module("scripts/export_suite.py", "export_suite_test")
RECORDS = module("skills/a-share-assistant/scripts/records.py", "records_test")


class SuiteTests(unittest.TestCase):
    def test_self_contained_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a, b = base / "a.zip", base / "b.zip"
            EXPORT.build(a)
            EXPORT.build(b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as z:
                z.extractall(base / "extracted")
            suite = base / "extracted/a-share-family-suite"
            manifest = json.loads((suite / "manifest.json").read_text())
            self.assertEqual(len(manifest["modules"]), 12)
            for path, sha in manifest["files"].items():
                self.assertEqual(hashlib.sha256((suite / path).read_bytes()).hexdigest(), sha)
            for wrapper in (suite / "scripts/astock.py", suite / "modules/a-share-assistant/scripts/astock.py"):
                result = subprocess.run([sys.executable, str(wrapper), "doctor"], cwd=base,
                                        text=True, capture_output=True, check=True)
                self.assertEqual(json.loads(result.stdout)["core"], "READY")
            result = subprocess.run([sys.executable, str(suite / "scripts/astock.py"), "valuation",
                                     str(suite / "assets/examples/dcf.json"), "--out", str(base / "dcf.json")],
                                    cwd=base, text=True, capture_output=True, check=True)
            self.assertTrue((base / "dcf.json").is_file(), result.stdout)
            for original in (ROOT / "vendor/financial-services").rglob("*"):
                if original.is_file():
                    self.assertEqual(original.read_bytes(),
                                     (suite / "vendor/financial-services" / original.relative_to(
                                         ROOT / "vendor/financial-services")).read_bytes())

    def test_link_and_path_rejection(self):
        payload = EXPORT.collect()
        payload["SKILL.md"] += b"\n[missing](gone.md)\n"
        with self.assertRaises(ValueError):
            EXPORT.validate_payload(payload)
        payload = EXPORT.collect()
        payload["../private.json"] = b"{}"
        with self.assertRaises(ValueError):
            EXPORT.validate_payload(payload)

    def test_preserves_all_original_modules(self):
        payload = EXPORT.collect()
        for path in (ROOT / "skills").glob("*/SKILL.md"):
            self.assertEqual(payload["modules/" + path.parent.name + "/SKILL.md"], path.read_bytes())


class RecordTests(unittest.TestCase):
    def test_revisions_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp, RECORDS.connect(Path(tmp) / "r.sqlite") as db:
            self.assertEqual(RECORDS.put(db, "profile", {"horizon": None})["revision"], 1)
            self.assertTrue(RECORDS.put(db, "profile", {"horizon": None})["unchanged"])
            self.assertEqual(RECORDS.put(db, "profile", {"horizon": "用户已确认"})["revision"], 2)
            self.assertEqual(len(RECORDS.rows(db)), 2)

    def test_new_process_handoff(self):
        script = ROOT / "skills/a-share-assistant/scripts/records.py"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            data = base / "input.json"
            data.write_text('{"fixture": true}', encoding="utf-8")
            def run(store, *args):
                p = subprocess.run([sys.executable, str(script), "--store", str(store), *args],
                                   text=True, capture_output=True, check=True, cwd=tmp)
                return json.loads(p.stdout)
            left, right = base / "first/r.sqlite", base / "second/r.sqlite"
            run(left, "put", "thesis:600519.SH", str(data))
            first = run(left, "get", "thesis:600519.SH")
            handoff = base / "handoff.json"
            run(left, "export", "--out", str(handoff))
            run(right, "import", str(handoff))
            self.assertEqual(first, run(right, "get", "thesis:600519.SH"))

    def test_tampering_and_conflict_are_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            with RECORDS.connect(Path(tmp) / "one.sqlite") as db:
                RECORDS.put(db, "profile", {"fixture": 1})
                records = RECORDS.rows(db)
            with RECORDS.connect(Path(tmp) / "two.sqlite") as db:
                RECORDS.put(db, "profile", {"fixture": 2})
                package = {"schema": "a-share-records/1", "records": records}
                with self.assertRaises(ValueError):
                    RECORDS.restore(db, package)
                self.assertEqual(RECORDS.rows(db)[0]["value"], {"fixture": 2})
                records[0]["value"]["fixture"] = 100
                with self.assertRaises(ValueError):
                    RECORDS.restore(db, package)
                self.assertEqual(len(RECORDS.rows(db)), 1)

    def test_invalid_keys_and_nonfinite(self):
        with self.assertRaises(ValueError):
            RECORDS.check_key("../private")
        with self.assertRaises(ValueError):
            RECORDS.canonical({"value": float("nan")})


if __name__ == "__main__":
    unittest.main()
