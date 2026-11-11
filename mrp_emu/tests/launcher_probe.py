"""启动界面 / 游戏中心 / 一键启动链路自检。

跑法（在 mrp_emu/ 目录下，用装了 unicorn+pygame 的解释器）：
    python tests/launcher_probe.py

包含两组：
  A. 纯逻辑：MRP 头字段、入口判断、本地/在线索引、已下载标记、页面状态机、
     Tab 切换、搜索过滤、点击本地项触发 on_launch。
  B. 集成：预置 pygame 事件（点「本地列表」→ 点第 1 行），跑真正的 cli.main()
     headless 循环，断言日志里出现 start_dsm(...) -> 0；再测挂机键回桌面。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYMRP_PROXY", "http://127.0.0.1:7890")

import pygame  # noqa: E402

from mrp_emu.catalog import (  # noqa: E402
    Catalog, MrpMeta, probe_entry_ext, read_mrp_header,
)
from mrp_emu.ui.launcher import Launcher  # noqa: E402

RUNTIME = ROOT / "runtime"
PASS = 0
FAIL = 0


def check(cond: bool, label: str, extra: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [OK] {label}")
    else:
        FAIL += 1
        print(f"  [!!] {label} {extra}")


# ---------------------------------------------------------------- A. 逻辑
def test_header() -> None:
    print("\n-- MRP 头字段 --")
    sample = RUNTIME / "mythroad" / "10066_240320_rxhcl.mrp"
    h = read_mrp_header(sample)
    check(h["title"] == "小火柴里的大谜题", "GBK 标题", h["title"])
    check(h["vendor"] == "杭州斯凯", "开发商", h["vendor"])
    check(h["appid"] == 10066 and h["version"] == 138, "appid / version")
    check(h["desc"].startswith("小小的火柴棒"), "应用描述")
    check(h["screen_width"] == 240, "屏宽 240")
    check(h["appid_be"] == 10066, "大端 appid 副本")
    check(h["total_size"] == sample.stat().st_size, "0x08 文件总长")

    exts = {p.name: probe_entry_ext(p)
            for p in sorted((RUNTIME / "mythroad").glob("*.mrp"))}
    # 应用包的入口是 start.mr；插件包（abxmain.mrp 之类）的入口是 cfunction.ext。
    # runtime 目录会随下载/清理变化，所以只允许这两种形态，不做绝对断言。
    odd = {k: v for k, v in exts.items() if v not in ("start.mr", "cfunction.ext")}
    check(exts and not odd,
          f"入口均为 start.mr / cfunction.ext（{len(exts)} 个样本）", str(odd))


def test_catalog() -> None:
    print("\n-- 目录 / 缓存 --")
    cat = Catalog(RUNTIME)
    cat.start_refresh()
    import time
    for _ in range(40):
        if cat.online_state != "loading":
            break
        time.sleep(0.05)
    cat.scan_local()
    check(cat.online_state == "ready", "在线索引可用", cat.online_message)
    check(len(cat.online_items) >= 600, f"在线条目 {len(cat.online_items)} 条")
    check(len(cat.local_items) >= 10, f"本地条目 {len(cat.local_items)} 条")
    check(cat.online_file.is_file() and cat.local_file.is_file(),
          "两份 JSON 缓存已落盘")
    dl = [m for m in cat.online_items if m.downloaded]
    check(0 < len(dl) < 30, f"已下载标记数合理（{len(dl)}）")
    check(all(cat.find_local_file(m.file) for m in dl),
          "标记为已下载的都能在磁盘上找到")
    plain = [m for m in cat.online_items if not m.downloaded]
    check(bool(plain) and not cat.find_local_file(plain[0].file),
          "未下载项确实不在磁盘上")
    one = cat.online_items[0]
    check(bool(one.title) and bool(one.vendor) and one.size > 0,
          "在线项含标题/厂商/大小")
    check(one.url.endswith(one.file), "下载 URL 拼接正确")
    cat.poll()


def test_state_machine() -> None:
    print("\n-- 系统界面状态机 --")
    pygame.init()
    cat = Catalog(RUNTIME)
    cat.start_refresh()
    cat.scan_local()
    l = Launcher(cat, log=lambda *_: None, start_page="home")
    launched: list[MrpMeta] = []
    l.on_launch = launched.append
    check(l.page == "home", "初始待机桌面")
    l.handle_key("SOFT_L")
    check(l.page == "menu", "左软键进九宫格")
    l.handle_click(45, 60)
    check(l.page == "gamecenter", "点游戏中心图标进游戏中心")
    l.handle_click(170, 50)
    check(l.tab == 1, "点第二个 Tab → 本地列表")
    check(len(l.items()) == len(cat.local_items), "本地条目数一致")
    l.handle_key("LEFT")
    check(l.tab == 0, "左方向键切回在线列表")
    check(len(l.items()) == len(cat.online_items), "在线条目数一致")

    l.handle_key("*")
    check(l.searching, "* 进入搜索模式")
    l.handle_text("2")
    l.handle_text("0")
    l.handle_text("4")
    l.handle_text("8")
    check("2048" in l.search and len(l.items()) < len(cat.online_items),
          "搜索过滤生效", f"命中 {len(l.items())} 条")
    l.handle_key("END")
    check(not l.searching and l.search == "", "END 退出搜索并清空")

    # 本地列表点第 1 行 = 直接启动
    l.tab = 1
    l.sel = l.top = 0
    l.handle_click(100, 80)
    check(len(launched) == 1, "点击本地列表项触发启动回调")
    if launched:
        check(bool(launched[0].path), "回调携带本地文件路径")
    # 模拟后台下载完成事件 → 应自动启动，不需要用户再点一次
    target = cat.online_items[0]
    cat._events.put(("download_ready", target.file))
    l.tick(0.016)
    check(len(launched) == 2 and launched[-1].file == target.file,
          "在线项下载完成后自动触发启动")
    check(l.surface().get_size() == (240, 320), "输出 240x320 屏幕 Surface")
    cat.poll()


# ---------------------------------------------------------------- B. 集成
def _run_cli(extra: str, shot: str) -> str:
    """在**独立子进程**里跑 cli.main()。

    cli.main() 收尾会 pygame.quit()，同一进程二次 init SDL 在部分平台会崩，
    所以每次集成用例都开新进程 —— 也更贴近用户真实的一次次启动。
    """
    import subprocess

    code = f'''
import os, sys
from pathlib import Path
ROOT = Path({str(ROOT)!r})
sys.path.insert(0, str(ROOT))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYMRP_PROXY"] = "http://127.0.0.1:7890"
import pygame
pygame.init()
pygame.display.set_mode((300, 660))
def click(sx, sy):
    x, y = 30 + sx, 60 + sy      # headless scale=1，屏幕区域在 (30,60)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(x, y)))
click(170, 50)                   # 切到「本地列表」
click(100, 80)                   # 点第 1 行（2048）→ 直接玩
{extra}
from mrp_emu.cli import main
main(["--boot", "gamecenter", "--workdir", str(ROOT / "runtime"),
      "--headless", "--frames", "24", "--audio", "off",
      "--screenshot", str(ROOT / "out" / {shot!r})])
'''
    r = subprocess.run([sys.executable, "-u", "-c", code], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=180)
    return (r.stdout or "") + (r.stderr or "")


def test_click_launch() -> None:
    print("\n-- 集成：点击列表直接启动 --")
    log = _run_cli("", "probe_click_launch.png")
    check("start_dsm(" in log and "-> 0" in log,
          "点击本地项后 start_dsm 返回 0",
          next((x for x in log.splitlines() if "start_dsm" in x), ""))
    check((ROOT / "out" / "probe_click_launch.png").is_file(),
          "生成启动后截图")


def test_back_home() -> None:
    print("\n-- 集成：挂机键返回桌面 --")
    esc = ('pygame.event.post(pygame.event.Event(pygame.KEYDOWN, '
           'key=pygame.K_ESCAPE, unicode="", mod=0))')
    log = _run_cli(esc, "probe_back_home.png")
    check("start_dsm(" in log and "-> 0" in log, "先成功启动 MRP")
    check("timer 异常" not in log and "启动失败" not in log,
          "返回桌面后无定时器/启动异常")


def main() -> int:
    print("PymRP 启动界面 / 游戏中心自检")
    test_header()
    test_catalog()
    test_state_machine()
    test_click_launch()
    test_back_home()
    print(f"\n通过 {PASS} 项，失败 {FAIL} 项")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
