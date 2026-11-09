"""命令行入口与主循环。"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# 键盘 -> MRP 键名
KEYMAP = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT",
    "ENTER": "SELECT", "F1": "SOFT_L", "F2": "SOFT_R",
    "ESCAPE": "END", "BACKSPACE": "CLEAR",
    "ASTERISK": "*", "HASH": "#",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mrp_emu",
        description="MRP 模拟器（Python + Unicorn），UI 模拟 MTK 直板机",
    )
    p.add_argument("mrp", nargs="?", help="要运行的 .mrp 文件")
    p.add_argument("--workdir", help="工作目录（存放 cfunction.ext 与 mythroad 资源）")
    p.add_argument("--runtime", help="cfunction.ext 路径，或包含它的目录")
    p.add_argument("--ext", default="", help="mrp 内入口 ext 名；留空自动判断（启动器用 start.mr，普通应用用 cfunction.ext）")
    p.add_argument("--skin", help="皮肤 JSON 路径")
    p.add_argument("--scale", type=float, default=0.0, help="界面缩放倍数，0=自动")
    p.add_argument("--headless", action="store_true", help="无窗口模式，渲染一帧后退出")
    p.add_argument("--screenshot", help="把界面截图保存到指定 PNG")
    p.add_argument("--frames", type=int, default=0, help="headless 模式渲染帧数（默认 1）")
    p.add_argument("--verbose", action="store_true", help="打印每次 API 调用")
    p.add_argument("--stats", action="store_true", help="退出时打印统计")
    p.add_argument("--demo", action="store_true", help="强制演示模式（不加载 runtime）")
    p.add_argument(
        "--audio", choices=("auto", "on", "off"), default="auto",
        help="声音：auto=有音频设备就开、没有就静音降级（默认）；on=强制开；off=完全静音",
    )
    p.add_argument("--audio-rate", type=int, default=44100, help="混音采样率，默认 44100")
    p.add_argument(
        "--pcm-rate", type=int, default=8000,
        help="MR_SOUND_PCM 流的采样率，默认 8000（mrporting.h 注释 //8K）",
    )
    p.add_argument(
        "--touch", choices=("native", "nav", "off"), default="native",
        help="点屏幕的行为：native=把点击坐标用 mr_event(MR_MOUSE_*) 直接传给虚拟机（默认，"
             "与 vmrp 的 main.c 一致）；nav=翻译成方向键/确定（可选辅助）；off=不处理",
    )
    return p


def prog_dir() -> Path:
    """程序自身所在目录（兼容 .pyz：此时 __file__ 在 zip 内，不能用）。"""
    try:
        return Path(sys.argv[0]).resolve().parent
    except Exception:  # noqa: BLE001 - 交互式环境/异常 argv 退化为当前目录
        return Path.cwd()


def find_runtime(workdir: Path, explicit: str | None) -> Path | None:
    cands: list[Path] = []
    if explicit:
        e = Path(explicit)
        cands.append(e if e.is_file() else e / "cfunction.ext")
    cands += [
        workdir / "cfunction.ext",
        workdir / "mythroad" / "cfunction.ext",
        Path.cwd() / "cfunction.ext",
        Path.cwd() / "bin" / "cfunction.ext",
        Path.cwd() / "runtime" / "cfunction.ext",
        Path.cwd() / "runtime" / "mythroad" / "cfunction.ext",
        prog_dir() / "runtime" / "cfunction.ext",
        prog_dir() / "cfunction.ext",
    ]
    for c in cands:
        if c.is_file():
            return c
    return None


# ---------------------------------------------------------------- 演示画面
def paint_demo(gfx, app, last_key: str) -> None:
    import numpy as np

    h, w = gfx.h, gfx.w
    ys = np.linspace(0.0, 1.0, h)[:, None]
    r = (18 * (1 - ys) + 4 * ys).astype(np.int32)
    g = (34 * (1 - ys) + 8 * ys).astype(np.int32)
    b = (58 * (1 - ys) + 16 * ys).astype(np.int32)
    col = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    arr = np.repeat(col, w, axis=1).astype("<u2")
    gfx.mem.write(gfx.fb_addr, arr.tobytes())

    gfx.overlay_clear()
    gfx.status_bar("中国移动", time.strftime("%H:%M"))
    gfx.text_center("MRP 模拟器", w // 2, 96, (240, 246, 255), size=22)
    gfx.text_center("Python + Unicorn", w // 2, 124, (140, 170, 210), size=11)

    if app.mrp_name:
        gfx.text_center(app.mrp_name[:26], w // 2, 160, (200, 214, 232), size=12)
    gfx.text_center("未找到 cfunction.ext", w // 2, 190, (250, 190, 120), size=12)
    gfx.text_center("请从 vmrp 发行版解压到工作目录", w // 2, 208, (150, 160, 176), size=10)

    if last_key:
        gfx.text_center(f"按键 {last_key}", w // 2, 250, (140, 230, 170), size=13)

    gfx.soft_keys("演示模式", "退出")
    pygame_dummy = None  # noqa: F841


# ---------------------------------------------------------------- 主程序
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

    import pygame

    from .api.dsmfuncs import DSM_FUNCS
    from .api.mrtable import MR_TABLE
    from .app import App
    from .consts import KEY_NAME_TO_CODE
    from .ui.phone import PhoneUI
    from .ui.skin import load_skin
    from .vm import Vm

    def log(msg: str) -> None:
        print(msg, flush=True)

    pygame.init()

    # ---------------- 工作目录
    mrp_path = Path(args.mrp).resolve() if args.mrp else None
    if args.workdir:
        workdir = Path(args.workdir).resolve()
    elif mrp_path:
        workdir = mrp_path.parent
    else:
        workdir = Path.cwd() / "runtime"
        if not workdir.is_dir():
            alt = prog_dir() / "runtime"
            if alt.is_dir():
                workdir = alt
    workdir.mkdir(parents=True, exist_ok=True)

    # ---------------- 皮肤与界面
    skin = load_skin(args.skin or (workdir / "skin.json"))
    ui = PhoneUI(skin)

    # ---------------- 虚拟机
    vm = Vm(log=log)
    app = App(
        vm, workdir, log=log,
        audio=(args.audio != "off"),
        sample_rate=args.audio_rate,
        pcm_rate=args.pcm_rate,
    )
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)

    for t in vm.tables.values():
        t.verbose = args.verbose

    if args.verbose:
        missing = sorted({f.name for f in MR_TABLE if f.fn is None})
        log(f"[api] 未实现槽位 {len(missing)} 项: {', '.join(missing[:12])}"
            + (" ..." if len(missing) > 12 else ""))

    # ---------------- 运行 MRP
    runtime = None if args.demo else find_runtime(workdir, args.runtime)

    # 没指定 mrp 时，自动找启动器 dsm_gm.mrp —— 双击 run.bat 就能直接进应用列表
    if runtime and mrp_path is None and not args.demo:
        auto = workdir / "mythroad" / "dsm_gm.mrp"
        if not auto.is_file():
            found = sorted(workdir.rglob("dsm_gm.mrp"))
            auto = found[0] if found else None
        if auto and auto.is_file():
            mrp_path = auto
            log(f"[vm] 未指定 mrp，自动使用启动器 {auto.relative_to(workdir)}")

    ext_name = args.ext
    if not ext_name:
        ext_name = ("start.mr" if mrp_path and mrp_path.name.lower() == "dsm_gm.mrp"
                    else "cfunction.ext")
    mrp_loaded = False
    if runtime and mrp_path:
        app.mrp_name = mrp_path.name
        try:
            vm.load_code(runtime)
            vm.ext_init()
            if vm.dsm_init():
                r = vm.start_dsm(mrp_path.name, ext_name, None)
                log(f"[vm] start_dsm('{mrp_path.name}', '{ext_name}') -> {r}")
                mrp_loaded = r in (0, 1)
                if not mrp_loaded:
                    log("[vm] 启动返回值异常，请尝试 --ext start.mr 或改用启动器 dsm_gm.mrp")
        except Exception as exc:  # noqa: BLE001
            log(f"[vm] 启动失败: {exc}")
            import traceback
            traceback.print_exc()
    elif runtime and not mrp_path:
        log("[vm] 只给了 runtime 没给 mrp，进入演示模式")
    elif not runtime:
        log(f"[vm] 未找到 cfunction.ext（工作目录 {workdir}），进入演示模式")

    # ---------------- 窗口
    info = pygame.display.Info()
    if args.headless:
        scale = 1.0
    elif args.scale > 0:
        scale = args.scale
    else:
        avail_h = max(400, info.current_h - 90)
        avail_w = max(300, info.current_w - 60)
        scale = min(avail_h / skin["height"], avail_w / skin["width"], 1.0)
        scale = max(scale, 0.5)

    win_w = int(skin["width"] * scale)
    win_h = int(skin["height"] * scale)
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption(
        f"MRP Emulator · {skin['name']}" + (f" · {app.mrp_name}" if app.mrp_name else "")
    )
    clock = pygame.time.Clock()

    # ---------------- 输入状态
    held: dict[str, str] = {}     # 来源 -> key id
    last_key_text = ""

    def key_id_for(name: str) -> str | None:
        return ui.key_at_name(name)

    def press_key(name: str, source: str) -> None:
        nonlocal last_key_text
        kid = key_id_for(name)
        if kid is None:
            return
        if source in held:
            return
        held[source] = kid
        ui.press(kid)
        last_key_text = f"{name}"
        code = KEY_NAME_TO_CODE.get(name)
        if code is not None and mrp_loaded:
            vm.key_event(code, True)

    def release_key(source: str) -> None:
        kid = held.pop(source, None)
        if kid is None:
            return
        ui.release(kid)
        for key in ui.keys:
            if key["id"] == kid:
                code = KEY_NAME_TO_CODE.get(key["key"])
                if code is not None and mrp_loaded:
                    vm.key_event(code, False)
                return
        if kid.startswith("nav:"):
            code = KEY_NAME_TO_CODE.get(kid.split(":", 1)[1])
            if code is not None and mrp_loaded:
                vm.key_event(code, False)

    # ---------------- 主循环
    running = True
    frames = 0
    max_frames = args.frames if args.headless and args.frames else (1 if args.headless else 0)

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_q and (e.mod & pygame.KMOD_CTRL):
                    running = False
                    continue
                if e.key == pygame.K_F12:
                    out_dir = Path.cwd() / "out"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    shot_path = args.screenshot or str(
                        out_dir / f"shot_{time.strftime('%H%M%S')}.png")
                    surface = (app.gfx.surface() if mrp_loaded
                               else _demo_surface(app, last_key_text))
                    pygame.image.save(ui.draw(surface), shot_path)
                    log(f"[shot] 已保存 {shot_path}")
                    continue
                name = _key_name(e)
                if name:
                    press_key(name, f"kb:{e.key}")
            elif e.type == pygame.KEYUP:
                name = _key_name(e)
                if name:
                    release_key(f"kb:{e.key}")
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = (int(e.pos[0] / scale), int(e.pos[1] / scale))
                kid = ui.hit(pos)
                if kid:
                    last_key_text = kid
                    ui.press(kid)
                    held["mouse"] = kid
                    code = ui.key_code(kid)
                    if code is not None and mrp_loaded:
                        vm.key_event(code, True)
                else:
                    sp = ui.screen_pos(pos)
                    if sp and mrp_loaded and args.touch != "off":
                        if args.touch == "native":
                            # 与 vmrp 的 main.c 一致：坐标原样送进虚拟机
                            from .consts import MR_MOUSE_DOWN
                            vm.touch_event(MR_MOUSE_DOWN, *sp)
                            held["screen"] = "touch"
                        else:  # nav：坐标翻译成方向键/确定（辅助模式）
                            name = ui.tap_to_key(*sp)
                            code = KEY_NAME_TO_CODE.get(name)
                            if code is not None:
                                last_key_text = name
                                vm.key_event(code, True)
                                vm.key_event(code, False)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                kid = held.pop("mouse", None)
                releasing_touch = held.pop("screen", None) == "touch"
                if kid:
                    ui.release(kid)
                    code = ui.key_code(kid)
                    if code is not None and mrp_loaded:
                        vm.key_event(code, False)
                if releasing_touch and mrp_loaded:
                    from .consts import MR_MOUSE_UP
                    sp = ui.screen_pos((int(e.pos[0] / scale), int(e.pos[1] / scale)))
                    vm.touch_event(MR_MOUSE_UP, *(sp or (0, 0)))
            elif e.type == pygame.MOUSEMOTION and mrp_loaded and args.touch == "native":
                if held.get("screen") == "touch":
                    sp = ui.screen_pos((int(e.pos[0] / scale), int(e.pos[1] / scale)))
                    if sp:
                        from .consts import MR_MOUSE_MOVE
                        vm.touch_event(MR_MOUSE_MOVE, *sp)

        # 定时器
        if mrp_loaded and app.timer_due():
            try:
                vm.timer()
            except Exception as exc:  # noqa: BLE001
                log(f"[vm] timer 异常: {exc}")
                mrp_loaded = False

        # 音频：续投流式 PCM、推进流媒体播放器的状态机
        app.audio.tick()

        # 画面
        if mrp_loaded:
            gfx_surface = app.gfx.surface()
        else:
            paint_demo(app.gfx, app, last_key_text)
            gfx_surface = app.gfx.surface()

        frame = ui.draw(gfx_surface)
        if scale != 1.0:
            frame = pygame.transform.smoothscale(frame, (win_w, win_h))
        screen.blit(frame, (0, 0))
        pygame.display.flip()

        frames += 1
        if max_frames and frames >= max_frames:
            running = False

        if not args.headless:
            clock.tick(60)

    # ---------------- 收尾
    if args.screenshot:
        shot = ui.draw(app.gfx.surface() if mrp_loaded else _demo_surface(app, last_key_text))
        pygame.image.save(shot, args.screenshot)
        log(f"[shot] 已保存 {args.screenshot}")

    if args.stats:
        log("\n--- 统计 ---")
        log(app.report())
        log(app.audio.stats())
        for t in vm.tables.values():
            top = sorted(t.calls.items(), key=lambda kv: -kv[1])[:8]
            if top:
                log(f"{t.name} 热点: " + ", ".join(f"{k}×{v}" for k, v in top))

    app.audio.shutdown()
    pygame.quit()
    return 0


def _demo_surface(app, last_key: str):
    paint_demo(app.gfx, app, last_key)
    return app.gfx.surface()


def _key_name(e) -> str | None:
    import pygame

    table = {
        pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
        pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7",
        pygame.K_8: "8", pygame.K_9: "9",
        pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3",
        pygame.K_KP4: "4", pygame.K_KP5: "5", pygame.K_KP6: "6", pygame.K_KP7: "7",
        pygame.K_KP8: "8", pygame.K_KP9: "9",
        pygame.K_UP: "UP", pygame.K_DOWN: "DOWN",
        pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT",
        pygame.K_RETURN: "SELECT", pygame.K_KP_ENTER: "SELECT",
        pygame.K_F1: "SOFT_L", pygame.K_F2: "SOFT_R",
        pygame.K_ESCAPE: "END", pygame.K_BACKSPACE: "CLEAR",
        pygame.K_ASTERISK: "*", pygame.K_HASH: "#",
    }
    return table.get(e.key)


if __name__ == "__main__":
    sys.exit(main())
