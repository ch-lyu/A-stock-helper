"""日频原始价格现金账本与独立标记的复权收益代理研究。"""
import math
from dataclasses import asdict, dataclass
from datetime import date

from .data import validate_bars
from .signals import metrics, signals


@dataclass(frozen=True)
class Config:
    initial_cash: float = 100000
    commission: float = 0.0003
    min_commission: float = 5
    transfer_rate: float | None = None
    slippage_bps: float = 5
    participation: float = 0.01
    min_buy: int = 100
    buy_increment: int = 100
    strict: bool = False
    corporate_actions_complete: bool = False

    def __post_init__(self):
        if not math.isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("资金必须为正数")
        if not 0 < self.participation <= 1 or min(self.min_buy, self.buy_increment) < 1:
            raise ValueError("参与率或交易数量设置非法")
        if not isinstance(self.min_buy, int) or not isinstance(self.buy_increment, int):
            raise TypeError("交易数量必须为整数")
        costs = [self.commission, self.min_commission, self.slippage_bps]
        if self.transfer_rate is not None:
            costs.append(self.transfer_rate)
        if any(not math.isfinite(v) or v < 0 for v in costs):
            raise ValueError("成本必须非负且有限")


def fees(notional, side, day, cfg):
    commission = max(cfg.min_commission, notional * cfg.commission)
    transfer_rate = cfg.transfer_rate
    if transfer_rate is None:
        transfer_rate = 0.00001 if day >= "2022-04-29" else 0.00002
    transfer = notional * transfer_rate
    stamp = notional * (0.0005 if day >= "2023-08-28" else 0.001) if side == "sell" else 0
    return {"commission": commission, "transfer_fee": transfer, "stamp_tax": stamp,
            "fees": commission + transfer + stamp}


