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

本探针固化四条宿主侧语义：

1. ``mr_stop_ex`` 只停实例（置 instance_stopped），**不**置 vm.exited ——
   否则插件链一启动就被判定为「应用退出」，直接退回主界面。
2. ``mr_exit`` / DSM ``exit`` 才是真退出，仍置 vm.exited。
3. 插件包用**裸文件名**（"ipqq.mrp"）或 "plugins/xxx.mrp" 形式引用时，
   文件系统必须能在 MRP 安装目录 mythroad/ 下找到 ——
   插件重启时 ext 用 mr_open(pack_filename) 加载，路径解析错了插件就跑不起来。
4. **VM 内存地址必须跨重启稳定**（斯凯的 dump/恢复机制前提）：
   官方 mythroad.c:7364 在 ``mr_stop_ex(freemem!=0)`` 里
   ``mr_mem_free(Origin_LG_mem_base, ...)``，下一轮 ``_mr_mem_init()``
   重新 ``mr_mem_get()`` 必须拿到**同一地址** ——
   dump 的是内存内容，恢复按同一地址写回，地址漂移就全是野指针。
   外加 DNS 映射必须覆盖 proxy.51mrp.com / proxy2.51mrp.com
   （浏览器插件组件下载域名，对齐 skyengine-v2 的 e2e 用例）。
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


def test_dump_snapshot_path() -> None:
    """斯凯的现场快照文件必须落在 mythroad/plugins/ 下。

    ext 在切插件前把整个运行内存 dump 到 ``plugins/dump%d``
    （cfunction.ext 的字符串表里就是这个模板），插件退出后按**同一路径**
    读回恢复。文件还不存在时也必须解析到 mythroad/plugins/ 下，
    否则写到了别处、恢复时读不回来，指针全是野的。
    """
    print("\n-- 现场快照路径（plugins/dump%d）--")
    from mrp_emu.fs import VirtualFs

    root = (ROOT / "runtime").resolve()
    fs = VirtualFs(ROOT / "runtime")

    p = fs.resolve("plugins/dump0")
    check("plugins/dump0 解析到 mythroad/plugins/",
          p is not None and p.parent == root / "mythroad" / "plugins",
          str(p))
    check("plugins/dump0 是新建文件（尚不存在）",
          p is not None and not p.exists())

    p1 = fs.resolve("plugins/dump1")
    check("plugins/dump1 同样解析到 mythroad/plugins/",
          p1 is not None and p1.parent == root / "mythroad" / "plugins",
          str(p1))

    # 浏览目录语义不能被破坏
    check("'plugins/' 仍是 plugins（目录形态不变）",
          fs.resolve("plugins/") == root / "plugins")
    check("'mythroad' 仍是 root/mythroad",
          fs.resolve("mythroad") == root / "mythroad")
    check("'./' 仍是 root", fs.resolve("./") == root)


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


def test_vm_memory_address_stability() -> None:
    """VM 内存地址必须跨重启稳定 —— dump/恢复机制的前提。

    官方 mythroad.c:626 的 ``_mr_mem_init()`` 调 ``mr_mem_get()`` 申请整块
    VM 内存；``mr_stop_ex(freemem!=0)``（mythroad.c:7364）调
    ``mr_mem_free(Origin_LG_mem_base, ...)`` 释放。重启链的下一轮必须
    拿到**同一地址**：斯凯插件机制把整个运行内存 dump 到
    ``plugins/dump%d``，退出插件后按同一地址读回恢复。
    """
    print("\n-- VM 内存地址跨重启稳定（dump/恢复前提）--")
    from mrp_emu.api.impl import dsm_mem_get, mr_stop_ex
    from mrp_emu.memory import MrpMemory

    class _Ctx:
        def __init__(self, vm, *args):
            self.vm = vm
            self._a = list(args)
            self._ret = 0

        def arg(self, i):
            return self._a[i]

        def ret(self, v):
            self._ret = v

        @property
        def mem(self):
            return self.vm.mem

    v, _a = _make_vm(ROOT / "runtime")
    # 用独立的内存模型，避免动到共享 runtime 的状态
    v.mem = MrpMemory()
    v.vm_mem_block = None

    bp, lp = 0x80000, 0x80004
    dsm_mem_get(_Ctx(v, bp, lp), v)
    base1 = v.mem.u32(bp)
    len1 = v.mem.u32(lp)
    check("首次 mem_get 成功", base1 != 0, f"0x{base1:X}")
    check("mem_get 记录了 VM 内存块", v.vm_mem_block == base1,
          f"{v.vm_mem_block!r} vs 0x{base1:X}")

    # freemem=1 -> 释放（官方语义）
    mr_stop_ex(_Ctx(v, 1), v)
    check("mr_stop_ex(freemem=1) 释放了 VM 内存块", v.vm_mem_block is None)
    check("释放后 instance_stopped 为 True", v.instance_stopped is True)
    check("释放后 vm.exited 仍为 False（不是退出应用）", v.exited is False)

    # 第二轮：必须拿到同一地址
    dsm_mem_get(_Ctx(v, bp, lp), v)
    base2 = v.mem.u32(bp)
    check("第二轮 mem_get 拿到同一地址（dump/恢复可成立）",
          base1 == base2, f"0x{base1:X} vs 0x{base2:X}")
    check("两轮长度一致", v.mem.u32(lp) == len1)

    # 堆必须还够再分配一次 4MB（6MB 堆 - 4MB 已在用）
    check("堆未耗尽（第二轮分配成功）", base2 != 0)


