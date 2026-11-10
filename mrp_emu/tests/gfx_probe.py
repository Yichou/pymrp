#!/usr/bin/env python3
"""图形层探针：DSM 脏矩形刷屏语义 + RX 管理器花屏回归。

背景（2026-11-10）：dsm_require_funcs.drawBitmap 曾被复用成 mr_table 的
紧凑位图 blit，导致 RX 管理器局部刷新时把屏顶标题栏贴到列表行上，
出现「重复标题栏 + 蓝色斜纹」。这里同时验证：

1. 两条 drawBitmap 路径绑定不同实现；
2. refresh_rect 按「全屏 stride」取源、只改脏矩形；
3. 旧紧凑语义在这个输入下确实会错（证明用例有区分度）；
4. 真实 RX 管理器 90 步按键期间，每一次 DSM 刷新后 fb 与离屏缓冲一致。

用法：python tests/gfx_probe.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

pygame.init()

from mrp_emu.api import impl  # noqa: E402
from mrp_emu.api.dsmfuncs import ALIAS, DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.catalog import probe_entry_ext  # noqa: E402
from mrp_emu.consts import KEY_NAME_TO_CODE  # noqa: E402
from mrp_emu.gfx import Gfx  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402
from rx_env import RX_MRP, make_rx_env  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  {detail}" if detail else ""))
    if cond:
        PASS += 1
    else:
        FAIL += 1


def new_vm(tmp: Path):
    vm = Vm(log=lambda *a: None)
    app = App(vm, tmp, log=lambda *a: None, audio=False)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    return vm, app


# ---------------------------------------------------------------- 1. 绑定
def test_bindings() -> None:
    print("\n-- 两条 drawBitmap 路径必须分开 --")
    check("ALIAS[drawBitmap] == dsm_drawBitmap",
          ALIAS.get("drawBitmap") == "dsm_drawBitmap", str(ALIAS.get("drawBitmap")))
    dsm_impl = impl.get("dsm_drawBitmap")
    mrp_impl = impl.get("mr_drawBitmap")
    check("两个实现都存在", dsm_impl is not None and mrp_impl is not None)
    check("两个实现不是同一个函数", dsm_impl is not mrp_impl)
    slot = next((f for f in DSM_FUNCS if f.name == "drawBitmap"), None)
    check("dsm 槽位绑定 dsm_drawBitmap", slot is not None and slot.fn is dsm_impl)
    mr_slot = next((f for f in MR_TABLE if f.name == "mr_drawBitmap"), None)
    check("mr_table 槽位仍绑定紧凑位图实现",
          mr_slot is not None and mr_slot.fn is mrp_impl)


# ---------------------------------------------------------------- 2. 语义
def test_refresh_semantics(vm, app) -> None:
    print("\n-- refresh_rect：全屏 stride 脏矩形同步 --")
    W, H = app.gfx.w, app.gfx.h
    buf = vm.mem.malloc(W * H * 2)
    check("离屏全屏缓冲分配成功", buf != 0, f"0x{buf:X}")
    if not buf:
        return
    # 每个像素值 = y*W+x，保证 (x,y) 唯一（16 位内不回绕，脏矩形区域 < 65536）
    pattern = (np.arange(H, dtype=np.uint32)[:, None] * W
               + np.arange(W, dtype=np.uint32)[None, :]).astype("<u2")
    vm.mem.write(buf, pattern.tobytes())

    app.gfx.clear(0)
    ok = app.gfx.refresh_rect(buf, 3, 61, 226, 26)
    fb = app.gfx.array()
    check("按全屏 stride 同步成功", ok)
    check("目标矩形与源缓冲同位置逐像素一致",
          np.array_equal(fb[61:87, 3:229], pattern[61:87, 3:229]))
    check("矩形之外保持清屏（未被误写）",
          bool(np.all(fb[:61, :] == 0) and np.all(fb[87:, :] == 0)
               and np.all(fb[61:87, :3] == 0) and np.all(fb[61:87, 229:] == 0)))

    # 敏感性对照：旧实现（紧凑 w 行跨度）在同一输入下必然错位
    app.gfx.clear(0)
    app.gfx.draw_bitmap(buf, 3, 61, 226, 26)
    bad = app.gfx.array()
    check("紧凑 blit 用在此处确实会错位（用例有区分度）",
          not np.array_equal(bad[61:87, 3:229], pattern[61:87, 3:229]))

    # 整屏刷新两种语义等价，回归不能破坏老应用
    app.gfx.clear(0)
    check("整屏刷新成功", app.gfx.refresh_rect(buf, 0, 0, W, H))
    check("整屏刷新后 fb == 源缓冲", np.array_equal(app.gfx.array(), pattern))

    # 裁剪与同址
    app.gfx.clear(0)
    check("越界矩形被裁剪不抛异常",
          app.gfx.refresh_rect(buf, 200, 300, 100, 100))
    check("右下角内容取自源的同位置",
          np.array_equal(app.gfx.array()[300:320, 200:240],
                         pattern[300:320, 200:240]))
    check("源 == fb 时直接视为已同步",
          app.gfx.refresh_rect(app.gfx.fb_addr, 0, 0, W, H))
    check("空地址被安全忽略", not app.gfx.refresh_rect(0, 0, 0, 10, 10))


# ---------------------------------------------------------------- 3. 真机
RX_STEPS = (["DOWN"] * 6 + ["SELECT"] + ["DOWN"] * 4 + ["SOFT_R"] +
            ["UP"] * 3 + ["SELECT"] + ["DOWN"] * 8 + ["SELECT"] + ["SOFT_R"] +
            ["1"] + ["DOWN"] * 10 + ["2"] + ["SOFT_L"] + ["3"] + ["SELECT"] +
            ["SOFT_R"] * 3 + ["UP"] * 12 + ["SELECT"] +
            ["LEFT", "RIGHT", "LEFT", "RIGHT", "CLEAR", "*", "#"] +
            ["DOWN"] * 20 + ["SELECT"] + ["SOFT_R"] * 5)


def test_rx_live() -> None:
    print("\n-- 真实 RX 管理器：每次 DSM 刷新后立即比对 fb --")
    # 固定隔离环境：不带应用自建的 brw/ cookie/ app240320/ 缓存目录，
    # 否则目录枚举结果会随上一次运行漂移，90 步按键不可复现（见 rx_env.py）
    wd, cleanup = make_rx_env(ROOT / "runtime")
    if wd is None:
        print("  skip 运行环境不完整（缺 cfunction.ext 或 RX 管理器 .mrp）")
        return
    target = wd / "mythroad" / RX_MRP
    ext = wd / "cfunction.ext"

    calls: list[tuple[int, int, int, int]] = []
    mismatches: list[tuple[int, int, int, int, int]] = []
    orig = Gfx.refresh_rect

    def checked(self, buf_addr, x, y, w, h):
        ok = orig(self, buf_addr, x, y, w, h)
        if ok:
            calls.append((x, y, w, h))
            W = self.w
            x0, y0 = max(0, x), max(0, y)
            x1, y1 = min(W, x + w), min(self.h, y + h)
            n = (x1 - x0) * 2
            for row in range(y0, y1):
                off = (row * W + x0) * 2
                if self.mem.read(self.fb_addr + off, n) != self.mem.read(buf_addr + off, n):
                    mismatches.append((row, x, y, w, h))
                    break
        return ok

    Gfx.refresh_rect = checked
    try:
        vm = Vm(log=lambda *a: None)
        app = App(vm, wd, log=lambda *a: None, audio=False)
        vm.app = app
        vm.install_tables(MR_TABLE, DSM_FUNCS)
        vm.load_code(ext)
        vm.ext_init()
        vm.dsm_init()
        r = vm.start_dsm(target.name, probe_entry_ext(target), None)
        check("RX 管理器启动成功", r in (0, 1), f"r={r}")

        crashed = ""
        try:
            for i, name in enumerate(RX_STEPS):
                code = KEY_NAME_TO_CODE[name]
                vm.key_event(code, True)
                vm.timer()
                vm.key_event(code, False)
                vm.timer()
                if i == 20:
                    out = ROOT / "out"
                    out.mkdir(exist_ok=True)
                    app.gfx.screenshot(out / "gfx_probe_rx_mid.png")
        except Exception as exc:  # noqa: BLE001
            crashed = f"{type(exc).__name__}: {exc}"
        check("90 步按键无异常", not crashed, crashed)
        check("DSM 脏矩形刷新被调用", len(calls) >= 20, f"共 {len(calls)} 次")
        partial = [c for c in calls if c[2:] != (app.gfx.w, app.gfx.h)
                   or c[:2] != (0, 0)]
        check("包含局部（非整屏）刷新", len(partial) >= 5, f"局部 {len(partial)} 次")
        check("每次刷新后 fb 与离屏缓冲一致（无花屏）",
              not mismatches, f"不一致 {len(mismatches)} 次，例：{mismatches[:3]}")
        app.net.shutdown()
    finally:
        Gfx.refresh_rect = orig
        cleanup()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mrp_gfx_probe_"))
    test_bindings()
    vm, app = new_vm(tmp)
    test_refresh_semantics(vm, app)
    app.net.shutdown()
    test_rx_live()
    print(f"\n==== gfx_probe: {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
