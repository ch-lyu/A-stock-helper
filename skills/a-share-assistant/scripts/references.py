"""检索并解包只读专业参考资料；绝不执行其中的业务脚本。"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unpack(entry, output=None, root=ROOT):
    if entry.get("runtime_status") == "BLOCKED" or not entry.get("archive"):
        raise ValueError(entry.get("reason", "此来源模块禁止调用"))
    archive = root / entry["archive"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != entry["archive_sha256"]:
        raise ValueError("原始参考归档哈希不一致")
    output = Path(output) if output else Path(tempfile.mkdtemp(prefix="astock-reference-parent-")) / entry["name"]
    if output.exists() or output.is_symlink():
        raise ValueError("不覆盖现有目录；请为参考资料指定新目录")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astock-reference-", dir=output.parent))
    try:
        with zipfile.ZipFile(archive) as z:
            seen = set()
            if sum(x.file_size for x in z.infolist()) > 128 * 1024 * 1024:
                raise ValueError("参考归档解压大小超限")
            for item in z.infolist():
                parts = Path(item.filename).parts
                if (Path(item.filename).is_absolute() or ".." in parts or "\\" in item.filename
                        or item.filename in seen or stat.S_ISLNK(item.external_attr >> 16)):
                    raise ValueError("参考归档含不安全或重复路径")
                seen.add(item.filename)
            for item in z.infolist():
                dest = staging / item.filename
                if item.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(z.read(item))
                    os.chmod(dest, 0o600)
        if hashlib.sha256((staging / "source-SKILL.md").read_bytes()).hexdigest() != entry["instructions_sha256"]:
            raise ValueError("原始指令指纹不一致")
        reading_digest = hashlib.sha256((staging / "INSTRUCTIONS.md").read_bytes()).hexdigest()
        if reading_digest != entry["reading_copy_sha256"]:
            raise ValueError("阅读副本指纹不一致")
        staging.rename(output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"name": entry["name"], "instructions": str((output / "INSTRUCTIONS.md").resolve()),
            "directory": str(output.resolve()), "status": "REFERENCE_ONLY_NOT_EXECUTED",
            "next": "读取原文与依赖；原项目命令、付费数据和账户能力并未接入本包。"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("list")
    a.add_argument("--query", default="")
    a = sub.add_parser("read")
    a.add_argument("name")
    a.add_argument("--out")
    args = p.parse_args()
    try:
        catalog = json.loads((ROOT / "references/professional-catalog.json").read_text(encoding="utf-8"))
        if args.command == "list":
            result = [{k: e.get(k) for k in ("name", "description", "runtime_status", "reference_only")}
                      for e in catalog["entries"] if args.query.lower() in
                      (e["name"] + " " + e.get("description", "")).lower()]
        else:
            entry = next((x for x in catalog["entries"] if x["name"] == args.name), None)
            if entry is None:
                raise ValueError("该来源未随核心包保留；查coverage.json后使用独立完整资料库，不能假装已读")
            result = unpack(entry, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as e:
        print(json.dumps({"status": "ERROR", "reason": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
