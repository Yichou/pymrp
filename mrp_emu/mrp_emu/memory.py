"""模拟器内存模型。

设计要点：unicorn 与 Python 共享同一块 bytearray（mem_map_ptr 零拷贝），
所以 API 回调里读写 MRP 内存是纯 Python 切片，没有跨引擎拷贝开销。
"""

from __future__ import annotations

import ctypes

from .consts import (
    END_ADDRESS,
    MEMORY_MANAGER_ADDRESS,
    MEMORY_MANAGER_SIZE,
    START_ADDRESS,
    TOTAL_MEMORY,
)

ALIGN = 8


class Allocator:
    """first-fit 分配器，对应 vmrp 的 my_mallocExt / my_freeExt。

    元数据只存在 Python 侧，不占用模拟内存，避免和 MRP 的内存布局打架。
    """

    def __init__(self, base: int, size: int) -> None:
        self.base = base
        self.size = size
        self.free: list[list[int]] = [[base, size]]
        self.used: dict[int, int] = {}
        self.peak = 0

    def malloc(self, n: int) -> int:
        if n <= 0:
            n = 1
        n = (n + ALIGN - 1) & ~(ALIGN - 1)
        for i, blk in enumerate(self.free):
            addr, size = blk
            if size < n:
                continue
            if size - n >= ALIGN:
                blk[0] += n
                blk[1] -= n
            else:
                n = size            # 剩余碎片太小，整块给出
                self.free.pop(i)
            self.used[addr] = n
            self.peak = max(self.peak, self.in_use())
            return addr
        return 0

    def free_block(self, addr: int) -> bool:
        n = self.used.pop(addr, None)
        if n is None:
            return False
        self.free.append([addr, n])
        self.free.sort(key=lambda b: b[0])
        self._coalesce()
        return True

    def _coalesce(self) -> None:
        out: list[list[int]] = []
        for blk in self.free:
            if out and out[-1][0] + out[-1][1] == blk[0]:
                out[-1][1] += blk[1]
            else:
                out.append(blk)
        self.free = out

    def in_use(self) -> int:
        return sum(self.used.values())

    def report(self) -> str:
        return (
            f"heap {self.size // 1024}KB | used {self.in_use() // 1024}KB "
            f"| peak {self.peak // 1024}KB | blocks {len(self.used)}"
        )


class MrpMemory:
    """0x80000..0x880000 的 8MB 线性地址空间。"""

    def __init__(self) -> None:
        self.base = START_ADDRESS
        self.size = TOTAL_MEMORY
        self.buf = bytearray(self.size)
        # 保持引用，防止 GC 回收导致 unicorn 侧访问野指针
        self._c_buf = (ctypes.c_char * self.size).from_buffer(self.buf)
        self.heap = Allocator(MEMORY_MANAGER_ADDRESS, MEMORY_MANAGER_SIZE)

    # -- 地址换算 ---------------------------------------------------
    def offset(self, addr: int) -> int:
        off = addr - self.base
        if off < 0 or off > self.size:
            raise ValueError(f"address 0x{addr:X} outside simulated memory")
        return off

    def valid(self, addr: int, n: int = 1) -> bool:
        off = addr - self.base
        return 0 <= off and off + n <= self.size

    # -- 读写 -------------------------------------------------------
    def read(self, addr: int, n: int) -> bytes:
        off = self.offset(addr)
        return bytes(self.buf[off:off + n])

    def write(self, addr: int, data: bytes) -> None:
        off = self.offset(addr)
        self.buf[off:off + len(data)] = data

    def memset(self, addr: int, value: int, n: int) -> None:
        off = self.offset(addr)
        self.buf[off:off + n] = bytes([value & 0xFF]) * n

    def u8(self, addr: int) -> int:
        return self.buf[self.offset(addr)]

    def u16(self, addr: int) -> int:
        off = self.offset(addr)
        return int.from_bytes(self.buf[off:off + 2], "little")

    def u32(self, addr: int) -> int:
        off = self.offset(addr)
        return int.from_bytes(self.buf[off:off + 4], "little")

    def s16(self, addr: int) -> int:
        v = self.u16(addr)
        return v - 0x10000 if v & 0x8000 else v

    def s32(self, addr: int) -> int:
        v = self.u32(addr)
        return v - 0x100000000 if v & 0x80000000 else v

    def set_u16(self, addr: int, v: int) -> None:
        off = self.offset(addr)
        self.buf[off:off + 2] = (v & 0xFFFF).to_bytes(2, "little")

    def set_u32(self, addr: int, v: int) -> None:
        off = self.offset(addr)
        self.buf[off:off + 4] = (v & 0xFFFFFFFF).to_bytes(4, "little")

    # -- 字符串：MRP 是 GBK 时代的东西 ------------------------------
    def cstr(self, addr: int, limit: int = 4096) -> str:
        if not self.valid(addr, 1):
            return ""
        off = self.offset(addr)
        end = self.buf.find(b"\x00", off, min(off + limit, self.size))
        if end < 0:
            end = min(off + limit, self.size)
        raw = bytes(self.buf[off:end])
        for enc in ("gbk", "utf-8"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1")

    def cstr_bytes(self, addr: int, limit: int = 4096) -> bytes:
        if not self.valid(addr, 1):
            return b""
        off = self.offset(addr)
        end = self.buf.find(b"\x00", off, min(off + limit, self.size))
        if end < 0:
            end = min(off + limit, self.size)
        return bytes(self.buf[off:end])

    def put_cstr(self, addr: int, text: str, encoding: str = "gbk") -> int:
        try:
            raw = text.encode(encoding)
        except UnicodeEncodeError:
            raw = text.encode("utf-8")
        self.write(addr, raw + b"\x00")
        return len(raw) + 1

    # -- 分配 -------------------------------------------------------
    def malloc(self, n: int) -> int:
        return self.heap.malloc(n)

    def free(self, addr: int) -> bool:
        return self.heap.free_block(addr)

    # -- 帧缓冲 -----------------------------------------------------
    def rgb565_rect(self, addr: int, w: int, h: int) -> bytes:
        return self.read(addr, w * h * 2)
