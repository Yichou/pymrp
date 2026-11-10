#!/usr/bin/env python3
"""退出 / 崩溃收尾回归：声音要停、socket 要关、句柄要关、退回系统界面。

背景（2026-11-10）：``vm.exited`` 之前只被设置、**从来没有被消费**。
MRP 应用调用 ``mr_exit()`` 之后：

  · 背景音乐继续放（老应用还会以为声音没停而反复重播）；
  · 网络 socket 一直挂着（下次会话又建一批）；
  · 文件句柄一直占着（句柄号会被下一次会话复用，MRP 侧可能读到别的文件）；
  · 界面停在应用里，回不到系统界面。

现在统一走 ``App.shutdown_session()``：停声音 → 关网络 → 关句柄 → 回桌面。
"""

from __future__ import annotations

import inspect
import os
import socket
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from mrp_emu.app import App  # noqa: E402
from mrp_emu.audio.mixer import AudioEngine  # noqa: E402
from mrp_emu.consts import MR_FILE_RDONLY  # noqa: E402
from mrp_emu.fs import VirtualFs  # noqa: E402
from mrp_emu.net import DSM_SOC_CLOSE  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

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


def make_wav(seconds: float = 0.2, rate: int = 22050) -> bytes:
    # Windows 上 NamedTemporaryFile 不关句柄就没法删，务必先退出 with
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as buf:
        path = buf.name
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    data = Path(path).read_bytes()
    Path(path).unlink(missing_ok=True)
    return data


def new_app(tmp: Path) -> App:
    vm = Vm(log=lambda *a: None)
    app = App(vm, tmp, log=lambda *a: None, audio=True)
    vm.app = app
    return app


def main() -> int:
    print("== 1. mr_exit 槽位 ==")
    tmp = Path(tempfile.mkdtemp(prefix="pymrp-exit-"))
    app = new_app(tmp)
    vm = app.vm

    from mrp_emu.api import impl  # noqa: E402
    fn = impl.get("mr_exit")
    check("mr_exit 槽位存在", fn is not None)
    if fn is not None:
        vm.exited = False
        fn(_Ctx(vm), vm)
        check("mr_exit 置 vm.exited", vm.exited is True)

    print("\n== 2. shutdown_session 清理三件套 ==")
    # 文件句柄
    (tmp / "a.txt").write_text("hello", encoding="utf-8")
    f1 = app.fs.open("a.txt", MR_FILE_RDONLY)
    f2 = app.fs.open("a.txt", MR_FILE_RDONLY)
    check("测试前置：两个文件句柄已打开", len(app.fs.handles) == 2, str(len(app.fs.handles)))

    # socket
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    app.net.slots[0].sock = sk
    app.net.slots[0].state = 1
    app.net.initialized = True

    # 音频：真播一次，才有通道
    audio = app.audio
    played = audio.play(1, make_wav(), False)      # 1 = WAV
    check("音频已播放（产生通道）", len(audio._channels) > 0,
          f"channels={len(audio._channels)} played={played}")

    info = app.shutdown_session("测试退出")
    check("文件句柄已全部关闭", len(app.fs.handles) == 0, str(len(app.fs.handles)))
    check("关闭句柄数已统计", info.get("files", 0) >= 2, str(info))
    check("socket 已关闭", app.net.slots[0].sock is None
          and app.net.slots[0].state == DSM_SOC_CLOSE)
    check("socket 数已统计", info.get("sockets", 0) >= 1, str(info))
    check("音频通道已清空", len(audio._channels) == 0, str(len(audio._channels)))
    check("音频 hold 已清空", len(audio._hold) == 0)
    check("收尾标记为已完成", info.get("audio") is True, str(info))

    print("\n== 3. 幂等与异常隔离 ==")
    again = app.shutdown_session("重复收尾")
    check("重复收尾不抛异常", isinstance(again, dict), str(again))
    check("重复收尾后仍无句柄", len(app.fs.handles) == 0)

    print("\n== 4. VirtualFs.close_all ==")
    fs = VirtualFs(tmp)
    fs.open("a.txt", MR_FILE_RDONLY)
    fs.open("a.txt", MR_FILE_RDONLY)
    fs.open("a.txt", MR_FILE_RDONLY)
    n = fs.close_all()
    check("close_all 返回关掉的句柄数", n == 3, str(n))
    check("close_all 后句柄表为空", not fs.handles)
    check("close_all 对空表安全", fs.close_all() == 0)

    print("\n== 5. cli 主循环消费 vm.exited ==")
    import mrp_emu.cli as cli_mod
    src = inspect.getsource(cli_mod.main)
    check("主循环里有 vm.exited 消费分支", "vm.exited" in src)
    check("退出后调用统一收尾", "back_to_home(" in src and "teardown_session(" in src)
    check("收尾走 App.shutdown_session", "shutdown_session(" in src)

    print("\n== 6. 端到端：应用一启动就 mr_exit ==")
    child = r'''
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, %r)
import mrp_emu.vm as vm_mod
_orig = vm_mod.Vm
class _FakeVm(_orig):
    def start_dsm(self, *a, **kw):
        r = super().start_dsm(*a, **kw)
        self.exited = True          # 模拟应用刚起来就调用 mr_exit()
        return r
vm_mod.Vm = _FakeVm
from mrp_emu.cli import main
sys.exit(main(%r))
''' % (str(ROOT), ["runtime/mythroad/dsm_gm.mrp", "--workdir", "runtime",
                  "--headless", "--frames", "4"])
    proc = subprocess.run([sys.executable, "-c", child], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=120)
    out = proc.stdout + proc.stderr
    check("子进程退出码 0", proc.returncode == 0, f"rc={proc.returncode}")
    check("出现收尾日志", "[teardown]" in out, out[-300:])
    check("收尾原因正确", "mr_exit" in out, out[-300:])
    check("退出后不再渲染应用画面", "timer 异常" not in out)

    print(f"\n== 摘要 ==  exit_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    return 0 if not FAILS else 1


class _Ctx:
    """最小 ctx 桩：mr_exit 只需要 arg()/ret()。"""

    def __init__(self, vm):
        self._vm = vm
        self.mem = vm.mem

    def arg(self, i):
        return 0

    def ret(self, v):
        self._ret = v


if __name__ == "__main__":
    sys.exit(main())
