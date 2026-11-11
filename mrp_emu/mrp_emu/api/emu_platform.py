"""自编译 mythroad VM 特有的平台接口实现。

`api/impl.py` 里已有的 51 个 mr_* 实现直接复用（见 `mythroad_port.py`），
这里补的是**老架构里用不到、但 mythroad 内部必需**的那批：

* ``mr_mem_get`` / ``mr_mem_get_ex`` / ``mr_mem_free`` —— mythroad 堆的底座
  （``_mr_mem_init`` 靠它拿到一整块内存，然后自己实现 mr_malloc/first-fit）
* ``mr_printf`` —— 变参调试输出
* ``mr_getCharBitmap`` / ``mr_platDrawCharReal`` / ``mr_drawText`` —— 字模与文本
* ``mr_getNetworkID`` / ``mr_sendSms`` / ``mr_call`` / ``mr_connectWAP`` —— 电话与网络
* 异步文件、系统菜单/对话框/编辑框 —— 真机 UI，这边用自绘 UI，统一回
  ``MR_FAILED``（真机上这些也是平台自己弹的）

签名与 impl.py 保持一致：``fn(ctx, vm)``。
"""

from __future__ import annotations

import time
from pathlib import Path

from ..consts import (
    IMSI,
    MR_FAILED,
    MR_SUCCESS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

# ==================================================================== 内存

# 给 mythroad 的那块堆：斯凯插件机制会把它整个 dump 到 plugins/dump%d，
# 退出插件后按**同一绝对地址**读回恢复，所以地址必须恒定。
VM_MEM_SIZE = 2 * 1024 * 1024


def mr_mem_get(ctx, vm):
    """给 mythroad 一整块可用的堆。

    官方语义（mythroad.c `_mr_mem_init`）：把 ``*mem_base`` / ``*mem_len``
    填好，返回 MR_SUCCESS。mythroad 随后在这块内存上自己实现
    ``mr_malloc``/``mr_free``/``mr_realloc`` 的 first-fit 分配器。
    """
    base_ptr = ctx.arg(0)
    len_ptr = ctx.arg(1)
    size = getattr(vm, "vm_mem_request", VM_MEM_SIZE)
    addr = vm.alloc_vm_memory(size)
    if not addr:
        ctx.ret(MR_FAILED)
        return
    ctx.mem.set_u32(base_ptr, addr)
    ctx.mem.set_u32(len_ptr, size)
    ctx.ret(MR_SUCCESS)


def mr_mem_get_ex(ctx, vm):
    """带 ram 参数的版本（斯凯用它区分内部 RAM / 扩展 RAM）。"""
    base_ptr = ctx.arg(1)
    len_ptr = ctx.arg(2)
    size = getattr(vm, "vm_mem_request", VM_MEM_SIZE)
    addr = vm.alloc_vm_memory(size)
    if not addr:
        ctx.ret(MR_FAILED)
        return
    ctx.mem.set_u32(base_ptr, addr)
    ctx.mem.set_u32(len_ptr, size)
    ctx.ret(MR_SUCCESS)


def mr_mem_free(ctx, vm):
    """释放 VM 内存块（官方 mr_mem_free）。

    只清「本轮已释放」标记：预留区留着下一轮复用 —— **地址必须恒定**，
    否则斯凯的 dump/恢复机制读回来的指针全是野的。
    """
    vm.release_vm_memory()
    ctx.ret(MR_SUCCESS)


# ==================================================================== 调试

def mr_printf(ctx, vm):
    """变参调试输出。

    AAPCS：第 5 个及以后的参数走栈。变参里的 double 要按 8 字节对齐，
    这里只处理 %s / %d / %x / %c 之类，整数参数一律按 4 字节取。
    """
    fmt = ctx.str_arg(0)
    if not fmt:
        ctx.ret(0)
        return

    out: list[str] = []
    ai = 1                      # 下一个整型参数序号（1-based）
    fi = 4                      # 下一个浮点参数序号（浮点单独占栈槽）
    i = 0
    while i < len(fmt):
        c = fmt[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= len(fmt):
            break
        spec = fmt[i]
        i += 1
        if spec == "%":
            out.append("%")
            continue
        # 跳过宽度/精度修饰
        while i < len(fmt) and fmt[i] in "0123456789.-+ #lL":
            i += 1
        if i >= len(fmt):
            break
        spec = fmt[i]
        i += 1
        if spec in "s":
            out.append(ctx.str_arg(ai))
            ai += 1
        elif spec in "diu":
            out.append(str(ctx.sarg(ai)))
            ai += 1
        elif spec in "xXo":
            out.append(format(ctx.arg(ai) & 0xFFFFFFFF, "x"))
            ai += 1
        elif spec == "c":
            out.append(chr(ctx.arg(ai) & 0xFF))
            ai += 1
        elif spec in "fFeEgG":
            out.append(f"{ctx.farg(fi):.6f}")
            fi += 1
        elif spec == "p":
            out.append(f"0x{ctx.arg(ai) & 0xFFFFFFFF:X}")
            ai += 1
        else:
            out.append("%" + spec)
    text = "".join(out)
    try:
        vm.log(f"[mvm] {text}")
    except Exception:           # noqa: BLE001
        pass
    ctx.ret(len(text))


# ==================================================================== 电话 / 网络

def mr_getNetworkID(ctx, vm):
    """取 IMSI（真机返回 SIM 卡号）。"""
    raw = IMSI.encode("gbk", "replace") + b"\x00"
    buf = vm.heap.malloc(len(raw))
    ctx.mem.write(buf, raw)
    ctx.ret(buf)


def mr_sendSms(ctx, vm):
    """发短信 —— 本模拟器不发，返回 MR_FAILED。"""
    ctx.ret(MR_FAILED)


def mr_call(ctx, vm):
    """拨号 —— 本模拟器不拨，返回 MR_IGNORE。"""
    ctx.ret(1)


def mr_connectWAP(ctx, vm):
    """连接 WAP 网关。

    真正的连接由 app.net 负责（斯凯走 ``proxy.51mrp.com``），
    这里只把 WAP 参数透传给网络层并返回成功。
    """
    wap = ctx.str_arg(0)
    net = getattr(getattr(vm, "app", None), "net", None)
    if net is not None:
        try:
            net.set_wap(wap)
        except Exception:       # noqa: BLE001
            pass
    ctx.ret(MR_SUCCESS)


# ==================================================================== 异步文件

def mr_asyn_read(ctx, vm):
    """异步读 —— 不支持，返回 MR_FAILED（真机上是平台线程完成的）。"""
    ctx.ret(MR_FAILED)


def mr_asyn_write(ctx, vm):
    ctx.ret(MR_FAILED)


# ==================================================================== 系统 UI
# 真机上菜单/对话框/编辑框由平台自己弹。这里是自绘 UI，统一回失败。

def _unsupported(ctx, vm):
    ctx.ret(MR_FAILED)


mr_menuCreate = _unsupported
mr_menuSetItem = _unsupported
mr_menuShow = _unsupported
mr_menuSetFocus = _unsupported
mr_menuRelease = _unsupported
mr_menuRefresh = _unsupported
mr_dialogCreate = _unsupported
mr_dialogRelease = _unsupported
mr_dialogRefresh = _unsupported
mr_textCreate = _unsupported
mr_textRelease = _unsupported
mr_textRefresh = _unsupported
mr_editCreate = _unsupported
mr_editRelease = _unsupported
mr_winCreate = _unsupported
mr_winRelease = _unsupported


def mr_editGetText(ctx, vm):
    ctx.ret(0)


# ==================================================================== 保存 MRP

def mr_save_mrp(ctx, vm):
    """保存 MRP 包 —— 不支持。"""
    ctx.ret(MR_FAILED)


def mr_save_mrp_with_handle(ctx, vm):
    ctx.ret(MR_FAILED)
