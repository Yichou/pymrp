"""RX 管理器花屏诊断：无窗口跑一遍真实按键序列，记录所有桥接调用。

用法：
    python tests/rx_gfx_trace.py [输出前缀]

产出：
    out/<前缀>_start.png / _mid.png / _end.png  纯帧缓冲截图
    out/<前缀>_calls.txt                          调用统计与图形 API 明细

这是诊断工具，不参与自检；确认根因后保留作回归证据。
"""

from __future__ import annotations

import collections
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# PYMRP_FROM_PYZ=1 时优先从 mrp_emu.pyz 导入，用于验证打包产物
if os.environ.get("PYMRP_FROM_PYZ"):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "mrp_emu.pyz"))
else:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

pygame.init()

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.bridge import ARG_REGS, BridgeTable  # noqa: E402
from mrp_emu.catalog import probe_entry_ext  # noqa: E402
from mrp_emu.consts import KEY_NAME_TO_CODE  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

import mrp_emu  # noqa: E402

print(f"[import] mrp_emu from {mrp_emu.__file__}")

OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

# 关注这些名字：图形 / 刷屏 / 控件 / 平台扩展
WATCH = {
    "mr_drawBitmap", "drawBitmap", "_DrawBitmap", "_DrawBitmapEx", "_DrawPoint",
    "DrawRect", "_DrawText", "_DrawTextEx", "_BitmapCheck", "_DispUpEx",
    "_mr_EffSetCon", "mr_plat", "mr_platEx", "mr_getScreenInfo",
    "mr_getCharBitmap", "mr_screenBuf", "mr_menuCreate", "mr_menuShow",
    "mr_menuRefresh", "mr_dialogCreate", "mr_dialogRefresh", "mr_winCreate",
    "mr_textCreate", "mr_textRefresh", "mr_editCreate", "mr_platDrawChar",
    "mr_timerStart", "opendir", "readdir",
}
DETAIL_LIMIT = 4000

stats: collections.Counter = collections.Counter()
unimpl: collections.Counter = collections.Counter()
details: list[str] = []
orig_hook = BridgeTable._hook


def traced_hook(self, uc, address, size, user_data):
    f = self.dispatch.get(address)
    if f is not None:
        name = f.name
        stats[name] += 1
        if f.fn is None:
            unimpl[name] += 1
        if name in WATCH and len(details) < DETAIL_LIMIT:
            args = [uc.reg_read(r) for r in ARG_REGS]
            extra = ""
            if name in ("mr_plat", "mr_platEx"):
                code, iaddr, ilen = args[0], args[1], args[2]
                blob = b""
                if self._vm is not None and 0 < ilen <= 64 and self._vm.mem.valid(iaddr, ilen):
                    blob = self._vm.mem.read(iaddr, ilen)
                extra = f" code={code} in=@{iaddr:08X} len={ilen} blob={blob!r}"
            elif name in ("drawBitmap", "mr_drawBitmap", "_DrawBitmap", "_DrawBitmapEx"):
                from unicorn.arm_const import UC_ARM_REG_SP
                sp = uc.reg_read(UC_ARM_REG_SP)
                a4 = int.from_bytes(uc.mem_read(sp, 4), "little") if sp else 0
                bmp, x, y, w = args[:4]
                x = x - 0x100000000 if x & 0x80000000 else x
                y = y - 0x100000000 if y & 0x80000000 else y
                mem = self._vm.mem if self._vm is not None else None
                head = b""
                ok = False
                if mem is not None and 0 < w <= 480 and 0 < a4 <= 640:
                    ok = mem.valid(bmp, min(w * a4 * 2, 32))
                    if ok:
                        head = mem.read(bmp, 32)
                extra = (f" bmp=@{bmp:08X} x={x} y={y} w={w} h={a4} "
                         f"valid={ok} head={head[:32].hex()}")
            details.append(
                f"{self.name}.{name}{' [UNIMPL]' if f.fn is None else ''} "
                f"args=({', '.join(f'0x{a:08X}' for a in args)}){extra}"
            )
    return orig_hook(self, uc, address, size, user_data)


BridgeTable._hook = traced_hook


def shot(app: App, tag: str) -> None:
    p = OUT / f"{PREFIX}_{tag}.png"
    app.gfx.screenshot(p)
    print(f"[shot] {p}")


