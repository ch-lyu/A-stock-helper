"""仅依赖已收盘前缀的透明信号；不承诺存在超额收益。"""
import math
import statistics
from itertools import pairwise


def signals(rows, strategy="ma", fast=20, slow=120):
    if not 1 <= fast < slow:
        raise ValueError("参数必须满足 1 <= fast < slow")
    if strategy not in ("ma", "breakout", "buyhold"):
        raise ValueError("未知策略")
    closes = [r["close"] for r in rows]
    result, position = [], 0
    for i, price in enumerate(closes):
        if strategy == "buyhold":
            position = 1
        elif i + 1 < slow:
            position = 0
        elif strategy == "ma":
            position = int(statistics.mean(closes[i-fast+1:i+1]) > statistics.mean(closes[i-slow+1:i+1]))
        else:
            # 当前收盘与前 slow 根高点比较；退出看前 fast 根低点。
            if i >= slow and price > max(r["high"] for r in rows[i-slow:i]):
                position = 1
            elif i >= fast and price < min(r["low"] for r in rows[i-fast:i]):
                position = 0
        result.append(position)
    return result


def metrics(equity, initial):
    if not equity or initial <= 0:
        raise ValueError("净值与起始资金必须有效")
    levels = [initial] + [r["equity"] for r in equity]
    returns = [b / a - 1 for a, b in pairwise(levels)]
    std = statistics.stdev(returns) if len(returns) > 1 else 0
    peak, max_dd = initial, 0
    for x in levels:
        peak = max(peak, x)
        max_dd = min(max_dd, x / peak - 1)
    years = len(equity) / 252
    total = levels[-1] / initial - 1
    return {"total_return": total, "cagr": (1 + total)**(1 / years) - 1,
            "sharpe_rf0": statistics.mean(returns) / std * math.sqrt(252) if std else None,
            "max_drawdown": max_dd, "annual_volatility": std * math.sqrt(252),
            "annualization": 252, "risk_free_rate": 0, "observations": len(equity),
            "first_date": equity[0]["date"], "last_date": equity[-1]["date"]}


def technical_snapshot(rows):
    prices = [r["close"] for r in rows]
    last = prices[-1]
    ret = lambda n: last / prices[-n-1] - 1 if len(prices) > n else None
    sma = {str(n): statistics.mean(prices[-n:]) if len(prices) >= n else None for n in (20, 60, 120, 250)}
    daily = [b/a-1 for a, b in zip(prices[-61:], prices[-60:])] if len(prices) > 60 else []
    return {"as_of": rows[-1]["date"], "close": last, "sma": sma,
            "return_20d": ret(20), "return_60d": ret(60), "return_250d": ret(250),
            "volatility_60d": statistics.stdev(daily) * math.sqrt(252) if len(daily) > 1 else None,
            "drawdown_from_250d_high": last / max(prices[-250:]) - 1,
            "interpretation": "趋势描述；不是已验证买卖建议"}
