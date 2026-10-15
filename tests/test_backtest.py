import unittest

from astock.backtest import Config, ledger_backtest


def bar(day, price=10, volume=100000, **kwargs):
    return {"date": day, "open": price, "high": price*1.01, "low": price*0.99,
            "close": price, "volume": volume, **kwargs}


class ExecutionTests(unittest.TestCase):
    def test_missing_in_range_corporate_action_day_cannot_be_silently_ignored(self):
        rows = [bar("2024-01-02", upper_limit=11, lower_limit=9),
                bar("2024-01-03", upper_limit=11, lower_limit=9),
                bar("2024-01-05", 5, upper_limit=5.5, lower_limit=4.5)]
        with self.assertRaisesRegex(ValueError, "公司行动日缺行情"):
            ledger_backtest(rows, [1, 1, 1], Config(strict=True, corporate_actions_complete=True),
                            [{"date": "2024-01-04", "split_ratio": 2}])

    def test_suspension_and_invalid_slippage_do_not_fill(self):
        rows = [bar("2024-01-02"), bar("2024-01-03", volume=0),
                bar("2024-01-04", high=10, low=10)]
        result = ledger_backtest(rows, [1, 1, 1], Config(initial_cash=10000))
        self.assertFalse(result["fills"])
        self.assertEqual([r["reason"] for r in result["rejections"]],
                         ["SUSPENDED_OR_NO_VOLUME", "SLIPPAGE_OUTSIDE_BAR"])

    def test_star_board_accepts_single_share_increment_after_minimum(self):
        rows = [bar("2024-01-02"), bar("2024-01-03")]
        cfg = Config(initial_cash=2010, min_buy=200, buy_increment=1, commission=0,
                     min_commission=0, transfer_rate=0, slippage_bps=0, participation=1)
        result = ledger_backtest(rows, [1, 1], cfg)
        self.assertEqual(result["fills"][0]["quantity"], 201)

    def test_signal_executes_next_day_and_keeps_cash_nonnegative(self):
        rows = [bar("2024-01-02"), bar("2024-01-03"), bar("2024-01-04", 11)]
        result = ledger_backtest(rows, [1, 0, 0], Config(initial_cash=10000, participation=1))
        self.assertEqual([f["date"] for f in result["fills"]], ["2024-01-03", "2024-01-04"])
        self.assertEqual(result["fills"][0]["quantity"], 900)
        self.assertTrue(all(r["cash"] >= 0 for r in result["equity"]))
        self.assertAlmostEqual(result["fills"][1]["stamp_tax"], 4.947525)

    def test_limit_up_buy_and_limit_down_sell_are_blocked(self):
        rows = [bar("2024-01-02"), bar("2024-01-03", 11, upper_limit=11),
                bar("2024-01-04", 10), bar("2024-01-05", 9, lower_limit=9)]
        result = ledger_backtest(rows, [1, 1, 0, 0], Config(initial_cash=10000, participation=1))
        self.assertEqual(len(result["fills"]), 1)
        self.assertEqual(result["fills"][0]["date"], "2024-01-04")
        self.assertEqual([r["reason"] for r in result["rejections"]], ["LIMIT_UP", "LIMIT_DOWN"])

    def test_dividend_is_receivable_until_payment_and_split_preserves_wealth(self):
        rows = [bar("2024-01-02"), bar("2024-01-03"), bar("2024-01-04", 4.5),
                bar("2024-01-05", 4.5)]
        cfg = Config(initial_cash=10000, commission=0, min_commission=0, transfer_rate=0,
                     slippage_bps=0, participation=1)
        result = ledger_backtest(rows, [1, 1, 1, 1], cfg,
                                 [{"date": "2024-01-04", "split_ratio": 2, "cash_dividend": 1,
                                   "pay_date": "2024-01-05"}])
        self.assertEqual(result["equity"][2]["receivable"], 1000)
        self.assertEqual(result["equity"][3]["receivable"], 0)
        self.assertAlmostEqual(result["equity"][2]["equity"], 10000)

    def test_strict_refuses_unverified_corporate_actions_and_limits(self):
        with self.assertRaises(ValueError):
            ledger_backtest([bar("2024-01-02"), bar("2024-01-03")], [1, 1], Config(strict=True))

    def test_future_prices_do_not_change_earlier_fills(self):
        rows = [bar("2024-01-02"), bar("2024-01-03"), bar("2024-01-04", 11)]
        a = ledger_backtest(rows, [1, 0, 1])
        b = ledger_backtest(rows + [bar("2024-01-05", 20)], [1, 0, 1, 0])
        self.assertEqual(a["fills"], b["fills"][:len(a["fills"])])
