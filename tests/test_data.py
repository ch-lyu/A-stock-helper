import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from astock.data import (
    load_bars,
    metadata_path,
    normalize_symbol,
    read_metadata,
    shanghai_today,
    write_dataset,
)


class DataContractTests(unittest.TestCase):
    def test_hash_only_metadata_is_not_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.csv"
            p.write_text("date,open,high,low,close,volume\n2024-01-02,10,11,9,10,100\n")
            metadata_path(p).write_text(json.dumps({"sha256": hashlib.sha256(p.read_bytes()).hexdigest()}))
            with self.assertRaisesRegex(ValueError, "必要字段"):
                read_metadata(p)

    def test_metadata_range_and_units_must_match_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.csv"
            meta = write_dataset(p, [{"date": "2024-01-02", "open": 10, "high": 11,
                                      "low": 9, "close": 10, "volume": 100}],
                                 {"symbol": "sh600519", "price_mode": "raw"})
            for field, value in (("rows", 2), ("volume_unit", "lots"), ("price_mode", "unknown")):
                metadata_path(p).write_text(json.dumps({**meta, field: value}))
                with self.assertRaises(ValueError):
                    read_metadata(p)

    def test_shanghai_today_does_not_require_iana_database(self):
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch
        expected = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
        with patch("zoneinfo.ZoneInfo", side_effect=RuntimeError("no timezone database")):
            self.assertEqual(shanghai_today(), expected)

    def test_symbol_identity_disambiguates_shanghai_index(self):
        self.assertEqual(normalize_symbol("000001"), "sz000001")
        self.assertEqual(normalize_symbol("000001.SH"), "sh000001")
        self.assertEqual(normalize_symbol("sh.600519"), "sh600519")
        self.assertEqual(normalize_symbol("920001"), "bj920001")
        with self.assertRaises(ValueError):
            normalize_symbol("贵州茅台")

    def test_csv_rejects_duplicates_and_invalid_ohlc(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("date,open,high,low,close,volume\n2024-01-02,10,9,8,10,100\n")
            with self.assertRaises(ValueError):
                load_bars(p)
            p.write_text("date,open,high,low,close,volume\n2024-01-02,10,11,9,10,100\n" * 2)
            with self.assertRaises(ValueError):
                load_bars(p)
