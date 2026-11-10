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

> **2026-11 修订**：结合官方《mythroad 工程文件（mpr 文件）编写指南》与
> vmrp.github.io 的 `public/data.txt`（664 条站点自建索引）交叉验证，
> 原表里标"未确证"的字段已全部定位。字段长度与官方 `.mpr` 工程配置的
> 上限**逐字节吻合**：`filename` 11 ASCII → 12 字节、`appname` 23 → 24、
> `vendor` 39 → 40、`description` 63 → 64。

| 偏移 | 类型 | 含义 | 置信 |
|---|---|---|---|
| 0x00 | char[4] | `MRPG` 魔数 | A |
| 0x04 | uint32 | 条目表结束偏移 **- 8**；站点索引的 `FileStart = 0x04 + 8`。语义未确证，repack 时原样保留 | A(规律) / D(语义) |
| 0x08 | uint32 | 文件总字节数 | A |
| 0x0C | uint32 | 屏幕宽度（实测恒 240） | A |
| 0x10 | char[12] | `filename`：应用在手机上保存时的名字，11 ASCII + NUL | A |
| 0x1C | char[24] GBK | `appname` / DisplayName：应用列表里显示的名字 | A |
| 0x34 | char[16] | `AuthStr`：认证串。builder ≥ 10002 有效；老包此处是 16 字节特征码 | A |
| 0x44 | uint32 | `appid` | A |
| 0x48 | uint32 | `version` | A |
| 0x4C | uint32 | `flag` | A |
| 0x50 | uint32 | `BuilderVersion`（10000 = 老 / 10002 = 新） | A |
| 0x54 | uint32 | `Crc32`（老包恒 0） | A |
| 0x58 | char[40] GBK | `vendor`：制造商，39 有效字符 + NUL | A |
| 0x80 | char[64] GBK | `description`：应用描述，63 有效字符 + NUL | A |
| 0xC0 | uint32 BE | `appid` 的大端副本 | A |
| 0xC4 | uint32 BE | `version` 的大端副本 | A |
| 0xC8 | uint32 | ScreenWidth（多数为 0） | B |
| 0xCC | uint32 | ScreenHeight（多数为 0） | B |
| 0xD0 | uint32 | Plat（0 / 1） | B |
| 0xD4–0xEF | — | 保留 | D |
| 0xF0 | — | 条目表起点 | A |

**验证样例**（`10066_240320_rxhcl.mrp`，与 data.txt 逐字段一致）：

```
000  4D 52 50 47 00 02 00 00 E2 83 00 00 F0 00 00 00  MRPG............
010  72 78 68 63 6C 00 ...          D0 A1 BB F0        rxhcl  小火...
020  B2 F1 C0 EF B5 C4 B4 F3 C3 D5 CC E2 00 ...        柴里的大谜题
030  00 00 00 00 37 65 31 32 33 38 34 66 64 00 ...    7e12384fd
040  00 00 00 00 52 27 00 00 8A 00 00 00 01 00 00 00  appid=10066 ver=138
050  12 27 00 00 0D B0 03 69 BA BC D6 DD CB B9 BF AD  builder/crc 杭州斯凯
080  D0 A1 D0 A1 B5 C4 BB F0 B2 F1 B0 F4 C0 EF ...     描述（GBK）
0C0  00 00 27 52 00 00 00 8A ...                      大端 appid/version
```

> repack 策略：`0x000–0x0EF` 整块原样保留，只更新 `0x08` 的总长度。
> 实测这样做的包能被 mythroad 正常加载。
>
> 只读前 0xF0 字节就能拿到标题、开发商、描述、appid、版本 —— 游戏中心的
> 本地列表就是这么建的，664 个文件也只需各自读 240 字节。

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

1. **`0x04` 字段语义**：现已确认恒等于「条目表结束偏移 - 8」，站点索引的
   `FileStart`（数据区起点）恰好等于 `0x04 + 8`（15 个样本零例外）。
   为什么偏偏差 8 字节仍无解释，猜是 builder 把「条目表末项 + 两个 u32」
   记成了长度基准；
2. **老 builder(10000) 的 `0x34` 起 16 字节**：新包是 ASCII `AuthStr`，
   老包是随机特征码（dsm_gm 为 `01×16`），用途未确证；
3. **`.mr` 字节码指令集**：`1B "MRP"` 之后是长度表还是代码段，未系统分析
   （对模拟器实现不构成障碍，但对"重新编译 MRP"是死结）；
4. **数据区里每个 gzip 前的 `uint32`**：与 csize 恒等，冗余存储的目的不明。

## 9. `start.mr` 是通用入口（重要纠错）

早期结论「`dsm_gm.mrp` 用 `start.mr`，普通应用用 `cfunction.ext`」是**错的**。

实测（15 个本地样本 + 在线抽样）：**所有** MRP 包的条目表里都有 `start.mr`，
且 `start_dsm(filename, "start.mr")` 全部返回 0；给普通应用传
`cfunction.ext` 会报

```
[arm] cfunction.ext:1: invalid control char near `char(16)'
[arm] exit de is nil!
[arm] init failed
[vm] start_dsm('box.mrp', 'cfunction.ext') -> -1
```

`cfunction.ext` 是**宿主运行时**（331 KB 裸 ARM 文件，加载到 0x80000），
不是包内入口。`start.mr` 才是包内那段负责初始化的 mythroad 字节码。
启动器 `dsm_gm.mrp` 内部再拉起子应用时由 DSM 层自行决定入口，与宿主无关。

因此 `cli.py` 现在默认用 `probe_entry_ext()` 读条目表判断：有 `start.mr`
就用它，遇到不含该条目的老包才退回 `cfunction.ext`；两种都失败时会用
干净的 VM 换入口重试一次。

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
