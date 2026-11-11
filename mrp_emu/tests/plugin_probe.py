"""插件调用 / 返回专项探针。

真机（mythroad.c）里插件调用是一个**重启链**，宿主只负责不出错：

    应用 Lua: RunFile("ipqq.mrp", "startqq.mr", param)
      -> MRF_RunFile: pack_filename / start_filename 就位，mr_state=MR_STATE_RESTART
      -> 下一帧 mr_timer() 命中 RESTART 分支
           mr_stop()  ->  mr_stop_ex(TRUE)      <- 只停当前实例，不退应用
           _mr_intra_start(start_filename)      <- 加载并运行插件 MRP
    插件 Lua: Exit()
      -> MRF_Exit: old_pack_filename 非空 -> 恢复上级包名 -> 再次 RESTART
                   old_pack_filename 为空 -> mr_exit() -> 真正退到系统桌面

本探针固化三条宿主侧语义：

1. ``mr_stop_ex`` 只停实例（置 instance_stopped），**不**置 vm.exited ——
   否则插件链一启动就被判定为「应用退出」，直接退回主界面。
2. ``mr_exit`` / DSM ``exit`` 才是真退出，仍置 vm.exited。
3. 插件包用**裸文件名**（"ipqq.mrp"）或 "plugins/xxx.mrp" 形式引用时，
   文件系统必须能在 MRP 安装目录 mythroad/ 下找到 ——
   插件重启时 ext 用 mr_open(pack_filename) 加载，路径解析错了插件就跑不起来。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def _make_vm(workdir: Path):
    from mrp_emu.vm import Vm
    from mrp_emu.app import App

    v = Vm(log=lambda *a: None, zero_page=True)
    a = App(v, workdir, log=lambda *a: None, audio=False, net_enabled=False)
    v.app = a
    return v, a


def test_stop_ex_semantics() -> None:
    print("\n-- mr_stop_ex 语义：停实例，不退应用 --")
    from mrp_emu.api.impl import mr_stop_ex, mr_exit, dsm_exit
    import inspect

    src_stop = inspect.getsource(mr_stop_ex)
    src_exit = inspect.getsource(mr_exit)
    src_dsm = inspect.getsource(dsm_exit)

    check("mr_stop_ex 不再置 vm.exited", "vm.exited = True" not in src_stop)
    check("mr_stop_ex 置 instance_stopped", "instance_stopped" in src_stop)
    check("mr_exit 仍置 vm.exited（真退出）", "vm.exited = True" in src_exit)
    check("DSM exit 仍置 vm.exited（真退出）", "vm.exited = True" in src_dsm)


def test_vm_state_fields() -> None:
    print("\n-- Vm 状态字段 --")
    from mrp_emu.vm import Vm

    v, _a = _make_vm(ROOT / "runtime")
    check("Vm 有 app_stack 字段", hasattr(v, "app_stack"))
    check("Vm 有 instance_stopped 字段", hasattr(v, "instance_stopped"))
    check("app_stack 初始为空", v.app_stack == [])
    check("instance_stopped 初始为 False", v.instance_stopped is False)

    v.push_app({"pack": "a.mrp", "entry": "start.mr"})
    check("push_app 压入上级现场", len(v.app_stack) == 1)
    top = v.pop_app()
    check("pop_app 取出上级现场", top is not None and top["pack"] == "a.mrp")
    check("pop_app 后栈空", v.app_stack == [])
    check("空栈 pop_app 返回 None", v.pop_app() is None)


def test_plugin_path_resolution() -> None:
    print("\n-- 插件包路径解析（mythroad/ 回退）--")
    from mrp_emu.fs import VirtualFs

    root = (ROOT / "runtime").resolve()
    fs = VirtualFs(ROOT / "runtime")

    # 插件重启时 ext 用裸包名加载：mr_open("dsm_gm.mrp")
    p = fs.resolve("dsm_gm.mrp")
    check("裸包名解析到 mythroad/ 下",
          p is not None and p.parent == root / "mythroad",
          str(p))
    check("裸包名确实存在（测试前提）", p is not None and p.is_file())

    # 插件本体常在 plugins/ 子目录
    p2 = fs.resolve("plugins/netpay.mrp")
    check("plugins/ 相对路径解析到 mythroad/plugins/",
          p2 is not None and p2.parent == root / "mythroad" / "plugins",
          str(p2))

    # 目录形态必须保持原样（浏览目录语义）
    check("'./' 仍是 root", fs.resolve("./") == root)
    check("'mythroad' 仍是 root/mythroad", fs.resolve("mythroad") == root / "mythroad")
    check("'..' 钳回 root", fs.resolve("./..") == root)

    # 绝对写法不受影响
    p3 = fs.resolve("mythroad/dsm_gm.mrp")
    check("mythroad/ 绝对写法不变",
          p3 is not None and p3 == root / "mythroad" / "dsm_gm.mrp")


def test_ext_internal_chain() -> None:
    print("\n-- ext 内部重启链：mr_stop_ex 不打断插件 --")
    from mrp_emu.api.mrtable import MR_TABLE

    slot = next(bf for bf in MR_TABLE if bf.name == "mr_stop_ex")
    check("mr_stop_ex 槽位在 0x058", slot.pos == 0x058, hex(slot.pos))

    v, _a = _make_vm(ROOT / "runtime")

    class _Ctx:
        def __init__(self, vm):
            self.vm = vm
            self._n = 0

        def arg(self, i):
            return 1 if i == 0 else 0

        def ret(self, v):
            self._n = v

    ctx = _Ctx(v)
    v.exited = False
    v.instance_stopped = False
    slot.fn(ctx, v)
    check("调用后 instance_stopped 为 True", v.instance_stopped is True)
    check("调用后 vm.exited 仍为 False（插件链未被打断）", v.exited is False)

    # 有上级现场时更不能退应用
    v.push_app({"pack": "dsm_gm.mrp", "entry": "start.mr"})
    v.instance_stopped = False
    slot.fn(ctx, v)
    check("有上级现场时也不置 vm.exited", v.exited is False)
    check("上级现场仍在栈里", len(v.app_stack) == 1)


def main() -> int:
    print("=== 插件调用 / 返回 专项探针 ===")
    test_stop_ex_semantics()
    test_vm_state_fields()
    test_plugin_path_resolution()
    test_ext_internal_chain()
    print(f"\n=== 摘要: plugin_probe {PASS} 项通过 / {FAIL} 项失败 ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
