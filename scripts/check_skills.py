"""无第三方依赖的技能元数据/引用/共享运行器检查。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if len(skills) != 12:
        raise ValueError("预期12个技能")
    for p in skills:
        text = p.read_text(encoding="utf-8")
        name = re.search(r"^name: (.+)$", text, re.MULTILINE)
        desc = re.search(r"^description: (.+)$", text, re.MULTILINE)
        if not text.startswith("---\n") or not name or not desc or name[1] != p.parent.name:
            raise ValueError(f"非法元数据：{p}")
        if len(text.splitlines()) > 500 or "TODO" in text:
            raise ValueError(f"未完成或过长：{p}")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target and not (p.parent / target).exists():
                raise ValueError(f"不存在的引用：{p} → {target}")
        for target in re.findall(r"`(\.\./[^`]+(?:\.md|\.py))`", text):
            if "<" not in target and not (p.parent / target).exists():
                raise ValueError(f"不存在的引用：{p} → {target}")
        if not (p.parent / "agents/openai.yaml").exists():
            raise ValueError(f"缺UI元数据：{p}")
    print(f"PASS: {len(skills)} skills, metadata, references, runtime")


if __name__ == "__main__":
    main()

