"""自编译 mythroad 虚拟机（替代 cfunction.ext）。

为什么要有这一层
----------------
`cfunction.ext` 是官方 mythroad 的**编译产物**（内含 TOM 解释器 + mr_* API），
我们只能整个用或者整个不用 —— 想改一个 API 语义都做不到。

现在改成：用 `ref/mrpoid/mr` 的官方源码自己编译一个 mythroad VM，
然后：

* **虚拟机 → 宿主**：平台接口走汇编 thunk，尾跳到宿主分配的钩子槽位
  （`build/mythroad/emu_stub.s`），宿主用 `UC_HOOK_CODE` 拦截；
* **宿主 → 虚拟机**：通过镜像自描述头里的 `emu_host_api` 表直接调
  `mr_event` / `mr_timer` / `mr_start_dsm` 等官方内部函数。

内存布局（与 `build/mythroad/mythroad.ld` 严格一致）
--------------------------------------------------
    0x000000 - 0x070000   低地址 ROM/RAM（NULL/野指针兼容）
    0x070000 - 0x080000   钩子槽位区（宿主分配，每个槽位 4 字节）
    0x880000 - 0xA80000   虚拟机镜像（代码 + 数据 + bss，链接固定地址）
    0xA80000 - 0xE80000   newlib 堆 / 宿主分配区
    0xE80000              虚拟机栈顶（向下生长）
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Callable

from unicorn import (
    UC_ARCH_ARM,
    UC_HOOK_CODE,
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
    UC_ARM_REG_SP,
)

from .elfload import ElfImage, load_elf, parse_elf32, parse_symbols
from .memory import Allocator

# ---------------------------------------------------------------- 布局常量
# 必须与 build/mythroad/mythroad.ld 一致
LOW_BASE = 0x00000000
LOW_SIZE = 0x00070000          # 低地址 ROM/RAM
HOOK_BASE = 0x00070000         # 钩子槽位区
HOOK_SIZE = 0x00010000         # 64KB -> 16384 个槽位，够用
VM_BASE = 0x00880000           # 虚拟机镜像基址（链接地址）
VM_SPACE = 0x00600000          # 0x880000..0xE80000
STACK_TOP = 0x00E80000
STACK_SIZE = 0x00100000

EMU_MAGIC = 0x4D52564D          # 'MRVM'


class VmSpace:
    """虚拟机侧内存视图。

    与 `MrpMemory` 接口对齐，但底层走 unicorn 的 mem_read/mem_write
    （mythroad VM 的地址空间在 0x880000 以上，和老 VM 不重叠）。
    """

    def __init__(self, uc: Uc, base: int, size: int) -> None:
        self.uc = uc
        self.base = base
        self.size = size

    # -- 地址换算 ---------------------------------------------------
    def offset(self, addr: int) -> int:
        off = addr - self.base
        if off < 0 or off > self.size:
            raise ValueError(f"address 0x{addr:X} outside VM memory")
        return off

    def valid(self, addr: int, n: int = 1) -> bool:
        off = addr - self.base
        return 0 <= off and off + n <= self.size

    # -- 读写 -------------------------------------------------------
    def read(self, addr: int, n: int) -> bytes:
        return bytes(self.uc.mem_read(addr, n))

    def write(self, addr: int, data: bytes) -> None:
        self.uc.mem_write(addr, bytes(data))

    def memset(self, addr: int, value: int, n: int) -> None:
        self.uc.mem_write(addr, bytes([value & 0xFF]) * n)

    def u8(self, addr: int) -> int:
        return self.read(addr, 1)[0]

    def u16(self, addr: int) -> int:
        return struct.unpack("<H", self.read(addr, 2))[0]

    def u32(self, addr: int) -> int:
        return struct.unpack("<I", self.read(addr, 4))[0]

    def s16(self, addr: int) -> int:
        v = self.u16(addr)
        return v - 0x10000 if v & 0x8000 else v

    def s32(self, addr: int) -> int:
        v = self.u32(addr)
        return v - 0x100000000 if v & 0x80000000 else v

    def set_u16(self, addr: int, v: int) -> None:
        self.write(addr, (v & 0xFFFF).to_bytes(2, "little"))

    def set_u32(self, addr: int, v: int) -> None:
        self.write(addr, (v & 0xFFFFFFFF).to_bytes(4, "little"))

    def read_u32(self, addr: int) -> int:
        if not self.valid(addr, 4):
            return 0
        return self.u32(addr)

    # -- 字符串 -----------------------------------------------------
    def cstr(self, addr: int, limit: int = 4096) -> str:
        if not self.valid(addr, 1):
            return ""
        raw = self.cstr_bytes(addr, limit)
        if not raw:
            return ""
        if max(raw) < 0x80:
            return raw.decode("ascii")
        gbk_text = raw.decode("gbk", errors="replace")
        if gbk_text.count("\ufffd") >= 2:
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                pass
        return gbk_text.replace("\ufffd", "")

    def cstr_bytes(self, addr: int, limit: int = 4096) -> bytes:
        if not self.valid(addr, 1):
            return b""
        chunk = 256
        out = bytearray()
        while len(out) < limit:
            n = min(chunk, limit - len(out))
            try:
                blob = self.read(addr + len(out), n)
            except UcError:
                break
            idx = blob.find(b"\x00")
            if idx >= 0:
                out += blob[:idx]
                break
            out += blob
        return bytes(out)

    def put_cstr(self, addr: int, text: str, encoding: str = "gbk") -> int:
        try:
            raw = text.encode(encoding)
        except UnicodeEncodeError:
            raw = text.encode("utf-8")
        self.write(addr, raw + b"\x00")
        return len(raw) + 1


class MythroadVm:
    """自编译的 mythroad 虚拟机。"""

    def __init__(self, image: str | Path,
                 log: Callable[[str], None] = print) -> None:
        self.log = log
        self.image_path = Path(image)
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.exited = False
        self.exit_code = 0
        self.instance_stopped = False
        self.app = None

        self._map_memory()
        self.img: ElfImage = load_elf(self.uc, self.image_path)
        self._read_header()
        self._read_symbols()
        self._build_hook_table()

        # 宿主分配区：从 newlib 堆尾往后
        self.heap = Allocator(self.heap_base + self.heap_size,
                              VM_BASE + VM_SPACE - (self.heap_base + self.heap_size))
        self.mem = VmSpace(self.uc, VM_BASE, VM_SPACE)

        # ---- 斯凯插件机制的「地址恒定」内存 ----
        # mr_mem_get 给 mythroad 的那块内存会被整个 dump 到 plugins/dump%d，
        # 退出插件后按**同一绝对地址**读回恢复，所以每轮必须拿到同一块。
        # 普通 first-fit 做不到（碎片一多地址就漂），要用专用预留区。
        self.vm_mem_block: int | None = None
        self.vm_mem_reserved: int | None = None
        self.vm_mem_len: int = 0

        self.host_api: dict[str, int] = {}
        self._read_host_api()

        self.log(f"[mvm] 镜像 {self.image_path.name} "
                 f"0x{self.img.load_base:X}-0x{self.img.load_end:X} "
                 f"({(self.img.load_end - self.img.load_base) // 1024}KB)")
        self.log(f"[mvm] 钩子 {self.n_slots} 个 @0x{HOOK_BASE:X} | "
                 f"堆 0x{self.heap_base:X}+{self.heap_size // 1024}KB | "
                 f"栈顶 0x{STACK_TOP:X}")

    # ------------------------------------------------------------ 内存
    def _map_memory(self) -> None:
        self.uc.mem_map(LOW_BASE, LOW_SIZE, UC_PROT_ALL)
        self.uc.mem_write(LOW_BASE, b"\x00" * LOW_SIZE)
        self.uc.mem_map(HOOK_BASE, HOOK_SIZE, UC_PROT_ALL)
        self.uc.mem_map(VM_BASE, VM_SPACE, UC_PROT_ALL)

    # ------------------------------------------------------------ 头部
    def _read_header(self) -> None:
        """读镜像自描述头（只有编译期常量字段）。"""
        raw = self.uc.mem_read(VM_BASE, 8)
        magic, version = struct.unpack("<2I", raw)
        if magic != EMU_MAGIC:
            raise RuntimeError(
                f"镜像自描述头不对：magic=0x{magic:X}（期望 0x{EMU_MAGIC:X}）")
        self.version = version
        # 槽位数量由名字表（NULL 结尾）决定，不放在头里 ——
        # 跨翻译单元的 const 变量在 C 里不是常量表达式。

    def _read_symbols(self) -> None:
        """从 ELF 符号表定位运行时结构。

        链接脚本符号（`__heap_start = .`）在符号表里的值就是那个地址，
        所以堆/栈边界也能直接读出来。
        """
        syms = parse_symbols(self.image_path)
        self.syms = syms

        def need(name: str) -> int:
            v = syms.get(name)
            if not v:
                raise RuntimeError(f"镜像里找不到符号 {name}")
            return v

        self.host_api_addr = need("emu_host_api")
        self.slot_names_addr = need("emu_slot_names")
        self.self_test_addr = need("emu_self_test")
        self.heap_base = syms.get("__heap_start", 0)
        self.heap_size = syms.get("__heap_end", 0) - self.heap_base
        self.stack_top = syms.get("__stack_top", STACK_TOP)

    def _read_host_api(self) -> None:
        names = ("mr_event", "mr_timer", "mr_exit", "mr_start_dsm",
                 "mr_stop", "mr_mem_get", "mr_mem_free", "self_test",
                 "get_state")
        raw = self.uc.mem_read(self.host_api_addr, 4 * len(names))
        addrs = struct.unpack(f"<{len(names)}I", raw)
        self.host_api = dict(zip(names, addrs))
        self.log("[mvm] host_api: " + " ".join(
            f"{k}=0x{v:X}" for k, v in self.host_api.items()))

    # ------------------------------------------------------------ 钩子
    def _build_hook_table(self) -> None:
        """按镜像里的名字表建立钩子槽位。

        槽位里写**它自己的地址**（沿用老 VM 的做法），Python 侧用
        `UC_HOOK_CODE` 在这个区间拦截，命中后按地址反查是哪个接口。
        """
        names: list[str] = []
        addr = self.slot_names_addr
        # 名字表是 NULL 结尾的；上限只是防跑飞
        for _ in range(1024):
            ptr = struct.unpack("<I", self.uc.mem_read(addr, 4))[0]
            if ptr == 0:
                break
            raw = bytes(self.uc.mem_read(ptr, 64))
            end = raw.find(b"\x00")
            names.append(raw[:end].decode("ascii", "replace"))
            addr += 4
        self.slot_names = names
        self.n_slots = len(names)

        self.slot_base = HOOK_BASE
        self.slot_map: dict[int, str] = {}
        for i, name in enumerate(names):
            a = HOOK_BASE + i * 4
            self.uc.mem_write(a, struct.pack("<I", a))
            self.slot_map[a] = name
        self.uc.hook_add(UC_HOOK_CODE, self._hook, None,
                         HOOK_BASE, HOOK_BASE + len(names) * 4)
        self.log(f"[mvm] 钩子表就绪：{len(names)} 项")

    def _hook(self, uc, address: int, size: int, user_data) -> None:
        name = self.slot_map.get(address)
        if name is None:
            return
        fn = self.platform_handlers.get(name)
        if fn is None:
            uc.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF)
        else:
            fn(self)
        # 汇编 thunk 不改 LR，直接把 PC 写回 LR 即返回调用者
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    platform_handlers: dict[str, Callable[["MythroadVm"], None]] = {}

    # ------------------------------------------------------------ 调用
    def _call(self, name: str, *args: int) -> int:
        addr = self.host_api.get(name)
        if not addr:
            raise RuntimeError(f"host_api 里没有 {name}")
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        for i, a in enumerate(args):
            uc.reg_write((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                          UC_ARM_REG_R3)[i], a)
        uc.reg_write(UC_ARM_REG_LR, 0)
        try:
            uc.emu_start(addr, 0, 0, 1)
        except UcError as exc:
            self.log(f"[mvm] 调用 {name} 失败: {exc}")
            return 0xFFFFFFFF
        return uc.reg_read(UC_ARM_REG_R0)

    def self_test(self) -> int:
        return self._call("self_test")

    def mr_event(self, code: int, p0: int, p1: int) -> int:
        return self._call("mr_event", code & 0xFFFF, p0, p1)

    def mr_timer(self) -> int:
        return self._call("mr_timer")

    def mr_start_dsm(self, entry: str) -> int:
        raw = entry.encode("gbk", errors="replace") + b"\x00"
        buf = self.heap.malloc(len(raw))
        self.mem.write(buf, raw)
        try:
            return self._call("mr_start_dsm", buf)
        finally:
            self.heap.free(buf)

    # ------------------------------------------------- 地址恒定的 VM 内存
    def alloc_vm_memory(self, size: int) -> int:
        """给 mythroad 一块**跨重启恒定**的内存（斯凯 dump/恢复的前提）。

        官方 ``mr_mem_get`` 的语义：交给 mythroad 一整块可用的堆。
        斯凯的插件机制把这块内存整个 dump 到 ``plugins/dump%d``，
        退出插件后按**同一绝对地址**读回恢复 —— 地址一旦漂移，
        恢复出来的指针全是野的。
        """
        if self.vm_mem_reserved is None:
            block = self.heap.reserve(size)
            if not block:
                return 0
            self.vm_mem_reserved = block
            self.vm_mem_len = size
            self.log(f"[mvm] 预留 VM 内存区 0x{block:X} ({size // 1024}KB)")
        self.vm_mem_block = self.vm_mem_reserved
        return self.vm_mem_block

    def release_vm_memory(self) -> bool:
        """``mr_stop_ex(freemem!=0)`` 时释放 VM 内存块（官方 mr_mem_free）。"""
        block = self.vm_mem_block
        if not block:
            return False
        self.vm_mem_block = None
        if block == self.vm_mem_reserved:
            # 预留区留着下一轮复用 —— 地址必须恒定
            return True
        return self.heap.free(block)
