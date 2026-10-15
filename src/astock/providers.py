"""只读行情与新闻适配；供应商错误不回退到演示数据。"""

import importlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

from .data import normalize_symbol, shanghai_today, validate_bars


def request_json(url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "A-stock-helper/0.1",
                                                        "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                return json.loads(response.read(20_000_000))
        except (OSError, ValueError) as exc:
            if attempt == 2:
                host = urllib.parse.urlparse(url).hostname
                reason = f"{type(exc).__name__}: {exc!s}"
                if isinstance(exc, urllib.error.HTTPError):
                    reason = f"HTTP {exc.code} {exc.reason}"
                token = os.environ.get("TUSHARE_TOKEN")
                if token:
                    reason = reason.replace(token, "[REDACTED]")
                # 不回显query、request payload或响应内容。
                reason = reason.replace(url, f"https://{host}/[request]")
                raise RuntimeError(f"数据源请求失败 [{host}] {reason[:180]}") from None
            time.sleep(0.3 * (attempt + 1))


def optional_module(name):
    try:
        return importlib.import_module(name)
    except ImportError:
        raise RuntimeError(f"缺少 {name}；运行 python -m pip install -e '.[data]' 或选 tencent") from None


def akshare_records(function, params):
    optional_module("akshare")
    if function not in ("stock_zh_a_hist", "stock_news_em"):
        raise ValueError("不支持的AKShare函数")
    script = ("import json,sys,akshare as ak; x=json.load(sys.stdin); "
              "r=getattr(ak,x['function'])(**x['params']); "
              "print(json.dumps({'records':r.to_dict('records'),'version':ak.__version__},"
              "ensure_ascii=False,default=str))")
    try:
        p = subprocess.run([sys.executable, "-c", script],
                           input=json.dumps({"function": function, "params": params}),
                           capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError("AKShare接口超过60秒，已停止；请换数据源或稍后重试") from None
    if p.returncode:
        reason = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else f"exit {p.returncode}"
        token = os.environ.get("TUSHARE_TOKEN")
        if token:
            reason = reason.replace(token, "[REDACTED]")
        raise RuntimeError(f"AKShare {function} 失败：{reason[:240]}")
    try:
        return json.loads(p.stdout)
    except ValueError:
        raise RuntimeError("AKShare返回不可解析结果") from None


def tencent_history(symbol, start, end, adjust):
    """逐年窗口避免供应商单次尾部截断；复权数据只用于技术研究。"""
    if symbol.startswith("bj"):
        raise ValueError("腾讯适配不保证北交所覆盖，请选 AKShare/Tushare 或导入 CSV")
    collected, urls = {}, []
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    for year in range(first.year, last.year + 1):
        a, b = max(first, date(year, 1, 1)), min(last, date(year, 12, 31))
        mode = "" if adjust == "raw" else adjust
        param = f"{symbol},day,{a.isoformat()},{b.isoformat()},400,{mode}"
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode({"param": param})
        data = request_json(url)
        if data.get("code") != 0:
            raise RuntimeError("腾讯返回失败状态")
        item = data.get("data", {}).get(symbol, {})
        key = "day" if adjust == "raw" else adjust + "day"
        records = item.get(key)
        if records is None:
            raise RuntimeError(f"腾讯缺少 {key}，拒绝静默替换价格口径")
        urls.append(url)
        for r in records:
            if not a.isoformat() <= r[0] <= b.isoformat():
                continue
            row = dict(zip(("date", "open", "close", "high", "low", "volume"), r[:6]))
            # 腾讯日K量字段以手计；作为估算源，需另源交叉验证量。
            row["volume"] = float(row["volume"]) * 100
            if r[0] in collected and row != collected[r[0]]:
                raise ValueError("数据窗口重叠值冲突")
            collected[r[0]] = row
    return [collected[d] for d in sorted(collected)], {
        "source": "Tencent public fqkline", "source_urls": urls,
        "volume_normalization": "provider lots x100; independently verify before liquidity execution",
        "adjustment_warning": "供应商复权算法与跨窗口锚未独立核验；不是实际成交价" if adjust != "raw" else None}


def akshare_history(symbol, start, end, adjust):
    data = akshare_records("stock_zh_a_hist", {"symbol": symbol[2:], "period": "daily",
                          "start_date": start.replace("-", ""), "end_date": end.replace("-", ""),
                          "adjust": "" if adjust == "raw" else adjust})
    columns = {"日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close",
               "成交量": "volume", "成交额": "amount"}
    rows = [{columns.get(k, k): v for k, v in r.items()} for r in data["records"]]
    for r in rows:
        r["date"] = str(r["date"])[:10]
        r["volume"] = float(r["volume"]) * 100
    return rows, {"source": "AKShare stock_zh_a_hist / Eastmoney",
                  "source_urls": ["https://akshare.akfamily.xyz/data/stock/stock.html"],
                  "adapter_version": data["version"]}


def tushare_call(api, params, fields=""):
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("未配置 TUSHARE_TOKEN；不要把 Token 写入仓库或报告")
    r = request_json("https://api.tushare.pro", {"api_name": api, "token": token,
                                               "params": params, "fields": fields})
    if r.get("code") != 0:
        # 不回显服务端消息，避免凭据出现在错误报告。
        raise RuntimeError(f"Tushare {api} 请求被拒绝；请检查接口权限/配额")
    data = r.get("data") or {}
    return [dict(zip(data.get("fields", []), row)) for row in data.get("items", [])]


def tushare_history(symbol, start, end, adjust):
    ts_code = symbol[2:] + "." + symbol[:2].upper()
    p = {"ts_code": ts_code, "start_date": start.replace("-", ""), "end_date": end.replace("-", "")}
    rows = tushare_call("daily", p)
    if adjust != "raw":
        raise ValueError("Tushare适配当前只支持 raw；复权需另存因子并核验")
    limits = {r["trade_date"]: r for r in tushare_call("stk_limit", p)}
    out = []
    for r in sorted(rows, key=lambda x: x["trade_date"]):
        compact = r["trade_date"]
        d = date(int(compact[:4]), int(compact[4:6]), int(compact[6:8])).isoformat()
        row = {"date": d, **{k: r[k] for k in ("open", "high", "low", "close")},
               "volume": float(r["vol"]) * 100, "amount": float(r["amount"]) * 1000,
               "reference_close": r["pre_close"]}
        if r["trade_date"] in limits:
            row.update(upper_limit=limits[r["trade_date"]]["up_limit"],
                       lower_limit=limits[r["trade_date"]]["down_limit"])
        out.append(row)
    return out, {"source": "Tushare daily + stk_limit", "source_urls": ["https://tushare.pro/document/2"]}


def history(symbol, start, end, provider="tencent", adjust="raw"):
    symbol = normalize_symbol(symbol)
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("起点必须不晚于终点")
    fetch = {"tencent": tencent_history, "akshare": akshare_history, "tushare": tushare_history}[provider]
    rows, meta = fetch(symbol, start, end, adjust)
    # 当日K默认不使用：盘后由用户显式CSV提供，避免时钟/供应商更新不一致。
    today = shanghai_today()
    rows = [r for r in rows if r["date"] < today]
    return validate_bars(rows), {**meta, "symbol": symbol, "price_mode": adjust,
                                 "requested_start": start, "requested_end": end,
                                 "timezone": "Asia/Shanghai", "current_day_policy": "exclude"}


def news(symbol, limit=20):
    symbol = normalize_symbol(symbol)
    data = akshare_records("stock_news_em", {"symbol": symbol[2:]})
    seen, result, excluded = set(), [], []
    for r in data["records"]:
        url = str(r.get("新闻链接", ""))
        title = str(r.get("新闻标题", ""))
        published_at = str(r.get("发布时间", ""))
        parsed_url = urllib.parse.urlparse(url)
        if not title or not published_at or parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            excluded.append({"title": title, "status": "UNVERIFIABLE_MISSING_TITLE_DATE_OR_URL"})
            continue
        try:
            datetime.fromisoformat(published_at)
        except ValueError:
            excluded.append({"title": title, "status": "UNVERIFIABLE_PUBLICATION_DATE"})
            continue
        if (url, title) in seen:
            continue
        seen.add((url, title))
        result.append({"title": title, "published_at": published_at,
                       "source": str(r.get("文章来源", "")), "url": url,
                       "evidence_type": "NEWS_NOT_OFFICIAL_DISCLOSURE"})
    result.sort(key=lambda r: r["published_at"], reverse=True)
    return {"symbol": symbol, "items": result[:limit], "provider": "AKShare / Eastmoney",
            "status": "NEWS_WINDOW" if result else "DATA_UNAVAILABLE", "excluded_items": excluded,
            "publication_timezone": "Asia/Shanghai; provider timestamps usually omit offset",
            "coverage": "供应商返回窗口；不是全量新闻档案", "content_trust": "UNTRUSTED_EXTERNAL_TEXT"}


def fundamentals(symbol, as_of):
    symbol = normalize_symbol(symbol)
    code = symbol[2:] + "." + symbol[:2].upper()
    cutoff = date.fromisoformat(as_of).strftime("%Y%m%d")
    result = {}
    for api in ("income", "balancesheet", "cashflow", "fina_indicator"):
        rows = tushare_call(api, {"ts_code": code, "end_date": cutoff})
        # 日期级披露时间未知时，只允许前一日及更早公告，避免同日盘后泄漏。
        result[api] = [r for r in rows if (r.get("f_ann_date") or r.get("ann_date") or "99999999") < cutoff]
    return {"symbol": symbol, "as_of": as_of, "tables": result, "source": "Tushare",
            "status": "FINANCIAL_TABLES_PARTIAL" if any(result.values()) else "DATA_UNAVAILABLE",
            "empty_tables": [key for key, value in result.items() if not value],
            "pit_status": "ANNOUNCEMENT_DATE_FILTERED_NOT_VINTAGE_ARCHIVE",
            "warning": "接口可能只保留修订后数据；公告日筛选不等于完整历史PIT快照；原文另核"}
