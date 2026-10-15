"""复现公开行情信号验证；不把复权研究代理说成可成交收益。"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from astock.backtest import validate_strategy
from astock.data import load_bars, read_metadata, write_dataset
from astock.providers import history
from astock.research import save_json

SAMPLES = [("600519", "qfq", "2018-01-01"), ("000001", "qfq", "2018-01-01"),
           ("600036", "qfq", "2018-01-01"), ("601899", "qfq", "2018-01-01"),
           ("300750", "hfq", "2018-01-01"), ("688981", "qfq", "2020-07-16")]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", default="work/market")
    p.add_argument("--out", default="work/validation-results.json")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()
    outcomes = []
    for symbol, adjust, start in SAMPLES:
        path = Path(a.cache) / (f"{symbol}.csv" if adjust == "qfq" else f"{symbol}-{adjust}.csv")
        alternate = Path(a.cache) / f"{symbol}-{adjust}.csv"
        if not path.exists() and alternate.exists():
            path = alternate
        try:
            if a.refresh or not path.exists():
                if a.offline:
                    raise ValueError("离线缓存缺失或要求刷新")
                rows, meta = history(symbol, start, "2026-10-06", "tencent", adjust)
                write_dataset(path, rows, meta)
            rows, meta = load_bars(path), read_metadata(path)
            if meta.get("price_mode") != adjust or meta.get("symbol", "")[2:] != symbol:
                raise ValueError("缓存身份或复权口径不一致")
            for strategy in ("ma", "breakout"):
                outcome = validate_strategy(rows, strategy)
                outcomes.append({"symbol": symbol, "metadata": meta, **outcome})
            print(symbol, len(rows), rows[-1]["date"], "validated proxy", flush=True)
        except (ValueError, RuntimeError, OSError) as exc:
            outcomes.append({"symbol": symbol, "adjust": adjust, "status": "DATA_UNAVAILABLE",
                             "error": str(exc)})
            print(symbol, "DATA_UNAVAILABLE", str(exc), flush=True)
    result = {"study": "A-stock-helper 0.1 signal validation", "as_of_requested": "2026-10-06",
              "sample_selection": "六个便利标的，非随机/全市场；保留失败；300750前复权非正改用明确hfq",
              "initial_failed_attempts": [
                  {"symbol": "300750", "mode": "qfq", "error": "2018-06-11 非正价格，拒绝；另试hfq"},
                  {"symbol": "688981", "provider": "Tencent", "error": "缺少请求的qfqday字段"},
                  {"symbol": "688981", "provider": "AKShare", "error": "接口失败，未造数据"}],
              "outcomes": outcomes,
              "limitations": ["全部策略结果为复权收益代理，未验证实际可成交收益",
                              "没有PIT全市场股票池、公司行动独立归档、盘口或真实券商手续费记录",
                              "2018–2021开发，2022–2024选参，2025–最新日留出；重复调参会污染留出"]}
    save_json(a.out, result)
    print(json.dumps({"output": a.out, "strategies": sum("selected" in o for o in outcomes),
                      "failed_samples": sum(o["status"] == "DATA_UNAVAILABLE" for o in outcomes)}, indent=2))
    return 0 if any("selected" in o for o in outcomes) else 2


if __name__ == "__main__":
    raise SystemExit(main())

