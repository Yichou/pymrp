# 03 · MRP 包格式规范

> **状态**：本文档所有结论均由真实样本实测得出（dsm_gm.mrp、box.mrp 等），并用
> "重新打包 → 真实 mythroad 层加载 → 正常渲染" 的闭环验证过（A 级）。
> 凡未确证的字段，明确标注"未确证"，请不要当作事实传播。

## 1. 总览

`.mrp` 是一个**自定义归档**：固定 0xF0 字节头 + 变长条目表 + 数据区。
包内**每个条目独立 gzip 压缩**，条目类型包括字节码（`.mr`）、ARM 扩展（`.ext`）、
位图（`.bmp`）、MIDI 音乐（`.mid`）等。

```
┌──────────────────────────────┐ 0x000
│ 固定头（0xF0 字节）            │
├──────────────────────────────┤ 0x0F0
│ 条目表（变长）                 │  每条: nameLen|name|offset|csize|0
├──────────────────────────────┤
│ 数据区                        │  每条: uint32 长度 + gzip 流
└──────────────────────────────┘
```

## 2. 固定头（0x000 – 0x0EF）

| 偏移 | 类型 | 实测值（dsm_gm / box） | 含义 | 置信 |
|---|---|---|---|---|
| 0x00 | char[4] | `MRPG` | 魔数 | A |
| 0x04 | uint32 | 507 / 584 | **未确证**。两次样本均落在"条目表结束点附近"，但既不等于条目表长度也不等于数据区起点，与包内容相关。repack 时建议原样保留 | D |
| 0x08 | uint32 | 41315 / 50434 | **文件总字节数**（两个样本都精确等于文件大小） | A |
| 0x0C | uint32 | 240 / 240 | 屏幕宽度 | A |
| 0x10 | char[12] | `dsm_gm.mr\0` / `box.mr\0` | 主程序名（包内 `.mr` 条目名） | A |
| 0x1C | char[] GBK | `应用列表` / `推箱子` | 应用显示名（GBK 编码） | A |
| 0x2C– | — | `00…00` | 保留区（观察为全 0） | D |
| 0x40– | — | `01 01 …` | 标志序列（dsm_gm 观察到连续 `01`，box 为 MD5 样式的杂凑值）。**未确证**，repack 时原样复制 | D |
| 0xF0 | — | — | 条目表起点 | A |

> repack 策略：`0x000–0x0EF` 整块原样保留，只更新 `0x08` 的总长度。
> 实测这样做的包能被 mythroad 正常加载。

## 3. 条目表

从 `0xF0` 开始，变长条目连续排列，直到读出的 `nameLen` 不再合理：

```
uint32  nameLen          名字字节数，含结尾 NUL
uint8   name[nameLen]    ASCII 文件名 + NUL
uint32  offset           数据区绝对偏移，指向 gzip 流起点（不是 size 字段！）
uint32  csize            压缩后字节数（gzip 流长度）
uint32  reserved         实测全 0
```

单条长度 = `4 + nameLen + 12`。以 dsm_gm.mrp 为例：

```
000F0  09 00 00 00 74 63 70 69 70 2e 6d 72 00 14 02 00   ....tcpip.mr....
00100  00 1d 1a 00 00 00 00 00 00                        ........
       └─nameLen=9─┘└─ tcpip.mr+NUL ─┘└offset=0x214┘└csize=0x1A1D┘└rsv=0┘
```

解析循环的终止条件：`nameLen` 必须在 2–64 之间，且 `name` 以 NUL 结尾，
且 `offset + csize ≤ 文件长度`。三个条件一起用，越过条目表进入数据区时会立即失败退出。

## 4. 数据区

每个条目对应一段：

```
uint32  size        与条目表里的 csize 相同（冗余，用途未确证）
uint8   gz[size]    标准 gzip 流（RFC 1952，1F 8B 08 开头）
```

解压后就是文件原文。实测（dsm_gm.mrp 全部 9 条）：

