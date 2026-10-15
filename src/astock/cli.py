import argparse
import importlib.util
import json
import sys
from pathlib import Path

from . import __version__
from .backtest import Config, ledger_backtest, proxy_backtest, validate_strategy
from .data import audit, load_bars, read_metadata, shanghai_today, write_dataset
from .finance import dcf, valuation_review
from .financial_audit import financial_audit
from .providers import fundamentals, history, news
from .research import analyze, compare_data, portfolio, save_json, screen
from .risk import portfolio_risk
from .signals import signals


def parser():
    p = argparse.ArgumentParser(description="中文A股助手：先取证据，再做研究；核心命令无需模型API")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="检查运行环境，不输出任何Token")
    f = sub.add_parser("fetch", help="抓取已结束日K并保存来源/哈希")
    f.add_argument("symbol")
    f.add_argument("--start", required=True)
    f.add_argument("--end", default=shanghai_today())
    f.add_argument("--provider", choices=["tencent", "akshare", "tushare"], default="tencent")
    f.add_argument("--adjust", choices=["raw", "qfq", "hfq"], default="raw")
    f.add_argument("--out", required=True)
    a = sub.add_parser("audit", help="校验CSV、来源哈希和日期覆盖")
    a.add_argument("csv")
    a.add_argument("--start")
    a.add_argument("--end")
    a = sub.add_parser("compare", help="两个供应商同口径行情交叉核验")
    a.add_argument("left")
    a.add_argument("right")
    a.add_argument("--tolerance", type=float, default=0.02)
    a = sub.add_parser("analyze", help="行情指标证据包与中文报告，AI再补完整基本面")
    a.add_argument("csv")
    a.add_argument("--title")
    a.add_argument("--out", required=True)
    for command in ("news", "fundamentals"):
        a = sub.add_parser(command, help="新闻(AKShare) / 公告日筛选财报(Tushare)")
        a.add_argument("symbol")
        a.add_argument("--out", required=True)
        if command == "fundamentals":
            a.add_argument("--as-of", required=True)
    a = sub.add_parser("screen", help="对用户观察名单排序，不宣称全市场")
    a.add_argument("csv", nargs="+")
    a.add_argument("--out", required=True)
    a = sub.add_parser("portfolio", help="用户CSV持仓快照的集中度分析")
    a.add_argument("csv")
    a.add_argument("--out", required=True)
    a = sub.add_parser("valuation", help="用户核实的三情景FCFF/DCF，不适用于所有行业")
    a.add_argument("model", help="examples/dcf.json 格式")
    a.add_argument("--out", required=True)
    a = sub.add_parser("risk", help="当前权重历史风险代理：相关性、风险贡献、VaR/ES；不是账户盈亏")
    a.add_argument("holdings")
    a.add_argument("series_manifest", help="JSON: series证券到复权CSV映射、window、confidence")
    a.add_argument("--out", required=True)
    for name, description in (("financial-audit", "普通非金融企业年度财报6类线索；不是造假结论"),
                              ("valuation-review", "概率、敏感性、固定参数反向现金流缩放；治理仍待核")):
        a = sub.add_parser(name, help=description)
        a.add_argument("input")
        a.add_argument("--out", required=True)
    a = sub.add_parser("backtest", help="原始价格现金账本或显式复权收益代理")
    a.add_argument("csv")
    a.add_argument("--mode", choices=["ledger", "proxy"], default="ledger")
    a.add_argument("--strategy", choices=["ma", "breakout", "buyhold"], default="ma")
    a.add_argument("--fast", type=int, default=20)
    a.add_argument("--slow", type=int, default=120)
    a.add_argument("--initial-cash", type=float, default=100000)
    a.add_argument("--cost-bps", type=float, default=15)
    a.add_argument("--slippage-bps", type=float, default=5)
    a.add_argument("--commission", type=float, default=0.0003)
    a.add_argument("--min-commission", type=float, default=5)
    a.add_argument("--participation", type=float, default=0.01)
    a.add_argument("--board", choices=["auto", "main", "star", "bse"], default="auto")
    a.add_argument("--strict", action="store_true")
    a.add_argument("--corporate-actions-complete", action="store_true")
    a.add_argument("--actions", help="JSON公司行动列表，日、拆股比例、每原股税前分红和支付日")
    a.add_argument("--out", required=True)
    a = sub.add_parser("validate", help="三候选按时间划分、最终留出与成本压力；仅收益代理")
    a.add_argument("csv")
    a.add_argument("--strategy", choices=["ma", "breakout"], default="ma")
    a.add_argument("--train-end", default="2021-12-31")
    a.add_argument("--validation-end", default="2024-12-31")
    a.add_argument("--out", required=True)
    return p