def quantity_for_buy(budget, price, cap, cfg, day):
    quantity = int(min(budget / price, cap))
    if quantity < cfg.min_buy:
        return 0
    quantity = cfg.min_buy + ((quantity - cfg.min_buy) // cfg.buy_increment) * cfg.buy_increment
    while quantity >= cfg.min_buy:
        notional = price * quantity
        if notional + fees(notional, "buy", day, cfg)["fees"] <= budget:
            return quantity
        quantity -= cfg.buy_increment
    return 0


def ledger_backtest(rows, targets, cfg=None, actions=None):
    cfg = cfg or Config()
    rows = validate_bars([dict(r) for r in rows])
    if len(rows) != len(targets) or any(not math.isfinite(t) or not 0 <= t <= 1 for t in targets):
        raise ValueError("每个日期需要一个 0 到 1 的目标仓位")
    if cfg.strict and (not cfg.corporate_actions_complete or any(
            not r.get("upper_limit") or not r.get("lower_limit") for r in rows)):
        raise ValueError("严格回测需逐日涨跌停价格和已核验的完整公司行动记录")
    events = {}
    trading_dates = {r["date"] for r in rows}
    for event in actions or []:
        day = event["date"]
        date.fromisoformat(day)
        if event.get("pay_date"):
            date.fromisoformat(event["pay_date"])
        if rows[0]["date"] <= day <= rows[-1]["date"] and day not in trading_dates:
            raise ValueError("研究区间公司行动日缺行情，不能静默忽略；补充数据或另行处理")
        if day in events:
            raise ValueError("同日公司行动须合并成一个明确事件")
        ratio = float(event.get("split_ratio", 1))
        dividend = float(event.get("cash_dividend", 0))
        if not math.isfinite(ratio) or not math.isfinite(dividend) or ratio <= 0 or dividend < 0:
            raise ValueError("公司行动比例和分红非法")
        if dividend and (not event.get("pay_date") or event["pay_date"] < day):
            raise ValueError("现金分红必须提供不早于除息日的支付日期")
        if set(event) - {"date", "split_ratio", "cash_dividend", "pay_date"}:
            raise ValueError("不支持的公司行动字段，不能忽略配股等事件")
        events[day] = event
    cash, shares, unsettled_receivables = cfg.initial_cash, 0, []
    fills, rejected, curve = [], [], []
    for i, row in enumerate(rows):
        day, opening = row["date"], row["open"]
        if day in events:
            ev = events[day]
            dividend = shares * float(ev.get("cash_dividend", 0))
            if dividend:
                unsettled_receivables.append((ev["pay_date"], dividend))
            new_shares = shares * float(ev.get("split_ratio", 1))
            if abs(new_shares - round(new_shares)) > 1e-8:
                raise ValueError("碎股公司行动需要明确现金替代方案；当前不支持")
            shares = round(new_shares)
        cash += sum(amount for pay_day, amount in unsettled_receivables if pay_day <= day)
        unsettled_receivables = [(d, v) for d, v in unsettled_receivables if d > day]
        receivable = sum(v for _, v in unsettled_receivables)
        # 首日只记录现金；上一收盘决定下一开盘。每日模型不支持日内买后卖。
        if i:
            wealth = cash + shares * opening + receivable
            target_value = wealth * targets[i-1]
            delta = target_value - shares * opening
            side = "buy" if delta > 1e-8 else "sell"
            tradable = row.get("tradable", True) and row["volume"] > 0
            reason = None
            if not tradable:
                reason = "SUSPENDED_OR_NO_VOLUME"
            elif side == "buy" and row.get("upper_limit") and opening >= row["upper_limit"] - 1e-8:
                reason = "LIMIT_UP"
            elif side == "sell" and row.get("lower_limit") and opening <= row["lower_limit"] + 1e-8:
                reason = "LIMIT_DOWN"
            execution = opening * (1 + (1 if side == "buy" else -1) * cfg.slippage_bps / 10000)
            if not reason and (execution > row["high"] + 1e-8 or execution < row["low"] - 1e-8):
                reason = "SLIPPAGE_OUTSIDE_BAR"
            if not reason and ((row.get("upper_limit") and execution > row["upper_limit"] + 1e-8)
                               or (row.get("lower_limit") and execution < row["lower_limit"] - 1e-8)):
                reason = "SLIPPAGE_OUTSIDE_LIMIT"
            # 日K无法证明开盘成交量：此 cap 仅为当日量近似，报告明确限制。
            cap = int(row["volume"] * cfg.participation)
            if side == "buy":
                qty = quantity_for_buy(min(delta, cash), execution, cap, cfg, day) if delta > 0 else 0
            else:
                qty = min(shares, cap, int(max(0, -delta) / execution + 1e-8))
                if qty != shares:
                    qty = (qty // cfg.buy_increment) * cfg.buy_increment
                if qty < cfg.min_buy and qty != shares:
                    qty = 0
            if reason and abs(delta) >= cfg.min_buy * opening:
                rejected.append({"date": day, "side": side, "reason": reason})
            elif qty and not reason:
                notional = qty * execution
                cost = fees(notional, side, day, cfg)
                if side == "buy":
                    cash -= notional + cost["fees"]
                    shares += qty
                else:
                    cash += notional - cost["fees"]
                    shares -= qty
                if cash < -1e-7:
                    raise ValueError("费用导致现金为负；降低卖出最小费用或增加现金")
                cash = max(0, cash)
                fills.append({"date": day, "signal_date": rows[i-1]["date"], "side": side,
                              "quantity": qty, "price": execution, "notional": notional, **cost})
        curve.append({"date": day, "cash": cash, "shares": shares, "receivable": receivable,
                      "equity": cash + shares * row["close"] + receivable})
    return {"mode": "RAW_PRICE_LEDGER", "status": "CONSTRAINED_DAILY_SIMULATION" if cfg.strict else "PROVISIONAL",
            "config": asdict(cfg), "metrics": metrics(curve, cfg.initial_cash), "fills": fills,
            "rejections": rejected, "equity": curve,
            "limitations": ["日K开盘价/当日量无法证明订单队列与开盘可成交量；开盘涨停买/跌停卖保守拒绝",
                            "分红按税前权益处理；持有期股息税、配股、退市结算需另行建模",
                            "末日持仓按收盘标记，未强制平仓；没有把浮盈计为已实现利润"]}


def proxy_backtest(rows, targets, cost_bps=15, initial=100000):
    """复权收益代理：昨日收盘目标在下一开盘变仓，无真实股数/现金账本。"""
    rows = validate_bars([dict(r) for r in rows])
    if len(rows) != len(targets) or any(not math.isfinite(t) or not 0 <= t <= 1 for t in targets):
        raise ValueError("非法目标仓位")
    if not math.isfinite(cost_bps) or not 0 <= cost_bps < 10000 or not math.isfinite(initial) or initial <= 0:
        raise ValueError("非法成本或资金")
    wealth, position, curve, changes = initial, 0, [], []
    for i, r in enumerate(rows):
        if i:
            desired = targets[i-1]
            # 昨日持仓经历隔夜，今天新持仓经历开盘到收盘；成本按变仓比例扣减。
            overnight = r["open"] / rows[i-1]["close"] - 1
            overnight_growth = 1 + position * overnight
            wealth *= overnight_growth
            position = position * (1 + overnight) / overnight_growth
            wealth *= 1 - abs(desired-position) * cost_bps / 10000
            intraday = r["close"] / r["open"] - 1
            intraday_growth = 1 + desired * intraday
            wealth *= intraday_growth
            if abs(desired-position) > 1e-12:
                changes.append({"date": r["date"], "signal_date": rows[i-1]["date"],
                                "from": position, "to": desired})
            position = desired * (1 + intraday) / intraday_growth
        curve.append({"date": r["date"], "equity": wealth, "exposure": position})
    return {"mode": "ADJUSTED_RETURN_PROXY", "status": "RESEARCH_ONLY_NOT_EXECUTION_VALIDATED",
            "cost_bps_per_side": cost_bps, "metrics": metrics(curve, initial), "equity": curve,
            "exposure_changes": changes,
            "limitations": ["复权收益代理，没有实际股数、手数、最小佣金、涨跌停队列或停牌成交模型",
                            "供应商复权与分红再投资方法未独立核验；不能称准确总回报",
                            "指定标的便利样本；不能宣称全市场选股收益"]}


def validate_strategy(rows, strategy="ma", train_end="2021-12-31", validation_end="2024-12-31",
                      costs=(15, 30, 60), candidates=((10, 60), (20, 120), (50, 250))):
    if not train_end < validation_end < rows[-1]["date"]:
        raise ValueError("必须有按时间分离的训练、验证和最终留出段")
    partitions = [[i for i, r in enumerate(rows) if condition(r["date"])] for condition in
                  (lambda d: d <= train_end, lambda d: train_end < d <= validation_end,
                   lambda d: d > validation_end)]
    if min(map(len, partitions)) < 60:
        raise ValueError("每段至少需要60根行情；不能用极短留出段宣称验证")
    def evaluate(target, indices, cost):
        # 开始日仅初始化现金，之前历史只用于形成指标；不继承优化期间的资金。
        return proxy_backtest([rows[i] for i in indices], [target[i] for i in indices], cost)
    scored = []
    for fast, slow in candidates:
        target = signals(rows, strategy, fast, slow)
        train = evaluate(target, partitions[0], costs[0])["metrics"]
        val = evaluate(target, partitions[1], costs[0])["metrics"]
        scored.append({"fast": fast, "slow": slow, "train": train, "validation": val})
    # 参数选择只看验证段，最终留出不参与排序；一次三候选，完整登记。
    chosen = max(scored, key=lambda x: x["validation"]["sharpe_rf0"]
                 if x["validation"]["sharpe_rf0"] is not None else -float("inf"))
    target = signals(rows, strategy, chosen["fast"], chosen["slow"])
    heldout = {str(c): evaluate(target, partitions[2], c)["metrics"] for c in costs}
    benchmark = evaluate([1] * len(rows), partitions[2], costs[0])["metrics"]
    return {"strategy": strategy, "mode": "ADJUSTED_RETURN_PROXY", "candidates": scored,
            "selected": {k: chosen[k] for k in ("fast", "slow")}, "trial_count": len(scored),
            "train_end": train_end, "validation_end": validation_end, "heldout_cost_stress": heldout,
            "heldout_buyhold": benchmark, "status": "RESEARCH_ONLY_NOT_EXECUTION_VALIDATED",
            "selection_rule": "validation Sharpe rf0; never heldout",
            "limitations": ["当前固定时间三段测试，不是滚动训练或全市场PIT选股",
                            "再次按留出结果修改参数，会污染该留出集，必须登记并获取新的未见样本"]}
