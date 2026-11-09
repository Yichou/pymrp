"""把 mrp_emu 打包成单文件 .pyz（Python zipapp）。

用法:
    python build_pyz.py                 # 产出 mrp_emu.pyz
    python build_pyz.py -o dist/emu.pyz # 指定输出

注意:
  * .pyz 只装代码，不含 runtime/（cfunction.ext、字库、游戏）。
    运行时仍需把 runtime/ 放在 pyz 同级目录或当前目录，或者用 --workdir 指定。
  * 第三方依赖（unicorn / pygame / numpy）不打进去，需要 pip 安装。
"""

from __future__ import annotations

import argparse
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "mrp_emu"

MAIN_TEMPLATE = '''\
# -*- coding: utf-8 -*-
"""mrp_emu 单文件入口（由 build_pyz.py 生成）。"""
import sys

from mrp_emu.cli import main

if __name__ == "__main__":
    sys.exit(main())
'''


def iter_sources():
    for p in sorted(PKG.rglob("*.py")):
        parts = set(p.parts)
        if "__pycache__" in parts:
            continue
        yield p


def build(target: Path, compress: bool = True) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    mode = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    count = 0
    with zipfile.ZipFile(target, "w", mode) as z:
        for src in iter_sources():
            arc = src.relative_to(ROOT).as_posix()
            z.write(src, arc)
            count += 1
        z.writestr("__main__.py", MAIN_TEMPLATE)
        count += 1

    size = target.stat().st_size
    print(f"[pyz] {target.name}")
    print(f"[pyz] 打包 {count - 1} 个模块 + 入口，共 {size / 1024:.1f} KB")
    print(f"[pyz] 路径 {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="打包 mrp_emu 为 .pyz")
    ap.add_argument("-o", "--output", default="mrp_emu.pyz", help="输出文件")
    ap.add_argument("--no-compress", action="store_true", help="不压缩（加载略快）")
    args = ap.parse_args(argv)

    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    t0 = time.time()
    rc = build(out, compress=not args.no_compress)
    print(f"[pyz] 耗时 {time.time() - t0:.2f}s")
    print(f"\n运行方式:\n  python {out.name}"
          f"\n  python {out.name} --headless --screenshot out/pyz.png")
    return rc


if __name__ == "__main__":
    sys.exit(main())