def run(args):
    cmd = args.command
    if cmd == "doctor":
        return {"version": __version__, "python": sys.version.split()[0], "core": "READY",
                "optional": {x: importlib.util.find_spec(x) is not None for x in ("akshare", "tushare", "baostock")},
                "capabilities": {"tencent_history": "needs_network", "news": "needs_akshare_and_network",
                                 "fundamentals": "needs_TUSHARE_TOKEN_and_permissions", "broker_trading": False},
                "client_installation": "技能可发现性需在目标AI中单独确认；此命令仅检查Python"}
    if cmd == "fetch":
        rows, meta = history(args.symbol, args.start, args.end, args.provider, args.adjust)
        meta = write_dataset(args.out, rows, meta)
        return {"path": str(Path(args.out).resolve()), "metadata": meta,
                "audit": audit(args.out, args.start, args.end)}
    if cmd == "audit":
        return audit(args.csv, args.start, args.end)
    if cmd == "compare":
        return compare_data(args.left, args.right, args.tolerance)
    if cmd in ("news", "fundamentals"):
        result = news(args.symbol) if cmd == "news" else fundamentals(args.symbol, args.as_of)
    elif cmd == "portfolio":
        result = portfolio(args.csv)
    elif cmd == "screen":
        result = screen(args.csv)
    elif cmd == "valuation":
        result = dcf(json.loads(Path(args.model).read_text(encoding="utf-8")))
    elif cmd == "risk":
        result = portfolio_risk(args.holdings, args.series_manifest)
    elif cmd == "financial-audit":
        result = financial_audit(json.loads(Path(args.input).read_text(encoding="utf-8")))
    elif cmd == "valuation-review":
        config = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = valuation_review(config["model"], config["probabilities"], config["wacc_grid"],
                                  config["growth_grid"], config.get("target_price"))
    else:
        rows, meta = load_bars(args.csv), read_metadata(args.csv)
        if cmd == "analyze":
            result = analyze(rows, meta, args.title)
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(result.pop("report"), encoding="utf-8")
            save_json(str(out) + ".json", result)
            return {"report": str(out.resolve()), "status": result["status"]}
        if cmd == "validate":
            if meta.get("price_mode") not in ("qfq", "hfq"):
                raise ValueError("validate需有来源记录的复权CSV；不能把未复权分红跳空当收益")
            result = validate_strategy(rows, args.strategy, args.train_end, args.validation_end)
        else:
            target = signals(rows, args.strategy, args.fast, args.slow)
            if args.mode == "proxy":
                if meta.get("price_mode") not in ("qfq", "hfq"):
                    raise ValueError("proxy需明确复权口径")
                result = proxy_backtest(rows, target, args.cost_bps, args.initial_cash)
            else:
                if meta.get("price_mode") != "raw":
                    raise ValueError("股数/现金账本必须使用带来源记录的 raw 价格")
                symbol = meta.get("symbol", "")
                if not symbol.startswith(("sh6", "sz0", "sz3", "bj")):
                    raise ValueError("账本只支持普通A股，不能将指数/ETF规则混入股票回测")
                inferred = "bse" if symbol.startswith("bj") else "star" if symbol.startswith(("sh688", "sh689")) else "main"
                board = inferred if args.board == "auto" else args.board
                if board != inferred:
                    raise ValueError("指定板块与证券代码不一致，停止回测")
                qty = {"main": (100, 100), "star": (200, 1), "bse": (100, 1)}[board]
                cfg = Config(initial_cash=args.initial_cash, commission=args.commission,
                             min_commission=args.min_commission, slippage_bps=args.slippage_bps,
                             participation=args.participation, min_buy=qty[0], buy_increment=qty[1],
                             strict=args.strict, corporate_actions_complete=args.corporate_actions_complete)
                actions = json.loads(Path(args.actions).read_text(encoding="utf-8")) if args.actions else []
                result = ledger_backtest(rows, target, cfg, actions)
        result["input_metadata"] = meta
        result["strategy"] = args.strategy
    save_json(args.out, result)
    summary = {"output": str(Path(args.out).resolve()), "status": result.get("status", "SAVED")}
    for key in ("metrics", "selected"):
        if result.get(key) is not None:
            summary[key] = result[key]
    if cmd == "portfolio":
        summary["portfolio_summary"] = {k: result[k] for k in
                                        ("as_of", "currency", "total", "cash_weight", "largest_stock_weight",
                                         "hhi", "hhi_definition", "limitations")}
    return summary


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
