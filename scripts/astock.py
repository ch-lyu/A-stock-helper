#!/usr/bin/env python3
"""从源码运行，避免用户必须先安装 Python 包。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from astock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
