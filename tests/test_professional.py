import copy
import json
import math
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from astock.data import write_dataset
from astock.finance import valuation_review
from astock.financial_audit import financial_audit
from astock.risk import portfolio_risk, risk_statistics

ROOT = Path(__file__).resolve().parents[1]


class RiskTests(unittest.TestCase):
    def test_identical_assets_cash_scaling_and_contributions(self):
        seq = [-0.02, 0.01, 0.03, -0.01] * 20
        full = risk_statistics({"a": seq}, {"a": 1})
        half = risk_statistics({"a": seq, "b": seq}, {"a": 0.2, "b": 0.3})
        self.assertAlmostEqual(half["correlation"]["a"]["b"], 1)
        self.assertAlmostEqual(half["annualized_volatility"], full["annualized_volatility"] * 0.5)
        self.assertAlmostEqual(sum(half["annualized_risk_contribution"].values()), half["annualized_volatility"])
        self.assertAlmostEqual(half["historical_var_1d"], 0.01)
        self.assertGreaterEqual(half["historical_es_1d"], half["historical_var_1d"])

    def test_perfect_hedge_and_zero_variance_have_no_nan(self):
        seq = [-0.02, 0.01] * 40
        result = risk_statistics({"a": seq, "b": [-x for x in seq]}, {"a": 0.5, "b": 0.5})
        self.assertAlmostEqual(result["correlation"]["a"]["b"], -1)
        self.assertAlmostEqual(result["annualized_volatility"], 0)
        self.assertIsNone(result["annualized_risk_contribution"]["a"])
        constant = risk_statistics({"a": [0.0] * 60}, {"a": 0.5})
        self.assertIsNone(constant["correlation"]["a"]["a"])
        json.dumps(constant, allow_nan=False)

    def test_short_nonfinite_and_leverage_rejected(self):
        for returns, weights in (({"a": [0.1] * 59}, {"a": 1}),
                                 ({"a": [math.nan] * 60}, {"a": 1}),
                                 ({"a": [0.1] * 60}, {"a": 1.1})):
            with self.assertRaises(ValueError):
                risk_statistics(returns, weights)

    def test_native_return_intervals_and_snapshot_exclude_future(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            start = date(2024, 1, 1)
            def bars(skip=None):
                return [{"date": (start + timedelta(days=i)).isoformat(), "open": 10 + i * 0.1,
                         "high": 11 + i * 0.1, "low": 9 + i * 0.1, "close": 10 + i * 0.1,
                         "volume": 10000} for i in range(85) if i != skip]
            for code, skip in (("sh600519", None), ("sh600036", 5)):
                write_dataset(p / f"{code}.csv", bars(skip),
                              {"source": "synthetic_test_fixture", "symbol": code, "price_mode": "qfq"})
            (p / "h.csv").write_text("symbol,market_value,sector,currency,as_of\n"
                                    "600519,30,消费,CNY,2024-03-20\n600036,20,银行,CNY,2024-03-20\n"
                                    "cash,50,现金,CNY,2024-03-20\n", encoding="utf-8")
            (p / "series.json").write_text(json.dumps({"series": {"600519": "sh600519.csv",
                                                                  "600036": "sh600036.csv"}}))
            r = portfolio_risk(p / "h.csv", p / "series.json")
            ends = [x["end"] for x in r["return_intervals"]]
            self.assertNotIn("2024-01-06", ends)
            self.assertNotIn("2024-01-07", ends)
            self.assertLessEqual(max(ends), "2024-03-20")
            self.assertEqual(r["cash_weight"], 0.5)
            self.assertGreater(r["rows_after_snapshot_excluded"]["sh600519"], 0)


class ValuationReviewTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((ROOT / "examples/dcf.json").read_text())
        self.prob = {"bear": 0.2, "base": 0.6, "bull": 0.2}

    def test_sensitivity_monotonicity_and_reverse_identity(self):
        r = valuation_review(self.model, self.prob, [0.09, 0.1, 0.11], [0.01, 0.02])
        vals = { (v["wacc"], v["terminal_growth"]): v["value_per_share"] for v in r["sensitivity"]}
        self.assertGreater(vals[(0.09, 0.02)], vals[(0.1, 0.02)])
        self.assertGreater(vals[(0.1, 0.02)], vals[(0.1, 0.01)])
        p = r["cases"]["base"]["value_per_share"]
        reverse = valuation_review(self.model, self.prob, [0.1], [0.02], p)
        self.assertAlmostEqual(reverse["reverse_uniform_fcff"]["uniform_fcff_multiplier"], 1)
        self.assertEqual(r["status"], "DRAFT_REVIEW")

    def test_bad_probabilities_and_different_equity_bridge_rejected(self):
        with self.assertRaises(ValueError):
            valuation_review(self.model, {"bear": 0.2, "base": 0.5, "bull": 0.2}, [0.1], [0.02])
        self.model["bull"]["shares"] *= 2
        with self.assertRaises(ValueError):
            valuation_review(self.model, self.prob, [0.1], [0.02])

    def test_invalid_sensitivity_cell_does_not_produce_fake_value(self):
        r = valuation_review(self.model, self.prob, [0.02], [0.02])
        self.assertIsNone(r["sensitivity"][0]["value_per_share"])


class FinancialAuditTests(unittest.TestCase):
    def setUp(self):
        self.model = {"symbol": "600519", "as_of": "2026-10-14", "currency": "CNY", "unit": "CNY",
                      "industry": "ordinary_nonfinancial", "periods": [
                          {"period": f"{y}-12-31", "disclosed_at": f"{y+1}-04-01",
                           "source_url": "https://example.org/teaching-fixture", "comparable": True,
                           "revenue": 100, "receivables": 40, "equity": 100, "goodwill": 40,
                           "cash": 50, "restricted_cash": 20, "net_profit": 10,
                           "nonrecurring_profit": 4, "ocf": -1, "audit_opinion": "qualified"}
                          for y in (2023, 2024, 2025)]}

    def test_triggered_is_screening_not_fraud(self):
        r = financial_audit(self.model)
        self.assertEqual(r["triggered_count"], 6)
        self.assertEqual(r["status"], "SCREEN_ONLY_REQUIRES_FILINGS_REVIEW")

    def test_missing_is_unavailable_not_zero_or_pass(self):
        model = copy.deepcopy(self.model)
        model["periods"][-1]["receivables"] = None
        model["periods"] = model["periods"][-1:]
        r = financial_audit(model)
        self.assertEqual(r["findings"][0]["status"], "UNAVAILABLE")
        self.assertEqual(r["findings"][4]["status"], "UNAVAILABLE")

    def test_nonconsecutive_years_do_not_satisfy_three_year_rule(self):
        model = copy.deepcopy(self.model)
        model["periods"][0].update({"period": "2021-12-31", "disclosed_at": "2022-04-01"})
        self.assertEqual(financial_audit(model)["findings"][4]["status"], "UNAVAILABLE")

    def test_industry_vintage_comparability_and_nonfinite_guards(self):
        for mutation in (lambda m: m.update(industry="bank"),
                         lambda m: m.update(as_of="2024-01-01"),
                         lambda m: m["periods"][-1].update(comparable=False),
                         lambda m: m["periods"][-1].update(revenue=float("nan"))):
            m = copy.deepcopy(self.model)
            mutation(m)
            with self.assertRaises(ValueError):
                financial_audit(m)


if __name__ == "__main__":
    unittest.main()
