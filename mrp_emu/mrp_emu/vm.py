"""Unicorn ARM 引擎封装 —— 对应 vmrp 的 vmrp.c。

关键点：Python 的 bytearray 与 unicorn 通过 mem_map_ptr 共享同一块物理内存，
两边看到的是同一份数据，无需同步。
"""

from __future__ import annotations

import ctypes
import struct
import time
from pathlib import Path
from typing import Callable

from unicorn import (
    UC_ARCH_ARM,
    UC_HOOK_CODE,
    UC_HOOK_MEM_INVALID,
    UC_MODE_ARM,
    UC_PROT_ALL,
    Uc,
    UcError,
)
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R9,
    UC_ARM_REG_SP,
)

from .consts import (
    CODE_ADDRESS,
    DSM_INIT,
    MR_EVENT,
    MR_FAILED,
    MR_START_DSM,
    MR_SUCCESS,
    MR_TIMER,
    STACK_ADDRESS,
    STACK_SIZE,
    START_ADDRESS,
    TOTAL_MEMORY,
    VMRP_VER,
)
from .memory import MrpMemory

STOP_ADDRESS = CODE_ADDRESS          # 所有 runCode 的停止地址

# 真 MTK 机器从 0 地址往上直到代码段起点都是固件 ROM / 低地址 RAM，可读可写；
# 老 MRP 拿到 NULL 或野指针时会读到 0 并当成空数据，不会终止。
#   * RX 管理器：sprintf("%s") 拿到 NULL 字符串，读 0 页 —— 需要 0x0..0x10000。
#   * 曲奇启动器：透明位图 blit 的源指针是 0x15858（低地址垃圾值），
#     在 0x87A24 执行 ldrh 读 2 字节 —— 只映射 0 页仍会 UcError 终止整个 VM。
# 所以整段 0x0..CODE_ADDRESS 都按真机语义铺成零填充可读区。
# 注意：这会容忍一部分真正的野指针解引用（读到 0 而非崩溃），是复古兼容取舍。
ZERO_PAGE_SIZE = 0x10000                 # 最小零页，保留给旧调用方
LOW_MEMORY_SIZE = CODE_ADDRESS           # 0x80000，覆盖全部低地址 ROM/RAM


