import unittest
from datetime import date, timedelta

from astock.backtest import proxy_backtest
from astock.signals import signals


class SignalTests(unittest.TestCase):
    def test_fractional_exposure_drifts_with_prices_and_rebalances(self):
        rows = [{"date": "2024-01-02", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 100},
                {"date": "2024-01-03", "open": 10, "high": 20, "low": 10, "close": 20, "volume": 100},
                {"date": "2024-01-04", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 100}]
        result = proxy_backtest(rows, [0.5, 0.5, 0.5], cost_bps=0)
        self.assertAlmostEqual(result["equity"][1]["exposure"], 2/3)
        self.assertAlmostEqual(result["equity"][-1]["equity"], 100000)
        costly = proxy_backtest(rows, [0.5, 0.5, 0.5], cost_bps=15)
        self.assertLess(costly["equity"][-1]["equity"], 100000)

    def test_prefix_signals_do_not_repaint(self):
        prices = [10 + (i % 7)*0.2 + i*0.01 for i in range(100)]
        rows = [{"date": (date(2024, 1, 1)+timedelta(days=i)).isoformat(), "open": p,
                 "high": p+1, "low": p-1, "close": p, "volume": 10000} for i, p in enumerate(prices)]
        for strategy in ("ma", "breakout"):
            full = signals(rows, strategy, 5, 20)
            for cutoff in (21, 50, 99):
                self.assertEqual(full[:cutoff], signals(rows[:cutoff], strategy, 5, 20))

    def test_proxy_next_open_does_not_capture_pre_entry_gap(self):
        rows = [{"date": "2024-01-02", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 100},
                {"date": "2024-01-03", "open": 20, "high": 22, "low": 20, "close": 22, "volume": 100}]
        result = proxy_backtest(rows, [1, 1], cost_bps=0, initial=10000)
        self.assertAlmostEqual(result["metrics"]["total_return"], 0.1)
