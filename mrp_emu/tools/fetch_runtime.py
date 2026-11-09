#!/usr/bin/env python3
"""从 vmrp 官方发行版抓取 MRP 运行时（cfunction.ext + mythroad 资源）。

没有 cfunction.ext 任何真实 mrp 都无法启动 —— 它就是 ARM 版的 mythroad 层。
本脚本下载 vmrp 的 Windows 发行包，把其中的运行时文件解到 ./runtime/。

用法:
    python tools/fetch_runtime.py
    python tools/fetch_runtime.py --zip 已下载的vmrp.zip   # 离线模式
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

RELEASE_URL = "https://github.com/vmrp/vmrp/releases/download/1.0.0/vmrp_win32_20220102.zip"

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"


def extract(zip_path: Path) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # 定位 cfunction.ext，把它所在目录当作运行时根
        ext_entry = next((n for n in names if Path(n).name.lower() == "cfunction.ext"), None)
        if ext_entry is None:
            print("发行包里没有 cfunction.ext，这个包可能不完整。")
            sys.exit(2)
        base = Path(ext_entry).parent

        copied = 0
        for n in names:
            p = Path(n)
            if p.suffix.lower() in (".dll", ".exe"):
                continue
            try:
                rel = p.relative_to(base)
            except ValueError:
                continue
            if not rel.parts or p.is_dir():  # 跳过目录自身条目
                continue
            target = RUNTIME / rel
            # 防御：zip 里同一名字可能既当文件又当目录出现
            if target.is_dir():
                continue
            if target.parent.is_file():
                target.parent.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(n) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            copied += 1
    print(f"已解出 {copied} 个文件到 {RUNTIME}")
    for p in sorted(RUNTIME.rglob("*"))[:20]:
        if p.is_file():
            print(f"  {p.relative_to(RUNTIME)}  {p.stat().st_size}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", help="使用已下载的 vmrp zip（离线）")
    args = ap.parse_args()

    if args.zip:
        extract(Path(args.zip))
        return 0

    cache = ROOT / "out" / "vmrp_release.zip"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.is_file():
        print(f"使用缓存 {cache}")
    else:
        print(f"下载 {RELEASE_URL} ...")
        try:
            urllib.request.urlretrieve(RELEASE_URL, cache)
        except Exception as exc:  # noqa: BLE001
            print(f"下载失败: {exc}")
            print("请手动下载后执行:  python tools/fetch_runtime.py --zip 路径.zip")
            return 1
    extract(cache)
    return 0


if __name__ == "__main__":
    sys.exit(main())
