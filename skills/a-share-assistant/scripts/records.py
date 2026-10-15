"""显式私有目录内的版本化研究记录；不依赖聊天记忆，不连接外部服务。"""
import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    if not isinstance(value, dict):
        raise TypeError("记录必须为JSON对象")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def check_key(key):
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", key):
        raise ValueError("键须为1-100位字母、数字、点、冒号、横线或下划线")


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS records (key TEXT, revision INTEGER, saved_at TEXT, "
               "sha256 TEXT, body TEXT, PRIMARY KEY(key,revision))")
    return db


def put(db, key, value):
    check_key(key)
    body = canonical(value)
    digest = hashlib.sha256(body.encode()).hexdigest()
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT revision,sha256 FROM records WHERE key=? ORDER BY revision DESC LIMIT 1",
                         (key,)).fetchone()
        if row and row[1] == digest:
            return {"key": key, "revision": row[0], "sha256": digest, "unchanged": True}
        revision = row[0] + 1 if row else 1
        db.execute("INSERT INTO records VALUES(?,?,?,?,?)",
                   (key, revision, datetime.now(timezone.utc).isoformat(), digest, body))
    return {"key": key, "revision": revision, "sha256": digest, "unchanged": False}


def rows(db):
    return [{"key": k, "revision": v, "saved_at": t, "sha256": h, "value": json.loads(b)}
            for k, v, t, h, b in db.execute("SELECT * FROM records ORDER BY key, revision")]


def restore(db, package):
    if not isinstance(package, dict) or package.get("schema") != "a-share-records/1":
        raise ValueError("未知交接格式")
    incoming = package.get("records")
    if not isinstance(incoming, list):
        raise TypeError("缺少记录列表")
    checked, seen = [], set()
    for item in incoming:
        key, revision = item["key"], item["revision"]
        check_key(key)
        if type(revision) is not int or revision < 1 or (key, revision) in seen:
            raise ValueError("非法/重复版本")
        seen.add((key, revision))
        body = canonical(item["value"])
        digest = hashlib.sha256(body.encode()).hexdigest()
        if digest != item["sha256"]:
            raise ValueError("交接内容哈希不一致")
        datetime.fromisoformat(item["saved_at"])
        checked.append((key, revision, item["saved_at"], digest, body))
    # 事务中先校验所有冲突，再写；遇错全部回滚。
    with db:
        db.execute("BEGIN IMMEDIATE")
        for key, revision, timestamp, digest, body in checked:
            old = db.execute("SELECT sha256 FROM records WHERE key=? AND revision=?", (key, revision)).fetchone()
            if old and old[0] != digest:
                raise ValueError("现有版本冲突；保留原库，停止导入")
        db.executemany("INSERT OR IGNORE INTO records VALUES(?,?,?,?,?)", checked)
    return {"imported_or_existing": len(checked)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--store", required=True, help="用户明确选择的私有SQLite路径")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("put")
    s.add_argument("key")
    s.add_argument("json_file")
    s = sub.add_parser("get")
    s.add_argument("key")
    s.add_argument("--revision", type=int)
    sub.add_parser("list")
    s = sub.add_parser("export")
    s.add_argument("--out", required=True)
    s = sub.add_parser("import")
    s.add_argument("json_file")
    a = p.parse_args()
    try:
        with connect(a.store) as db:
            if a.command == "put":
                result = put(db, a.key, json.loads(Path(a.json_file).read_text(encoding="utf-8")))
            elif a.command == "get":
                check_key(a.key)
                options = [x for x in rows(db) if x["key"] == a.key and
                           (a.revision is None or x["revision"] == a.revision)]
                if not options:
                    raise ValueError("记录不存在")
                result = options[-1]
            elif a.command == "list":
                result = [{k: v for k, v in x.items() if k != "value"} for x in rows(db)]
            elif a.command == "export":
                result = {"schema": "a-share-records/1", "records": rows(db)}
                out = Path(a.out)
                if out.resolve() == Path(a.store).resolve():
                    raise ValueError("交接文件不能覆盖记录库")
                out.parent.mkdir(parents=True, exist_ok=True)
                # 交接文件禁止静默覆盖已有用户文件。
                with out.open("x", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
                result = {"path": str(out.resolve()), "records": len(result["records"])}
            else:
                result = restore(db, json.loads(Path(a.json_file).read_text(encoding="utf-8")))
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as e:
        print(json.dumps({"status": "ERROR", "reason": str(e)}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
