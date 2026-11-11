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

# 键盘 -> MRP 键名（对外说明用；实际按键转换在 _key_name()）
# 左右软键各有三个入口：F1/F2 保留，Ctrl = 左软键、Alt = 右软键（双手握持更好按）
KEYMAP = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT",
    "ENTER": "SELECT", "F1": "SOFT_L", "F2": "SOFT_R",
    "LCTRL": "SOFT_L", "RCTRL": "SOFT_L",
    "LALT": "SOFT_R", "RALT": "SOFT_R",
    "ESCAPE": "END", "BACKSPACE": "CLEAR",
    "ASTERISK": "*", "HASH": "#",
}


def init_pygame_minimal() -> None:
    """只初始化界面真正需要的 SDL 子系统。

    ``pygame.init()`` 会连带 ``SDL_INIT_AUDIO``；在没有音频输出端点的
    Windows 机器上，WASAPI 枚举一次要 ~8 秒，且 ``pygame.mixer.init()``
    还会再花一次。display + font 两项实测合计 < 10ms，事件/计时器/
    Surface/图片模块随 display 自动可用，手柄等用不到的子系统一律不开。
    """
    import pygame

    pygame.display.init()
    pygame.font.init()


def enable_dpi_awareness() -> str:
    """Windows 高分屏：让进程自己感知每显示器 DPI。

    进程不感知 DPI 时，Windows 会把整个窗口当位图拉伸（125% / 150% 缩放下
    满屏发虚），pygame 报上来的鼠标坐标也跟着偏。必须在创建窗口之前调用。
    """
    if sys.platform != "win32":
        return "n/a"
    try:
        import ctypes
        try:                                   # Win10 1703+：PER_MONITOR_AWARE_V2
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return "per-monitor-v2"
        except Exception:
            pass
        try:                                   # Win8.1+
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return "per-monitor"
        except Exception:
            pass
        ctypes.windll.user32.SetProcessDPIAware()
        return "system"
    except Exception:
        return "failed"


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
    p.add_argument("--scale", type=float, default=0.0,
                   help="界面缩放倍数（取整到整数倍），0=自动")
    p.add_argument("--headless", action="store_true", help="无窗口模式，渲染一帧后退出")
    p.add_argument("--screenshot", help="把界面截图保存到指定 PNG")
    p.add_argument("--frames", type=int, default=0,
                   help="渲染多少帧后自动退出（headless 默认 1，窗口模式默认不限；"
                        "用于启动计时与自动化截图）")
    p.add_argument("--verbose", action="store_true", help="打印每次 API 调用")
    p.add_argument("--stats", action="store_true", help="退出时打印统计")
    p.add_argument("--demo", action="store_true", help="强制演示模式（不加载 runtime、不进桌面）")
    p.add_argument(
        "--audio", choices=("auto", "on", "off"), default="auto",
        help="声音：auto=有音频设备就开、没有就静音降级（默认）；on=强制开；off=完全静音",
    )
    p.add_argument("--audio-rate", type=int, default=44100, help="混音采样率，默认 44100")
    p.add_argument(
        "--audio-driver", default="auto",
        choices=("auto", "fast", "wasapi", "directsound", "winmm", "dummy"),
        help="音频驱动：auto=自动（默认，无声卡时快速静音降级）；"
             "fast=Windows 上走 DirectSound 跳过 WASAPI 慢枚举；"
             "其余=显式指定 SDL_AUDIODRIVER",
    )
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
    p.add_argument("--dns-map", default=None,
                   help="老斯凯域名覆写，格式 'HOST->IPv4[:PORT];...'；"
                        "默认把 rop/spd.skymobiapp.com、wap.skmeg.com 指向 159.75.119.124，"
                        "传空字符串可清空；也可写 10.0.0.172->IP:PORT 覆盖 WAP 网关")
    p.add_argument("--wap-proxy", choices=("on", "off"), default="on",
                   help="内置 WAP 代理（接管 10.0.0.172，支持绝对 URL / Host / CONNECT），默认 on")
    p.add_argument("--retro-wap", choices=("on", "off"), default="off",
                   help="启动本地复古 WAP 服务端（替代已停运的腾讯 3G QQ / "
                        "斯凯网关），并把 info.3g.qq.com 等域名指向它")
    p.add_argument("--retro-wap-port", type=int, default=0,
                   help="本地复古 WAP 服务端端口，0=自动挑空闲端口")
    p.add_argument("--strict-null", action="store_true",
                   help="不映射 0 页，用于抓 NULL 指针解引用（调试用，默认映射以兼容真机行为）")
    p.add_argument("--keys", default="",
                   help="按键脚本：用逗号分隔的按键序列自动操作应用，"
                        "用于可复现的回归测试。可用键名："
                        "0-9/*/#、UP/DOWN/LEFT/RIGHT、ENTER(SELECT)、"
                        "SOFT_L/SOFT_R(左/右软键)、END、CLEAR；"
                        "每步之间默认间隔 12 帧，可用 @N 指定间隔")
    p.add_argument("--key-delay", type=int, default=12,
                   help="--keys 每步之间的帧间隔，默认 12")
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
    _t_start = time.perf_counter()
    args = build_parser().parse_args(argv)
    _timing = os.environ.get("PYMRP_TIMING", "") == "1"

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

    # 音频驱动必须在 SDL 首次初始化音频子系统之前定下来
    if args.audio_driver == "fast":
        os.environ.setdefault("SDL_AUDIODRIVER",
                             "directsound" if sys.platform == "win32" else "dummy")
    elif args.audio_driver != "auto":
        os.environ["SDL_AUDIODRIVER"] = args.audio_driver

    import pygame

    from .api.dsmfuncs import DSM_FUNCS
    from .api.mrtable import MR_TABLE
    from .app import App
    from .audio.mixer import AudioEngine
    from .catalog import Catalog, probe_entry_ext, safe_run_name
    from .consts import KEY_NAME_TO_CODE
    from .ui.launcher import Launcher
    from .ui.phone import PhoneUI
    from .ui.skin import load_skin
    from .vm import Vm

    def log(msg: str) -> None:
        print(msg, flush=True)

    def mark(tag: str) -> None:
        if _timing:
            log(f"[timing] {tag}: {(time.perf_counter() - _t_start) * 1000:.1f} ms")

    mark("模块导入完成")
    dpi_mode = enable_dpi_awareness()
    mark(f"DPI 感知（{dpi_mode}）")
    init_pygame_minimal()
    mark("SDL 最小初始化（display + font）")

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
    runtime = None if args.demo else find_runtime(workdir, args.runtime)

    # ---------------- 系统字库（全局，与是否跑 QQ 无关）
    # DSM 层的应用会直接读 ``mythroad/system/gb16.uc2`` 来画中文
    # （实测 QQ 2007 启动第一件事就是 open 它，见 docs/21）。字库一旦
    # 缺失或笔画粘连，所有应用的中文界面全糊。
    # 这里无条件准备一次：优先复制发行包里的原厂点阵字，其次用系统
    # 字体（宋体/雅黑）现场生成。
    if runtime is not None:
        try:
            from .fontgen import ensure_uc2
            ensure_uc2(workdir / "mythroad" / "system" / "gb16.uc2",
                       log=log,
                       factory_dirs=[workdir / "mythroad" / "fonts",
                                     workdir / "mythroad" / "system"])
        except Exception as exc:  # noqa: BLE001
            log(f"[font] 系统字库准备失败（中文可能显示不出）: {exc}")

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

    # ---------------- 本地复古 WAP 服务端（替代停运的腾讯 3G QQ / 斯凯网关）
    retro_srv = None
    dns_map_text = args.dns_map
    if args.retro_wap == "on":
        from .retrowap import WapServer, dns_map_for
        retro_srv = WapServer("127.0.0.1", args.retro_wap_port,
                               log=log)
        retro_srv.start_background()
        rhost, rport = retro_srv.server_address[0], retro_srv.server_address[1]
        log(f"[retro-wap] 本地复古 WAP 服务端: http://{rhost}:{rport}/")
        dns_map_text = dns_map_for(rhost, rport, args.dns_map)
        log(f"[retro-wap] 域名覆写: {len(dns_map_text.split(';'))} 条")
        # 古董 QQ 还需要一堆真机预置的私有配置（服务器列表 / 账号库 / 字库），
        # 一并生成，让它们能直接连上本地服务端。
        try:
            from .qqenv import prepare_qq_environment
            prepare_qq_environment(workdir, rhost, rport, log=log)
        except Exception as exc:  # noqa: BLE001
            log(f"[qq-env] 准备运行环境失败: {exc}")

    def new_session():
        v = Vm(log=log, zero_page=not args.strict_null)
        a = App(v, workdir, log=log, audio=(args.audio != "off"),
                sample_rate=args.audio_rate, pcm_rate=args.pcm_rate,
                audio_engine=shared_audio, http_proxy=args.net_proxy,
                net_enabled=not args.net_off, dns_map=dns_map_text,
                wap_proxy=(args.wap_proxy != "off"))
        v.app = a
        v.install_tables(MR_TABLE, DSM_FUNCS)
        for t in v.tables.values():
            t.verbose = args.verbose
        return v, a

    vm, app = new_session()
    mark("VM / 会话就绪")
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
        """dsm 层默认在 <workdir>/mythroad/ 下找 mrp，不在那儿就复制一份。

        同时换成 ``safe_run_name()`` 给出的短 ASCII 运行名：ext 的路径缓冲
        装不下长中文名，会把路径截断导致打不开自己的 MRP 包。
        """
        folder = workdir / "mythroad"
        folder.mkdir(parents=True, exist_ok=True)
        dst = folder / safe_run_name(path)
        try:
            if path.resolve() == dst.resolve():
                return dst
        except OSError:
            pass
        if not dst.exists() or dst.stat().st_size != path.stat().st_size:
            shutil.copy2(path, dst)
            log(f"[catalog] 已放入运行环境 {dst.name}（安全运行名）")
        return dst

    def teardown_session(reason: str) -> None:
        """应用退出 / 崩溃时的统一收尾。

        MRP 侧的 ``mr_exit()`` 只置一个标志位，真正干活的是这里：
        背景音乐与音效要停、网络 socket 要关、文件句柄要关，
        否则退到系统界面后喇叭还在响、连接还挂着、句柄还占着。
        """
        nonlocal mrp_loaded
        try:
            info = app.shutdown_session(reason)
            if info.get("files") or info.get("sockets"):
                log(f"[teardown] 已关闭 {info.get('files', 0)} 个文件句柄、"
                    f"{info.get('sockets', 0)} 个 socket")
        except Exception as exc:  # noqa: BLE001
            log(f"[teardown] 收尾失败: {exc}")
        mrp_loaded = False
        log(f"[teardown] {reason}")

    def back_to_home(reason: str = "返回待机桌面") -> None:
        nonlocal mode
        teardown_session(reason)
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
        # 真机行为：应用把图标/WML 等资源从包里释放到自己的目录，
        # 不释放的话应用打开资源全部失败（页面空白）。见 docs/20。
        try:
            from .release import detect_app_dirs, release_mrp_resources
            dirs = detect_app_dirs(target)
            app_dir = dirs[0] if dirs else ""
            if app_dir:
                release_mrp_resources(target, workdir, app_dir=app_dir,
                                      log=log)
        except Exception as exc:  # noqa: BLE001
            log(f"[release] 释放包内资源失败: {exc}")
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
        # 运行名会换成短 ASCII，但窗口标题仍显示用户给的中文名
        if not launch_path(mrp_path, mrp_path.stem):
            mode = "demo"
    elif direct and not runtime:
        log(f"[vm] 未找到 cfunction.ext（工作目录 {workdir}），进入演示模式")
        mode = "demo"

    # ---------------- 窗口
    info = pygame.display.Info()
    if args.headless:
        k = 1
    elif args.scale > 0:
        # 整数倍缩放：非整数倍会把每个像素打散到半个物理像素上，怎么缩都糊
        k = max(1, int(round(args.scale)))
    else:
        avail_h = max(400, info.current_h - 90)
        avail_w = max(300, info.current_w - 60)
        k = max(1, int(min(avail_h / skin["height"], avail_w / skin["width"])))

    # 机壳按 k 倍**矢量重绘**（不是拉伸成品图），文字/圆盘在高分屏上锐利
    ui = PhoneUI(skin, scale=k)
    win_w, win_h = ui.w, ui.h
    screen = pygame.display.set_mode((win_w, win_h))
    update_caption()
    mark(f"窗口创建完成（{win_w}x{win_h}，{k}x 矢量）")
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
                guarded("key_event", vm.key_event, code, True)
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
                    guarded("key_event", vm.key_event, code, False)
                return
        if kid.startswith("nav:"):
            code = KEY_NAME_TO_CODE.get(kid.split(":", 1)[1])
            if code is not None:
                guarded("key_event", vm.key_event, code, False)

    def guarded(desc: str, fn, *args):
        """包住虚拟机调用。

        MRP 是机器码，越界访问和野指针随时会把 Unicorn 打断。以前只有
        timer 有 try/except，按键路径（key_event / touch_event）崩了会直接
        带崩整个模拟器进程。现在统一走这里：记录 → 收尾 → 回系统界面。
        """
        try:
            return fn(*args)
        except Exception as exc:  # noqa: BLE001
            log(f"[vm] {desc} 异常: {exc}")
            back_to_home(f"{desc} 异常")
            return None

    def current_surface():
        if mode == "mrp" and mrp_loaded:
            return app.gfx.surface()
        if mode == "launcher" and launcher:
            return launcher.surface()
        paint_demo(app.gfx, app, last_key_text)
        return app.gfx.surface()

    # ---------------- 按键脚本（可复现的回归驱动）
    # 格式："5,5,ENTER,SOFT_L,@30,0" —— 每项一个键名，@N 表示等待 N 帧。
    key_script: list[tuple[str | None, int]] = []
    if args.keys:
        for raw in args.keys.split(","):
            item = raw.strip()
            if not item:
                continue
            if item.startswith("@"):
                try:
                    key_script.append((None, max(1, int(item[1:]))))
                except ValueError:
                    pass
                continue
            key_script.append((item.upper(), args.key_delay))
    key_script_pos = 0
    key_wait = 0

    def script_key(name: str) -> None:
        """按一次脚本指定的键（按下 + 抬起）。"""
        name = {"ENTER": "SELECT", "LEFT_SOFT": "SOFT_L",
                "RIGHT_SOFT": "SOFT_R"}.get(name, name)
        code = KEY_NAME_TO_CODE.get(name)
        if code is None:
            log(f"[keys] 未知键名 {name!r}，跳过")
            return
        if mode == "mrp" and mrp_loaded:
            guarded("key_event", vm.key_event, code, True)
            guarded("key_event", vm.key_event, code, False)
        elif launcher and mode == "launcher":
            launcher.handle_key(name)

    # ---------------- 主循环
    running = True
    frames = 0
    max_frames = args.frames or (1 if args.headless else 0)
    _first_frame_marked = False
    dt = 1.0 / 60

    while running:
        if quit_requested:
            running = False
            break
        if mode == "mrp" and mrp_loaded and vm.exited:
            # 应用主动调用 mr_exit()：收尾干净再退回系统界面
            log("[vm] 应用调用 mr_exit()")
            back_to_home("应用退出（mr_exit）")
            continue
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_q and (e.mod & pygame.KMOD_CTRL):
                    # Ctrl 现在是左软键：退出前先释放可能按住的软键，
                    # 免得给虚拟机/桌面留下一个没松开的按键状态。
                    for src in (f"kb:{pygame.K_LCTRL}", f"kb:{pygame.K_RCTRL}"):
                        if src in held:
                            release_key(src)
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
                pos = e.pos
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
                            guarded("key_event", vm.key_event, code, True)
                    elif launcher and mode == "launcher" and name:
                        launcher.handle_key(name)
                else:
                    sp = ui.screen_pos(pos)
                    if not sp:
                        continue
                    if mode == "mrp" and mrp_loaded and args.touch != "off":
                        if args.touch == "native":
                            from .consts import MR_MOUSE_DOWN
                            guarded("touch_event", vm.touch_event, MR_MOUSE_DOWN, *sp)
                            held["screen"] = "touch"
                        else:
                            name = ui.tap_to_key(*sp)
                            code = KEY_NAME_TO_CODE.get(name)
                            if code is not None:
                                last_key_text = name
                                guarded("key_event", vm.key_event, code, True)
                                guarded("key_event", vm.key_event, code, False)
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
                            guarded("key_event", vm.key_event, code, False)
                if releasing_touch and mrp_loaded:
                    from .consts import MR_MOUSE_UP
                    sp = ui.screen_pos(e.pos)
                    guarded("touch_event", vm.touch_event, MR_MOUSE_UP, *(sp or (0, 0)))
            elif e.type == pygame.MOUSEMOTION and mrp_loaded and mode == "mrp" \
                    and args.touch == "native":
                if held.get("screen") == "touch":
                    sp = ui.screen_pos(e.pos)
                    if sp:
                        from .consts import MR_MOUSE_MOVE
                        guarded("touch_event", vm.touch_event, MR_MOUSE_MOVE, *sp)

        # 定时器 / 后台任务
        if mode == "mrp" and mrp_loaded and app.timer_due():
            guarded("timer", vm.timer)
        if launcher and mode == "launcher":
            launcher.tick(dt)
        # 网络异步回调不能在 emu_start() 内重入，统一在主循环这里执行
        if mode == "mrp" and mrp_loaded:
            app.net.poll()
        shared_audio.tick()

        # 按键脚本：到达间隔就按下一次
        if key_script_pos < len(key_script):
            name, delay = key_script[key_script_pos]
            if key_wait <= 0:
                if name is not None:
                    script_key(name)
                    key_wait = delay
                else:
                    key_wait = delay          # @N：纯等待
                key_script_pos += 1
            else:
                key_wait -= 1

        frame = ui.draw(current_surface())
        screen.blit(frame, (0, 0))
        pygame.display.flip()
        if not _first_frame_marked:
            mark("首帧上屏（界面可见）")
            _first_frame_marked = True

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
    if retro_srv is not None:
        retro_srv.stop()
        log("[retro-wap] 本地复古 WAP 服务端已停止")
    pygame.quit()
    return 0


def _key_name(e) -> str | None:
    """pygame 键盘事件 -> MRP 键名。

    Ctrl(左右) = 左软键，Alt(左右) = 右软键，与 F1/F2 等价。
    修饰键自身会产生 KEYDOWN/KEYUP，所以能正常支持长按软键。
    """
    import pygame

    mod = getattr(e, "mod", 0) or 0
    ctrl_keys = (pygame.K_LCTRL, pygame.K_RCTRL)
    alt_keys = (pygame.K_LALT, pygame.K_RALT)

    if e.key in ctrl_keys or e.key in alt_keys:
        is_ctrl = e.key in ctrl_keys
        other = pygame.KMOD_ALT if is_ctrl else pygame.KMOD_CTRL
        shift_gui = pygame.KMOD_SHIFT | getattr(pygame, "KMOD_GUI", 0)
        # Windows 的 AltGr(右 Alt) 会同时注入 LCTRL+RALT，两边都带对方的
        # 修饰位。若不当软键，避免一次按键触发左右软键两下。
        # Ctrl+Shift / Alt+Shift 之类的系统组合也不当软键。
        if mod & other or mod & shift_gui:
            return None
        return "SOFT_L" if is_ctrl else "SOFT_R"

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