def test_vm_memory_reserved_region() -> None:
    """VM 内存走专用预留区：地址恒定，普通 malloc 拿不到。

    普通 first-fit 堆做不到地址恒定：碎片一多，同尺寸的两次分配就落到
    不同地址（实测 0x280000 vs 0x299000）。dump 记录的是绝对地址，
    恢复按同一地址写回，漂移就全是野指针。
    """
    print("\n-- VM 内存预留区（地址恒定）--")
    from mrp_emu.memory import MrpMemory

    m = MrpMemory()
    r = m.heap.reserve(4 * 1024 * 1024)
    check("reserve 成功", r != 0, hex(r))
    check("reserve 的块进入 used（不归还可被抢占）", r in m.heap.used)

    # 制造碎片后再分配，不能命中预留区
    hit = False
    for _ in range(40):
        p = m.malloc(64 * 1024)
        if p == r:
            hit = True
            break
    check("普通 malloc 抢不到预留区", not hit)

    # 碎片环境下，第二次 reserve 也不能复用已占的预留区地址
    m2 = MrpMemory()
    res = m2.heap.reserve(4 * 1024 * 1024)
    check("预留区地址非 0", res != 0, hex(res))
    junk = [m2.malloc(128 * 1024) for _ in range(8)]
    check("碎片分配后预留区仍在 used 里", res in m2.heap.used)
    print(f"       （预留区 0x{res:X}，堆 {m2.heap.report()}）")


def test_plugin_dns_mapping() -> None:
    """浏览器插件组件下载域名必须在 DNS 映射里。

    skyengine-v2 的 e2e 用例（test/e2e/dota/download-plugin.test.ts、
    test/e2e/optwar/speed.test.ts）在 brwshell 场景显式传入
    ``proxy.51mrp.com->159.75.119.124;proxy2.51mrp.com->159.75.119.124``；
    缺了这两条，插件组件下载不下来，表现为「插件打开后立刻退回主界面」。
    """
    print("\n-- 插件组件下载域名 DNS 映射 --")
    from mrp_emu.net import parse_dns_map, DEFAULT_DNS_MAP

    mapping = parse_dns_map(DEFAULT_DNS_MAP)
    sources = {m.source for m in mapping}
    for host in ("proxy.51mrp.com", "proxy2.51mrp.com"):
        check(f"{host} 在默认 DNS 映射里", host in sources)
        m = next((x for x in mapping if x.source == host), None)
        check(f"{host} 指向复刻服务端", m is not None and m.address == "159.75.119.124",
              str(m))


def main() -> int:
    print("=== 插件调用 / 返回 专项探针 ===")
    test_stop_ex_semantics()
    test_vm_state_fields()
    test_plugin_path_resolution()
    test_dump_snapshot_path()
    test_ext_internal_chain()
    test_vm_memory_address_stability()
    test_vm_memory_reserved_region()
    test_plugin_dns_mapping()
    print(f"\n=== 摘要: plugin_probe {PASS} 项通过 / {FAIL} 项失败 ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
