"""构建一个可独立导入的技能ZIP；只从明确允许的公共文件构建。"""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "a-share-family-suite"
SAFE_SUFFIXES = {".py", ".md", ".yaml", ".json", ".csv", ".zip"}


def collect(root=ROOT):
    payload = {}

    def add_tree(source, dest):
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"包来源不能为符号链接: {path}")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in SAFE_SUFFIXES:
                payload[(Path(dest) / path.relative_to(source)).as_posix()] = path.read_bytes()

    add_tree(root / "packaging" / NAME, "")
    add_tree(root / "skills", "modules")
    primary = root / "skills/a-share-assistant"
    add_tree(primary / "references", "references")
    add_tree(primary / "assets", "assets")
    add_tree(primary / "scripts", "scripts")
    add_tree(root / "src", "scripts/src")
    add_tree(root / "src", "modules/a-share-assistant/scripts/src")
    add_tree(root / "examples", "assets/examples")
    add_tree(root / "vendor/financial-services", "vendor/financial-services")
    for name in ("LICENSE", "NOTICE"):
        path = root / "vendor/financial-services" / name
        payload[f"vendor/financial-services/{name}"] = path.read_bytes()
    payload["LICENSE"] = (root / "LICENSE").read_bytes()
    payload["THIRD_PARTY_NOTICES.md"] = (root / "THIRD_PARTY_NOTICES.md").read_bytes()
    payload["references/source-catalog.json"] = (root / "docs/research/adoption.json").read_bytes()
    # 同一资料在原技能目录与整合包根目录使用不同相对路径。
    key = "references/adoption-map.md"
    payload[key] = payload[key].replace(b"../../../vendor/", b"../vendor/")
    return payload


def validate_payload(payload):
    names = set(payload)
    required = {"SKILL.md", "scripts/astock.py", "scripts/records.py", "scripts/src/astock/cli.py",
                "references/adoption-map.md", "references/continuity.md", "assets/profile-template.json"}
    if not required <= names:
        raise ValueError(f"缺少文件: {required - names}")
    modules = [n for n in names if re.fullmatch(r"modules/[^/]+/SKILL.md", n)]
    if len(modules) != 12:
        raise ValueError("必须保留全部12模块")
    for name, body in payload.items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("不安全路径")
        if name.endswith(".md"):
            for link in re.findall(r"\]\(([^)]+)\)", body.decode("utf-8")):
                if "://" in link or link.startswith("#"):
                    continue
                # 原始参考材料可能引用未包含的上游工程，不把它安装为独立技能。
                if name.startswith("vendor/"):
                    continue
                import posixpath
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), link.split("#")[0]))
                if target not in names:
                    raise ValueError(f"失效引用: {name} -> {link}")


def build(out, root=ROOT):
    payload = collect(root)
    validate_payload(payload)
    version = re.search(r'__version__\s*=\s*"([^"]+)"',
                        (root / "src/astock/__init__.py").read_text())[1]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    manifest = {"name": NAME, "version": version, "source_commit": sha,
                "source_state": "artifact_file_hashes_are_authoritative",
                "modules": sorted(n.split("/")[1] for n in payload if re.fullmatch(r"modules/[^/]+/SKILL.md", n)),
                "capabilities": {"core_python_tools": "LOCAL_VALIDATED",
                                 "target_coze_account": "NOT_DEPLOYED_OR_TESTED",
                                 "chanlun_engine": "UPSTREAM_REFERENCE_BUNDLED_NOT_INTEGRATED_OR_VALIDATED",
                                 "advanced_covariance_var_es": "LOCAL_VALIDATED_HISTORICAL_RISK_PROXY",
                                 "financial_red_flags": "SIX_RULE_SCREEN_NOT_FULL_AUDIT",
                                 "valuation_review": "NUMERIC_SENSITIVITY_NOT_GOVERNANCE_APPROVAL",
                                 "professional_source_archives": "REFERENCE_ONLY_NOT_EXECUTED",
                                 "qlib_walk_forward_ml": "METHOD_ONLY",
                                 "persistent_cloud_storage": "TARGET_CLIENT_VERIFICATION_REQUIRED",
                                 "broker_trading": False},
                "files": {n: hashlib.sha256(b).hexdigest() for n, b in sorted(payload.items())}}
    catalog = json.loads(payload["references/professional-catalog.json"])
    manifest["distribution_profile"] = catalog.get("distribution_profile", "PRIVATE_FULL_REFERENCES")
    manifest["bundled_professional_archives"] = sum(bool(e.get("archive")) for e in catalog["entries"])
    if not manifest["bundled_professional_archives"]:
        manifest["capabilities"]["professional_source_archives"] = "NOT_BUNDLED_IN_PUBLIC_SOURCE"
        manifest["capabilities"]["chanlun_engine"] = "NOT_BUNDLED_OR_INTEGRATED_IN_PUBLIC_SOURCE"
    payload["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, body in sorted(payload.items()):
            entry = zipfile.ZipInfo(f"{NAME}/{name}", (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, body)
    return {"path": str(out.resolve()), "version": version, "files": len(payload),
            "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "modules": len(manifest["modules"])}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="dist/a-share-family-suite.zip")
    args = p.parse_args()
    print(json.dumps(build(args.out), ensure_ascii=False, indent=2))
