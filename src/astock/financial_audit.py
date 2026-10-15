"""非金融企业年度财报线索初筛；阈值不等于审计结论或造假判断。"""
import math
from datetime import date
from itertools import pairwise
from urllib.parse import urlparse

from .data import normalize_symbol


def financial_audit(model):
    symbol = normalize_symbol(model["symbol"])
    as_of = date.fromisoformat(model["as_of"])
    if model.get("currency") != "CNY" or model.get("unit") != "CNY":
        raise ValueError("所有财务金额须为人民币元，不能混用万/亿")
    if model.get("industry") != "ordinary_nonfinancial":
        raise ValueError("本初筛仅适用于明确声明的普通非金融企业；银行/保险/券商等需专门适配")
    rows, seen = [], set()
    fields = ("revenue", "receivables", "inventory", "goodwill", "equity", "cash", "restricted_cash",
              "net_profit", "ocf", "nonrecurring_profit")
    for row in model["periods"]:
        period, disclosure = date.fromisoformat(row["period"]), date.fromisoformat(row["disclosed_at"])
        if period.month != 12 or period.day != 31 or period in seen or disclosure <= period or disclosure > as_of:
            raise ValueError("需唯一自然年度、期后且不晚于截止日的实际披露日期")
        seen.add(period)
        url = urlparse(row["source_url"])
        if url.scheme not in ("http", "https") or not url.netloc:
            raise ValueError("每个报告期需可核原始来源URL；程序不替代原文核读")
        for key in fields:
            value = row.get(key)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError("财务金额必须为有限数或null")
            if value is not None and key in ("revenue", "receivables", "inventory", "goodwill", "cash",
                                             "restricted_cash") and value < 0:
                raise ValueError("资产与营收不能为负；请先核字段口径")
        if row.get("comparable") is not True:
            raise ValueError("须先核会计政策/重述/合并范围并声明comparable=true；未知不能默认为可比")
        if (row.get("restricted_cash") is not None and row.get("cash") is not None
                and row["restricted_cash"] > row["cash"]):
            raise ValueError("受限现金不得超过所声明货币资金，请核分子分母")
        rows.append(row)
    if not rows:
        raise ValueError("至少一个已披露年度")
    rows.sort(key=lambda x: x["period"])
    latest, findings = rows[-1], []

    def ratio(key, numerator, denominator, threshold):
        a, b = latest.get(numerator), latest.get(denominator)
        state, value = "UNAVAILABLE", None
        if a is not None and b is not None:
            state = "NOT_COMPARABLE" if b <= 0 else "NOT_TRIGGERED"
            if b > 0:
                value = a / b
                if value > threshold:
                    state = "TRIGGERED"
        findings.append({"rule": key, "status": state, "value": value, "threshold": threshold,
                         "period": latest["period"], "source_url": latest["source_url"]})

    ratio("receivables_to_revenue", "receivables", "revenue", 0.30)
    ratio("goodwill_to_equity", "goodwill", "equity", 0.30)
    ratio("restricted_cash_to_cash", "restricted_cash", "cash", 0.30)
    ratio("nonrecurring_to_net_profit", "nonrecurring_profit", "net_profit", 0.30)
    annual = rows[-3:]
    consecutive = len(annual) == 3 and all(int(b["period"][:4]) - int(a["period"][:4]) == 1
                                         for a, b in pairwise(annual))
    ocf = [r.get("ocf") for r in annual]
    findings.append({"rule": "negative_ocf_three_consecutive_years",
                     "status": "UNAVAILABLE" if not consecutive or any(x is None for x in ocf)
                     else "TRIGGERED" if all(x < 0 for x in ocf) else "NOT_TRIGGERED"})
    opinion = latest.get("audit_opinion")
    valid = {"unmodified", "qualified", "adverse", "disclaimer"}
    if opinion not in valid | {None, "unknown"}:
        raise ValueError("审计意见字段非法；强调事项与持续经营另核，不自动当非标意见")
    findings.append({"rule": "modified_audit_opinion", "status": "UNAVAILABLE" if opinion not in valid
                     else "NOT_TRIGGERED" if opinion == "unmodified" else "TRIGGERED", "value": opinion})
    return {"symbol": symbol, "as_of": model["as_of"], "status": "SCREEN_ONLY_REQUIRES_FILINGS_REVIEW",
            "input_kind": model.get("input_kind", "USER_SUPPLIED_NOT_INDEPENDENTLY_VERIFIED"),
            "currency": "CNY", "unit": "CNY", "findings": findings,
            "triggered_count": sum(x["status"] == "TRIGGERED" for x in findings),
            "unavailable_count": sum(x["status"] in ("UNAVAILABLE", "NOT_COMPARABLE") for x in findings),
            "input_periods": rows,
            "limitations": ["只执行6类线索，不是完整38规则/15域评分；程序未获取或验证来源原文",
                            "阈值须行业、周期、会计和现金流解释，触发不证明造假，未触发不证明安全",
                            "缺失保留未知；不能将初筛作为审计意见、法律结论或买卖指令"]}
