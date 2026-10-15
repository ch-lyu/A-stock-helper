"""CSV 数据边界；所有行情使用股票交易所本地日期，量统一为股。"""

import csv
import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from itertools import pairwise
from pathlib import Path


def shanghai_today():
    """现代A股使用UTC+8，无需Windows安装IANA时区数据库。"""
    return datetime.now(timezone(timedelta(hours=8))).date().isoformat()


def normalize_symbol(value):
    value = value.strip().lower()
    m = re.fullmatch(r"(\d{6})\.(sh|sz|bj)", value)
    if m:
        return m[2] + m[1]
    value = value.replace(".", "")
    if re.fullmatch(r"(sh|sz|bj)\d{6}", value):
        return value
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError("请提供六位代码或交易所代码，例如 600519.SH；公司名称需先核实代码")
    if value.startswith(("4", "8", "92")):
        return "bj" + value
    if value.startswith(("5", "6")):
        return "sh" + value
    if value.startswith(("0", "1", "2", "3")):
        return "sz" + value
    raise ValueError("无法确定交易所，请显式使用 .SH / .SZ / .BJ")


def validate_bars(rows):
    if not rows:
        raise ValueError("没有行情数据")
    seen = set()
    previous = ""
    for row in rows:
        day = row["date"]
        date.fromisoformat(day)
        if day in seen or day <= previous:
            raise ValueError("日期重复或未按日期递增")
        seen.add(day)
        previous = day
        for key in ("open", "high", "low", "close", "volume"):
            row[key] = float(row[key])
            if not math.isfinite(row[key]):
                raise ValueError(f"{day} {key} 不是有限数")
        if min(row[k] for k in ("open", "high", "low", "close")) <= 0:
            raise ValueError(f"{day} 价格必须为正数")
        if row["volume"] < 0 or row["high"] < max(row["open"], row["close"], row["low"]):
            raise ValueError(f"{day} 非法 OHLCV")
        if row["low"] > min(row["open"], row["close"], row["high"]):
            raise ValueError(f"{day} 非法最低价")
        for key in ("upper_limit", "lower_limit", "reference_close"):
            if row.get(key) not in (None, ""):
                row[key] = float(row[key])
                if not math.isfinite(row[key]) or row[key] <= 0:
                    raise ValueError(f"{day} 非法 {key}")
        if row.get("tradable") not in (None, ""):
            if str(row["tradable"]).lower() not in ("0", "1", "true", "false"):
                raise ValueError("tradable 必须是 0/1/true/false")
            row["tradable"] = str(row["tradable"]).lower() in ("1", "true")
    return rows


def load_bars(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return validate_bars(list(csv.DictReader(f)))


def metadata_path(path):
    return Path(str(path) + ".meta.json")


def read_metadata(path):
    p = metadata_path(path)
    if not p.exists():
        return {"source": "user_csv", "price_mode": "unknown", "provenance_status": "UNVERIFIED"}
    meta = json.loads(p.read_text(encoding="utf-8"))
    required = ("symbol", "source", "price_mode", "sha256", "rows", "first_date", "last_date",
                "fetched_at", "volume_unit", "currency", "timezone")
    if not isinstance(meta, dict) or any(meta.get(k) in (None, "") for k in required):
        raise ValueError("来源记录缺少必要字段，不能通过数据审计")
    if meta["price_mode"] not in ("raw", "qfq", "hfq"):
        raise ValueError("非法或未核价格口径")
    if normalize_symbol(meta["symbol"]) != meta["symbol"]:
        raise ValueError("元数据证券身份未规范化")
    if meta["volume_unit"] != "shares" or meta["currency"] != "CNY" or meta["timezone"] != "Asia/Shanghai":
        raise ValueError("元数据单位/币种/时区不符合A股数据契约")
    date.fromisoformat(meta["first_date"])
    date.fromisoformat(meta["last_date"])
    fetched = datetime.fromisoformat(meta["fetched_at"])
    if fetched.tzinfo is None:
        raise ValueError("抓取时间必须包含时区")
    rows = load_bars(path)
    if meta["rows"] != len(rows) or meta["first_date"] != rows[0]["date"] or meta["last_date"] != rows[-1]["date"]:
        raise ValueError("元数据行数/范围与CSV不符")
    if meta.get("sha256") != hashlib.sha256(Path(path).read_bytes()).hexdigest():
        raise ValueError("数据哈希与来源记录不符，文件可能被修改")
    return meta


def write_dataset(path, rows, meta):
    rows = validate_bars(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["date", "open", "high", "low", "close", "volume"]
    keys += [k for k in ("amount", "upper_limit", "lower_limit", "reference_close", "tradable")
             if any(k in r for r in rows)]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    meta = {"source": "user_csv_unverified", "timezone": "Asia/Shanghai", **meta,
            "first_date": rows[0]["date"], "last_date": rows[-1]["date"],
            "rows": len(rows), "volume_unit": "shares", "currency": "CNY",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    metadata_path(path).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def audit(path, start=None, end=None):
    rows, meta = load_bars(path), read_metadata(path)
    warnings = []
    if meta.get("source") == "user_csv_unverified":
        warnings.append("用户CSV来源未独立核验，哈希只证明文件完整性")
    if meta.get("price_mode") == "unknown":
        warnings.append("缺少已核验价格口径")
    if start and rows[0]["date"] > start:
        warnings.append("实际起点晚于请求起点：可能上市较晚或供应商截断")
    if end and rows[-1]["date"] < end:
        warnings.append("最后日期早于请求终点：需核交易日历，不能自动判定已更新")
    gaps = []
    for a, b in pairwise(rows):
        n = (date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days
        if n > 10:
            gaps.append({"from": a["date"], "to": b["date"], "days": n})
    if gaps:
        warnings.append("存在长日期间隔，需核停牌/节假日/缺失；不自动补交易日")
    return {"status": "PASS_WITH_WARNINGS" if warnings else "PASS", "rows": len(rows),
            "metadata": meta, "warnings": warnings, "long_gaps": gaps,
            "zero_volume_days": sum(r["volume"] == 0 for r in rows),
            "calendar_completeness": "NOT_VERIFIED_WITH_EXCHANGE_CALENDAR"}
