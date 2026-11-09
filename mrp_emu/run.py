#!/usr/bin/env python3
"""启动脚本。

用法:
    python run.py                 # 演示模式（未加载 mrp 时显示功能机界面）
    python run.py game.mrp        # 运行 mrp
    python run.py --help
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    try:
        import unicorn  # noqa: F401
        import pygame   # noqa: F401
    except ImportError as exc:
        print(f"缺少依赖: {exc.name}")
        print("请先执行:  pip install -r requirements.txt")
        return 5

    from mrp_emu.cli import main as cli_main
    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
