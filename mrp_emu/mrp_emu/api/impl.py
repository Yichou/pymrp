"""MRP API 实现。

命名与 mr_table / dsm_require_funcs 里的条目一一对应，注册进 IMPL 表后由
mrtable.py / dsmfuncs.py 按名字绑定到槽位。

约定：每个实现收到 (ctx: ArmCall, vm: Vm)，用 ctx.arg(n) 取参数、
ctx.ret(v) 设返回值。ctx.mem 是 8MB 模拟内存，vm.app 是宿主应用。
"""

from __future__ import annotations

import time
from datetime import datetime

from ..consts import (
    DEVICE_MODEL,
    DEVICE_VENDOR,
    IMEI,
    MR_FAILED,
    MR_FILE_CREATE,
    MR_FILE_RDONLY,
    MR_FILE_RDWR,
    MR_FILE_WRONLY,
    MR_KEY_PRESS,
    MR_KEY_RELEASE,
    MR_NO_EXIST,
    MR_SUCCESS,
    MR_WAITING,
    SCREEN_BPP,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

IMPL: dict[str, callable] = {}


def api(*names: str):
    def deco(fn):
        for n in names:
            IMPL[n] = fn
        return fn
    return deco


def get(name: str):
    return IMPL.get(name)


# ==================================================================== 工具
def _s(ctx, i: int) -> str:
    return ctx.mem.cstr(ctx.arg(i))


_MAX_BLOB = 8 << 20          # 8MB，正好是整块模拟内存的上限


def _read_blob(vm, addr: int, length: int) -> bytes:
    """从模拟内存里安全地取一段数据。

    MRP 传进来的长度经常不可信（未初始化、按 0 取反、故意喂假值），
    所以一律先验地址、再把长度 clamp 到内存末尾，宁可少读也不越界。
    """
    mem = vm.mem
    n = int(length)
    if not addr or n <= 0:
        return b""
    if not mem.valid(addr, 1):
        return b""
    if n > _MAX_BLOB:
        n = _MAX_BLOB
    room = mem.base + mem.size - addr
    n = min(n, room)
    if n <= 0:
        return b""
    return mem.read(addr, n)


_FMT_FLAG = "-+ #0'"


def _parse_fmt(fmt: str) -> list[dict]:
    """把格式串拆成「文本段 + 转换项」列表。

    支持：``%`` ``d i u o x X f e g G a A c s p n``、长度修饰符
    ``hh h l ll L j z t``、``- + 空格 # 0 '`` 标志、宽度、精度，以及
    ``*`` 动态宽度/精度。
    """
    out: list[dict] = []
    lit: list[str] = []
    i, n = 0, len(fmt)
    while i < n:
        c = fmt[i]
        if c != "%":
            lit.append(c)
            i += 1
            continue
        i += 1
        if i < n and fmt[i] == "%":
            lit.append("%")
            i += 1
            continue
        if lit:
            out.append({"kind": "text", "lit": "".join(lit)})
            lit = []
        j = i
        while j < n and fmt[j] in _FMT_FLAG:
            j += 1
        flags = fmt[i:j]
        i = j
        width = None
        width_star = False
        if i < n and fmt[i] == "*":
            width_star = True
            i += 1
        else:
            j = i
            while j < n and fmt[j].isdigit():
                j += 1
            if j > i:
                width = int(fmt[i:j])
                i = j
        prec = None
        prec_star = False
        if i < n and fmt[i] == ".":
            i += 1
            if i < n and fmt[i] == "*":
                prec_star = True
                i += 1
            else:
                j = i
                while j < n and fmt[j].isdigit():
                    j += 1
                prec = int(fmt[i:j]) if j > i else 0
                i = j
        lenmod = ""
        # 注意：不要把 'q' 收进来（ARM 上 %q 不是转换符，收了会把 %q 吃掉）
        if i < n and fmt[i] in "hlLjzt":
            lenmod = fmt[i]
            i += 1
            if lenmod in "lL" and i < n and fmt[i] == "l":
                lenmod = "ll"
                i += 1
        if i >= n:
            break
        conv = fmt[i]
        i += 1
        out.append({"kind": "conv", "conv": conv, "flags": flags, "width": width,
                    "width_star": width_star, "prec": prec, "prec_star": prec_star,
                    "lenmod": lenmod})
    if lit:
        out.append({"kind": "text", "lit": "".join(lit)})
    return out


def _collect(specs: list[dict], get_int, get_q, get_f) -> dict[int, tuple[str, object]]:
    """按 C 的顺序取变参：``*`` 宽度、``*`` 精度先于转换符本身的参数。"""
    vals: dict[int, tuple[str, object]] = {}
    vi = 0
    for sp in specs:
        if sp["kind"] == "text":
            continue
        if sp["width_star"]:
            vals[vi] = ("i", get_int(vi))
            vi += 1
        if sp["prec_star"]:
            vals[vi] = ("i", get_int(vi))
            vi += 1
        conv = sp["conv"]
        if conv in "feEgG":
            vals[vi] = ("f", get_f(vi))
        elif sp["lenmod"] in ("ll", "j", "L"):
            vals[vi] = ("q", get_q(vi))
        else:
            vals[vi] = ("i", get_int(vi))
        vi += 1
    return vals


def _fmt(fmt: str, args: list[int], mem, floats: dict | None = None,
         longs: dict | None = None) -> str:
    """迷你 printf：MRP 常用的格式都支持。

    ``args`` 是整数变参列表，``floats``/``longs`` 按同一个下标补充浮点与
    64 位参数（旧调用方只传 ``args`` 时保持兼容）。
    """
    specs = _parse_fmt(fmt)

    def _gi(vi: int) -> int:
        return args[vi] if vi < len(args) else 0

    def _gq(vi: int) -> int:
        if longs and vi in longs:
            return longs[vi]
        return _gi(vi)

    def _gf(vi: int) -> float:
        return (floats or {}).get(vi, 0.0)

    vals = _collect(specs, _gi, _gq, _gf)
    return _render(specs, vals, mem)


def _render(specs: list[dict], vals: dict[int, tuple[str, object]], mem) -> str:
    out: list[str] = []
    vi = 0
    for sp in specs:
        if sp["kind"] == "text":
            out.append(sp["lit"])
            continue
        conv = sp["conv"]
        flags = sp["flags"]
        width = sp["width"]
        prec = sp["prec"]
        if sp["width_star"]:
            width = int(vals[vi][1])
            vi += 1
        if sp["prec_star"]:
            prec = int(vals[vi][1])
            vi += 1
        kind, val = vals.get(vi, ("i", 0))
        vi += 1

        if conv == "n":
            continue
        if conv == "s":
            text = mem.cstr(int(val)) if int(val) else "(null)"
            if prec is not None:
                text = text[:prec]
            out.append(_pad_str(text, width, flags))
            continue
        if conv == "c":
            out.append(_pad_str(chr(int(val) & 0xFF), width, flags))
            continue
        if conv == "p":
            out.append(_pad_str(f"0x{int(val) & 0xFFFFFFFF:08X}", width, flags))
            continue
        if conv in "feEgG":
            f = float(val)
            p = 6 if prec is None else prec
            if conv == "f":
                text = f"{f:.{p}f}"
            elif conv in "eE":
                text = f"{f:.{p}e}"
                if conv == "E":
                    text = text.upper()
            else:
                text = f"{f:.{p}g}"
                if conv == "G":
                    text = text.upper()
            out.append(_pad_num(text, width, flags, True))
            continue

        # 整数类：先按无符号宽度解释，再看符号位（Python 的负数 & 0x80000000
        # 不等于 C 的行为，必须先截断再判断）
        iv = int(val)
        if kind == "q":
            u = iv & 0xFFFFFFFFFFFFFFFF
            s = u - 0x10000000000000000 if u & 0x8000000000000000 else u
        else:
            if sp["lenmod"] in ("hh", "h"):
                u = iv & 0xFFFF
                s = u - 0x10000 if u & 0x8000 else u
            else:
                u = iv & 0xFFFFFFFF
                s = u - 0x100000000 if u & 0x80000000 else u
        if conv in "di":
            if flags:
                if s >= 0 and "+" in flags:
                    s = f"+{s}"
                elif s >= 0 and " " in flags:
                    s = f" {s}"
            text = str(s)
            out.append(_pad_num(text, width, flags, False))
        elif conv == "u":
            text = str(u)
            out.append(_pad_num(text, width, flags, False))
        elif conv == "o":
            text = format(u, "o")
            if "#" in flags:
                text = "0" + text
            out.append(_pad_num(text, width, flags, False))
        elif conv in "xX":
            text = format(u, "x" if conv == "x" else "X")
            if "#" in flags:
                text = ("0x" if conv == "x" else "0X") + text
            out.append(_pad_num(text, width, flags, False))
        else:
            out.append("%" + flags + conv)
    return "".join(out)


def _pad_str(text: str, width: int | None, flags: str) -> str:
    if not width or len(text) >= width:
        return text
    return text.ljust(width, " ") if "-" in flags else text.rjust(width, " ")


def _pad_num(text: str, width: int | None, flags: str, is_float: bool) -> str:
    """数值填充：``0`` 标志零填充（浮点要保留符号位），``-`` 左对齐。"""
    if not width or len(text) >= width:
        return text
    if "-" in flags:
        return text.ljust(width, " ")
    if "0" in flags and not is_float:
        sign = ""
        body = text
        if body[:1] in "+- ":
            sign, body = body[0], body[1:]
        return sign + body.rjust(width - len(sign), "0")
    return text.rjust(width, " ")


# ==================================================================== 内存
@api("mr_malloc")
def mr_malloc(ctx, vm):
    ctx.ret(ctx.mem.malloc(ctx.arg(0)))


@api("mr_free")
def mr_free(ctx, vm):
    ctx.mem.free(ctx.arg(0))
    ctx.ret(MR_SUCCESS)


@api("mr_realloc")
def mr_realloc(ctx, vm):
    mem = ctx.mem
    p, new_len = ctx.arg(0), ctx.arg(1)
    if not p:
        ctx.ret(mem.malloc(new_len))
        return
    old = mem.heap.used.get(p, 0)
    if new_len <= old:
        ctx.ret(p)
        return
    np_ = mem.malloc(new_len)
    if np_:
        mem.write(np_, mem.read(p, min(old, new_len)))
        mem.free(p)
    ctx.ret(np_)


@api("memcpy")
def memcpy(ctx, vm):
    dst, src, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    if n:
        ctx.mem.write(dst, ctx.mem.read(src, n))
    ctx.ret(dst)


@api("memmove")
def memmove(ctx, vm):
    memcpy(ctx, vm)


@api("memset")
def memset(ctx, vm):
    dst, c, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    ctx.mem.memset(dst, c, n)
    ctx.ret(dst)


@api("memcmp")
def memcmp(ctx, vm):
    a, b, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    x, y = ctx.mem.read(a, n), ctx.mem.read(b, n)
    ctx.ret(0 if x == y else (1 if x > y else -1 & 0xFFFFFFFF))


@api("memchr")
def memchr(ctx, vm):
    p, ch, n = ctx.arg(0), ctx.arg(1) & 0xFF, ctx.arg(2)
    off = ctx.mem.read(p, n).find(bytes([ch]))
    ctx.ret(p + off if off >= 0 else 0)


@api("strlen")
def strlen(ctx, vm):
    raw = ctx.mem.cstr_bytes(ctx.arg(0))
    ctx.ret(len(raw))


@api("strcpy")
def strcpy(ctx, vm):
    dst, src = ctx.arg(0), ctx.arg(1)
    ctx.mem.put_cstr(dst, ctx.mem.cstr(src))
    ctx.ret(dst)


@api("strncpy")
def strncpy(ctx, vm):
    dst, src, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    raw = ctx.mem.cstr_bytes(src)[:n]
    ctx.mem.write(dst, raw + b"\x00" * ((n if n else 1) - len(raw)))
    ctx.ret(dst)


@api("strcat")
def strcat(ctx, vm):
    dst, src = ctx.arg(0), ctx.arg(1)
    base = ctx.mem.cstr_bytes(dst)
    ctx.mem.put_cstr(dst + len(base), ctx.mem.cstr(src))
    ctx.ret(dst)


@api("strncat")
def strncat(ctx, vm):
    strcat(ctx, vm)


@api("strcmp")
def strcmp(ctx, vm):
    a, b = ctx.mem.cstr_bytes(ctx.arg(0)), ctx.mem.cstr_bytes(ctx.arg(1))
    ctx.ret(0 if a == b else (1 if a > b else 0xFFFFFFFF))


@api("strncmp")
def strncmp(ctx, vm):
    n = ctx.arg(2)
    a, b = ctx.mem.cstr_bytes(ctx.arg(0))[:n], ctx.mem.cstr_bytes(ctx.arg(1))[:n]
    ctx.ret(0 if a == b else (1 if a > b else 0xFFFFFFFF))


@api("strcoll")
def strcoll(ctx, vm):
    strcmp(ctx, vm)


@api("strstr")
def strstr(ctx, vm):
    hay_p, needle_p = ctx.arg(0), ctx.arg(1)
    hay = ctx.mem.cstr_bytes(hay_p)
    needle = ctx.mem.cstr_bytes(needle_p)
    idx = hay.find(needle)
    ctx.ret(hay_p + idx if idx >= 0 else 0)


@api("sprintf", "mr_sprintf")
def sprintf(ctx, vm):
    """``sprintf(buf, fmt, ...)`` / ``mr_sprintf`` —— MRP 的字符串格式化。

    返回值按 C 标准给**写入的字节数**（不含结尾 null）。以前返回的是
    Python 字符数，遇到中文文件名就会短一截 —— 应用拿返回值定位下一列
    （比如文件名右边再画一列）时就会错位。

    格式支持：``%d %i %u %o %x %X %f %e %g %c %s %p %%``、长度修饰符
    ``hh h l ll L j z t``、``- + 空格 # 0`` 标志、宽度/精度与 ``*``。
    """
    dst = ctx.arg(0)
    fmt = ctx.mem.cstr(ctx.arg(1))
    specs = _parse_fmt(fmt)

    # AAPCS 变参布局：整数/指针前 4 个走 r0-r3（这里 r2/r3），
    # double 永远走栈（8 字节、8 字节对齐），其余整数走栈（4 字节槽）。
    # %f 的浮点实参不在 r2/r3 里 —— 按寄存器取会读到栈底的垃圾，
    # 屏幕上就会冒出 "f" 这种残留字符。
    reg = 2              # 还能用的整数寄存器
    stk = 0              # 栈上已占用字节

    def _int(_vi: int = 0) -> int:
        nonlocal reg, stk
        if reg < 4:
            v = ctx.arg(reg)
            reg += 1
            return v
        off = (stk + 3) & ~3
        v = ctx.arg(4 + off // 4)
        stk = off + 4
        return v

    def _wide(_vi: int = 0) -> int:
        """64 位整数变参：寄存器放不下，直接走栈（8 字节对齐）。"""
        nonlocal reg, stk
        if reg < 4:
            reg = 4
        off = (stk + 7) & ~7
        v = ctx.qstack(off)
        stk = off + 8
        return v

    def _dbl(_vi: int = 0) -> float:
        """double 变参：AAPCS 规定永远走栈（8 字节对齐）。"""
        nonlocal reg, stk
        if reg < 4:
            reg = 4
        off = (stk + 7) & ~7
        v = ctx.fstack(off)
        stk = off + 8
        return v

    vals = _collect(specs, _int, _wide, _dbl)
    text = _render(specs, vals, ctx.mem)
    try:
        raw = text.encode("gbk")
    except UnicodeEncodeError:
        raw = text.encode("utf-8")
    ctx.mem.write(dst, raw + b"\x00")
    ctx.ret(len(raw))


@api("mr_stop_ex")
def mr_stop_ex(ctx, vm):
    """停止当前应用（对应 mythroad/mythroad.c 的 ``mr_stop_ex``）。

    官方语义：置 ``mr_state=0`` 并通知宿主停止当前应用；``freemem != 0``
    时额外释放屏幕缓冲。我们这边等价于「应用请求退出」——置 ``vm.exited``，
    主循环下一帧统一收尾（停声音 / 关网络 / 关句柄）并退回系统界面。

    这个槽位在官方 mythroad 的 C 库表里是 0x058，此前我们留成了空位 ——
    应用一调就跳到地址 0。
    """
    vm.app.log("[mrp] mr_stop_ex 停止应用")
    vm.exited = True
    ctx.ret(MR_SUCCESS)


@api("atoi")
def atoi(ctx, vm):
    s = ctx.mem.cstr(ctx.arg(0)).strip()
    num = ""
    for ch in s:
        if ch in "-+" and not num:
            num += ch
        elif ch.isdigit():
            num += ch
        else:
            break
    try:
        ctx.ret(int(num) & 0xFFFFFFFF if num not in ("", "-", "+") else 0)
    except ValueError:
        ctx.ret(0)


@api("strtoul")
def strtoul(ctx, vm):
    atoi(ctx, vm)


@api("rand")
def rand_(ctx, vm):
    import random
    ctx.ret(random.getrandbits(31))


@api("srand")
def srand_(ctx, vm):
    import random
    random.seed(ctx.arg(0))


# ==================================================================== 字符串编码 / 数学
@api("c2u")
def c2u(ctx, vm):
    """GBK -> UCS-2 宽字符串（mr_table 槽位 1939）。

    官方 ``mr/mr_gb2312.c`` 的签名是
    ``unicode_char *c2u(const char *cp, int *err, int *size)``：
    返回一块新分配的 ``uint16`` 数组，``*size`` 是**字节数**（含结尾 0）。
    源码在小端机上手工交换过高低字节，因此内存布局是 UTF-16BE。

    旧实现把它当成「写 UTF-8 到 arg1」：arg1 其实是 ``err`` 指针，
    arg2 是 ``size`` 指针，返回值也不该是入参缓冲 —— 全错。
    曲奇启动器没走这个槽位（实测 0 次调用），但其它调用该 API 的 MRP
    会拿到野指针，故按官方语义修正。
    """
    cp, err_p, size_p = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    raw = ctx.mem.cstr_bytes(cp)
    text = raw.decode("gbk", errors="replace")
    try:
        data = text.encode("utf-16-be", errors="replace") + b"\x00\x00"
    except UnicodeEncodeError:          # pragma: no cover - utf-16 不会失败
        data = b"\x00\x00"
    buf = ctx.mem.malloc(len(data))
    if not buf:
        if err_p and ctx.mem.valid(err_p, 4):
            ctx.mem.set_u32(err_p, 0xFFFFFFFF)
        ctx.ret(0)
        return
    ctx.mem.write(buf, data)
    # 官方函数开头 *err = -1，成功时不改回；照抄以便调用方行为一致
    if err_p and ctx.mem.valid(err_p, 4):
        ctx.mem.set_u32(err_p, 0xFFFFFFFF)
    if size_p and ctx.mem.valid(size_p, 4):
        ctx.mem.set_u32(size_p, len(data))
    ctx.ret(buf)


@api("mr_wstrlen")
def mr_wstrlen(ctx, vm):
    n = 0
    p = ctx.arg(0)
    while ctx.mem.valid(p, 2) and ctx.mem.u16(p) != 0:
        n += 1
        p += 2
    ctx.ret(n)


@api("_mr_div")
def mr_div(ctx, vm):
    a, b = ctx.sarg(0), ctx.sarg(1)
    ctx.ret(0 if b == 0 else int(a / b) & 0xFFFFFFFF)


@api("_mr_mod")
def mr_mod(ctx, vm):
    a, b = ctx.sarg(0), ctx.sarg(1)
    ctx.ret(0 if b == 0 else a % b)


@api("mr_updcrc")
def mr_updcrc(ctx, vm):
    ctx.ret(ctx.arg(0))


# ==================================================================== 图形
@api("mr_drawBitmap")
def mr_drawBitmap(ctx, vm):
    """void mr_drawBitmap(uint16* bmp, int16 x, int16 y, uint16 w, uint16 h)"""
    bmp = ctx.arg(0)
    x = ctx.sarg(1)
    y = ctx.sarg(2)
    w = ctx.arg(3)
    h = ctx.arg(4)
    vm.app.gfx.draw_bitmap(bmp, x, y, w, h)


@api("dsm_drawBitmap")
def dsm_drawBitmap(ctx, vm):
    """dsm_require_funcs.drawBitmap —— 离屏全屏缓冲的脏矩形同步。

    与 mr_table 的 ``mr_drawBitmap`` 同名但语义不同！mrpoid 里两条路径分别是：

    * ``mr/mythroad.c::mr_drawBitmap`` -> ``emu_drawBitmap``：紧凑 ``w x h`` 位图，
      源 stride = w（应用自己贴图标/图片时用）；
    * ``dsm.c::mr_drawBitmap`` -> ``emu_bitmapToscreen``：整屏缓冲，
      源 stride = 屏宽，x/y 是矩形左上角（DSM 刷屏时用）。

    之前 dsmfuncs.ALIAS 把两者指向同一个实现，导致 RX 管理器局部刷新时
    把屏顶标题栏贴到列表行上，出现重复标题栏与蓝色斜纹（2026-11-10 修复）。
    """
    bmp = ctx.arg(0)
    x, y = ctx.sarg(1), ctx.sarg(2)
    w, h = ctx.arg(3), ctx.arg(4)
    vm.app.gfx.refresh_rect(bmp, x, y, w, h)


@api("_DrawBitmap", "_DrawBitmapEx")
def draw_bitmap_ex(ctx, vm):
    mr_drawBitmap(ctx, vm)


@api("_DrawPoint")
def draw_point(ctx, vm):
    x, y, color = ctx.sarg(0), ctx.sarg(1), ctx.arg(2)
    vm.app.gfx.fill_rect(x, y, 1, 1, color & 0xFFFF)


@api("DrawRect")
def draw_rect(ctx, vm):
    left, top, right, bottom, color = ctx.sarg(0), ctx.sarg(1), ctx.sarg(2), ctx.sarg(3), ctx.arg(4)
    g = vm.app.gfx
    g.fill_rect(left, top, right - left + 1, 1, color & 0xFFFF)
    g.fill_rect(left, bottom, right - left + 1, 1, color & 0xFFFF)
    g.fill_rect(left, top, 1, bottom - top + 1, color & 0xFFFF)
    g.fill_rect(right, top, 1, bottom - top + 1, color & 0xFFFF)


@api("_BitmapCheck")
def bitmap_check(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_platDrawChar")
def mr_platDrawChar(ctx, vm):
    """让宿主用系统字体画一个字符：真机上由固件完成。"""
    ctx.ret(MR_SUCCESS)


@api("_DrawText", "_DrawTextEx")
def draw_text(ctx, vm):
    ctx.ret(MR_SUCCESS)


# ==================================================================== 时间 / 定时器
@api("mr_timerStart")
def mr_timerStart(ctx, vm):
    vm.app.timer_start(ctx.arg(0))
    ctx.ret(MR_SUCCESS)


@api("mr_timerStop")
def mr_timerStop(ctx, vm):
    vm.app.timer_stop()
    ctx.ret(MR_SUCCESS)


@api("mr_getTime")
def mr_getTime(ctx, vm):
    ctx.ret(int(time.time()) & 0xFFFFFFFF)


@api("mr_getDatetime")
def mr_getDatetime(ctx, vm):
    p = ctx.arg(0)
    if p:
        now = datetime.now()
        mem = ctx.mem
        mem.set_u16(p + 0, now.year)
        mem.write(p + 2, bytes([now.month, now.day, now.hour, now.minute,
                                now.second, (now.weekday() + 1) % 7]))
    ctx.ret(MR_SUCCESS)


@api("mr_sleep")
def mr_sleep(ctx, vm):
    ms = ctx.arg(0)
    if 0 < ms < 2000:
        time.sleep(ms / 1000.0)
    ctx.ret(MR_SUCCESS)


@api("get_uptime_ms")
def get_uptime_ms(ctx, vm):
    ctx.ret(int(vm.app.uptime_ms()))


# ==================================================================== 系统
@api("mr_getScreenInfo")
def mr_getScreenInfo(ctx, vm):
    p = ctx.arg(0)
    if p:
        for i, v in enumerate((SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_BPP, 1, 0)):
            ctx.mem.set_u32(p + i * 4, v)
    ctx.ret(MR_SUCCESS)


@api("mr_getUserInfo")
def mr_getUserInfo(ctx, vm):
    p = ctx.arg(0)
    if p:
        ctx.mem.put_cstr(p + 0, "460000000000000")
        ctx.mem.put_cstr(p + 16, IMEI)
    ctx.ret(MR_SUCCESS)


@api("mr_plat")
def mr_plat(ctx, vm):
    """int32 mr_plat(int32 code, int32 param)

    音频相关的两个 code（SKYENGINE 手册 mr_plat(102)/(103)）：最底层的
    PCM 环形缓冲直写模式 —— 应用自己往内存里写 PCM，驱动只管播。
    """
    code = ctx.arg(0)
    param = ctx.arg(1)
    audio = getattr(vm.app, "audio", None)

    if audio is not None:
        if code == 102:                     # 告知驱动 PCM 写入数据的绝对地址
            audio.ring_notify_write(param, vm.mem)
            ctx.ret(MR_SUCCESS)
            return
        if code == 103:                     # 取已播放掉的数据的绝对地址
            ctx.ret(audio.ring_played_ptr())
            return
        if code == 1302:                    # 设置播放音量（sky 音量等级）
            level = max(0, min(15, param))
            audio.volume = max(0.0, min(1.0, level / 15.0))
            ctx.ret(MR_SUCCESS)
            return

    if code == 0x1000:      # MR_PLAT_VALUE
        ctx.ret(0x1000)
    else:
        ctx.ret(MR_SUCCESS)


@api("mr_platEx")
def mr_platEx(ctx, vm):
    """int32 mr_platEx(int32 code, uint8* input, int32 input_len,
                       uint8** output, int32* output_len, MR_PLAT_EX_CB* cb)

    音频族 201x-216x / 222x-225x 走 audio.media（流媒体播放器），
    其余 code 交给原来的兜底逻辑。
    """
    code = ctx.arg(0)
    input_addr = ctx.arg(1)
    input_len = ctx.arg(2)
    output_ptr = ctx.arg(3)
    output_len_ptr = ctx.arg(4)
    # ctx.arg(5) 是 MR_PLAT_EX_CB*，我们同步完成操作，不回异步回调

    audio = getattr(vm.app, "audio", None)
    if audio is not None:
        result = audio.media.handle(
            code, vm.mem, input_addr, input_len, output_ptr, output_len_ptr,
            vm.app.fs,
        )
        if result is not None:
            ctx.ret(result)
            return

    if code == 1204:                    # MR_SWITCHPATH / dsmSwitchPath
        ctx.ret(_dsm_switch_path(ctx, vm, input_addr, input_len,
                                 output_ptr, output_len_ptr))
        return

    vm.app.log(f"[mr_platEx] code=0x{code:X}")
    ctx.ret(MR_SUCCESS)


def _dsm_switch_path(ctx, vm, iaddr: int, ilen: int,
                     optr: int, olenptr: int) -> int:
    """复刻 mrpoid/dsm.c 的 ``dsmSwitchPath()``（mr_plat.h: MR_SWITCHPATH 1204）。

    ``output`` 是 ``uint8**``、``output_len`` 是 ``int32*``——两者都要写回，
    否则应用拿到野指针，下一次 sprintf("%s") 就会解引用 NULL 崩掉。
    分支语义：Y 查当前绝对路径 / Z 回启动目录 / X 隐藏根 / A、B 隐藏盘 / C 用户盘。
    """
    mem, fs = ctx.mem, vm.app.fs
    if not iaddr:
        return MR_FAILED
    raw = _read_blob(vm, iaddr, min(max(0, ilen), 256))
    arg = raw.split(b"\x00")[0].decode("gbk", "replace")
    if ilen <= 0:
        fs.work_path = ""
    elif arg[:1].upper() == "Y":
        text = "c:/" + (fs.work_path or "")
        ptr = vm.app.scratch_str(text, "dsm_path", 256)
        if optr and mem.valid(optr, 4):
            mem.set_u32(optr, ptr)
        if olenptr and mem.valid(olenptr, 4):
            mem.set_u32(olenptr, len(text.encode("gbk", "replace")))
    elif arg[:1].upper() == "Z":
        fs.work_path = "mythroad/"
    elif arg[:1].upper() == "X":
        fs.work_path = "mythroad/disk/x/"
    elif arg[:1].upper() in ("A", "B"):
        drive = arg[0].lower()
        sub = arg[3:] if len(arg) > 3 else ""
        fs.work_path = f"mythroad/disk/{drive}/" + sub
    elif len(arg) > 3:
        rel = arg[3:].replace("\\", "/").lstrip("/")
        if rel.lower().startswith("mythroad/"):
            rel = rel[len("mythroad/"):]
        fs.work_path = (rel.rstrip("/") + "/") if rel else ""
    else:
        fs.work_path = ""
    fs.work_path = fs.work_path.replace("\\", "/")
    vm.app.log(f"[platEx 1204] {arg!r} -> work_path={fs.work_path!r}")
    return MR_SUCCESS


@api("mr_ferrno")
def mr_ferrno(ctx, vm):
    ctx.ret(0)


@api("mr_exit")
def mr_exit(ctx, vm):
    vm.app.log("[mrp] 应用请求退出")
    vm.exited = True
    ctx.ret(MR_SUCCESS)


@api("mr_startShake")
def mr_startShake(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_stopShake")
def mr_stopShake(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_playSound")
def mr_playSound(ctx, vm):
    """int32 mr_playSound(int type, const void *data, uint32 dataLen, int32 loop)

    与 mrporting.h 一致：data 是**模拟内存里的指针**，不是文件名 —— 应用
    总是先把音频读进内存（mr_open+read，或直接嵌在代码段）再传指针过来。

    type 见 MR_SOUND_TYPE：MIDI/WAV/MP3/PCM/M4A/AMR/AMR_WB。其中 PCM 是
    分段流式推送，每次只给几十毫秒，由 audio.stream 攒块拼接。
    """
    stype = ctx.arg(0)
    addr = ctx.arg(1)
    length = ctx.arg(2)
    loop = ctx.arg(3) != 0

    audio = getattr(vm.app, "audio", None)
    if audio is None:
        ctx.ret(MR_SUCCESS)
        return

    data = _read_blob(vm, addr, length)
    if not data and addr and length == 0:
        # 极少数老实现会传 (type, "xxx.mid", 0, loop)：把 data 当路径。
        # 只在长度明确为 0 时才走这条路，避免把真实音频数据误判成字符串。
        name = vm.mem.cstr(addr, 260)
        if name and name.lower().endswith((".mid", ".midi", ".imy", ".wav", ".mp3")):
            try:
                data = vm.app.fs.read_all(name)
                vm.app.log(f"[audio] 以文件名方式读取 {name} ({len(data)}B)")
            except Exception:
                data = b""

    ctx.ret(audio.play(stype, data, loop))


@api("mr_stopSound")
def mr_stopSound(ctx, vm):
    """int32 mr_stopSound(int type)"""
    audio = getattr(vm.app, "audio", None)
    if audio is not None:
        audio.stop(ctx.arg(0))
    ctx.ret(MR_SUCCESS)


@api("mr_registerAPP")
def mr_registerAPP(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_entry")
def mr_entry(ctx, vm):
    ctx.ret(MR_SUCCESS)


# ==================================================================== 文件
@api("mr_open")
def mr_open(ctx, vm):
    name = _s(ctx, 0)
    mode = ctx.arg(1)
    fh = vm.app.fs.open(name, mode)
    vm.app.log(f"[fs] open {name!r} mode=0x{mode:X} -> {fh}")
    ctx.ret(fh)


@api("mr_close")
def mr_close(ctx, vm):
    ctx.ret(vm.app.fs.close(ctx.arg(0)))


@api("mr_read")
def mr_read(ctx, vm):
    f, p, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    data = vm.app.fs.read(f, n)
    if data:
        ctx.mem.write(p, data)
    ctx.ret(len(data))


@api("mr_write")
def mr_write(ctx, vm):
    f, p, n = ctx.arg(0), ctx.arg(1), ctx.arg(2)
    ctx.ret(vm.app.fs.write(f, ctx.mem.read(p, n)))


@api("mr_seek")
def mr_seek(ctx, vm):
    ctx.ret(vm.app.fs.seek(ctx.arg(0), ctx.sarg(1), ctx.arg(2)))


@api("mr_getLen")
def mr_getLen(ctx, vm):
    ctx.ret(vm.app.fs.get_len(_s(ctx, 0)))


@api("mr_info")
def mr_info(ctx, vm):
    ctx.ret(vm.app.fs.info(_s(ctx, 0)))


@api("mr_remove")
def mr_remove(ctx, vm):
    ctx.ret(vm.app.fs.remove(_s(ctx, 0)))


@api("mr_rename")
def mr_rename(ctx, vm):
    ctx.ret(vm.app.fs.rename(_s(ctx, 0), _s(ctx, 1)))


@api("mr_mkDir")
def mr_mkDir(ctx, vm):
    ctx.ret(vm.app.fs.mkdir(_s(ctx, 0)))


@api("mr_rmDir")
def mr_rmDir(ctx, vm):
    ctx.ret(vm.app.fs.rmdir(_s(ctx, 0)))


@api("_mr_readFile")
def mr_readFile(ctx, vm):
    """int32 _mr_readFile(const char* name, uint8* buf, int32 len)"""
    name, buf, length = _s(ctx, 0), ctx.arg(1), ctx.arg(2)
    data = vm.app.fs.read_all(name)
    if data is None:
        ctx.ret(MR_FAILED)
        return
    data = data[:length]
    ctx.mem.write(buf, data)
    ctx.ret(len(data))


@api("mr_findStart")
def mr_findStart(ctx, vm):
    """int32 mr_findStart(const char* name, char* buf, uint32 len)"""
    name, buf = _s(ctx, 0), ctx.arg(1)
    h, first = vm.app.fs.find_start(name, ctx.arg(2))
    if h == MR_FAILED:
        ctx.ret(MR_FAILED)
        return
    ctx.mem.put_cstr(buf, first or "")
    ctx.ret(h)


@api("mr_findGetNext")
def mr_findGetNext(ctx, vm):
    h, buf = ctx.arg(0), ctx.arg(1)
    nxt = vm.app.fs.find_next(h)
    if nxt is None:
        ctx.ret(MR_NO_EXIST)
        return
    ctx.mem.put_cstr(buf, nxt)
    ctx.ret(MR_SUCCESS)


@api("mr_findStop")
def mr_findStop(ctx, vm):
    ctx.ret(vm.app.fs.find_stop(ctx.arg(0)))


# ==================================================================== 网络
#
# 两张表里同名函数的参数并不一样，别混用：
#   mr_table        : mr_initNetwork(cb, mode) / mr_getHostByName(name, cb)
#   dsm_require_funcs: initNetwork(cb, mode, userData) / getHostByName(name, cb, userData)
# 见 vmrp/dl_dsm.h 的 DSM_REQUIRE_FUNCS 与 mr/mrporting.h。
def _net(ctx, vm):
    return getattr(vm.app, "net", None)


def _net_ret(ctx, value) -> None:
    ctx.ret(MR_FAILED if value is None else value)


@api("mr_initNetwork")
def mr_initNetwork(ctx, vm):
    """MRP 标准版：int32 mr_initNetwork(MR_INIT_NETWORK_CB cb, const char* mode)"""
    net = _net(ctx, vm)
    _net_ret(ctx, net.init_network(ctx.arg(0), _s(ctx, 1), 0) if net else None)


@api("dsm_initNetwork")
def dsm_initNetwork(ctx, vm):
    """ext 版：initNetwork(NETWORK_CB cb, const char* mode, void* userData)"""
    net = _net(ctx, vm)
    _net_ret(ctx, net.init_network(ctx.arg(0), _s(ctx, 1), ctx.arg(2))
             if net else None)


@api("mr_getHostByName")
def mr_getHostByName(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.get_host_by_name(_s(ctx, 0), ctx.arg(1), 0)
             if net else None)


@api("dsm_getHostByName")
def dsm_getHostByName(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.get_host_by_name(_s(ctx, 0), ctx.arg(1), ctx.arg(2))
             if net else None)


@api("mr_closeNetwork")
def mr_closeNetwork(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.close_network() if net else None)


@api("mr_socket")
def mr_socket(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.socket(ctx.arg(0), ctx.arg(1)) if net else None)


@api("mr_connect")
def mr_connect(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.connect(ctx.arg(0), ctx.arg(1), ctx.arg(2), ctx.arg(3))
             if net else None)


@api("mr_getSocketState")
def mr_getSocketState(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.get_socket_state(ctx.arg(0)) if net else None)


@api("mr_closeSocket")
def mr_closeSocket(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.close_socket(ctx.arg(0)) if net else None)


@api("mr_recv")
def mr_recv(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.recv(ctx.arg(0), ctx.arg(1), ctx.arg(2)) if net else None)


@api("mr_send")
def mr_send(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.send(ctx.arg(0), ctx.arg(1), ctx.arg(2)) if net else None)


@api("mr_recvfrom")
def mr_recvfrom(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.recvfrom(ctx.arg(0), ctx.arg(1), ctx.arg(2),
                               ctx.arg(3), ctx.arg(4)) if net else None)


@api("mr_sendto")
def mr_sendto(ctx, vm):
    net = _net(ctx, vm)
    _net_ret(ctx, net.sendto(ctx.arg(0), ctx.arg(1), ctx.arg(2),
                             ctx.arg(3), ctx.arg(4)) if net else None)


# ==================================================================== 弹窗类（占位句柄）
_dialog_seq = [1]


@api("mr_dialogCreate")
def mr_dialogCreate(ctx, vm):
    _dialog_seq[0] += 1
    ctx.ret(_dialog_seq[0])


@api("mr_dialogRelease")
def mr_dialogRelease(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_dialogRefresh")
def mr_dialogRefresh(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_textCreate")
def mr_textCreate(ctx, vm):
    _dialog_seq[0] += 1
    ctx.ret(_dialog_seq[0])


@api("mr_textRelease")
def mr_textRelease(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_textRefresh")
def mr_textRefresh(ctx, vm):
    ctx.ret(MR_SUCCESS)


_edit_texts: dict[int, str] = {}


@api("mr_editCreate")
def mr_editCreate(ctx, vm):
    _dialog_seq[0] += 1
    _edit_texts[_dialog_seq[0]] = ""
    ctx.ret(_dialog_seq[0])


@api("mr_editRelease")
def mr_editRelease(ctx, vm):
    _edit_texts.pop(ctx.arg(0), None)
    ctx.ret(MR_SUCCESS)


@api("mr_editGetText")
def mr_editGetText(ctx, vm):
    h = ctx.arg(0)
    text = vm.app.take_edit_text(h) or _edit_texts.get(h, "")
    p = vm.app.scratch_str(text)
    ctx.ret(p)


# ==================================================================== 菜单/窗口（占位）
for _n in ("mr_menuCreate", "mr_menuSetItem", "mr_menuShow", "mr_menuRelease",
           "mr_menuRefresh", "mr_winCreate", "mr_winRelease", "mr_sendSms",
           "mr_call", "mr_getNetworkID", "mr_connectWAP", "mr_unzip"):
    IMPL[_n] = lambda ctx, vm: ctx.ret(MR_SUCCESS)


# ==================================================================== md5（占位）
@api("mr_md5_init")
def mr_md5_init(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_md5_append")
def mr_md5_append(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("mr_md5_finish")
def mr_md5_finish(ctx, vm):
    p = ctx.arg(0)
    if p:
        ctx.mem.write(p, b"\x00" * 16)
    ctx.ret(MR_SUCCESS)


# ==================================================================== dsm 表专用
@api("test")
def dsm_test(ctx, vm):
    ctx.ret(MR_SUCCESS)


@api("log")
def dsm_log(ctx, vm):
    vm.app.log(f"[arm] {_s(ctx, 0)}")
    ctx.ret(MR_SUCCESS)


@api("exit")
def dsm_exit(ctx, vm):
    vm.app.log("[arm] exit()")
    vm.exited = True
    ctx.ret(MR_SUCCESS)


@api("mem_get")
def dsm_mem_get(ctx, vm):
    """int32 mem_get(char** mem_base, uint32* mem_len)"""
    base_p, len_p = ctx.arg(0), ctx.arg(1)
    size = 4 * 1024 * 1024
    block = ctx.mem.malloc(size)
    if not block:
        ctx.ret(MR_FAILED)
        return
    ctx.mem.set_u32(base_p, block)
    ctx.mem.set_u32(len_p, size)
    vm.app.log(f"[dsm] mem_get -> 0x{block:X} ({size // 1024}KB)")
    ctx.ret(MR_SUCCESS)


@api("mem_free")
def dsm_mem_free(ctx, vm):
    ctx.mem.free(ctx.arg(0))
    ctx.ret(MR_SUCCESS)


@api("opendir")
def dsm_opendir(ctx, vm):
    ctx.ret(vm.app.fs.opendir(_s(ctx, 0)))


@api("readdir")
def dsm_readdir(ctx, vm):
    name = vm.app.fs.readdir(ctx.arg(0))
    if name is None:
        ctx.ret(0)
        return
    ctx.ret(vm.app.scratch_str(name, slot="readdir", size=128))


@api("closedir")
def dsm_closedir(ctx, vm):
    ctx.ret(vm.app.fs.closedir(ctx.arg(0)))
