#!/usr/bin/env python3
"""格式化器回归：sprintf / mr_sprintf 的格式覆盖与返回值语义。

2026-11-10 老板问「你是不是没有实现 sprintf」。查下来：

* ``sprintf`` 一直有（mr_table 0x044），但**残缺**：不支持 ``%f``、长度
  修饰符 ``l/ll`` 不生效、宽度/精度/对齐只做了零填充；
* ``mr_sprintf``（MRP 专用版）**没有**；
* 更要命的是**返回值给的是 Python 字符数**，而 C 标准要的是**字节数** ——
  中文文件名短一截，应用拿返回值定位下一列就会错位。

这个探针把上面每一条都钉死。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mrp_emu.api import impl  # noqa: E402
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


class _Ctx:
    """最小 ctx 桩：给 sprintf 用。"""

    def __init__(self, mem, args: list, dst: int = 0):
        self.mem = mem
        self._args = args
        self._dst = dst
        self._ret = 0

    def arg(self, n: int) -> int:
        return self._args[n] if 0 <= n < len(self._args) else 0

    def qarg(self, n: int) -> int:
        return self._args[n] if 0 <= n < len(self._args) else 0

    def farg(self, n: int) -> float:
        v = self._args[n] if 0 <= n < len(self._args) else 0
        return float(v)

    def ret(self, v: int) -> None:
        self._ret = v


def main() -> int:
    vm = Vm(log=lambda *a: None)
    mem = vm.mem

    def S(text: str) -> int:
        """把字符串放进模拟内存，返回指针（%s 要的是地址不是内容）。"""
        a = mem.malloc(len(text) + 8)
        mem.put_cstr(a, text)
        return a

    print("== 1. 基本转换符 ==")
    cases = [
        ("%d", [42], "42"),
        ("%d", [-7], "-7"),
        ("%i", [123], "123"),
        ("%u", [-1], "4294967295"),
        ("%x", [255], "ff"),
        ("%X", [255], "FF"),
        ("%o", [8], "10"),
        ("%c", [65], "A"),
        ("%%", [], "%"),
        ("a=%d b=%d", [1, 2], "a=1 b=2"),
        ("%s", [], "(null)"),
        ("%d%%", [50], "50%"),
        ("%s", [S("hello")], "hello"),
    ]
    for fmt, args, want in cases:
        got = impl._fmt(fmt, args, mem)
        check(f"_fmt({fmt!r}, {args})", got == want, f"得到 {got!r} 期望 {want!r}")

    print("\n== 2. 宽度 / 精度 / 对齐 / 填充 ==")
    wcases = [
        ("%5d", [42], "   42"),
        ("%-5d|", [42], "42   |"),
        ("%05d", [42], "00042"),
        ("%-5d|", [42], "42   |"),
        ("%+d", [42], "+42"),
        ("% d", [42], " 42"),
        ("%.3s", [S("abcdef")], "abc"),
        ("%8.3s|", [S("abcdef")], "     abc|"),
        ("%x", [255], "ff"),
        ("%#x", [255], "0xff"),
        ("%#o", [8], "010"),
        ("%*d", [6, 42], "    42"),
        ("%.*s", [2, S("abcdef")], "ab"),
    ]
    for fmt, args, want in wcases:
        got = impl._fmt(fmt, args, mem)
        check(f"_fmt({fmt!r}, {args})", got == want, f"得到 {got!r} 期望 {want!r}")

    print("\n== 3. 浮点 ==")
    fcases = [
        ("%.2f", [3.14159], "3.14"),
        ("%f", [1.5], "1.500000"),
        ("%.0f", [2.5], "2"),
        ("%8.2f|", [3.14159], "    3.14|"),
        ("%-8.2f|", [3.14159], "3.14    |"),
        ("%e", [1234.5], "1.234500e+03"),
    ]
    for fmt, args, want in fcases:
        got = impl._fmt(fmt, args, mem, floats={0: float(args[0])})
        check(f"_fmt({fmt!r}, {args})", got == want, f"得到 {got!r} 期望 {want!r}")

    print("\n== 4. 长度修饰符 ==")
    # ARM AAPCS：long 是 32 位，long long 才是 64 位
    lcases = [
        ("%ld", [1234567890123], "1912276171"),   # long=32 位，按低 32 位解释
        ("%lu", [1234567890123], "1912276171"),
        ("%lx", [255], "ff"),
        ("%hd", [70000], "4464"),                  # short=16 位截断
    ]
    for fmt, args, want in lcases:
        got = impl._fmt(fmt, args, mem)
        check(f"_fmt({fmt!r}, {args})", got == want, f"得到 {got!r} 期望 {want!r}")
    got = impl._fmt("%lld", [1234567890123], mem, longs={0: 1234567890123})
    check("_fmt('%lld') 走 64 位路径", got == "1234567890123", f"得到 {got!r}")

    print("\n== 5. sprintf 端到端（返回值必须是字节数）==")
    buf = mem.malloc(256)
    strbuf = mem.malloc(64)
    mem.put_cstr(strbuf, "中文abc")
    fmtbuf = mem.malloc(64)
    mem.put_cstr(fmtbuf, "%s%d")

    ctx = _Ctx(mem, [buf, fmtbuf, strbuf, 7], dst=buf)
    impl.sprintf(ctx, vm)
    check("sprintf 写入内容正确", mem.cstr(buf) == "中文abc7",
          repr(mem.cstr(buf)))
    check("sprintf 返回字节数（不是字符数）", ctx._ret == len("中文abc7".encode("gbk")),
          f"返回 {ctx._ret}，期望 {len('中文abc7'.encode('gbk'))}")

    fmt2 = mem.malloc(64)
    mem.put_cstr(fmt2, "%s")
    ctx2 = _Ctx(mem, [buf, fmt2, strbuf], dst=buf)
    impl.sprintf(ctx2, vm)
    check("纯 ASCII 时返回值 = 字符数", ctx2._ret == len("中文abc".encode("gbk")),
          f"返回 {ctx2._ret}")

    fmt3 = mem.malloc(64)
    mem.put_cstr(fmt3, "%X")
    ctx3 = _Ctx(mem, [buf, fmt3, 255], dst=buf)
    impl.sprintf(ctx3, vm)
    check("十六进制大写", mem.cstr(buf) == "FF", repr(mem.cstr(buf)))

    print("\n== 6. mr_sprintf ==")
    check("mr_sprintf 已实现", impl.get("mr_sprintf") is not None)
    if impl.get("mr_sprintf"):
        fmt4 = mem.malloc(64)
        mem.put_cstr(fmt4, "%s%d")
        ctx4 = _Ctx(mem, [buf, fmt4, strbuf, 5], dst=buf)
        impl.get("mr_sprintf")(ctx4, vm)
        check("mr_sprintf 与 sprintf 同语义", mem.cstr(buf) == "中文abc5",
              repr(mem.cstr(buf)))

    print("\n== 7. 未知转换符不崩 ==")
    got = impl._fmt("%q", [1], mem)
    check("未知转换符原样输出", got == "%q", repr(got))

    print(f"\n== 摘要 ==  fmt_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
