#!/usr/bin/env python3
"""自检：Ctrl = 左软键、Alt = 右软键（含真实事件送达虚拟机）。

分两层：
  1. 单元  _key_name() 把 pygame 修饰键事件翻译成 MRP 键名，
           并挡住 AltGr / Ctrl+Shift 之类的误触发；
  2. 集成  往 pygame 事件队列注入 LCTRL / RALT / F1 / F2 的按下+松开，
           跑一次真实 CLI（box.mrp），断言 VM 收到了左右软键的 press/release。
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ["SDL_VIDEODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.init()

from mrp_emu.cli import KEYMAP, _key_name  # noqa: E402
from mrp_emu.consts import (  # noqa: E402
    KEY_NAME_TO_CODE,
    KEY_SOFTLEFT,
    KEY_SOFTRIGHT,
)

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


def ev(key, mod=0):
    return SimpleNamespace(key=key, mod=mod)


def unit():
    print("\n== 1. _key_name() 映射 ==")
    cases = [
        ("左 Ctrl", pygame.K_LCTRL, pygame.KMOD_LCTRL, "SOFT_L"),
        ("右 Ctrl", pygame.K_RCTRL, pygame.KMOD_RCTRL, "SOFT_L"),
        ("左 Alt", pygame.K_LALT, pygame.KMOD_LALT, "SOFT_R"),
        ("右 Alt", pygame.K_RALT, pygame.KMOD_RALT, "SOFT_R"),
        ("F1 保持", pygame.K_F1, 0, "SOFT_L"),
        ("F2 保持", pygame.K_F2, 0, "SOFT_R"),
        ("Esc 仍是挂机", pygame.K_ESCAPE, 0, "END"),
        ("回车仍是 OK", pygame.K_RETURN, 0, "SELECT"),
        ("数字键不受影响", pygame.K_5, pygame.KMOD_LCTRL, "5"),
        # KEYUP 时 SDL 可能已清掉自身修饰位，mod=0 也必须能配对释放
        ("左 Ctrl 松开(mod=0)", pygame.K_LCTRL, 0, "SOFT_L"),
        ("右 Alt 松开(mod=0)", pygame.K_RALT, 0, "SOFT_R"),
    ]
    for label, key, mod, want in cases:
        got = _key_name(ev(key, mod))
        check(label, got == want, f"got={got!r} want={want!r}")

    print("\n== 2. 组合键不误触发软键 ==")
    gui = getattr(pygame, "KMOD_GUI", 0)
    both = pygame.KMOD_CTRL | pygame.KMOD_ALT
    for label, key, mod in [
        ("AltGr 的 RALT 半边", pygame.K_RALT, both),
        ("AltGr 的 LCTRL 半边", pygame.K_LCTRL, both),
        ("Ctrl+Shift", pygame.K_LCTRL, pygame.KMOD_CTRL | pygame.KMOD_SHIFT),
        ("Alt+Shift", pygame.K_LALT, pygame.KMOD_ALT | pygame.KMOD_SHIFT),
        ("Ctrl+Win", pygame.K_LCTRL, pygame.KMOD_CTRL | gui),
    ]:
        if gui == 0 and "Win" in label:
            continue
        got = _key_name(ev(key, mod))
        check(label, got is None, f"got={got!r}")

    print("\n== 3. 映射表与常量一致 ==")
    for name, want in (("LCTRL", "SOFT_L"), ("RCTRL", "SOFT_L"),
                       ("LALT", "SOFT_R"), ("RALT", "SOFT_R")):
        check(f"KEYMAP[{name}]", KEYMAP.get(name) == want,
              f"got={KEYMAP.get(name)!r}")
    check("SOFT_L 有 MRP 键值", KEY_NAME_TO_CODE.get("SOFT_L") == KEY_SOFTLEFT)
    check("SOFT_R 有 MRP 键值", KEY_NAME_TO_CODE.get("SOFT_R") == KEY_SOFTRIGHT)


def integration():
    print("\n== 4. 真实 CLI：按键送达虚拟机 ==")
    runtime = ROOT / "runtime"
    mrp = runtime / "mythroad" / "box.mrp"
    if not (runtime / "cfunction.ext").is_file() or not mrp.is_file():
        print("  [SKIP] 缺少 runtime，跳过集成测试")
        return

    pygame.display.set_mode((300, 660))
    # 一次性注入 4 组完整的按下/松开；主循环第一帧会全部消费掉
    seq = [
        (pygame.K_LCTRL, pygame.KMOD_LCTRL, KEY_SOFTLEFT, "左 Ctrl"),
        (pygame.K_RCTRL, pygame.KMOD_RCTRL, KEY_SOFTLEFT, "右 Ctrl"),
        (pygame.K_LALT, pygame.KMOD_LALT, KEY_SOFTRIGHT, "左 Alt"),
        (pygame.K_RALT, pygame.KMOD_RALT, KEY_SOFTRIGHT, "右 Alt"),
        (pygame.K_F1, 0, KEY_SOFTLEFT, "F1"),
        (pygame.K_F2, 0, KEY_SOFTRIGHT, "F2"),
    ]
    for key, mod, _, _ in seq:
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=key, mod=mod, unicode=""))
        pygame.event.post(pygame.event.Event(
            pygame.KEYUP, key=key, mod=0, unicode=""))

    from mrp_emu.vm import Vm
    from mrp_emu.cli import main

    seen: list[tuple[int, bool]] = []
    orig = Vm.key_event

    def spy(self, code, pressed):
        seen.append((code, pressed))
        return orig(self, code, pressed)

    Vm.key_event = spy
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            main([str(mrp), "--workdir", str(runtime), "--headless",
                  "--frames", "3", "--audio", "off"])
    finally:
        Vm.key_event = orig

    for key, mod, code, label in seq:
        check(f"{label} → VM 收到 press", (code, True) in seen,
              f"seen={seen}")
        check(f"{label} → VM 收到 release", (code, False) in seen,
              f"seen={seen}")
    check("左右软键事件总数正确", len(seen) >= len(seq) * 2,
          f"seen={seen}")


def integration_launcher() -> None:
    """桌面/菜单/游戏中心模式下也要生效。独立子进程跑，避免同进程二次 init SDL。"""
    print("\n== 5. 系统桌面：Ctrl/Alt 当软键 ==")
    import subprocess
    import textwrap

    code = textwrap.dedent(f"""
        import contextlib, io, os, sys
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        sys.path.insert(0, {str(ROOT)!r})
        import pygame
        pygame.init(); pygame.display.set_mode((300, 660))
        from mrp_emu.ui.launcher import Launcher
        seen = []
        orig = Launcher.handle_key
        def spy(self, name):
            seen.append(name)
            return orig(self, name)
        Launcher.handle_key = spy
        for key, mod in ((pygame.K_LCTRL, pygame.KMOD_LCTRL),
                         (pygame.K_LALT, pygame.KMOD_LALT)):
            pygame.event.post(pygame.event.Event(
                pygame.KEYDOWN, key=key, mod=mod, unicode=''))
            pygame.event.post(pygame.event.Event(
                pygame.KEYUP, key=key, mod=0, unicode=''))
        from mrp_emu.cli import main
        with contextlib.redirect_stdout(io.StringIO()), \\
                contextlib.redirect_stderr(io.StringIO()):
            main(['--boot', 'home', '--workdir', {str(ROOT / 'runtime')!r},
                  '--headless', '--frames', '2', '--audio', 'off'])
        print('SEEN=' + ','.join(seen))
    """)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env,
                       capture_output=True, text=True, timeout=90)
    seen = ""
    for line in (r.stdout or "").splitlines():
        if line.startswith("SEEN="):
            seen = line[5:]
    names = [x for x in seen.split(",") if x]
    check("桌面收到左软键(左 Ctrl)", "SOFT_L" in names, f"seen={names} rc={r.returncode}")
    check("桌面收到右软键(左 Alt)", "SOFT_R" in names,
          f"seen={names} err={(r.stderr or '')[-300:]}")


def main() -> int:
    unit()
    integration()
    integration_launcher()
    print(f"\n== 摘要 ==\n  通过 {ok_count} 项，失败 {fail_count} 项")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