| 名字 | csize | 解压后 | 解压内容头 | 类型 |
|---|---|---|---|---|
| tcpip.mr | 6685 | 18712 | `1B 4D 52 50` | mythroad 字节码 |
| start.mr | 12576 | 37230 | `1B 4D 52 50` | mythroad 字节码 |
| bg.bmp | 51 | 14400 | `19 1D 19 1D` | 裸 RGB565（240×30） |
| dialog_top.bmp | 50 | 12480 | `F9 1C F9 1C` | 裸 RGB565（240×26） |
| player1.bmp | 3078 | 7200 | `D3 2B D3 2B` | 裸 RGB565（240×15） |
| lstic.bmp | 1816 | 3584 | `FF FF FF FF` | 裸 RGB565（32×56） |
| commonv2.mr | 13124 | 42449 | `1B 4D 52 50` | mythroad 字节码 |
| timer.mr | 2858 | 8538 | `1B 4D 52 50` | mythroad 字节码 |
| cfunction.ext | 317 | 368 | `4D 52 50 47` | ext（见 §6） |

box.mrp 里还有 `backsound.mid` / `turn.mid`，解压后是标准 MIDI（`MThd`）。

**两个重要推论**：

1. **包内 `.bmp` 不是 Windows BMP**——没有 `BM` 头，直接是 RGB565 像素流，
   行跨度 = 包头 0x0C 的宽度 × 2（个别例外如图标，宽不是 240，由应用自己约定）。
   `mr_drawBitmap` 吃的就是这种格式。
2. **`.mr` 文件有自己的魔数** `1B 4D 52 50`（`\x1b"MRP"`），后面跟内嵌文件名和
   若干长度/偏移表。字节码指令集未公开，本文不覆盖（模拟器不需要解释它——
   cfunction.ext 里的解释器会执行它）。

## 5. 解包与重打包

仓库自带工具（Python，无第三方依赖）：

```bash
python tools/mrp_pack.py info  game.mrp        # 头信息
python tools/mrp_pack.py list  game.mrp        # 条目表
python tools/mrp_pack.py x     game.mrp        # 解包到 game_x/
python tools/mrp_pack.py repack game.mrp -o new.mrp \
    --set backsound.mid=my_new_song.mid \
    --set bg.bmp=my_bg.bmp
```

`repack` 会重新压缩全部条目、重建条目表和偏移。**验证**：对 dsm_gm.mrp 做无修改
repack，产物交给真实 mythroad 层加载，应用列表正常渲染（A 级验证，2026-11）。

注意事项：

- `0x04` 字段原样保留，不重算；
- 新增条目直接追加，名字必须 ASCII；
- `.mr` 字节码没法重新编译（编译器已失传），只能原样保留或整条删除。

## 6. `cfunction.ext` 文件格式

独立于 `.mrp` 的 ext 文件（8 字节头 + ARM 代码）：

```
0x00  char[4]  "MRPG"
0x04  char[4]  "CMAP"
0x08  开始就是 ARM 机器码
```

官方发行版里的 `cfunction.ext` 是 331520 字节的**未压缩**裸文件（不在 MRP 包里时）。
它在包内出现时（如 dsm_gm.mrp 的 cfunction.ext 条目，解压 368 字节）是另一个小的
helper ext，不是那个 331 KB 的主运行时。

## 7. 未解之谜（欢迎补充）

按失传风险排序：

1. **`0x04` 字段语义**：两个样本值 507/584，与条目表长度、数据区起点都不吻合；
2. **头部 `0x40` 起的标志序列**：dsm_gm 是 `01×12`，box 是 16 字节杂凑——
   猜测是某种特征码或校验，未确证；
3. **`.mr` 字节码指令集**：`1B "MRP"` 之后是长度表还是代码段，未系统分析
   （对模拟器实现不构成障碍，但对"重新编译 MRP"是死结）；
4. **数据区里每个 gzip 前的 `uint32`**：与 csize 恒等，冗余存储的目的不明。

## 8. 解析器参考实现

最小解析（可直接复制运行）：

```python
import struct, zlib

def mrp_entries(data: bytes):
    assert data[:4] == b"MRPG", "不是 MRP 包"
    pos, out = 0xF0, []
    while pos + 4 <= len(data):
        (nlen,) = struct.unpack_from("<I", data, pos)
        if not (2 <= nlen <= 64):
            break
        name = data[pos+4:pos+4+nlen]
        if name[-1:] != b"\x00":
            break
        off, csize, _ = struct.unpack_from("<III", data, pos+4+nlen)
        if off + csize > len(data):
            break
        raw = zlib.decompress(data[off:off+csize], 16+zlib.MAX_WBITS)
        out.append((name[:-1].decode(), raw))
        pos += 4 + nlen + 12
    return out
```

配合 `docs/02` 的内存布局与事件循环，实现一个完整模拟器所需的全部二进制知识就在这个仓库里了。
