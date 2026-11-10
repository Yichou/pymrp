"""命令行入口与主循环。

三种运行形态：
    python run.py                       启动 MTK 真机桌面（默认）
    python run.py game.mrp              直接跑一个 MRP（跳过系统界面）
    python run.py --boot gamecenter     开机直接进游戏中心（便于调试/截图）

系统界面（Launcher）与 MRP 运行时共用同一个 240x320 屏幕：
    mode = launcher -> 宿主画开机/待机/菜单/游戏中心，输入交给 Launcher
    mode = mrp      -> 画 app.gfx.surface()，输入/触摸转给虚拟机
    mode = demo     -> 没有 runtime 时的老演示画面
从游戏中心点一个应用会**重建 VM**（干净状态）后 start_dsm()；挂机键回桌面。
"""

from __future__ import annotations

import argparse
import os
import shutil
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
    p.add_argument("mrp", nargs="?", help="要直接运行的 .mrp 文件（给了就跳过系统桌面）")
    p.add_argument("--workdir", help="工作目录（存放 cfunction.ext 与 mythroad 资源）")
    p.add_argument("--runtime", help="cfunction.ext 路径，或包含它的目录")
    p.add_argument("--ext", default="", help="mrp 内入口名；留空自动判断（包内通常有 start.mr）")
    p.add_argument("--skin", help="皮肤 JSON 路径")
    p.add_argument("--scale", type=float, default=0.0, help="界面缩放倍数，0=自动")
    p.add_argument("--headless", action="store_true", help="无窗口模式，渲染一帧后退出")
    p.add_argument("--screenshot", help="把界面截图保存到指定 PNG")
    p.add_argument("--frames", type=int, default=0, help="headless 模式渲染帧数（默认 1）")
    p.add_argument("--verbose", action="store_true", help="打印每次 API 调用")
    p.add_argument("--stats", action="store_true", help="退出时打印统计")
    p.add_argument("--demo", action="store_true", help="强制演示模式（不加载 runtime、不进桌面）")
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
    p.add_argument(
        "--boot", choices=("boot", "home", "menu", "gamecenter", "direct"),
        help="开机画面：boot=开机动画(默认) / home=待机桌面 / menu=九宫格 / "
             "gamecenter=游戏中心 / direct=直接跑 MRP。给了 mrp 位置时默认 direct",
    )
    p.add_argument("--proxy", help="在线列表用的 HTTP 代理，如 http://127.0.0.1:7890；"
                                   "留空自动读系统代理并探测常见本地代理端口")
    p.add_argument("--refresh", action="store_true", help="强制重新拉取在线列表（忽略本地 JSON 缓存）")
    p.add_argument("--cache-days", type=int, default=7, help="在线列表缓存有效天数，默认 7")
    p.add_argument("--net-proxy", default=os.environ.get("PYMRP_NET_PROXY", ""),
                   help="MRP 的 TCP 出站 HTTP 代理（支持 CONNECT），如 http://127.0.0.1:7890；"
                        "默认直连，也可设 PYMRP_NET_PROXY")
    p.add_argument("--net-off", action="store_true", help="关闭 MRP 网络（所有 socket API 返回 MR_FAILED）")
    p.add_argument("--strict-null", action="store_true",
                   help="不映射 0 页，用于抓 NULL 指针解引用（调试用，默认映射以兼容真机行为）")
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
    from .audio.mixer import AudioEngine
    from .catalog import Catalog, probe_entry_ext
    from .consts import KEY_NAME_TO_CODE
    from .ui.launcher import Launcher
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

    skin = load_skin(args.skin or (workdir / "skin.json"))
    ui = PhoneUI(skin)
    runtime = None if args.demo else find_runtime(workdir, args.runtime)

    # ---------------- 启动形态
    boot = args.boot or ("direct" if mrp_path else "boot")
    direct = boot == "direct"
    mode = "demo" if args.demo else ("mrp" if direct else "launcher")

    if direct and not mrp_path and runtime:
        auto = workdir / "mythroad" / "dsm_gm.mrp"
        if not auto.is_file():
            found = sorted(workdir.rglob("dsm_gm.mrp"))
            auto = found[0] if found else None
        if auto and auto.is_file():
            mrp_path = auto
            log(f"[vm] direct 未指定 mrp，自动使用 {auto.relative_to(workdir)}")

    # ---------------- 会话（VM 可重建，音频引擎整机唯一）
    shared_audio = AudioEngine(
        sample_rate=args.audio_rate, enabled=(args.audio != "off"),
        log=log, pcm_rate=args.pcm_rate,
    )

    def new_session():
        v = Vm(log=log, zero_page=not args.strict_null)
        a = App(v, workdir, log=log, audio=(args.audio != "off"),
                sample_rate=args.audio_rate, pcm_rate=args.pcm_rate,
                audio_engine=shared_audio, http_proxy=args.net_proxy,
                net_enabled=not args.net_off)
        v.app = a
        v.install_tables(MR_TABLE, DSM_FUNCS)
        for t in v.tables.values():
            t.verbose = args.verbose
        return v, a

    vm, app = new_session()
    mrp_loaded = False
    quit_requested = False

    if args.verbose:
        missing = sorted({f.name for f in MR_TABLE if f.fn is None})
        log(f"[api] 未实现槽位 {len(missing)} 项: {', '.join(missing[:12])}"
            + (" ..." if len(missing) > 12 else ""))

    # ---------------- 系统桌面 / 在线目录
    cat = None
    launcher = None
    if mode == "launcher":
        cat = Catalog(workdir, proxy=args.proxy, log=log,
                      ttl=max(0, args.cache_days) * 86400)
        if args.refresh:
            cat.start_refresh(force=True)     # Launcher 内的普通刷新会被 _refreshing 挡掉
        launcher = Launcher(cat, log=log, start_page=boot)

    def update_caption() -> None:
        if pygame.display.get_surface() is None:
            return
        if mode == "mrp" and app.mrp_name:
            title = f"MRP Emulator · {app.mrp_name}"
        elif mode == "launcher":
            title = f"PymRP · {skin['name']} · 游戏中心"
        else:
            title = f"MRP Emulator · {skin['name']}"
        pygame.display.set_caption(title)

    def ensure_in_mythroad(path: Path) -> Path:
        """dsm 层默认在 <workdir>/mythroad/ 下找 mrp，不在那儿就复制一份。"""
        folder = workdir / "mythroad"
        folder.mkdir(parents=True, exist_ok=True)
        if path.parent.resolve() == folder.resolve():
            return path
        dst = folder / path.name
        if not dst.exists() or dst.stat().st_size != path.stat().st_size:
            shutil.copy2(path, dst)
            log(f"[catalog] 已放入运行环境 {dst.name}")
        return dst

    def back_to_home() -> None:
        nonlocal mrp_loaded, mode
        app.net.close_network()      # 挂机回桌面时把所有 socket 收干净
        mrp_loaded = False
        if launcher:
            mode = "launcher"
            launcher.go("home")
            launcher.toast("已返回待机桌面")
            update_caption()

    def launch_path(path: Path, display: str | None = None) -> bool:
        """重建 VM，加载并启动一个 MRP。"""
        nonlocal vm, app, mrp_loaded, mode
        if runtime is None:
            if launcher:
                launcher.toast("未找到 cfunction.ext，无法运行应用", 3)
            log("[vm] 未找到 cfunction.ext，无法启动 MRP")
            return False
        try:
            target = ensure_in_mythroad(Path(path))
        except OSError as exc:
            if launcher:
                launcher.toast(f"准备文件失败：{exc}", 3)
            log(f"[vm] 准备文件失败: {exc}")
            return False

        ext = args.ext or probe_entry_ext(target)
        app.net.close_network()      # 换应用前关掉上一个应用的连接
        v, a = new_session()
        a.mrp_name = display or target.name
        try:
            v.load_code(runtime)
            v.ext_init()
            if not v.dsm_init():
                raise RuntimeError("DSM_INIT 握手失败")
            r = v.start_dsm(target.name, ext, None)
            log(f"[vm] start_dsm('{target.name}', '{ext}') -> {r}")
            if r not in (0, 1):
                # 入口猜错时换另一个再试一次（必须是干净的 VM）
                alt = "cfunction.ext" if ext == "start.mr" else "start.mr"
                v2, a2 = new_session()
                a2.mrp_name = a.mrp_name
                v2.load_code(runtime)
                v2.ext_init()
                if v2.dsm_init():
                    r2 = v2.start_dsm(target.name, alt, None)
                    log(f"[vm] 换入口 '{alt}' 重试 -> {r2}")
                    if r2 in (0, 1):
                        v, a, ext, r = v2, a2, alt, r2
            if r not in (0, 1):
                raise RuntimeError(f"start_dsm 返回 {r}")
        except Exception as exc:  # noqa: BLE001
            log(f"[vm] 启动失败: {exc}")
            import traceback
            traceback.print_exc()
            if launcher:
                launcher.toast(f"启动失败：{str(exc)[:26]}", 3)
                mode = "launcher"
            return False

        vm, app = v, a
        mrp_loaded = True
        mode = "mrp"
        update_caption()
        return True

    if launcher:
        def on_launch(item) -> None:
            p = item.path or cat.find_local_file(item.file)
            if not p:
                launcher.toast("文件还没下载好，请稍候", 2)
                return
            launch_path(Path(p), item.label)

        def on_exit() -> None:
            nonlocal quit_requested
            quit_requested = True

        launcher.on_launch = on_launch
        launcher.on_exit = on_exit

    if direct and mrp_path and not args.demo:
        if not launch_path(mrp_path):
            mode = "demo"
    elif direct and not runtime:
        log(f"[vm] 未找到 cfunction.ext（工作目录 {workdir}），进入演示模式")
        mode = "demo"

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
    update_caption()
    clock = pygame.time.Clock()

    # ---------------- 输入状态
    held: dict[str, str] = {}     # 来源 -> key id
    last_key_text = ""
    pending_text = {"v": ""}     # KEYDOWN/TEXTINPUT 去重（中文 IME 兼容）
    textinput_event = getattr(pygame, "TEXTINPUT", None)   # pygame 1 没有该事件

    def key_id_for(name: str) -> str | None:
        return ui.key_at_name(name)

    def key_name_for(kid: str) -> str | None:
        if kid.startswith("nav:"):
            return kid.split(":", 1)[1]
        for key in ui.keys:
            if key["id"] == kid:
                return key["key"]
        return None

    def press_key(name: str, source: str) -> None:
        nonlocal last_key_text
        kid = key_id_for(name)
        if kid is None or source in held:
            return
        held[source] = kid
        ui.press(kid)
        last_key_text = name
        if mode == "mrp" and mrp_loaded:
            if name == "END":                 # 挂机键：退出应用回待机桌面
                back_to_home()
                return
            code = KEY_NAME_TO_CODE.get(name)
            if code is not None:
                vm.key_event(code, True)
        elif launcher and mode == "launcher":
            launcher.handle_key(name)

    def release_key(source: str) -> None:
        kid = held.pop(source, None)
        if kid is None:
            return
        ui.release(kid)
        if mode != "mrp" or not mrp_loaded:
            return
        for key in ui.keys:
            if key["id"] == kid:
                code = KEY_NAME_TO_CODE.get(key["key"])
                if code is not None:
                    vm.key_event(code, False)
                return
        if kid.startswith("nav:"):
            code = KEY_NAME_TO_CODE.get(kid.split(":", 1)[1])
            if code is not None:
                vm.key_event(code, False)

    def current_surface():
        if mode == "mrp" and mrp_loaded:
            return app.gfx.surface()
        if mode == "launcher" and launcher:
            return launcher.surface()
        paint_demo(app.gfx, app, last_key_text)
        return app.gfx.surface()

    # ---------------- 主循环
    running = True
    frames = 0
    max_frames = args.frames if args.headless and args.frames else (1 if args.headless else 0)
    dt = 1.0 / 60

    while running:
        if quit_requested:
            running = False
            break
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
                    pygame.image.save(ui.draw(current_surface()), shot_path)
                    log(f"[shot] 已保存 {shot_path}")
                    continue
                uni = getattr(e, "unicode", "")
                pending_text["v"] = ""
                name = _key_name(e)
                if name:
                    press_key(name, f"kb:{e.key}")
                # 搜索框：普通字符从 KEYDOWN.unicode 拿，中文 IME 走 TEXTINPUT
                if (launcher and mode == "launcher" and launcher.searching
                        and uni and uni.isprintable() and uni not in ("*", "#", " ")):
                    launcher.handle_text(uni)
                    pending_text["v"] = uni
            elif textinput_event is not None and e.type == textinput_event:
                if launcher and mode == "launcher" and launcher.searching:
                    txt = getattr(e, "text", "")
                    if txt and txt != pending_text["v"]:
                        launcher.handle_text(txt)
                        pending_text["v"] = txt
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
                    name = key_name_for(kid)
                    if mode == "mrp" and mrp_loaded:
                        if name == "END":
                            back_to_home()
                            continue
                        code = ui.key_code(kid)
                        if code is not None:
                            vm.key_event(code, True)
                    elif launcher and mode == "launcher" and name:
                        launcher.handle_key(name)
                else:
                    sp = ui.screen_pos(pos)
                    if not sp:
                        continue
                    if mode == "mrp" and mrp_loaded and args.touch != "off":
                        if args.touch == "native":
                            from .consts import MR_MOUSE_DOWN
                            vm.touch_event(MR_MOUSE_DOWN, *sp)
                            held["screen"] = "touch"
                        else:
                            name = ui.tap_to_key(*sp)
                            code = KEY_NAME_TO_CODE.get(name)
                            if code is not None:
                                last_key_text = name
                                vm.key_event(code, True)
                                vm.key_event(code, False)
                    elif launcher and mode == "launcher":
                        launcher.handle_click(*sp)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                kid = held.pop("mouse", None)
                releasing_touch = held.pop("screen", None) == "touch"
                if kid:
                    ui.release(kid)
                    if mode == "mrp" and mrp_loaded:
                        code = ui.key_code(kid)
                        if code is not None:
                            vm.key_event(code, False)
                if releasing_touch and mrp_loaded:
                    from .consts import MR_MOUSE_UP
                    sp = ui.screen_pos((int(e.pos[0] / scale), int(e.pos[1] / scale)))
                    vm.touch_event(MR_MOUSE_UP, *(sp or (0, 0)))
            elif e.type == pygame.MOUSEMOTION and mrp_loaded and mode == "mrp" \
                    and args.touch == "native":
                if held.get("screen") == "touch":
                    sp = ui.screen_pos((int(e.pos[0] / scale), int(e.pos[1] / scale)))
                    if sp:
                        from .consts import MR_MOUSE_MOVE
                        vm.touch_event(MR_MOUSE_MOVE, *sp)

        # 定时器 / 后台任务
        if mode == "mrp" and mrp_loaded and app.timer_due():
            try:
                vm.timer()
            except Exception as exc:  # noqa: BLE001
                log(f"[vm] timer 异常: {exc}")
                back_to_home()
        if launcher and mode == "launcher":
            launcher.tick(dt)
        # 网络异步回调不能在 emu_start() 内重入，统一在主循环这里执行
        if mode == "mrp" and mrp_loaded:
            app.net.poll()
        shared_audio.tick()

        frame = ui.draw(current_surface())
        if scale != 1.0:
            frame = pygame.transform.smoothscale(frame, (win_w, win_h))
        screen.blit(frame, (0, 0))
        pygame.display.flip()

        frames += 1
        if max_frames and frames >= max_frames:
            running = False
        if not args.headless:
            dt = clock.tick(60) / 1000.0

    # ---------------- 收尾
    if args.screenshot:
        pygame.image.save(ui.draw(current_surface()), args.screenshot)
        log(f"[shot] 已保存 {args.screenshot}")

    if args.stats:
        log("\n--- 统计 ---")
        log(app.report())
        log(shared_audio.stats())
        for t in vm.tables.values():
            top = sorted(t.calls.items(), key=lambda kv: -kv[1])[:8]
            if top:
                log(f"{t.name} 热点: " + ", ".join(f"{k}×{v}" for k, v in top))

    shared_audio.shutdown()
    pygame.quit()
    return 0


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
