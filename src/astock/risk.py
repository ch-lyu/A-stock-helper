"""当前持仓权重的历史风险代理；先原生相邻收益，再共同日期对齐。"""
import hashlib
import json
import math
from datetime import date
from itertools import pairwise
from pathlib import Path
from statistics import mean

from .data import load_bars, normalize_symbol, read_metadata
from .research import portfolio


def risk_statistics(returns, weights, confidence=0.95):
    names = list(weights)
    if not names or set(returns) != set(names):
        raise ValueError("持仓与收益证券必须一一对应")
    if not math.isfinite(confidence) or not 0.5 < confidence < 1:
        raise ValueError("置信度须大于0.5且小于1")
    if any(not math.isfinite(w) or w < 0 for w in weights.values()) or sum(weights.values()) > 1 + 1e-10:
        raise ValueError("多头权重非负、和不超过1；不自动归一化")
    n = len(returns[names[0]])
    if n < 60 or any(len(x) != n for x in returns.values()):
        raise ValueError("至少需要60个共同日期收益，全部序列等长")
    if any(not math.isfinite(x) or x < -1 for xs in returns.values() for x in xs):
        raise ValueError("收益须有限且不得低于-100%")
    averages = {name: mean(returns[name]) for name in names}
    cov = {a: {b: sum((x - averages[a]) * (y - averages[b])
                     for x, y in zip(returns[a], returns[b], strict=True)) / (n - 1)
               for b in names} for a in names}
    marginal = {a: sum(cov[a][b] * weights[b] for b in names) for a in names}
    variance = max(0, sum(weights[a] * marginal[a] for a in names))
    sigma = math.sqrt(variance)
    correlation = {a: {b: cov[a][b] / math.sqrt(cov[a][a] * cov[b][b])
                       if cov[a][a] > 0 and cov[b][b] > 0 else None for b in names} for a in names}
    proxy = [sum(weights[a] * returns[a][i] for a in names) for i in range(n)]
    losses = sorted(-r for r in proxy)
    var = losses[math.ceil(confidence * n) - 1]
    tail = [loss for loss in losses if loss >= var]
    return {"observations": n, "weights": weights, "cash_weight": max(0, 1 - sum(weights.values())),
            "annualization": 252, "annualized_volatility": sigma * math.sqrt(252),
            "annualized_covariance": {a: {b: cov[a][b] * 252 for b in names} for a in names},
            "correlation": correlation,
            "annualized_risk_contribution": {a: weights[a] * marginal[a] / sigma * math.sqrt(252)
                                             if sigma else None for a in names},
            "historical_var_1d": var, "historical_es_1d": mean(tail), "tail_observations": len(tail),
            "confidence": confidence, "quantile_method": "nearest_rank_on_signed_losses",
            "loss_convention": "正值为损失；负VaR表示该样本分位仍为收益；不截零，不是最大损失上限",
            "status": "CURRENT_WEIGHT_HISTORICAL_RISK_PROXY_NOT_ACCOUNT_PNL"}


def portfolio_risk(holdings_path, manifest_path):
    snapshot = portfolio(holdings_path)
    date.fromisoformat(snapshot["as_of"])
    path = Path(manifest_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    series = {}
    for name, value in config["series"].items():
        symbol = normalize_symbol(name)
        if symbol in series:
            raise ValueError("收益清单含重复证券别名")
        series[symbol] = value
    stocks = [x for x in snapshot["positions"] if x["symbol"] != "cash" and x["weight"] > 0]
    if not stocks:
        raise ValueError("本命令需要至少一只非零股票持仓；全现金用portfolio快照")
    if set(series) != {x["symbol"] for x in stocks}:
        raise ValueError("需为每只非零股票提供且只提供一份复权CSV")
    window = config.get("window", 252)
    if type(window) is not int or not 60 <= window <= 5000:
        raise ValueError("窗口须为60到5000的整数")
    native, metadata, ignored = {}, {}, {}
    for symbol, filename in series.items():
        csv = path.parent / filename
        meta = read_metadata(csv)
        if meta.get("symbol") != symbol or meta.get("price_mode") not in ("qfq", "hfq"):
            raise ValueError("风险收益需身份一致且通过来源校验的qfq/hfq数据")
        rows = load_bars(csv)
        ignored[symbol] = sum(x["date"] > snapshot["as_of"] for x in rows)
        rows = [x for x in rows if x["date"] <= snapshot["as_of"]]
        native[symbol] = {(a["date"], b["date"]): b["close"] / a["close"] - 1
                          for a, b in pairwise(rows)}
        metadata[symbol] = meta
    # 两端日期都相同才是相同收益区间，避免停牌/缺失日期的跨日收益被当作单日收益。
    common = sorted(set.intersection(*(set(x) for x in native.values())))[-window:]
    if len(common) < 60:
        raise ValueError("共同原生相邻收益不足60期，不能补零或跨缺口拼接")
    result = risk_statistics({s: [native[s][d] for d in common] for s in series},
                             {x["symbol"]: x["weight"] for x in stocks}, config.get("confidence", 0.95))
    result.update({"as_of": snapshot["as_of"], "currency": "CNY", "total_market_value": snapshot["total"],
                   "return_intervals": [{"start": a, "end": b} for a, b in common],
                   "input_metadata": metadata, "rows_after_snapshot_excluded": ignored,
                   "holdings_sha256": hashlib.sha256(Path(holdings_path).read_bytes()).hexdigest(),
                   "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "limitations": ["按当前权重每日再平衡、现金收益为零；不是实际历史持仓或账户盈亏",
                                   "使用复权价格代理，未独立核验完整总回报、税费或成交约束",
                                   "停牌/缺失会改变样本；收益起止日期交集不等于已核交易日历",
                                   "历史尾部样本有限，不预测未来，不覆盖极端流动性及相关性突变"]})
    result["historical_var_1d_cny"] = result["historical_var_1d"] * snapshot["total"]
    result["historical_es_1d_cny"] = result["historical_es_1d"] * snapshot["total"]
    return result
