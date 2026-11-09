"""MRP 包读写工具。

格式结论来自对真实样本（dsm_gm.mrp / box.mrp）的实测，详见
docs/03-MRP包格式规范.md。

用法:
    python tools/mrp_pack.py list  <file.mrp>
    python tools/mrp_pack.py info  <file.mrp>
    python tools/mrp_pack.py x     <file.mrp> [-o outdir]
    python tools/mrp_pack.py repack <file.mrp> -o new.mrp [--set name=path]...

`repack` 会重新压缩全部条目并重建索引，用于替换包内图片/音乐后回填。
它不改动文件头 0x000-0x0EF 区（除 0x08 文件长度），因为该区部分字段语义未确证。
"""
from __future__ import annotations

import argparse
import gzip
import struct
import sys
import zlib
from pathlib import Path

HDR_SIZE = 0xF0          # 条目表起点
MAX_NAME = 64


def u32(d: bytes, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


class Entry:
    __slots__ = ("name", "offset", "csize", "reserved", "raw")

    def __init__(self, name: str, offset: int, csize: int, reserved: int, raw: bytes):
        self.name = name
        self.offset = offset        # 指向 gzip 流起点
        self.csize = csize
        self.reserved = reserved
        self.raw = raw              # 解压后的原始数据

    def __repr__(self) -> str:
        return (f"<{self.name} off=0x{self.offset:X} "
                f"csize={self.csize} raw={len(self.raw)}>")


class Mrp:
    def __init__(self, data: bytes):
        if data[:4] != b"MRPG":
            raise ValueError(f"不是 MRP 包（魔数 {data[:4]!r}）")
        self.data = data
        self.header = bytearray(data[:HDR_SIZE])
        self.total_size = u32(data, 0x08)
        self.width = u32(data, 0x0C)
        self.entry_name = data[0x10:0x10 + 24].split(b"\0")[0].decode("ascii", "replace")
        self.title_gbk = data[0x1C:0x2C].split(b"\0")[0].decode("gbk", "replace")
        self.entries: list[Entry] = []
        self._parse()

    def _parse(self) -> None:
        d = self.data
        pos = HDR_SIZE
        while pos + 4 <= len(d):
            name_len = u32(d, pos)
            if not (2 <= name_len <= MAX_NAME):
                break
            raw_name = d[pos + 4:pos + 4 + name_len]
            if raw_name[-1:] != b"\0":
                break
            name = raw_name[:-1].decode("ascii", "replace")
            off, csize, rsv = struct.unpack_from("<III", d, pos + 4 + name_len)
            if off + csize > len(d):
                break
            try:
                payload = zlib.decompress(d[off:off + csize], 16 + zlib.MAX_WBITS)
            except zlib.error:
                payload = d[off:off + csize]
            self.entries.append(Entry(name, off, csize, rsv, payload))
            pos += 4 + name_len + 12

    @classmethod
    def load(cls, path: str | Path) -> "Mrp":
        return cls(Path(path).read_bytes())

    # -------------------------------------------------------------- 输出
    def info(self) -> str:
        return (f"文件: {self.entry_name}  标题: {self.title_gbk or '(无)'}\n"
                f"声明长度: {self.total_size}  实际: {len(self.data)}  "
                f"屏宽: {self.width}  条目数: {len(self.entries)}")

    def table(self) -> str:
        rows = [f"{'名字':<18}{'偏移':>8}{'压缩':>9}{'解压':>9}  类型"]
        for e in self.entries:
            rows.append(f"{e.name:<18}{e.offset:>8X}{e.csize:>9}"
                        f"{len(e.raw):>9}  {sniff(e.name, e.raw)}")
        return "\n".join(rows)

    def extract(self, outdir: Path) -> None:
        outdir.mkdir(parents=True, exist_ok=True)
        for e in self.entries:
            (outdir / e.name).write_bytes(e.raw)

    def rebuild(self, replace: dict[str, bytes] | None = None) -> bytes:
        """重建整包。header 原样保留（只更新长度）。"""
        replace = replace or {}
        items: list[tuple[str, bytes]] = []
        for e in self.entries:
            items.append((e.name, replace.get(e.name, e.raw)))
        known = {n for n, _ in items}
        for name, payload in replace.items():          # 新增条目
            if name not in known:
                items.append((name, payload))

        # 先排布条目表（每项长度已知），算出数据区起点
        names = [n.encode("ascii") + b"\0" for n, _ in items]
        table_size = sum(4 + len(nm) + 12 for nm in names)
        data_start = HDR_SIZE + table_size

        table = bytearray()
        chunks = bytearray()
        pos = data_start
        for (name, payload), nm in zip(items, names):
            gz = gzip.compress(payload, 9, mtime=0)
            # 数据区: uint32 长度 + gzip 流（该长度与条目 csize 一致）
            chunks += struct.pack("<I", len(gz)) + gz
            table += (struct.pack("<I", len(nm)) + nm +
                      struct.pack("<III", pos + 4, len(gz), 0))
            pos += 4 + len(gz)

        header = bytearray(self.header)
        struct.pack_into("<I", header, 0x08, HDR_SIZE + table_size + len(chunks))
        return bytes(header) + bytes(table) + bytes(chunks)


def sniff(name: str, raw: bytes) -> str:
    if raw[:4] == b"\x1bMRP":
        return "mythroad 字节码 (.mr)"
    if raw[:4] == b"MRPG":
        return "mythroad ext (ARM)"
    if raw[:4] == b"MThd":
        return "MIDI"
    if raw[:4] == b"RIFF":
        return "WAV"
    if raw[:2] == b"BM":
        return "标准 BMP"
    if raw[:4] == b"\x89PNG":
        return "PNG"
    if name.lower().endswith(".bmp"):
        px = len(raw) // 2
        dims = f"{px}px"
        if px % 240 == 0:
            dims += f" = 240x{px // 240}"
        return f"裸 RGB565 位图 ({dims})"
    return f"未知 (头 {raw[:4].hex()})"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="MRP 包读写工具")
    ap.add_argument("cmd", choices=("list", "info", "x", "repack"))
    ap.add_argument("file")
    ap.add_argument("-o", "--out")
    ap.add_argument("--set", action="append", default=[],
                    metavar="NAME=PATH", help="repack 时替换/新增条目")
    args = ap.parse_args(argv)

    m = Mrp.load(args.file)
    if args.cmd == "info":
        print(m.info())
    elif args.cmd == "list":
        print(m.info())
        print(m.table())
    elif args.cmd == "x":
        outdir = Path(args.out or (Path(args.file).stem + "_x"))
        m.extract(outdir)
        print(f"已解出 {len(m.entries)} 个条目 -> {outdir}")
    elif args.cmd == "repack":
        if not args.out:
            print("repack 需要 -o", file=sys.stderr)
            return 2
        replace = {}
        for spec in args.set:
            name, _, path = spec.partition("=")
            replace[name] = Path(path).read_bytes()
        blob = m.rebuild(replace)
        Path(args.out).write_bytes(blob)
        print(f"已生成 {args.out}  ({len(blob)} 字节, 替换 {len(replace)} 项)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