class Vm:
    def __init__(self, log: Callable[[str], None] = print,
                 zero_page: bool = True) -> None:
        self.log = log
        self.mem = MrpMemory()
        self.app = None
        self.zero_page = zero_page
        self.invalid_accesses: list[tuple[int, int, int]] = []

        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self._map_memory()
        self._install_mem_guard()

        # 满递减栈
        self.uc.reg_write(UC_ARM_REG_SP, STACK_ADDRESS + STACK_SIZE)

        # bridge.c 里的全局槽位
        self.mr_table = 0
        self.dsm_funcs = 0
        self.mr_c_function_P = 0
        self.mr_extHelper_addr = 0
        self.mr_c_event = 0
        self.dsm_event = 0
        self.start_dsm_param = 0

        self.tables: dict[str, object] = {}
        self.exited = False
        self.exit_code = 0
        self.instr_count = 0
        self._codehook = None

        # ---- MRP 应用栈（真机 mythroad 的 RunFile / Exit 机制）----
        #
        # 真机（mythroad.c）里插件调用是一个**重启链**：
        #   RunFile(pack, entry, param)  -> MRF_RunFile 设 pack_filename /
        #       start_filename，mr_state = MR_STATE_RESTART
        #   下一帧 mr_timer() 命中 RESTART 分支 -> mr_stop() + _mr_intra_start()
        #   插件里 Exit() -> MRF_Exit 发现 old_pack_filename 非空 ->
        #       恢复上级包名，再次 RESTART -> 回到上级 MRP 现场
        #
        # 我们把「当前跑的是哪个 MRP」显式记在栈上：
        #   push：上级 MRP 调插件时压入（保留上级现场）
        #   pop ：插件返回时弹出并恢复上级
        # 栈非空 => 插件返回应回到上级，而不是退回系统桌面。
        self.app_stack: list[dict] = []
        # mr_stop_ex 置位：当前 MRP 实例已停止，等主循环决定重启还是退出。
        # 官方 mr_stop_ex 只把 mr_state 置 IDLE、停定时器、释放内存，
        # **不结束整个应用**（见 mythroad.c:7266），它只是重启链的一环。
        self.instance_stopped = False
        # 由 mr_mem_get 发出的 VM 内存块（对应官方的 Origin_LG_mem_base）。
        # 重启链要求「先 free 后 alloc」拿到同一地址，否则 dump/restore
        # 恢复出来的指针全是野的（斯凯插件机制把整个运行内存 dump 到
        # plugins/dump%d，退出插件后按同一地址读回恢复）。
        self.vm_mem_block: int | None = None
        self.vm_mem_len: int = 0
        # VM 内存块的**专用保留区**：从堆里单独划一块固定地址，
        # 每轮 mem_get 都从这里发。理由见 alloc_vm_memory()。
        self.vm_mem_reserved: int | None = None

    # ------------------------------------------------------------ 应用栈
    def push_app(self, info: dict) -> None:
        """压入上级 MRP 现场（插件调用时用）。"""
        self.app_stack.append(info)

    def pop_app(self) -> dict | None:
        """弹出上级 MRP 现场（插件返回时用）。"""
        if not self.app_stack:
            return None
        return self.app_stack.pop()

    # ------------------------------------------------------------ 内存
    def alloc_vm_memory(self, size: int) -> int:
        """给 ext 发一块 VM 内存，**地址跨重启恒定**。

        斯凯的插件机制把整个 MRP 运行内存 dump 到 ``plugins/dump%d``，
        退出插件后按**同一地址**读回恢复（dump 记录的是绝对地址）。
        如果每轮 ``mr_mem_get`` 拿到不同地址，恢复出来的指针全是野的 ——
        实测崩溃点就是 ``Invalid memory read @0x1C6826F4``（远超 8MB
        模拟空间，是典型野指针）。

        用普通 first-fit 堆做不到地址恒定：碎片一多，同尺寸的两次
        分配就落到不同地址（实测 0x280000 vs 0x299000）。
        所以这里给 VM 内存**单独预留一块固定区域**，每轮都从它发，
        且这块区域不参与普通 mr_malloc 的竞争。
        """
        if self.vm_mem_reserved is None:
            block = self.mem.heap.reserve(size)
            if not block:
                # 预留失败（堆太小）退回普通分配
                return self.mem.malloc(size)
            self.vm_mem_reserved = block
            self.vm_mem_len = size
            self.log(f"[vm] 预留 VM 内存区 0x{block:X} ({size // 1024}KB)")
        self.vm_mem_block = self.vm_mem_reserved
        return self.vm_mem_block

    def release_vm_memory(self) -> bool:
        """``mr_stop_ex(freemem!=0)`` 时释放 VM 内存块（官方 mr_mem_free）。

        官方 mythroad.c:7364 在 ``mr_stop_ex(freemem!=0)`` 里调
        ``mr_mem_free(Origin_LG_mem_base, Origin_LG_mem_len)``。
        我们这边必须做同样的事：否则 6MB 堆被第一轮 4MB 占住后，
        第二轮 ``mr_mem_get`` 直接失败（返回 0），插件根本起不来；
        而且 dump 出来的内存内容也无处安放。

        VM 内存走的是**专用预留区**，这里只把「本轮已释放」标记掉，
        预留区本身留着下一轮复用 —— 地址必须恒定（见 alloc_vm_memory）。
        """
        block = self.vm_mem_block
        if not block:
            return False
        self.vm_mem_block = None
        if block == self.vm_mem_reserved:
            self.log(f"[vm] 释放 VM 内存块 0x{block:X}（预留区保留，下轮复用）")
            return True
        try:
            ok = self.mem.free(block)
        except Exception:  # pragma: no cover
            return False
        if ok:
            self.log(f"[vm] 释放 VM 内存块 0x{block:X}")
        return ok

    # ------------------------------------------------------------ 内存
    def _map_memory(self) -> None:
        ptr = ctypes.addressof(self.mem._c_buf)
        try:
            self.uc.mem_map_ptr(START_ADDRESS, TOTAL_MEMORY, UC_PROT_ALL, ptr)
            self.log(f"[vm] 共享内存映射完成 0x{START_ADDRESS:X}-0x{START_ADDRESS + TOTAL_MEMORY:X}")
        except Exception as exc:  # pragma: no cover - 老版本 unicorn 回退
            self.log(f"[vm] mem_map_ptr 不可用({exc})，回退到独立映射 + 手动同步")
            self.uc.mem_map(START_ADDRESS, TOTAL_MEMORY, UC_PROT_ALL)
            self._sync_mem = True
        else:
            self._sync_mem = False

        if self.zero_page:
            try:
                self.uc.mem_map(0, LOW_MEMORY_SIZE, UC_PROT_ALL)
                self.uc.mem_write(0, b"\x00" * LOW_MEMORY_SIZE)
                self.log(
                    f"[vm] 低地址 0x0-0x{LOW_MEMORY_SIZE:X} 已映射"
                    "（真机 ROM/RAM；兼容 NULL 字符串与低地址野指针）")
            except UcError as exc:  # pragma: no cover
                self.log(f"[vm] 低地址映射失败（不影响主内存）: {exc}")

    def _install_mem_guard(self) -> None:
        """记录非法内存访问地址，崩溃时给出可诊断信息。"""
        def guard(uc, access, address, size, value, user_data):
            self.invalid_accesses.append(
                (address, size, uc.reg_read(UC_ARM_REG_PC)))
            if len(self.invalid_accesses) > 32:
                del self.invalid_accesses[:-32]
            return False        # 不修复，仍按原语义抛 UcError
        self.uc.hook_add(UC_HOOK_MEM_INVALID, guard)

    def sync_in(self) -> None:
        if getattr(self, "_sync_mem", False):
            self.uc.mem_write(START_ADDRESS, bytes(self.mem.buf))

    def sync_out(self) -> None:
        if getattr(self, "_sync_mem", False):
            self.mem.buf[:] = self.uc.mem_read(START_ADDRESS, TOTAL_MEMORY)

    # ------------------------------------------------------------ 执行
    def run_code(self, start: int, stop: int = STOP_ADDRESS, thumb: bool = False) -> None:
        self.uc.reg_write(UC_ARM_REG_LR, stop)
        begin = (start | 1) if thumb else start
        self.sync_in()
        try:
            self.uc.emu_start(begin, stop, 0, 0)
        except UcError as exc:
            pc = self.uc.reg_read(UC_ARM_REG_PC)
            self.log(f"[vm] 执行异常 {exc} @ PC=0x{pc:X}")
            if self.invalid_accesses:
                tail = self.invalid_accesses[-4:]
                self.log("[vm] 非法访问: " + ", ".join(
                    f"@0x{a:X}({n}B) PC=0x{p:X}" for a, n, p in tail))
                self.invalid_accesses.clear()
            raise
        finally:
            self.sync_out()

    def read_reg(self, reg: int) -> int:
        return self.uc.reg_read(reg)

    def dump_regs(self) -> str:
        names = {
            UC_ARM_REG_R0: "R0", UC_ARM_REG_R1: "R1", UC_ARM_REG_R2: "R2",
            UC_ARM_REG_R3: "R3", UC_ARM_REG_SP: "SP", UC_ARM_REG_LR: "LR",
            UC_ARM_REG_PC: "PC",
        }
        from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6
        from unicorn.arm_const import UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9
        from unicorn.arm_const import UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12
        names.update({
            UC_ARM_REG_R4: "R4", UC_ARM_REG_R5: "R5", UC_ARM_REG_R6: "R6",
            UC_ARM_REG_R7: "R7", UC_ARM_REG_R8: "R8", UC_ARM_REG_R9: "R9",
            UC_ARM_REG_R10: "R10", UC_ARM_REG_R11: "R11", UC_ARM_REG_R12: "R12",
        })
        parts = [f"{n}=0x{self.uc.reg_read(r):08X}" for r, n in names.items()]
        return " ".join(parts)

    # ------------------------------------------------------------ 加载
    def load_code(self, path: str | Path) -> bool:
        p = Path(path)
        if not p.is_file():
            self.log(f"[vm] 找不到 {p}")
            return False
        data = p.read_bytes()
        if len(data) > 1024 * 1024:
            self.log(f"[vm] {p.name} 超过 1MB 代码段上限（{len(data)} 字节）")
            return False
        self.mem.write(CODE_ADDRESS, data)
        self.log(f"[vm] 已加载 {p.name} -> 0x{CODE_ADDRESS:X} ({len(data)} 字节)")
        return True

    # ------------------------------------------------------------ 两张表
    def install_tables(self, mr_table_funcs, dsm_funcs) -> None:
        from .bridge import BridgeTable

        t1 = BridgeTable("mr_table", mr_table_funcs, size=len(mr_table_funcs) * 4)
        self.mr_table = t1.install(self)
        self.tables["mr_table"] = t1

        # DSM_REQUIRE_FUNCS 结构体：0xc8 处是 flags，末尾对齐到 0xd4
        t2 = BridgeTable("dsm", dsm_funcs, size=0xD8)
        self.dsm_funcs = t2.install(self)
        self.tables["dsm"] = t2

        # 平台参数：文件系统 GBK，编辑框走 UTF-8（与 vmrp 的 win32 分支一致）
        from .consts import FLAG_USE_UTF8_EDIT
        self.mem.set_u32(self.dsm_funcs + 0xC8, FLAG_USE_UTF8_EDIT)

        self.mr_c_event = self.mem.malloc(12)
        self.dsm_event = self.mem.malloc(12)
        self.start_dsm_param = self.mem.malloc(12)
        self.mem.memset(self.start_dsm_param, 0, 12)

        self.log(
            f"[vm] mr_table@0x{self.mr_table:X} ({len(mr_table_funcs)} 项) | "
            f"dsm_require_funcs@0x{self.dsm_funcs:X} ({len(dsm_funcs)} 项)"
        )

    # ------------------------------------------------------------ ext 初始化
    def ext_init(self) -> None:
        """bridge_ext_init：执行 cfunction.ext 的 mr_c_function_load()。"""
        self.mem.set_u32(CODE_ADDRESS, self.mr_table)
        self.uc.reg_write(UC_ARM_REG_R0, 1)   # 1 = 使用 mr_extHelper
        self.run_code(CODE_ADDRESS + 8, CODE_ADDRESS, thumb=False)
        r9 = self.read_r9()
        self.log(
            f"[vm] mr_extHelper@0x{self.mr_extHelper_addr:X} | "
            f"mr_c_function_P@0x{self.mr_c_function_P:X} | r9(SB)=0x{r9:X}"
        )

    # ------------------------------------------------------------ r9 / SB
    #
    # r9 是 ARM 的 sb（静态基址寄存器），在 MRP 体系里指向「当前 ext 模块的
    # 全局变量区」（mr_c_function_P->start_of_ER_RW）。
    #
    # 切换这件事本身由 ext 自己完成：ext 内部的 asm_* 汇编桩会在每次跨层调用
    # 前后 setR9/setR10 切过去再切回来（见 mythroad/fixR9.c）。
    # 宿主的责任只有两条：
    #   1) 把 mr_c_function_P 写到 CODE_ADDRESS+4 —— ext 靠这个位置找回上一级
    #      的 P（fixR9.c 里的 C_FUNCTION_P() = *(mr_c_function_load - 4)）；
    #   2) 凡是从宿主直接跳进 ARM 的回调路径，手动保存/改写/恢复 r9
    #      （vmrp 的 bridge_dsm_network_cb 就是这么做的）。
    #
    # 实测（tests/r9_trace.py）：ARM 执行期间 r9 恒等于 P->ER_RW，宿主不需要干预。

    def read_r9(self) -> int:
        return self.uc.reg_read(UC_ARM_REG_R9)

    def write_r9(self, value: int) -> None:
        self.uc.reg_write(UC_ARM_REG_R9, value)

    def sb_of_ext(self) -> int:
        """当前 ext 的 RW 段基址（即 ext 内应设置的 r9 值）。"""
        if not self.mr_c_function_P:
            return 0
        return self.mem.u32(self.mr_c_function_P)

    def ext_helper(self, code: int, input_addr: int, input_len: int) -> int:
        """bridge_mr_extHelper：把事件喂给 ARM 侧的 helper 函数。

        r9 由 ext 侧自行切换；这里只在进出时做一次保存/恢复，
        防止 ext 内部异常退出时把中间态的 r9 泄漏给下一次调用。
        """
        uc = self.uc
        r9_saved = uc.reg_read(UC_ARM_REG_R9)
        uc.reg_write(UC_ARM_REG_R0, self.mr_c_function_P)
        uc.reg_write(UC_ARM_REG_R1, code)
        uc.reg_write(UC_ARM_REG_R2, input_addr)
        uc.reg_write(UC_ARM_REG_R3, input_len)
        try:
            self.run_code(self.mr_extHelper_addr, CODE_ADDRESS, thumb=False)
            return uc.reg_read(UC_ARM_REG_R0)
        finally:
            uc.reg_write(UC_ARM_REG_R9, r9_saved)

    def call_arm(self, addr: int, p0: int = 0, p1: int = 0, p2: int = 0) -> int:
        """从宿主直接跳进 ARM 回调（对应 vmrp 的 bridge_dsm_network_cb）。

        这条路径不经过 mr_extHelper，ARM 侧没有机会自己设置 r9，
        因此必须先把 r9 切到 ext 的 SB，调用完再恢复原值。
        网络/异步回调、宿主触发的 direct callback 都应走这里。
        """
        uc = self.uc
        r9_saved = uc.reg_read(UC_ARM_REG_R9)
        uc.reg_write(UC_ARM_REG_R9, self.sb_of_ext())
        uc.reg_write(UC_ARM_REG_R0, p0)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_R2, p2)
        try:
            self.run_code(addr, CODE_ADDRESS, thumb=False)
            return uc.reg_read(UC_ARM_REG_R0)
        finally:
            uc.reg_write(UC_ARM_REG_R9, r9_saved)

    def mr_event(self, code: int, p0: int, p1: int) -> int:
        """bridge_mr_event：写 event_t 再调 helper。"""
        self.mem.set_u32(self.mr_c_event + 0, code)
        self.mem.set_u32(self.mr_c_event + 4, p0)
        self.mem.set_u32(self.mr_c_event + 8, p1)
        r = self.ext_helper(1, self.mr_c_event, 12)
        return struct.unpack("<i", struct.pack("<I", r & 0xFFFFFFFF))[0]

    # ------------------------------------------------------------ 生命周期
    def dsm_init(self) -> bool:
        v = self.mr_event(DSM_INIT, self.dsm_funcs, 0)
        if v == VMRP_VER:
            self.log(f"[vm] DSM_INIT 握手成功 (ver={v})")
            return True
        self.log(f"[vm] DSM_INIT 版本不匹配：得到 {v}，期望 {VMRP_VER}")
        return False

    def start_dsm(self, filename: str, ext: str = "cfunction.ext", entry: str | None = None) -> int:
        mem = self.mem
        p_filename = self._copy_str(filename)
        p_ext = self._copy_str(ext)
        p_entry = self._copy_str(entry) if entry else 0

        mem.set_u32(self.start_dsm_param + 0, p_filename)
        mem.set_u32(self.start_dsm_param + 4, p_ext)
        mem.set_u32(self.start_dsm_param + 8, p_entry)

        v = self.mr_event(MR_START_DSM, self.start_dsm_param, 0)

        for p in (p_filename, p_ext, p_entry):
            if p:
                mem.free(p)
        return v

    def _copy_str(self, text: str) -> int:
        raw = text.encode("gbk", errors="replace") + b"\x00"
        p = self.mem.malloc(len(raw))
        if p:
            self.mem.write(p, raw)
        return p

    # ------------------------------------------------------------ 事件
    def event(self, code: int, p0: int, p1: int) -> int:
        self.mem.set_u32(self.dsm_event + 0, code)
        self.mem.set_u32(self.dsm_event + 4, p0)
        self.mem.set_u32(self.dsm_event + 8, p1)
        return self.mr_event(MR_EVENT, self.dsm_event, 0)

    def timer(self) -> int:
        return self.mr_event(MR_TIMER, 0, 0)

    def key_event(self, key: int, pressed: bool) -> int:
        from .consts import MR_KEY_PRESS, MR_KEY_RELEASE
        return self.event(MR_KEY_PRESS if pressed else MR_KEY_RELEASE, key, 0)

    def touch_event(self, kind: int, x: int, y: int) -> int:
        """发送触摸事件（MR_MOUSE_DOWN / UP / MOVE），坐标为 MRP 屏幕坐标。

        注意：绝大多数 2008 年的 MTK 应用不处理触摸事件，发了也不会回应。
        要「点屏幕就有反应」请用 ui.tap_to_key() 把它翻译成按键。
        """
        from .consts import MR_MOUSE_DOWN, MR_MOUSE_MOVE, MR_MOUSE_UP
        if kind not in (MR_MOUSE_DOWN, MR_MOUSE_UP, MR_MOUSE_MOVE):
            raise ValueError(f"不是触摸事件码: {kind}")
        return self.event(kind, x, y)

    def exit_dsm(self) -> None:
        self.exited = True
