"""ARM <-> Python 桥接层。

vmrp 的原始机制（bridge.c）：

1. 在 MRP 内存里分配一块"函数表"，每项 4 字节，偏移即 API 编号。
2. 每个槽位里写入 **它自己的地址**；ARM 侧 ldr 出这个地址后 blx 过去，
   PC 落在槽位上，被 UC_HOOK_CODE 拦下。
3. 拦截回调直接用 R0-R3/栈 当参数、R0 当返回值，然后把 PC 改成 LR 模拟 ret。

本质上是用"可执行内存地址"当 syscall 号。这里原样复刻，未使用任何
Python 侧的 ABI 假设 —— 所以 cfunction.ext 不需要做任何修改。
"""

from __future__ import annotations

import struct
import traceback
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

from .consts import MR_FAILED

if TYPE_CHECKING:  # pragma: no cover
    from .memory import MrpMemory
    from .vm import Vm

ARG_REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


@dataclass
class BridgeFunc:
    """一个 API 槽位。fn=None 表示尚未实现（返回 MR_FAILED 而不崩）。"""
    pos: int
    name: str
    fn: Callable[["ArmCall", "Vm"], None] | None = None
    init: Callable[["Vm", int], None] | None = None
    note: str = ""


class ArmCall:
    """一次桥接调用的上下文：按 ARM AAPCS 读参数、写返回值。"""

    __slots__ = ("uc", "mem", "_ret")

    def __init__(self, uc, mem: "MrpMemory") -> None:
        self.uc = uc
        self.mem = mem
        self._ret: int | None = None

    # -- 参数 -------------------------------------------------------
    def arg(self, n: int) -> int:
        if n < 4:
            return self.uc.reg_read(ARG_REGS[n])
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        return struct.unpack("<I", self.uc.mem_read(sp + (n - 4) * 4, 4))[0]

    def qarg(self, n: int) -> int:
        """第 n 个（1-based）参数按 64 位整数取。

        AAPCS：64 位变参一律走栈，占 8 字节且 8 字节对齐；寄存器区放不下。
        """
        if n < 4:
            return self.arg(n) & 0xFFFFFFFFFFFFFFFF
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        off = ((n - 4) * 4 + 7) & ~7
        return struct.unpack("<q", self.uc.mem_read(sp + off, 8))[0]

    def farg(self, n: int) -> float:
        """第 n 个（1-based）参数按 double 取（%f/%e/%g）。

        AAPCS：浮点变参走栈，8 字节、8 字节对齐。
        """
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        off = ((n - 4) * 4 + 7) & ~7
        return struct.unpack("<d", self.uc.mem_read(sp + off, 8))[0]

    # -- 栈上按字节偏移取（AAPCS 变参布局要用）--------------------------
    def stack_read(self, off: int, size: int) -> bytes:
        """从栈底（SP）起按字节偏移读 —— AAPCS 变参的真实来源。"""
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        return self.uc.mem_read(sp + off, size)

    def fstack(self, off: int) -> float:
        """栈上 offset 处的 double。"""
        return struct.unpack("<d", self.stack_read(off, 8))[0]

    def qstack(self, off: int) -> int:
        """栈上 offset 处的 64 位整数。"""
        return struct.unpack("<q", self.stack_read(off, 8))[0]

    def sarg(self, n: int) -> int:
        v = self.arg(n)
        return v - 0x100000000 if v & 0x80000000 else v

    def args(self, count: int) -> list[int]:
        return [self.arg(i) for i in range(count)]

    def str_arg(self, n: int) -> str:
        return self.mem.cstr(self.arg(n))

    # -- 返回值 -----------------------------------------------------
    def ret(self, value: int) -> None:
        self._ret = value & 0xFFFFFFFF

    def flush(self) -> None:
        if self._ret is not None:
            self.uc.reg_write(UC_ARM_REG_R0, self._ret)


class BridgeTable:
    """一张函数表（mr_table 或 dsm_require_funcs）。"""

    def __init__(self, name: str, funcs: list[BridgeFunc], size: int | None = None) -> None:
        self.name = name
        self.funcs = funcs
        self.size = size or (max(f.pos for f in funcs) + 8)
        self.base = 0
        self.dispatch: dict[int, BridgeFunc] = {}
        self.calls: dict[str, int] = {}
        self.verbose = False
        self.verbose_every = 60
        self._vm: "Vm | None" = None

    # -------------------------------------------------- 安装
    def install(self, vm: "Vm") -> int:
        mem = vm.mem
        self.base = mem.malloc(self.size)
        if not self.base:
            raise RuntimeError(f"{self.name}: 无法为函数表分配 {self.size} 字节")
        mem.memset(self.base, 0, self.size)

        for f in self.funcs:
            addr = self.base + f.pos
            if f.init is not None:
                f.init(vm, addr)
            else:
                # 关键：槽位里写入自身地址，ARM 侧 blx 过来才会被 hook 住
                mem.set_u32(addr, addr)
            self.dispatch[addr] = f

        self._vm = vm
        vm.uc.hook_add(UC_HOOK_CODE, self._hook, None, self.base, self.base + self.size)
        return self.base

    # -------------------------------------------------- 拦截
    def _hook(self, uc, address: int, size: int, user_data) -> None:
        f = self.dispatch.get(address)
        if f is None:
            return

        vm = self._vm
        call = ArmCall(uc, vm.mem)

        if f.fn is None:
            # 未实现的 API 不中断程序，返回 MR_FAILED 让业务自己兜
            if self.verbose:
                print(f"[bridge] 未实现 {self.name}.{f.name} (0x{f.pos:X}) -> MR_FAILED")
            call.ret(MR_FAILED)
        else:
            self.calls[f.name] = self.calls.get(f.name, 0) + 1
            if self.verbose and self.calls[f.name] % self.verbose_every == 1:
                print(f"[bridge] {self.name}.{f.name}")
            try:
                f.fn(call, vm)
            except Exception:
                print(f"[bridge] ERROR in {self.name}.{f.name}:")
                traceback.print_exc()
                call.ret(MR_FAILED)

        call.flush()
        # 模拟 ret：把 PC 指回 LR
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
