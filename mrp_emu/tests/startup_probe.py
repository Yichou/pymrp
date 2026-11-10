#!/usr/bin/env python3
"""启动性能回归：启动路径不许再碰 SDL 音频慢枚举。

背景（2026-11-10 实测，Windows 无音频输出端点 + SDL 2.28.4）：

    pygame.init()          8.1s   <- 连带 SDL_INIT_AUDIO，WASAPI 枚举超时
    pygame.mixer.init()    8.0s   <- AudioEngine 启动时又同步开一次
    端到端基线            17.1s

改法：cli 只做 display+font 最小初始化；AudioEngine._init() 先用 winmm
的 waveOutGetNumDevs() 快速判断有没有音频端点，没有就直接静音。
优化后端到端 ~0.85s。这个探针把「不许退化回 17 秒」钉死。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.pop("SDL_AUDIODRIVER", None)   # 测真实设备探测路径，不要用 dummy 绕过

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from mrp_emu.audio.mixer import AudioEngine  # noqa: E402
from mrp_emu.cli import init_pygame_minimal  # noqa: E402

FAILS: list[str] = []
PASS = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS
    if ok:
        PASS += 1
        print(f"  [PASS] {name}" + (f"  {detail}" if detail else ""))
    else:
        FAILS.append(name)
        print(f"  [FAIL] {name}  {detail}")


def run_sub(args: list[str], extra_env: dict | None = None,
            timeout: float = 60) -> tuple[int, float, str]:
    env = dict(os.environ)
    env.pop("SDL_AUDIODRIVER", None)
    if extra_env:
        env.update(extra_env)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), *args],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, time.perf_counter() - t0, proc.stdout + proc.stderr


def main() -> int:
    print("== 1. 最小 SDL 初始化 ==")

    real_init = pygame.init

    def forbidden_init():
        raise AssertionError("启动路径调用了 pygame.init()（会连带 SDL_INIT_AUDIO）")

    pygame.init = forbidden_init  # type: ignore[assignment]
    t0 = time.perf_counter()
    try:
        init_pygame_minimal()
        check("未调用 pygame.init()", True)
    except AssertionError as exc:
        check("未调用 pygame.init()", False, str(exc))
    finally:
        pygame.init = real_init  # type: ignore[assignment]
    init_ms = (time.perf_counter() - t0) * 1000

    check("display 已初始化", bool(pygame.display.get_init()))
    check("font 已初始化", bool(pygame.font.get_init()))
    check("最小初始化 < 100ms", init_ms < 100, f"{init_ms:.1f}ms")
    check("mixer 未被初始化（启动零音频开销）",
          pygame.mixer.get_init() is None, str(pygame.mixer.get_init()))

    # 主循环真正会用到的 API 在「只 init display+font」下必须全部可用
    try:
        clock = pygame.time.Clock()
        clock.tick(60)
        pygame.event.pump()
        surf = pygame.Surface((32, 16))
        f = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 12) \
            if Path("C:/Windows/Fonts/msyh.ttc").is_file() \
            else pygame.font.Font(None, 12)
        surf.blit(f.render("中文", True, (255, 255, 255)), (0, 0))
        check("Clock / event / Surface / 中文字体可用", True)
    except Exception as exc:  # noqa: BLE001
        check("Clock / event / Surface / 中文字体可用", False, repr(exc))

    print("\n== 2. 音频设备快速探测 ==")
    check("_device_probe 存在", hasattr(AudioEngine, "_device_probe"))

    old_drv = os.environ.get("SDL_AUDIODRIVER")
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    check("显式 SDL_AUDIODRIVER 时不做探测", AudioEngine._device_probe() is True)
    if old_drv is None:
        os.environ.pop("SDL_AUDIODRIVER", None)
    else:
        os.environ["SDL_AUDIODRIVER"] = old_drv

    import mrp_emu.audio.mixer as mixer_mod
    old_platform = mixer_mod.sys.platform
    mixer_mod.sys.platform = "linux"
    check("非 Windows 平台直接交给 SDL", AudioEngine._device_probe() is True)
    mixer_mod.sys.platform = old_platform

    # 本机（无音频端点）应快速返回 False；有声卡的机器跳过这一条
    no_device = (sys.platform == "win32" and AudioEngine._device_probe() is False)
    if no_device:
        t0 = time.perf_counter()
        for _ in range(20):
            AudioEngine._device_probe()
        probe_ms = (time.perf_counter() - t0) * 1000 / 20
        check("本机无声卡：探测返回 False", True)
        check("单次探测 < 20ms", probe_ms < 20, f"{probe_ms:.3f}ms")
    else:
        check("本机有声卡/非 Win：探测放行", AudioEngine._device_probe() is True)
        check("单次探测 < 20ms（跳过计时）", True, "SKIP")

    print("\n== 3. 无设备时不碰 mixer.init ==")
    logs: list[str] = []
    calls = {"init": 0}
    real_mixer_init = pygame.mixer.init
    orig_probe = AudioEngine.__dict__["_device_probe"]   # 保留 staticmethod 描述器

    def counting_init(*a, **kw):
        calls["init"] += 1
        raise AssertionError("无声卡时不应调用 mixer.init()")

    AudioEngine._device_probe = staticmethod(lambda: False)
    pygame.mixer.init = counting_init  # type: ignore[assignment]
    t0 = time.perf_counter()
    try:
        eng = AudioEngine(sample_rate=44100, enabled=True, log=logs.append)
        cost_ms = (time.perf_counter() - t0) * 1000
    finally:
        pygame.mixer.init = real_mixer_init  # type: ignore[assignment]
        AudioEngine._device_probe = orig_probe  # type: ignore[assignment]

    check("mixer.init 调用 0 次", calls["init"] == 0, str(calls["init"]))
    check("引擎静音降级", eng.ok is False)
    check("构造 < 200ms", cost_ms < 200, f"{cost_ms:.1f}ms")
    check("有明确日志", any("跳过 mixer 初始化" in x for x in logs), str(logs[-1:]))
    r = eng.play(1, b"RIFF", False)
    check("静音时 play 仍返回成功（老应用不刷屏重试）", r == 0, f"={r}")
    eng.shutdown()

    print("\n== 4. 端到端启动（子进程，真实音频路径）==")
    rc, wall, out = run_sub(["--demo", "--headless", "--frames", "3"])
    check("headless 启动 rc=0", rc == 0, f"rc={rc} {out[-160:]}")
    check("headless 端到端 < 6s（基线 17.1s）", wall < 6.0, f"{wall:.2f}s")
    if no_device:
        check("日志含快速静音提示", "跳过 mixer 初始化" in out)

    rc, wall2, out2 = run_sub(["--demo", "--frames", "3"])
    check("--frames 在窗口模式也生效", rc == 0 and wall2 < 6.0,
          f"rc={rc} wall={wall2:.2f}s")

    rc, wall3, out3 = run_sub(["--demo", "--headless", "--frames", "3"],
                              {"PYMRP_TIMING": "1"})
    check("PYMRP_TIMING 输出首帧打点", "首帧上屏" in out3, out3[-200:])
    m = re.search(r"首帧上屏（界面可见）: ([\d.]+) ms", out3)
    check("首帧 < 1500ms", m is not None and float(m.group(1)) < 1500,
          f"{m.group(1) + 'ms' if m else '未解析到打点'}")

    rc, _, out4 = run_sub(["--demo", "--headless", "--frames", "2",
                           "--audio-driver", "dummy"])
    check("--audio-driver dummy 显式驱动可用", rc == 0, f"rc={rc}")
    rc, _, _ = run_sub(["--demo", "--headless", "--frames", "2", "--audio", "off"])
    check("--audio off 可用", rc == 0, f"rc={rc}")

    print(f"\n== 摘要 ==  启动探针 {PASS} 项通过 / {len(FAILS)} 项失败  "
          f"(headless {wall:.2f}s, 窗口 {wall2:.2f}s)")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
