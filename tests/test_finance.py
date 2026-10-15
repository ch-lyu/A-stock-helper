import unittest

from astock.finance import dcf_case, single_quarter


class FinanceTests(unittest.TestCase):
    def test_dcf_constant_cashflow_known_perpetuity(self):
        case = {"fcff": [100], "wacc": 0.1, "terminal_growth": 0,
                "net_debt": 200, "shares": 100, "currency": "CNY", "unit": "CNY_and_shares"}
        self.assertAlmostEqual(dcf_case(case)["enterprise_value"], 1000)
        self.assertAlmostEqual(dcf_case(case)["value_per_share"], 8)
        case["terminal_growth"] = 0.1
        with self.assertRaises(ValueError):
            dcf_case(case)

    def test_single_quarter_missing_previous_is_not_zero(self):
        records = [{"period": "2024-03-31", "profit": 10}, {"period": "2024-06-30", "profit": 25},
                   {"period": "2024-12-31", "profit": 100}]
        result = single_quarter(records, "profit")
        self.assertEqual([r["value"] for r in result], [10, 15, None])

