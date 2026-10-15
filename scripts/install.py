#!/usr/bin/env python3
"""安装原创技能和共享运行器；拒绝覆盖未知或被用户修改的文件。"""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(destination, replace=False):
    destination = Path(destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        raise ValueError("技能包为空")
    prepared = []
    with tempfile.TemporaryDirectory(prefix="astock-install-", dir=destination) as tmp:
        staging = Path(tmp)
        for skill in skills:
            name = skill.parent.name
            new = staging / name
            shutil.copytree(skill.parent, new, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            if name == "a-share-assistant":
                shutil.copytree(ROOT / "src", new / "scripts" / "src",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                shutil.copytree(ROOT / "vendor/financial-services", new / "references/upstream/financial-services")
                ref = new / "references/adoption-map.md"
                ref.write_text(ref.read_text(encoding="utf-8").replace("../../../vendor/", "upstream/"),
                               encoding="utf-8")
                shutil.copy2(ROOT / "docs/research/adoption.json", new / "references/source-catalog.json")
            manifest = {str(p.relative_to(new)): digest(p) for p in new.rglob("*") if p.is_file()}
            manifest_file = ".a-stock-helper-manifest.json"
            (new / manifest_file).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            target = destination / name
            if target.is_symlink():
                raise ValueError(f"拒绝修改符号链接：{name}")
            if target.exists():
                old_file = target / manifest_file
                if not old_file.exists():
                    raise ValueError(f"已有非本安装器管理的技能：{name}，请选新目录")
                old = json.loads(old_file.read_text(encoding="utf-8"))
                if any(Path(rel).is_absolute() or ".." in Path(rel).parts for rel in old):
                    raise ValueError(f"安装清单包含非法路径：{name}")
                existing = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()}
                if any(p.is_symlink() for p in target.rglob("*")):
                    raise ValueError(f"技能含符号链接，拒绝覆盖：{name}")
                if existing - set(old) - {manifest_file}:
                    raise ValueError(f"技能含用户新增文件，拒绝覆盖：{name}")
                if any(not (target / rel).is_file() or digest(target / rel) != h for rel, h in old.items()):
                    raise ValueError(f"技能已被修改，拒绝覆盖：{name}")
                if manifest == old:
                    continue
                if not replace:
                    raise ValueError(f"已有旧版：{name}；使用 --replace-managed 更新未修改的文件")
            prepared.append((new, target))
        # 全部冲突检查通过后才修改。每个旧目录先备份，失败时还原整个安装事务。
        completed = []
        try:
            for new, target in prepared:
                backup = staging / (target.name + ".backup")
                if target.exists():
                    target.rename(backup)
                completed.append((target, backup))
                new.rename(target)
        except OSError:
            for target, backup in reversed(completed):
                if target.exists():
                    shutil.rmtree(target)
                if backup.exists():
                    backup.rename(target)
            raise
    return {"skills": len(skills), "changed": len(prepared), "destination": str(destination),
            "doctor_command": f'python "{destination / "a-share-assistant/scripts/astock.py"}" doctor'}


def main(argv=None):
    p = argparse.ArgumentParser(description="安装 A 股助手技能；Python依赖需另行安装")
    p.add_argument("--target", choices=["codex", "claude", "generic"], default="codex")
    p.add_argument("--dest", help="可覆盖目标路径；generic 必填")
    p.add_argument("--replace-managed", action="store_true")
    a = p.parse_args(argv)
    if not a.dest and a.target == "generic":
        p.error("generic 需要 --dest 指向 AI 支持的 Agent Skills 目录")
    destination = a.dest or (Path.home() / (".codex/skills" if a.target == "codex" else ".claude/skills"))
    try:
        print(json.dumps(install(destination, a.replace_managed), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
