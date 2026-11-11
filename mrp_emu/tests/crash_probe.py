#!/usr/bin/env python3
"""崩溃隔离回归：MRP 野指针崩了不能带崩整个模拟器。

2026-11-10 老板报的三国志崩溃：

    [vm] 执行异常 Invalid memory read (UC_ERR_READ_UNMAPPED) @ PC=0x2FF282
    [vm] 非法访问:@0xCE875143(4B) PC=0x2FF282
    [vm] timer 异常: Invalid memory read (UC_ERR_READ_UNMAPPED)

根因在应用侧（间接跳转算错、跳进了运行时数据表；斯凯停运后
``system/userinfo.sys``、``gsgz/user.l`` 等运行时数据缺失是诱因），
补假资源后野指针值不变，属应用自身缺陷。模拟器该做的是**兜住它**：

  · 所有虚拟机调用（key_event / touch_event / timer）统一走 guarded；
  · 崩了就记录 → 收尾（停声音 / 关 socket / 关句柄）→ 退回系统界面；
  · 整个模拟器进程不退出，用户还能接着玩别的应用。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.catalog import probe_entry_ext  # noqa: E402
from mrp_emu.consts import KEY_NAME_TO_CODE  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

FAILS: list[str] = []
PASS = 0
GSZG = "301034_240320_gsgz.mrp"


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS
    if ok:
        PASS += 1
        print(f"  [PASS] {name}" + (f"  {detail}" if detail else ""))
    else:
        FAILS.append(name)
        print(f"  [FAIL] {name}  {detail}")


def isolated_env() -> Path:
    """只复制 cfunction.ext + mythroad/*.mrp，排除应用自建缓存目录。

    字库（``mythroad/system/gb16.uc2``）也要带上：DSM 层的应用启动
    第一件事就是 open 它来画中文，缺了会走另一条分支，崩溃类型从
    「写未映射」变成「读未映射」，断言就对不上了（见 docs/21）。
    """
    src = ROOT / "runtime"
    td = Path(tempfile.mkdtemp(prefix="pymrp-crash-"))
    (td / "mythroad").mkdir()
    shutil.copy2(src / "cfunction.ext", td / "cfunction.ext")
    for p in sorted((src / "mythroad").glob("*.mrp")):
        shutil.copy2(p, td / "mythroad" / p.name)
    # 字库：优先原厂，没有就现场生成一份
    try:
        from mrp_emu.fontgen import ensure_uc2
        ensure_uc2(td / "mythroad" / "system" / "gb16.uc2", log=lambda *a: None,
                   factory_dirs=[src / "mythroad" / "fonts",
                                 src / "mythroad" / "system"])
    except Exception:  # pragma: no cover - 字库不可用不该让测试崩
        pass
    return td


def main() -> int:
    print("== 1. cli 里所有虚拟机调用都有 guarded 保护 ==")
    import inspect

    import mrp_emu.cli as cli_mod
    src = inspect.getsource(cli_mod.main)
    naked = [ln.strip() for ln in src.splitlines()
             if ("vm.key_event(" in ln or "vm.touch_event(" in ln or "vm.timer(" in ln)
             and "guarded(" not in ln]
    check("没有裸调的虚拟机调用", not naked, str(naked))
    check("guarded 存在", "def guarded(" in src)
    check("guarded 异常后回桌面", "back_to_home(" in src)

    print("\n== 2. 真实三国志：崩溃被捕获且能干净收尾 ==")
    wd = isolated_env()
    target = wd / "mythroad" / GSZG
    if not target.is_file():
        print(f"  skip 本地没有 {GSZG}")
        return 0
    vm = Vm(log=lambda *a: None)
    app = App(vm, wd, log=lambda *a: None, audio=False)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    vm.load_code(wd / "cfunction.ext")
    vm.ext_init()
    vm.dsm_init()
    vm.start_dsm(target.name, probe_entry_ext(target), None)

    seq = ["DOWN", "SELECT", "DOWN", "SELECT", "RIGHT", "SOFT_R",
           "UP", "SELECT", "DOWN", "SELECT", "SOFT_L"]
    crashed = ""
    try:
        for i in range(900):
            if i % 25 == 0:
                k = seq[(i // 25) % len(seq)]
                vm.key_event(KEY_NAME_TO_CODE[k], True)
                vm.timer()
                vm.key_event(KEY_NAME_TO_CODE[k], False)
            vm.timer()
    except Exception as exc:  # noqa: BLE001
        crashed = f"{type(exc).__name__}: {exc}"
    check("崩溃被 Python 捕获（不会带走进程）", bool(crashed), crashed)

    info = app.shutdown_session("崩溃收尾")
    check("崩溃后句柄已清理", len(app.fs.handles) == 0, str(len(app.fs.handles)))
    check("崩溃后 socket 已清理",
          all(s.sock is None for s in app.net.slots), str(info))
    check("崩溃后音频已停", len(app.audio._channels) == 0)
    check("收尾返回统计", isinstance(info, dict) and "files" in info, str(info))
    app.net.shutdown()
    shutil.rmtree(wd, ignore_errors=True)

    print("\n== 3. 端到端：定时器崩溃后进程仍以 0 退出 ==")
    child = r'''
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, %r)
import mrp_emu.vm as vm_mod
import mrp_emu.app as app_mod
from unicorn import UcError, UC_ERR_READ_UNMAPPED
_orig = vm_mod.Vm
class _CrashVm(_orig):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._hits = 0
    def timer(self):
        self._hits += 1
        if self._hits >= 3:
            raise UcError(UC_ERR_READ_UNMAPPED)
        return super().timer()
vm_mod.Vm = _CrashVm
# dsm_gm 自己不一定设 timer，强制每帧都走一次，才能注入崩溃
app_mod.App.timer_due = lambda self: True
from mrp_emu.cli import main
sys.exit(main(%r))
''' % (str(ROOT), ["runtime/mythroad/dsm_gm.mrp", "--workdir", "runtime",
                  "--headless", "--frames", "60"])
    proc = subprocess.run([sys.executable, "-c", child], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=120)
    out = proc.stdout + proc.stderr
    check("崩溃后进程仍正常退出（rc=0）", proc.returncode == 0, f"rc={proc.returncode}")
    check("记录了崩溃原因", "[vm] timer 异常" in out, out[-240:])
    check("触发了收尾", "[teardown]" in out, out[-240:])
    check("崩溃只发生一次（之后应用不再被驱动）",
          out.count("[vm] timer 异常") == 1, str(out.count("[vm] timer 异常")))
    check("收尾把句柄和 socket 都关了", "[teardown] 已关闭" in out, out[-240:])
    # direct 模式（直接给 mrp 路径）没有 launcher 可退，但收尾必须完整
    check("direct 模式也能干净收尾", "[teardown] timer 异常" in out, out[-240:])
    check("launcher 模式下回桌面逻辑在位",
          'launcher.go("home")' in inspect.getsource(cli_mod.main))

    print(f"\n== 摘要 ==  crash_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
