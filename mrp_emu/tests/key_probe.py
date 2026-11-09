"""按键链路自检：UI 命中 -> 键值翻译 -> 事件送达 -> 画面变化。

覆盖老板报的「列表不响应触控」：
  第 1 层  ui.hit(坐标) 能否命中导航键 / 键盘
  第 2 层  ui.key_code(id) 能否翻译成正确的 mythroad 键值
  第 3 层  vm.key_event() 送达后 MRP 画面是否真的变化
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.consts import (  # noqa: E402
    KEY_DOWN,
    KEY_POWER,
    KEY_SELECT,
    KEY_SOFTLEFT,
    KEY_SOFTRIGHT,
    MR_KEY_PRESS,
    MR_KEY_RELEASE,
)
from mrp_emu.ui.skin import load_skin  # noqa: E402
from mrp_emu.ui.phone import PhoneUI  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(ROOT, "runtime")

ok_count = 0
fail_count = 0


def check(label, cond, detail=""):
    global ok_count, fail_count
    if cond:
        ok_count += 1
        print(f"  [PASS] {label}")
    else:
        fail_count += 1
        print(f"  [FAIL] {label}  {detail}")


def frame_bytes(app):
    return bytes(app.gfx.mem.read(app.gfx.fb_addr, app.gfx.w * app.gfx.h * 2))


def main():
    pygame.init()

    print("== 1. 常量对齐 mrporting.h ==")
    check("MR_KEY_PRESS == 0", MR_KEY_PRESS == 0, f"={MR_KEY_PRESS}")
    check("MR_KEY_RELEASE == 1", MR_KEY_RELEASE == 1, f"={MR_KEY_RELEASE}")
    check("MR_KEY_POWER == 16", KEY_POWER == 16, f"={KEY_POWER}")
    check("MR_KEY_SOFTLEFT == 17", KEY_SOFTLEFT == 17, f"={KEY_SOFTLEFT}")
    check("MR_KEY_SOFTRIGHT == 18", KEY_SOFTRIGHT == 18, f"={KEY_SOFTRIGHT}")
    check("MR_KEY_SELECT == 20", KEY_SELECT == 20, f"={KEY_SELECT}")
    check("MR_KEY_DOWN == 13", KEY_DOWN == 13, f"={KEY_DOWN}")

    print("\n== 2. 触控命中与键值翻译 ==")
    skin = load_skin(os.path.join(RUNTIME, "skin.json"))
    ui = PhoneUI(skin)
    cx, cy = ui.nav["cx"], ui.nav["cy"]
    hit_ok = ui.hit((cx, cy))
    check("点导航中心 -> nav:SELECT", hit_ok == "nav:SELECT", f"={hit_ok}")
    code_ok = ui.key_code(hit_ok) if hit_ok else None
    check("nav:SELECT 翻译为 20(选择)", code_ok == KEY_SELECT, f"={code_ok}")

    up_hit = ui.hit((cx, cy - int(ui.nav["r"] * 0.8)))
    check("点上方向 -> nav:UP", up_hit == "nav:UP", f"={up_hit}")
    down_hit = ui.hit((cx, cy + int(ui.nav["r"] * 0.8)))
    check("点下方向 -> nav:DOWN", down_hit == "nav:DOWN", f"={down_hit}")

    # 左软键：从皮肤里找
    soft = next((k for k in ui.keys if k["key"] == "SOFT_L"), None)
    if soft:
        x, y, w, h = soft["rect"]
        sid = ui.hit((x + w // 2, y + h // 2))
        check("点左软键命中", sid == soft["id"], f"={sid}")
        check("左软键翻译为 17", ui.key_code(sid) == KEY_SOFTLEFT, f"={ui.key_code(sid)}")

    print("\n== 2.5 屏幕点击 -> 按键映射（tap_to_key）==")
    sr = ui.screen_rect
    cx, cy = sr.center
    cases = [
        ((cx, sr.top + 20), "UP"),
        ((cx, sr.bottom - 60), "DOWN"),
        ((sr.left + 15, cy), "LEFT"),
        ((sr.right - 15, cy), "RIGHT"),
        ((cx, cy), "SELECT"),
        ((sr.left + 20, sr.bottom - 8), "SOFT_L"),
        ((sr.right - 20, sr.bottom - 8), "SOFT_R"),
    ]
    for pos, want in cases:
        sp = ui.screen_pos(pos)
        got = ui.tap_to_key(*sp) if sp else None
        check(f"点屏幕({pos[0]-sr.x},{pos[1]-sr.y}) -> {want}", got == want, f"={got}")

    # 窗口坐标 -> MRP 坐标换算（屏幕 240x320）
    sp = ui.screen_pos((sr.left + sr.w // 2, sr.top + sr.h // 2))
    check("screen_pos 中心 = (120,160)", sp == (120, 160), f"={sp}")
    outside = ui.screen_pos((cx, 10))
    check("屏幕外返回 None", outside is None, f"={outside}")

    print("\n== 3. 事件送达后画面是否变化 ==")
    cfunc = os.path.join(RUNTIME, "cfunction.ext")
    if not os.path.isfile(cfunc):
        print("  跳过：缺少 runtime/cfunction.ext")
        return 1

    vm = Vm(log=lambda m: None)
    app = App(vm, RUNTIME, log=lambda m: None)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    vm.load_code(cfunc)
    vm.ext_init()
    vm.dsm_init()
    r = vm.start_dsm("dsm_gm.mrp", "start.mr", None)
    check("start_dsm 成功", r in (0, 1), f"={r}")
    for _ in range(6):
        vm.timer()

    before = frame_bytes(app)
    ret = vm.key_event(KEY_DOWN, True)
    vm.key_event(KEY_DOWN, False)
    for _ in range(4):
        vm.timer()
    after = frame_bytes(app)

    diff = sum(1 for a, b in zip(before, after) if a != b)
    print(f"  画面变化字节数: {diff} (返回值 {ret})")
    check("按 DOWN 后画面有变化（高亮移动）", diff > 0, f"diff={diff}")

    # 再按一次 UP 应该回到原位
    vm.key_event(KEY_DOWN - 1, True)  # KEY_UP
    vm.key_event(KEY_DOWN - 1, False)
    for _ in range(4):
        vm.timer()
    back = frame_bytes(app)
    same_as_before = sum(1 for a, b in zip(before, back) if a != b)
    check("按 UP 回到首个选中项", same_as_before == 0, f"diff={same_as_before}")

    print("\n== 4. 按确定是否真的进入子应用 ==")
    helper_before = vm.mr_extHelper_addr
    p_before = vm.mr_c_function_P
    menu_frame = frame_bytes(app)

    vm.key_event(KEY_SELECT, True)
    vm.key_event(KEY_SELECT, False)
    for _ in range(20):
        vm.timer()
    game_frame = frame_bytes(app)

    entered = sum(1 for a, b in zip(menu_frame, game_frame) if a != b)
    print(f"  画面变化字节数: {entered}")
    print(f"  helper: 0x{helper_before:X} -> 0x{vm.mr_extHelper_addr:X}")
    print(f"  P     : 0x{p_before:X} -> 0x{vm.mr_c_function_P:X}")
    check("按确定后画面大幅变化（进入应用子菜单）", entered > 5000, f"diff={entered}")
    if vm.mr_extHelper_addr != helper_before:
        print("  注：helper 地址已变化 —— 子 ext 加载走了宿主回调，需做 P 栈")

    print(f"\n== 摘要 ==\n  通过 {ok_count} 项，失败 {fail_count} 项")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
