#!/usr/bin/env python3
"""安装后自包含；源码中使用仓库运行器。"""
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
runtime = here / "src"
if not runtime.exists():
    runtime = here.parents[2] / "src"
sys.path.insert(0, str(runtime))
from astock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

