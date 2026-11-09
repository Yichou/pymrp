"""触摸事件直通验证：点击坐标是否原样进入虚拟机的 dsm_event 结构体。

不做任何映射，只验证 mr_event 链路上的三个值：
    dsm_event[0] = MR_MOUSE_* 事件码
    dsm_event[4] = x
    dsm_event[8] = y
与 vmrp 的 main.c 行为对齐：
    case SDL_MOUSEMOTION:    if (isMouseDown) event(MR_MOUSE_MOVE, x, y);
    case SDL_MOUSEBUTTONDOWN: isMouseDown = true; event(MR_MOUSE_DOWN, x, y);
    case SDL_MOUSEBUTTONUP:   isMouseDown = false; event(MR_MOUSE_UP, x, y);
"""

import os
import struct
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.consts import (  # noqa: E402
    MR_MOUSE_DOWN,
    MR_MOUSE_MOVE,
    MR_MOUSE_UP,
)
from mrp_emu.vm import Vm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(ROOT, "runtime")

ok = 0
bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print(f"  [PASS] {label}")
    else:
        bad += 1
        print(f"  [FAIL] {label}  {detail}")


def main():
    print("== 1. 事件码对齐 mrporting.h / main.c ==")
    check("MR_MOUSE_DOWN == 2", MR_MOUSE_DOWN == 2, f"={MR_MOUSE_DOWN}")
    check("MR_MOUSE_UP == 3", MR_MOUSE_UP == 3, f"={MR_MOUSE_UP}")
    check("MR_MOUSE_MOVE == 12", MR_MOUSE_MOVE == 12, f"={MR_MOUSE_MOVE}")

    print("\n== 2. 坐标是否原样写入 dsm_event ==")
    vm = Vm(log=lambda m: None)
    app = App(vm, RUNTIME, log=lambda m: None)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)

    # 拦截真正送进 ARM 的 mr_event，记录 dsm_event 里的三元组。
    # 这里用纯记录桩，不真的跳进 ARM（此时还没加载 cfunction.ext）。
    seen = []
    orig_mr_event = vm.mr_event

    def spy(code, p0, p1):
        triple = struct.unpack("<III", vm.mem.read(vm.dsm_event, 12))
        seen.append((code, triple))
        return 0

    vm.mr_event = spy

    vm.touch_event(MR_MOUSE_DOWN, 120, 160)
    vm.touch_event(MR_MOUSE_MOVE, 130, 170)
    vm.touch_event(MR_MOUSE_UP, 135, 175)

    check("发了 3 个事件", len(seen) == 3, f"={len(seen)}")
    for i, (want_code, want_xy) in enumerate(
        [(MR_MOUSE_DOWN, (120, 160)),
         (MR_MOUSE_MOVE, (130, 170)),
         (MR_MOUSE_UP, (135, 175))]
    ):
        if i >= len(seen):
            break
        got_code, (g_code, gx, gy) = seen[i]
        check(
            f"事件{i} 码={want_code} 坐标={want_xy}",
            g_code == want_code and (gx, gy) == want_xy,
            f"实际 码={g_code} 坐标=({gx},{gy})",
        )

    print("\n== 3. 越界/异常输入 ==")
    try:
        vm.touch_event(MR_MOUSE_DOWN, 9999, -5)
        passed = True
    except Exception as exc:  # noqa: BLE001
        passed = False
        print(f"  异常: {exc}")
    check("极端坐标不抛异常（原样传递）", passed)

    try:
        vm.touch_event(77, 1, 1)
        rejected = False
    except ValueError:
        rejected = True
    check("非触摸事件码被拒绝", rejected)

    print("\n== 4. 真实应用中原样送达 ==")
    cfunc = os.path.join(RUNTIME, "cfunction.ext")
    if not os.path.isfile(cfunc):
        print("  跳过：缺少 runtime/cfunction.ext")
    else:
        vm.mr_event = orig_mr_event  # 先卸掉 spy，避免干扰
        vm.load_code(cfunc)
        vm.ext_init()
        vm.dsm_init()
        r = vm.start_dsm("dsm_gm.mrp", "start.mr", None)
        check("dsm_gm 启动", r in (0, 1), f"={r}")
        for _ in range(6):
            vm.timer()
        ret = vm.touch_event(MR_MOUSE_DOWN, 120, 160)
        ret2 = vm.touch_event(MR_MOUSE_UP, 120, 160)
        print(f"  返回值: DOWN={ret} UP={ret2}（应用不处理触摸时通常非 0）")
        check("触摸事件未导致崩溃", True)

    print(f"\n== 摘要 ==\n  通过 {ok} 项，失败 {bad} 项")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
