"""给 AI 的证据包与面向家庭用户的中文计算报告。"""
import csv
import json
import math
from pathlib import Path

from .data import audit, normalize_symbol
from .signals import technical_snapshot


def pct(value):
    return "缺失" if value is None else f"{value:.2%}"


def analyze(rows, metadata, title=None):
    snap = technical_snapshot(rows)
    symbol = metadata.get("symbol", "未核证券身份")
    text = f"# {title or symbol}｜行情证据与研究清单\n\n"
    text += f"数据截至 **{snap['as_of']}**；来源：{metadata.get('source', '未核')}；"
    text += f"价格口径：**{metadata.get('price_mode', 'unknown')}**。不是实时行情。\n\n"
    text += "| 项目 | 数值 |\n|---|---:|\n"
    text += f"| 收盘价（元，按所标价格口径） | {snap['close']:.3f} |\n"
    for n, value in snap["sma"].items():
        text += f"| {n} 日均线 | {value:.3f} |\n" if value is not None else f"| {n} 日均线 | 缺失 |\n"
    for name, key in (("20日涨跌", "return_20d"), ("60日涨跌", "return_60d"),
                      ("250日涨跌", "return_250d"), ("近250日收盘高点回撤", "drawdown_from_250d_high")):
        text += f"| {name} | {pct(snap[key])} |\n"
    ma = snap["sma"]["120"]
    state = "样本不足" if ma is None else "高于" if snap["close"] > ma else "低于"
    text += f"\n当前收盘{state}120日均线。这是趋势描述，不是独立买卖依据。\n\n"
    text += "## 下一步核查\n\n"
    text += "1. 查最新年报、季报和重大公告，记录公告日、报告期、原文链接。\n"
    text += "2. 比较营收、归母利润、扣非利润和经营现金流，解释非经常性损益与应收/存货变化。\n"
    text += "3. 按行业选择估值：银行看资产质量与ROE/PB；周期企业做盈利归一化；稳定现金流可做DCF。\n"
    text += "4. 写出上涨需要的证据、基本情景、证伪条件和需要等待的信息。\n"
    text += "5. 结合持仓集中度与家庭资金用途，核实承受能力后讨论仓位。\n\n"
    text += "## 未完成的证据\n\n财报、实时估值、新闻、公告、证券名称和历史完整性未由本行情命令自动核实。"
    text += "不得把此报告改称完整基本面研报。新闻和财报可用独立命令补充，AI再按技能整理。\n"
    return {"snapshot": snap, "metadata": metadata, "report": text,
            "status": "TECHNICAL_EVIDENCE_ONLY"}


def screen(paths):
    from .data import load_bars, read_metadata
    result = []
    for path in paths:
        rows, meta = load_bars(path), read_metadata(path)
        snap = technical_snapshot(rows)
        ma = snap["sma"]["120"]
        result.append({"path": str(path), "symbol": meta.get("symbol"), "as_of": snap["as_of"],
                       "price_mode": meta.get("price_mode"), "above_ma120": None if ma is None else snap["close"] > ma,
                       "momentum_60d": snap["return_60d"], "volatility_60d": snap["volatility_60d"]})
    dates = {r["as_of"] for r in result}
    modes = {r["price_mode"] for r in result}
    if len(dates) != 1 or len(modes) != 1 or "unknown" in modes:
        raise ValueError("筛选需要同一截止日期和已核价格口径，不能直接比较过期或不一致样本")
    result.sort(key=lambda r: r["momentum_60d"] if r["momentum_60d"] is not None else -float("inf"), reverse=True)
    return {"status": "WATCHLIST_ONLY_NOT_WHOLE_MARKET", "ranking": result,
            "rule": "60日动量排序；120日均线状态与波动率为描述，不合成主观胜率"}


def portfolio(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("空持仓文件")
    positions, seen = [], set()
    dates = {r.get("as_of") for r in rows}
    if len(dates) != 1 or not next(iter(dates)):
        raise ValueError("持仓必须有同一 as_of 快照日期")
    for r in rows:
        symbol = "cash" if r["symbol"].lower() == "cash" else normalize_symbol(r["symbol"])
        if symbol in seen:
            raise ValueError("重复证券请先合并账户，避免重复统计")
        seen.add(symbol)
        if r.get("currency") != "CNY":
            raise ValueError("本版持仓只接受 CNY；多币种需先核汇率")
        value = float(r["market_value"])
        if not math.isfinite(value) or value < 0:
            raise ValueError("非法持仓市值")
        positions.append({"symbol": symbol, "market_value": value, "sector": r.get("sector") or "未知"})
    total = sum(r["market_value"] for r in positions)
    if total <= 0:
        raise ValueError("总市值必须大于零")
    sectors = {}
    for r in positions:
        r["weight"] = r["market_value"] / total
        sectors[r["sector"]] = sectors.get(r["sector"], 0) + r["weight"]
    stocks = [r for r in positions if r["symbol"] != "cash"]
    return {"as_of": next(iter(dates)), "currency": "CNY", "total": total,
            "positions": sorted(positions, key=lambda r: r["weight"], reverse=True), "sector_weights": sectors,
            "largest_stock_weight": max((r["weight"] for r in stocks), default=0),
            "cash_weight": sum(r["weight"] for r in positions if r["symbol"] == "cash"),
            "hhi": sum(r["weight"]**2 for r in stocks),
            "hhi_definition": "股票权重平方和；分母含现金，现金不计入平方和，股票权重不重新归一化",
            "limitations": ["使用用户提供市值，未查询证券账户；行业标签未独立核验",
                            "集中度不等于完整风险：相关性、家庭其他资产、负债和资金用途需另核"]}


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def compare_data(left, right, tolerance=0.02):
    from .data import load_bars, read_metadata
    a, b = read_metadata(left), read_metadata(right)
    if not a.get("symbol") or not b.get("symbol") or a.get("price_mode") == "unknown" or b.get("price_mode") == "unknown":
        raise ValueError("交叉核验需要完整已声明的来源元数据")
    if a.get("symbol") != b.get("symbol") or a.get("price_mode") != b.get("price_mode"):
        raise ValueError("交叉核验必须是同证券、同复权口径")
    x, y = {r["date"]: r for r in load_bars(left)}, {r["date"]: r for r in load_bars(right)}
    common = sorted(x.keys() & y.keys())
    if not common:
        raise ValueError("没有重合交易日期")
    differences = [{"date": d, "column": k, "left": x[d][k], "right": y[d][k]}
                   for d in common for k in ("open", "high", "low", "close")
                   if abs(x[d][k]-y[d][k]) > tolerance]
    return {"overlap": len(common), "only_left": sorted(x.keys()-y.keys()),
            "only_right": sorted(y.keys()-x.keys()), "differences": differences,
            "absolute_price_tolerance": tolerance, "status": "DIFFERENCES" if differences else "MATCH_ON_OVERLAP",
            "volume_comparison": "NOT_IMPLEMENTED", "left": audit(left), "right": audit(right)}
