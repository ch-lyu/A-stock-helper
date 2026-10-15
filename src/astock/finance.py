"""跨美股/A股共用的确定估值与财报口径辅助。"""
import math
from datetime import date


def dcf_case(case):
    required = ("fcff", "wacc", "terminal_growth", "net_debt", "shares", "currency", "unit")
    if any(k not in case for k in required):
        raise ValueError("DCF缺少必要假设；请用 examples/dcf.json 结构")
    if case["currency"] != "CNY" or case["unit"] != "CNY_and_shares":
        raise ValueError("现金流和净债务使用人民币元、股数使用股，不可混用万元/亿股")
    flows = case["fcff"]
    if not flows or any(not math.isfinite(x) for x in flows):
        raise ValueError("现金流必须是非空有限数列表")
    r, g, debt, shares = [float(case[k]) for k in ("wacc", "terminal_growth", "net_debt", "shares")]
    if not all(math.isfinite(x) for x in (r, g, debt, shares)) or not r > g > -1 or r <= 0 or shares <= 0:
        raise ValueError("需 WACC > 终端增长 > -100%，WACC/股数为正")
    if flows[-1] <= 0:
        raise ValueError("永续增长法需要正的稳定期FCFF；亏损公司应使用其他估值路径")
    pv = sum(cf / (1+r)**t for t, cf in enumerate(flows, 1))
    tv = flows[-1] * (1+g) / (r-g) / (1+r)**len(flows)
    ev = pv + tv
    return {"enterprise_value": ev, "equity_value": ev-debt, "value_per_share": (ev-debt)/shares,
            "terminal_value_share": tv/ev if ev else None, "assumptions": case,
            "status": "ASSUMPTION_BASED_NOT_VERIFIED_FAIR_VALUE"}


def dcf(model):
    if set(model) != {"bear", "base", "bull"}:
        raise ValueError("需明确 bear / base / bull 三情景")
    return {"cases": {name: dcf_case(case) for name, case in model.items()},
            "status": "ASSUMPTION_BASED_NOT_VERIFIED_FAIR_VALUE",
            "limitations": ["输入由用户/AI提供，程序未核财报、净债务与稀释股数",
                            "银行/保险不应机械使用企业FCFF；折现率和增长率需要行业证据"]}


def single_quarter(records, value_field):
    """调用者须先按可获得时间选择同口径的累计快照；缺前季不计算。"""
    by_period = {}
    for r in records:
        period = r["period"]
        date.fromisoformat(period)
        if period in by_period:
            raise ValueError("同一报告期多个版本，须先核公告时间和报告口径")
        if period[5:] not in ("03-31", "06-30", "09-30", "12-31"):
            raise ValueError("只支持自然年季度报告")
        by_period[period] = r
    out = []
    previous = {"06-30": "03-31", "09-30": "06-30", "12-31": "09-30"}
    for period, r in sorted(by_period.items()):
        cumulative = r.get(value_field)
        prev = by_period.get(period[:5] + previous.get(period[5:], ""))
        if cumulative is None or (period[5:] != "03-31" and (prev is None or prev.get(value_field) is None)):
            out.append({"period": period, "value": None, "status": "MISSING_INPUT"})
        else:
            value = float(cumulative) - (float(prev[value_field]) if period[5:] != "03-31" else 0)
            if not math.isfinite(value):
                raise ValueError("非法累计财务值")
            out.append({"period": period, "value": value, "status": "CALCULATED_REQUIRES_VINTAGE_CHECK"})
    return out


def valuation_review(model, probabilities, wacc_grid, growth_grid, target_price=None):
    """数值情景与敏感性；证据与治理门禁始终需外部复核。"""
    result = dcf(model)
    if set(probabilities) != {"bear", "base", "bull"}:
        raise ValueError("需三情景概率")
    probs = list(probabilities.values())
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in probs) or not math.isclose(sum(probs), 1):
        raise ValueError("三情景概率须有限、非负、合计为1")
    if len({(v["shares"], v["net_debt"], v["currency"], v["unit"]) for v in model.values()}) != 1:
        raise ValueError("本数值复核需同一股数/净债务/币种/单位；情景桥差异请另显式建模")
    if not wacc_grid or not growth_grid or len(wacc_grid) * len(growth_grid) > 400:
        raise ValueError("敏感性网格非空且最多400单元")
    if any(not math.isfinite(x) for x in [*wacc_grid, *growth_grid]):
        raise ValueError("敏感性参数须有限")
    base = model["base"]
    sensitivity = []
    for r in wacc_grid:
        for g in growth_grid:
            case = {**base, "wacc": r, "terminal_growth": g}
            if r <= 0 or g <= -1 or r <= g:
                sensitivity.append({"wacc": r, "terminal_growth": g, "value_per_share": None,
                                    "status": "INVALID_WACC_GROWTH"})
            else:
                sensitivity.append({"wacc": r, "terminal_growth": g,
                                    "value_per_share": dcf_case(case)["value_per_share"], "status": "CALCULATED"})
    reverse = None
    if target_price is not None:
        if not math.isfinite(target_price) or target_price <= 0:
            raise ValueError("反向估值目标价格须为有限正数")
        ev = target_price * base["shares"] + base["net_debt"]
        baseline = dcf_case(base)["enterprise_value"]
        if baseline <= 0 or ev <= 0:
            raise ValueError("反向同倍缩放需正的企业价值")
        reverse = {"target_price": target_price, "uniform_fcff_multiplier": ev / baseline,
                   "meaning": "全部显式FCFF及终值现金流同倍缩放，其余基础情景参数固定；不是隐含收入增长率"}
    result.update({"status": "DRAFT_REVIEW", "numerical_status": "CALCULATED",
                   "probabilities": probabilities,
                   "probability_weighted_value": sum(probabilities[k] * v["value_per_share"]
                                                     for k, v in result["cases"].items()),
                   "sensitivity": sensitivity, "reverse_uniform_fcff": reverse,
                   "open_governance_gates": ["公告与假设证据", "经营预测至FCFF桥", "估值日及稀释股本",
                                             "行业方法适配", "独立复算与工作簿公式核验"]})
    return result

