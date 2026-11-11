"""ELF32 loader —— 把编译好的 mythroad 虚拟机镜像装进 Unicorn。

为什么不用裸二进制（objcopy -O binary）
--------------------------------------
裸二进制会丢掉 .bss 的地址与大小，而 .bss 里是解释器的静态数据
（Lua 的状态结构、mr_state、各种全局表）。清零范围不对就会踩到
野指针。用 ELF 的 program header 则能拿到精确的 p_memsz/p_filesz。

加载策略
--------
镜像按 mythroad.ld 链接到**固定绝对地址**（0x00880000），Python 侧
把它原样放到同一地址，镜像里的绝对地址全部有效，无需重定位。

只处理 PT_LOAD 段；零填充部分（memsz > filesz）显式清零。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from unicorn import UC_PROT_ALL
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
)

ELF_MAGIC = b"\x7fELF"
PT_LOAD = 1


@dataclass
class ElfSegment:
    vaddr: int
    memsz: int
    data: bytes
    offset: int


@dataclass
class ElfImage:
    entry: int
    segments: list[ElfSegment]
    bss_start: int = 0
    bss_end: int = 0

    @property
    def load_base(self) -> int:
        return min(s.vaddr for s in self.segments) if self.segments else 0

    @property
    def load_end(self) -> int:
        return max(s.vaddr + s.memsz for s in self.segments) if self.segments else 0


def parse_elf32(path: str | Path) -> ElfImage:
    """解析 ELF32 little-endian ARM 可执行文件。"""
    data = Path(path).read_bytes()
    if data[:4] != ELF_MAGIC:
        raise ValueError(f"{path} 不是 ELF 文件")
    if data[4] != 1:
        raise ValueError("只支持 ELF32")
    if data[5] != 1:
        raise ValueError("只支持 little-endian")

    e_type, e_machine, _ver = struct.unpack_from("<HHI", data, 16)
    e_entry, e_phoff = struct.unpack_from("<II", data, 24)
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 42)

    segments: list[ElfSegment] = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, p_memsz, _fl, _al = \
            struct.unpack_from("<IIIIIIII", data, off)
        if p_type != PT_LOAD:
            continue
        blob = data[p_offset:p_offset + p_filesz]
        segments.append(ElfSegment(p_vaddr, p_memsz, blob, p_offset))

    return ElfImage(entry=e_entry, segments=segments)


SHT_SYMTAB = 2
SHT_STRTAB = 3


def parse_symbols(path: str | Path) -> dict[str, int]:
    """解析 ELF 符号表，返回 {符号名: 值}。

    值对**函数/对象**来说是地址；对链接脚本里定义的**绝对符号**
    （如 `__heap_start = 0xA80000;`）来说就是那个常量本身。
    两种都用得上，所以原样返回。
    """
    data = Path(path).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, 46)

    symtab = None
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_type = struct.unpack_from("<I", data, off + 4)[0]
        if sh_type == SHT_SYMTAB:
            sh_offset, sh_size = struct.unpack_from("<II", data, off + 16)
            sh_link = struct.unpack_from("<I", data, off + 24)[0]
            sh_entsize = struct.unpack_from("<I", data, off + 36)[0]
            symtab = (sh_offset, sh_size, sh_link, sh_entsize or 16)
            break
    if symtab is None:
        return {}

    sh_offset, sh_size, str_idx, ent_size = symtab
    # 字符串表所在 section
    soff = e_shoff + str_idx * e_shentsize
    str_off, str_size = struct.unpack_from("<II", data, soff + 16)

    out: dict[str, int] = {}
    n = sh_size // ent_size
    for i in range(n):
        off = sh_offset + i * ent_size
        st_name, st_value = struct.unpack_from("<II", data, off)
        if st_name == 0:
            continue
        end = data.find(b"\x00", str_off + st_name)
        name = data[str_off + st_name:end].decode("ascii", "replace")
        if name:
            out[name] = st_value
    return out



def load_elf(uc, path: str | Path) -> ElfImage:
    """把 ELF 装进 Unicorn（调用方需先映射好地址空间）。"""
    img = parse_elf32(path)
    for seg in img.segments:
        if seg.data:
            uc.mem_write(seg.vaddr, seg.data)
        # .bss / 零填充部分
        if seg.memsz > len(seg.data):
            uc.mem_write(seg.vaddr + len(seg.data),
                         b"\x00" * (seg.memsz - len(seg.data)))
    return img
