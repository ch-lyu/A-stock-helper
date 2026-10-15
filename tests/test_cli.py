import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from astock.cli import main
from astock.data import write_dataset
from astock.research import compare_data


class CommandTests(unittest.TestCase):
    def test_two_undeclared_csvs_cannot_be_claimed_as_cross_verified(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            for p in (a, b):
                p.write_text("date,open,high,low,close,volume\n2024-01-02,10,11,9,10,100\n")
            with self.assertRaisesRegex(ValueError, "元数据"):
                compare_data(a, b)

    def test_modified_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.csv"
            write_dataset(p, [{"date": "2024-01-02", "open": 10, "high": 11,
                               "low": 9, "close": 10, "volume": 100}],
                          {"symbol": "sh600519", "price_mode": "raw"})
            p.write_text(p.read_text().replace("10.0", "10.1"))
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(main(["audit", str(p)]), 2)
            self.assertIn("哈希", json.loads(output.getvalue())["message"])

    def test_cash_concentration_and_currency_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "holdings.csv"
            p.write_text("symbol,market_value,sector,currency,as_of\n600519,600,消费,CNY,2024-01-02\n"
                         "cash,400,现金,CNY,2024-01-02\n", encoding="utf-8")
            out = Path(d) / "result.json"
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["portfolio", str(p), "--out", str(out)]), 0)
            self.assertEqual(json.loads(out.read_text())["largest_stock_weight"], 0.6)
            summary = json.loads(output.getvalue())
            self.assertAlmostEqual(summary["portfolio_summary"]["hhi"], 0.36)
            self.assertAlmostEqual(summary["portfolio_summary"]["cash_weight"], 0.4)
            self.assertIn("现金不计入", summary["portfolio_summary"]["hhi_definition"])
            self.assertNotIn("metrics", summary)