def shot_buf(app: App, addr: int, tag: str) -> None:
    """把任意一块 240x320 RGB565 内存导成 PNG（用于看 DSM 离屏缓冲）。"""
    import numpy as np
    raw = app.vm.mem.read(addr, app.gfx.size_bytes)
    a = np.frombuffer(raw, dtype="<u2").reshape(app.gfx.h, app.gfx.w)
    r = (((a >> 11) & 0x1F) << 3).astype(np.uint8)
    g = (((a >> 5) & 0x3F) << 2).astype(np.uint8)
    b = ((a & 0x1F) << 3).astype(np.uint8)
    surf = pygame.image.frombuffer(np.dstack((r, g, b)).tobytes(),
                                   (app.gfx.w, app.gfx.h), "RGB")
    p = OUT / f"{PREFIX}_{tag}.png"
    pygame.image.save(surf, p)
    print(f"[buf shot] 0x{addr:X} -> {p}")


def key(v: Vm, name: str) -> None:
    code = KEY_NAME_TO_CODE[name]
    v.key_event(code, True)
    v.timer()
    v.key_event(code, False)
    v.timer()


def main() -> int:
    global PREFIX
    PREFIX = sys.argv[1] if len(sys.argv) > 1 else "rx_trace"
    wd = ROOT / "runtime"
    target = wd / "mythroad" / "R_Xplore_MTK_all（RX管理器）.mrp"
    ext = wd / "cfunction.ext"
    if not target.is_file() or not ext.is_file():
        print("运行环境不完整：缺 cfunction.ext 或 RX 管理器 .mrp")
        return 2

    logs: list[str] = []
    vm = Vm(log=lambda *a: logs.append(" ".join(str(x) for x in a)))
    app = App(vm, wd, log=lambda *a: logs.append(" ".join(str(x) for x in a)),
              audio=False)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    vm.load_code(ext)
    vm.ext_init()
    vm.dsm_init()
    r = vm.start_dsm(target.name, probe_entry_ext(target), None)
    print(f"start_dsm -> {r}")
    shot(app, "start")

    seq = (["DOWN"] * 6 + ["SELECT"] + ["DOWN"] * 4 + ["SOFT_R"] +
           ["UP"] * 3 + ["SELECT"] + ["DOWN"] * 8 + ["SELECT"] + ["SOFT_R"] +
           ["1"] + ["DOWN"] * 10 + ["2"] + ["SOFT_L"] + ["3"] + ["SELECT"] +
           ["SOFT_R"] * 3 + ["UP"] * 12 + ["SELECT"] +
           ["LEFT", "RIGHT", "LEFT", "RIGHT", "CLEAR", "*", "#"] +
           ["DOWN"] * 20 + ["SELECT"] + ["SOFT_R"] * 5)
    for i, name in enumerate(seq):
        key(vm, name)
        if i == 20:
            shot(app, "mid")
    shot(app, "end")
    # DSM 层刷屏用的离屏全屏缓冲：所有 drawBitmap 调用的 bmp 参数都指向它
    bmp_addrs = [int(line.split("bmp=@")[1].split()[0], 16)
                 for line in details if "bmp=@" in line]
    if bmp_addrs:
        buf = collections.Counter(bmp_addrs).most_common(1)[0][0]
        print(f"fb_addr=0x{app.gfx.fb_addr:X}  dsm_buf=0x{buf:X}")
        shot_buf(app, buf, "dsmbuf")

    report = OUT / f"{PREFIX}_calls.txt"
    with report.open("w", encoding="utf-8") as fp:
        fp.write("=== 调用次数 Top 60 ===\n")
        for name, n in stats.most_common(60):
            fp.write(f"{n:8d}  {name}{'  [未实现]' if unimpl.get(name) else ''}\n")
        fp.write("\n=== 未实现但被调用的槽位 ===\n")
        for name, n in unimpl.most_common():
            fp.write(f"{n:8d}  {name}\n")
        fp.write(f"\n=== WATCH 明细（最多 {DETAIL_LIMIT} 条）===\n")
        fp.write("\n".join(details))
        fp.write("\n\n=== 宿主日志（尾部 200 行）===\n")
        fp.write("\n".join(logs[-200:]))
    print(f"[report] {report}")
    print("Top20:", stats.most_common(20))
    print("未实现:", unimpl.most_common(20))
    app.net.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
