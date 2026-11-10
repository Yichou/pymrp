#!/usr/bin/env python3
"""曲奇启动器回归探针：低地址映射 / GBK 容错 / 安全运行名 / c2u / 真机集成。

背景（2026-11-10）：老板贴的日志里「冒泡6.0（线条模拟器提取（曲奇启动）.mrp」
跑到一半 ``PC=0x87A24`` 读 ``0x15858`` 触发 ``UC_ERR_READ_UNMAPPED``，
整个 VM 被 timer 异常终止。反汇编确认那是透明位图 blit 循环
``ldrh sl,[lr]``，源指针是低地址垃圾值 —— 真机低地址是 ROM/RAM，读到 0
不会炸；我们只映射了 0x0..0x10000，于是终止。

顺带查出的另外三个坑，一并锁进回归：

1. ``cstr`` 遇到「被截断在半个汉字上的 GBK」会整串退化成 latin-1，
   ``冒泡`` 变 ``Ã°ÅÝ``，``mr_open`` 打开不存在的乱码路径；
2. ext 的路径缓冲只有约 32 字节，超长中文文件名必被截断，
   包内 ``res_lang0.rc`` 报 ``code=2002`` —— 必须换成包头声明的短名；
3. ``c2u`` 槽位按官方签名应返回新分配的 UCS-2 宽串，旧实现写 UTF-8 到
   ``err`` 指针。

用法：python tests/cookie_probe.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

pygame.init()

from unicorn import UcError  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.impl import get as get_impl  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.catalog import probe_entry_ext, safe_run_name  # noqa: E402
from mrp_emu.consts import CODE_ADDRESS  # noqa: E402
from mrp_emu.memory import MrpMemory  # noqa: E402
from mrp_emu.vm import LOW_MEMORY_SIZE, ZERO_PAGE_SIZE, Vm  # noqa: E402

COOKIE = "冒泡6.0（线条模拟器提取（曲奇启动）.mrp"
CRASH_ADDR = 0x15858
STR_ADDR = 0x300000

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if cond:
        PASS += 1
    else:
        FAIL += 1


# ---------------------------------------------------------------- 1. 低地址
def test_low_memory() -> None:
    print("\n-- 低地址 ROM/RAM 映射 --")
    check("LOW_MEMORY_SIZE 覆盖到代码段起点",
          LOW_MEMORY_SIZE == CODE_ADDRESS,
          f"0x{LOW_MEMORY_SIZE:X} / 0x{CODE_ADDRESS:X}")
    check("旧零页常量仍保留", ZERO_PAGE_SIZE == 0x10000)
    vm = Vm(log=lambda *a: None)
    try:
        for addr in (0x0, 0xFFFE, 0x10000, CRASH_ADDR, 0x7FFFE):
            try:
                data = vm.uc.mem_read(addr, 2)
                ok = bytes(data) == b"\x00\x00"
            except UcError:
                ok = False
            check(f"0x{addr:X} 可读且为 0", ok)
        check("曲奇崩溃点 0x15858 在映射范围内", CRASH_ADDR < LOW_MEMORY_SIZE)
    finally:
        del vm

    # 敏感性对照：关掉零页后同一地址必须仍然不可访问
    bare = Vm(log=lambda *a: None, zero_page=False)
    try:
        try:
            bare.uc.mem_read(CRASH_ADDR, 2)
            readable = True
        except UcError:
            readable = False
        check("zero_page=False 时 0x15858 确实未映射（用例有区分度）",
              not readable)
    finally:
        del bare


# ---------------------------------------------------------------- 2. 字符串
def test_cstr() -> None:
    print("\n-- GBK 字符串容错（半个汉字截断） --")
    mem = MrpMemory()

    def decode(raw: bytes) -> str:
        mem.write(STR_ADDR, raw + b"\x00")
        return mem.cstr(STR_ADDR)

    gbk = "冒泡6.0（线条模拟器提取（曲奇启动）.mrp".encode("gbk")
    check("完整 GBK 中文正确解码", decode(gbk).startswith("冒泡6.0"), decode(gbk)[:12])
    check("纯 ASCII 保持不变", decode(b"mythroad/cookie.mrp") == "mythroad/cookie.mrp")

    # ext 用 41 字节缓冲把路径截断在半个汉字上
    truncated = b"mythroad/" + gbk[:32]
    out = decode(truncated)
    check("截断 GBK 不再出现 latin-1 乱码", "Ã" not in out and "°" not in out,
          repr(out[:36]))
    check("截断 GBK 仍保留可辨认中文", "冒泡" in out, repr(out[:20]))

    check("空串", decode(b"") == "")
    check("非法地址返回空串", mem.cstr(0x1000) == "")
    check("半个汉字本身不抛异常", isinstance(decode(b"\xc3"), str))


# ---------------------------------------------------------------- 3. 运行名
def test_safe_run_name() -> None:
    print("\n-- 安全运行名（ext 路径缓冲 ~32 字节） --")
    check("短 ASCII 名原样返回", safe_run_name("dsm_gm.mrp") == "dsm_gm.mrp")
    check("box.mrp 原样返回", safe_run_name("box.mrp") == "box.mrp")

    src = ROOT / "runtime" / "mythroad" / COOKIE
    if src.is_file():
        short = safe_run_name(src)
        check("长中文名取包头 8.3 短名", short == "cookie.mrp", short)
        check("运行名是纯 ASCII", all(ord(c) < 128 for c in short))
        check("运行名长度不超过 24 字节", len(short.encode("gbk")) <= 24)
    else:
        print("  [SKIP] 真实曲奇 MRP 不在运行环境，跳过包头短名检查")

    fallback = safe_run_name(ROOT / "不存在的应用（超长中文名字测试）.mrp")
    check("文件不存在时不抛异常", bool(fallback))
    check("回退名是 ASCII 且以 .mrp 结尾",
          all(ord(c) < 128 for c in fallback) and fallback.endswith(".mrp"),
          fallback)


# ---------------------------------------------------------------- 4. c2u
class _FakeCtx:
    """只实现 c2u 用到的三个方法，避免为了单测拉起整个 VM。"""

    def __init__(self, mem: MrpMemory, args: tuple[int, int, int]) -> None:
        self.mem = mem
        self._args = args
        self.value = 0

    def arg(self, i: int) -> int:
        return self._args[i] if i < len(self._args) else 0

    def ret(self, v: int) -> None:
        self.value = v


def test_c2u() -> None:
    print("\n-- c2u 槽位：GBK -> UCS-2 宽串 --")
    fn = get_impl("c2u")
    check("c2u 实现已注册", fn is not None)
    if fn is None:
        return
    mem = MrpMemory()
    src, err_p, size_p = 0x300000, 0x300100, 0x300104
    mem.write(src, "A冒泡".encode("gbk") + b"\x00")
    ctx = _FakeCtx(mem, (src, err_p, size_p))
    fn(ctx, None)
    ptr = ctx.value
    check("返回新分配缓冲而不是入参指针", ptr != src and ptr != 0, f"0x{ptr:X}")
    if not ptr:
        return
    size = mem.u32(size_p)
    check("*size 是含结尾 NUL 的字节数", size == 4 * 2, str(size))
    raw = mem.read(ptr, size)
    check("内存布局是 UTF-16BE", raw == "A冒泡".encode("utf-16-be") + b"\x00\x00",
          raw.hex(" "))
    check("err 指针按官方写 -1", mem.u32(err_p) == 0xFFFFFFFF)
    mem.free(ptr)
    check("返回的块可被 mr_free 释放", ptr not in mem.heap.used)


# ---------------------------------------------------------------- 5. 真机集成
def test_real_cookie() -> None:
    print("\n-- 真实曲奇启动器 300 帧 --")
    src = ROOT / "runtime" / "mythroad" / COOKIE
    ext_file = ROOT / "runtime" / "cfunction.ext"
    if not (src.is_file() and ext_file.is_file()):
        print("  [SKIP] 运行环境缺少 cfunction.ext 或曲奇 MRP，跳过集成用例")
        return
    with tempfile.TemporaryDirectory(prefix="pymrp-cookie-",
                                    ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        shutil.copy2(ext_file, tmp / "cfunction.ext")
        sysdir = tmp / "mythroad" / "system"
        sysdir.mkdir(parents=True)
        for f in (ROOT / "runtime" / "mythroad" / "system").glob("*"):
            if f.is_file():
                shutil.copy2(f, sysdir / f.name)
        run_name = safe_run_name(src)
        target = tmp / "mythroad" / run_name
        shutil.copy2(src, target)

        logs: list[str] = []
        vm = Vm(log=lambda *a: None)
        app = App(vm, tmp, log=logs.append, audio=False)
        vm.app = app
        vm.install_tables(MR_TABLE, DSM_FUNCS)
        vm.load_code(tmp / "cfunction.ext")
        vm.ext_init()
        vm.dsm_init()
        r = vm.start_dsm(run_name, probe_entry_ext(target), None)
        check("start_dsm 返回值正常", r in (0, 1), str(r))

        frames, err = 0, None
        try:
            for _ in range(300):
                vm.timer()
                frames += 1
        except UcError as exc:
            err = exc
        check("300 帧无 UC_ERR_READ_UNMAPPED", err is None,
              f"frames={frames} err={err}")
        check("跑满 300 帧", frames == 300, str(frames))

        arr = app.gfx.array()
        nonzero = int((arr != 0).sum())
        check("帧缓冲确实绘制了内容（不是空屏）", nonzero > 5000,
              f"nonzero={nonzero}/{arr.size}")

        joined = "\n".join(logs)
        check("日志里没有 latin-1 乱码文件名", "Ã°ÅÝ" not in joined)
        check("短名生效：res_lang0.rc 不再报 2002",
              'res_lang0.rc" from mrp err,code=2002' not in joined)
        app.net.shutdown()
        # ext 会一直持有字库 fd；Windows 下不显式关闭就没法删临时目录
        for h in list(app.fs.handles.values()):
            try:
                h["fp"].close()
            except OSError:
                pass
        app.fs.handles.clear()
        del vm, app


def main() -> int:
    test_low_memory()
    test_cstr()
    test_safe_run_name()
    test_c2u()
    test_real_cookie()
    print(f"\n cookie_probe: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
