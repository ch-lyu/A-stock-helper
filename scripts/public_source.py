"""生成公开源码清理版；原始参考归档和私人Notion逐项清单仅留私有交付。"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = {"skills/a-share-assistant/references/coverage.json",
           "skills/a-share-assistant/references/professional-catalog.json"}


def prepare(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("公开暂存目录必须不存在")
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for rel in filter(None, files):
        if rel in PRIVATE or rel.endswith(".zip"):
            continue
        source = ROOT / rel
        if source.is_symlink():
            raise ValueError("公开源不接受符号链接")
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    primary = destination / "skills/a-share-assistant/references"
    original = json.loads((ROOT / "skills/a-share-assistant/references/professional-catalog.json").read_text())
    catalog = {"schema": original["schema"], "distribution_profile": "PUBLIC_SOURCE_LINKS_ONLY",
               "policy": "公开链接索引，不包含原始参考包或私人逐项目录；完整资料在用户私有交付。",
               "entries": [{"name": e["name"], "source_repository": e.get("source_repository"),
                            "archive": None, "reference_only": True,
                            "runtime_status": "BLOCKED" if e["runtime_status"] == "BLOCKED"
                            else "NOT_BUNDLED_IN_PUBLIC_SOURCE",
                            "reason": "原始归档未随公开源发布；使用已交付私有完整包。"}
                           for e in original["entries"]]}
    (primary / "professional-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    coverage = {"schema": "a-share-notion-coverage/1", "distribution_profile": "PUBLIC_SOURCE_LINKS_ONLY",
                "scope": "私人Notion逐项覆盖报告只在用户私有完整交付，不随公开源码发布。",
                "entries": [], "summary": {}, "private_original_pages_included": False}
    (primary / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
    readme = destination / "README.md"
    readme.write_text("# 公开源码分发说明\n\n当前仓库提供原创计算工具、12个A股模块、独立适配流程及公开来源链接。"
                      "完整原始参考包、Notion逐项覆盖清单、475模块扩展资料保存在用户私有Drive，"
                      "未公开发布。下文描述整个项目的完整私有交付能力，不代表此公开检出包含全部原始资料。"
                      "公开版可运行核心命令；原始资料完整性测试因文件未分发而明确跳过。\n\n"
                      + readme.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination")
    print(prepare(p.parse_args().destination))
