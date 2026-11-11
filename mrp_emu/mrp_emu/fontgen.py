"""生成 MTK 的 16 点阵字库（``system/gb16.uc2``）。

为什么要自己造
--------------
2008 年前后的 MTK 功能机把字库放在 ``mythroad/system/gb16.uc2``，
由运行时（``cfunction.ext``）加载后按 ``id * 32`` 偏移取字模：

.. code-block:: c

    /* mrpoid/libm/src/main/jni/src/font/font_sky16_2.c */
    ft_seek(font_sky16_f, id * 32, 0);
    ft_read(font_sky16_f, font_sky16_bitbuf, 32);
    /* 每个字模 16x16 = 256 bit = 32 字节，1bpp，高位在前 */

``system/gb16.uc2``
    MTK 的 16 点阵字库，运行时按 ``id * 32`` 偏移直接取字模。

**优先复用原厂字库**
--------------------
发行包里通常已经带了 MTK 原厂字库（``mythroad/fonts/gb16.uc2``、
``sky16.uc2`` 等，2MB 一个、65536 个字模）。它们是当年烧进固件的
**手工点阵字**，笔画清晰、字形规整，**比任何系统字体缩放出来的结果都强**。
所以本模块的策略是：

1. 先找原厂字库，找到就直接复制到目标路径（``:func:`ensure_uc2`）；
2. 找不到才用系统字体现场生成（宋体 → 微软雅黑），作为兜底。

现场生成这一步曾经踩过大坑：用 64px 粗体渲染再缩到 16x16，缩放会把
相邻笔画**糊成一团黑块**（「帐」「密」「录」全糊）。现在的做法见
:func:`_glyph_mask`。

斯凯服务器停运后这些字库无处可取，真机上的字库又因机型而异。
我们在本地用系统字体渲染出同样的 16x16 点阵，生成一个**能真正显示
中文**的字库 —— 这样古董应用（QQ、浏览器、文件管理器）的中文界面
才不会是一片空白。

索引方式
--------
MTK 的 ``id`` 有两种可能：GB2312 双字节码位（``(hi-0xA1)*94 + (lo-0xA1)``）
或 Unicode 码位。运行时到底用哪种，各家实现不一，**我们把两种索引
都写进同一个文件**：文件前段是 GB 索引区，后段是 Unicode 索引区，
靠文件长度区分（运行时只是 ``seek(id*32)`` 读，读到哪算哪）。

字模数据
--------
1bpp，**高位在前**：第 n 个像素在第 ``n/8`` 字节的第 ``n%8`` 位
（``(128 >> (n % 8)) & buf[n/8]``），行优先，一行 16 像素共 2 字节。
"""

from __future__ import annotations

import shutil
from pathlib import Path

# 候选系统字体（按优先级）
FONT_CANDIDATES = (
    "C:/Windows/Fonts/simsun.ttc",      # 宋体（点阵化最接近当年的字库）
    "C:/Windows/Fonts/msyh.ttc",         # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)

SIZE = 16                      # 字模边长
BYTES_PER_GLYPH = SIZE * SIZE // 8      # 32 字节

# 灰度阈值（0-255 的 alpha 覆盖率）。取 190 左右：字形主体全实，
# 抗锯齿边缘只留一档毛边，和原厂点阵字的观感一致。
INK_THRESHOLD = 190

# 质量自检用的常用汉字：墨迹率明显异常 = 字形糊了或缺笔画
PROBE_CHARS = "帐号密码记隐身登录手机菜单输入确定返回网页主页"


def _glyph_mask(font, ch: str):
    """渲染一个字，返回 16x16 的布尔墨迹矩阵（True = 有笔画）。

    做法：**16px 直接渲染**宋体/雅黑，再取灰度阈值化。

    为什么不能「64px 渲染再缩到 16px」
    --------------------------------
    缩放会让相邻笔画互相渗透，缩完再阈值化，**笔画之间就粘死了**：
    「帐」「密」「录」糊成黑块，「网」整个消失。真机点阵字是逐笔
    设计出来的，不是缩出来的。

    为什么不用大字号
    ----------------
    16px 字号下宋体汉字约 13px 见方，已经接近原厂字库的密度；
    而 64px 缩下来的字，笔画宽度会被放大到 2~3 像素，16x16 根本
    放不下那么多笔画，必然粘连。

    阈值怎么定
    ----------
    ``render(antialias=True)`` 返回 SRCALPHA surface，**抗锯齿信息在
    alpha 通道**（0=无笔画，255=全覆盖），取 190（约 75% 覆盖）能让
    主体笔画实心、边缘保留一档毛边——和原厂点阵字观感接近。
    """
    try:
        import pygame
    except ImportError:  # pragma: no cover
        return None

    try:
        surf = font.render(ch, True, (255, 255, 255))
    except Exception:  # pragma: no cover
        return None
    if surf.get_width() == 0 or surf.get_height() == 0:
        return None

    try:
        import numpy as np
        # **关键**：``font.render(antialias=True)`` 返回的是 SRCALPHA
        # surface，RGB 全是 255，抗锯齿信息全在 **alpha 通道** 里。
        # 直接读 RGB 会得到「整块全白」——阈值化后每个字都是实心方块。
        # 用 tobytes 取 RGBA 比 get_buffer 安全：后者受 surface pitch
        # 对齐影响，尺寸对不上时 reshape 会失败。
        raw = pygame.image.tobytes(surf, "RGBA")
        arr = np.frombuffer(raw, dtype=np.uint8)
        arr = arr.reshape(surf.get_height(), surf.get_width(), 4)
        gray = arr[:, :, 3].astype(np.uint16)   # alpha = 笔画覆盖率
        mask = gray > INK_THRESHOLD
    except Exception:  # pragma: no cover - 没有 numpy 时退回逐像素
        mask = [[False] * surf.get_width() for _ in range(surf.get_height())]
        for y in range(surf.get_height()):
            for x in range(surf.get_width()):
                r, g, b, a = surf.get_at((x, y))
                mask[y][x] = a > INK_THRESHOLD

    # 居中放进 16x16：按墨迹 bbox 裁剪，保留原始比例，不拉伸。
    return _fit_mask(mask)


def _fit_mask(mask, size: int = SIZE):
    """字形墨迹矩阵 -> **严格 16x16** 画布（居中，不缩放）。

    按墨迹 bbox 裁到最小外接矩形，再居中放进 16x16，**不缩放**。
    缩放是糊字的元凶，这里只做裁剪和居中。

    .. important::
       返回值**必须正好是 (size, size)**。1bpp 字模的位序是
       ``n = y * 16 + x``，行宽不是 16 时位序与运行时的取位约定对不上，
       字形会变成乱码笔画。所以这里保证输出恒为 16x16。
    """
    try:
        import numpy as np
        arr = np.asarray(mask, dtype=bool)
        out = np.zeros((size, size), dtype=bool)
        if arr.ndim != 2 or arr.size == 0:
            return out
        ys, xs = np.nonzero(arr)
        if len(ys) == 0:
            return out
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        sub = arr[y0:y1 + 1, x0:x1 + 1]
        h, w = sub.shape
        if h > size:                      # 超高：居中裁剪
            oy = (h - size) // 2
            sub = sub[oy:oy + size]
            h = size
        if w > size:                      # 超宽：居中裁剪
            ox = (w - size) // 2
            sub = sub[:, ox:ox + size]
            w = size
        oy = (size - h) // 2
        ox = (size - w) // 2
        out[oy:oy + h, ox:ox + w] = sub
        return out
    except ImportError:  # pragma: no cover
        return mask


def _mask_to_bytes(mask) -> bytes:
    """16x16 布尔矩阵 -> 1bpp 字模（高位在前）。

    位序：**按行展开**，第 n 个像素在第 ``n//8`` 字节的第 ``n%8`` 位
    （``0x80 >> (n % 8)``），n = ``y * 16 + x``。

    .. important::
       入参**必须正好是 16x16**。若行宽不是 16（比如裁剪后剩 14 列），
       flatten 出来的位序与运行时按 ``y*16+x`` 取位的约定对不上，
       字形会变成一堆乱码笔画。所以这里先补齐/裁到 16x16 再转换。
    """
    buf = bytearray(BYTES_PER_GLYPH)
    try:
        import numpy as np
        arr = np.asarray(mask, dtype=bool)
        if arr.shape != (SIZE, SIZE):
            fixed = np.zeros((SIZE, SIZE), dtype=bool)
            h = min(SIZE, arr.shape[0])
            w = min(SIZE, arr.shape[1]) if arr.ndim == 2 else 0
            if w:
                fixed[:h, :w] = arr[:h, :w]
            arr = fixed
        bits = arr.reshape(-1)
        for n in range(min(len(bits), SIZE * SIZE)):
            if bits[n]:
                buf[n // 8] |= 0x80 >> (n % 8)
        return bytes(buf)
    except ImportError:  # pragma: no cover
        for y in range(SIZE):
            for x in range(SIZE):
                if mask[y][x]:
                    n = y * SIZE + x
                    buf[n // 8] |= 0x80 >> (n % 8)
        return bytes(buf)


def _render_glyph(font, ch: str) -> bytes:
    """把一个字符渲染成 16x16 的 1bpp 字模（高位在前）。

    ``_glyph_mask`` 内部已经做过 ``_fit_mask``（裁剪 + 居中），这里
    **不能再裁一次** —— 二次裁剪会把行宽搞成 14/15，位序就乱了。
    """
    mask = _glyph_mask(font, ch)
    if mask is None:
        return b"\x00" * BYTES_PER_GLYPH
    return _mask_to_bytes(mask)


def _render_glyphs(font, chars: list[str]) -> list[bytes]:
    """批量渲染一串字符的字模。

    与 :func:`_render_glyph` 一样，``_glyph_mask`` 已含居中裁剪，
    这里**不再二次裁剪**。
    """
    out: list[bytes] = []
    blank = b"\x00" * BYTES_PER_GLYPH
    for ch in chars:
        mask = _glyph_mask(font, ch)
        if mask is None:
            out.append(blank)
            continue
        out.append(_mask_to_bytes(mask))
    return out


def build_uc2(include_gb: bool = False, include_unicode: bool = True,
              font_path: str | None = None,
              layout: str = "unicode-first") -> bytes:
    """生成 ``gb16.uc2`` 的完整内容。

    运行时是 ``seek(id * 32)`` 直接线性取字模，**没有偏移表**，
    所以「id 是什么」决定了字库怎么排。两种可能：

    * **Unicode**：id = 码位（``0x4E2D`` 表示「中」）；
    * **GB2312**：id = ``(hi-0xA1)*94 + (lo-0xA1)``。

    厂商实现不统一，我们把两区都生成，但**它们会互相错位**——
    只能二选一放在正确的位置上。因此这里按 ``layout`` 排布：

    * ``unicode-first``：Unicode 区在前（id = 码位）；
    * ``gb-first``：GB 区在前（id = GB 下标）。

    实测本仓库的 ``cfunction.ext`` 用的是 **Unicode 码位**（见 docs/20：
    ``unicode-first`` 布局下「输入网址」「搜索」「手机网站」全部清晰可读，
    ``gb-first`` 布局下同一批字错乱成别的字）。

    .. note::
       这条路径只在**找不到原厂字库**时才会走。发行包自带
       ``mythroad/fonts/gb16.uc2``（原厂手工点阵字，清晰度远高于
       任何系统字体缩放结果），:func:`ensure_uc2` 会优先复制它。
    """
    import pygame
    pygame.init()

    path = font_path
    if path is None:
        for cand in FONT_CANDIDATES:
            if Path(cand).is_file():
                path = cand
                break
    if path is None:
        return b"\x00" * BYTES_PER_GLYPH

    font = pygame.font.Font(path, SIZE)
    blank = b"\x00" * BYTES_PER_GLYPH

    def gb_block() -> bytes:
        chars: list[str] = []
        blank = "\x00"
        for hi in range(0xA1, 0xA1 + 94):
            for lo in range(0xA1, 0xA1 + 94):
                try:
                    chars.append(bytes([hi, lo]).decode("gb2312"))
                except UnicodeDecodeError:
                    chars.append(blank)
        return b"".join(_render_glyphs(font, chars))

    def uni_block() -> bytes:
        """Unicode 区（下标 = 码位）。

        只渲染真正可能用到的区间：ASCII/符号区（0x0020-0x2E80）与
        汉字区（0x4E00-0x9FFF）。中间的 CJK 兼容区、扩展区等一律留空，
        既省掉大半渲染时间，也够 MTK 老应用用了。
        """
        chars: list[str] = []
        blank = "\x00"
        for cp in range(0x0000, 0xA000):
            if cp < 0x0020:
                chars.append(blank)
            elif cp <= 0x2E80 or 0x4E00 <= cp <= 0x9FFF:
                chars.append(chr(cp))
            else:
                chars.append(blank)
        return b"".join(_render_glyphs(font, chars))

    if layout == "gb-first":
        out = bytearray()
        if include_gb:
            out += gb_block()
        if include_unicode:
            out += uni_block()
    else:
        out = bytearray()
        if include_unicode:
            out += uni_block()
        if include_gb:
            out += gb_block()
    return bytes(out)


def write_uc2(path: str | Path, font_path: str | None = None) -> Path:
    """生成并写出字库文件，返回路径。"""
    data = build_uc2(font_path=font_path)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


# ---------------------------------------------------------------- 原厂字库
# 发行包（vmrp 解压后的 runtime）里通常带着 MTK 原厂字库：
#   mythroad/fonts/gb16.uc2   2MB / 65536 个字模
#   mythroad/fonts/sky16.uc2  同上，MTK 自研「天语」风格
#   mythroad/fonts/gb12v2.uc2 12 点阵
# 它们是当年烧进固件的手工点阵字，清晰度远高于系统字体缩放的结果。
# 优先级：gb16 > sky16（QQ 等应用的 DSM 默认读 system/gb16.uc2）。
FACTORY_FONT_NAMES = ("gb16.uc2", "sky16.uc2")


def find_factory_font(search_dirs) -> Path | None:
    """在给定目录里找原厂 16 点阵字库，返回第一个命中的路径。"""
    for d in search_dirs:
        base = Path(d)
        if not base.is_dir():
            continue
        for name in FACTORY_FONT_NAMES:
            p = base / name
            if p.is_file() and p.stat().st_size >= 1024 * 1024:
                return p
    return None


def ink_ratio(data: bytes, ch: str) -> float:
    """某个字模的墨迹率（黑像素占比），-1 表示没有字模。

    质量自检用：糊掉的字库笔画粘连，墨迹率会异常高（0.5+）；
    缺笔画则异常低（<0.05）。
    """
    cp = ord(ch)
    off = cp * BYTES_PER_GLYPH
    if off + BYTES_PER_GLYPH > len(data):
        return -1.0
    blob = data[off:off + BYTES_PER_GLYPH]
    n = 0
    for i in range(SIZE * SIZE):
        if blob[i // 8] & (0x80 >> (i % 8)):
            n += 1
    return n / (SIZE * SIZE)


def check_font_quality(data: bytes) -> tuple[bool, str]:
    """检查字库质量，返回 (是否合格, 说明)。

    判据来自实测（见 docs/21）：
      * 原厂 gb16/sky16：常用汉字墨迹率 avg ≈ 0.19~0.24，max < 0.32；
      * 早期「64px 粗体缩放」自造版：avg ≈ 0.37，max 达 0.59（糊成黑块）。
    """
    if len(data) < 100_000:
        return False, f"字库太小（{len(data)} 字节）"
    ratios = [ink_ratio(data, ch) for ch in PROBE_CHARS]
    valid = [r for r in ratios if r >= 0]
    if len(valid) < len(PROBE_CHARS) * 0.8:
        return False, f"常用汉字字模缺失（{len(valid)}/{len(PROBE_CHARS)}）"
    avg = sum(valid) / len(valid)
    mx = max(valid)
    if avg > 0.32 or mx > 0.45:
        return False, f"笔画粘连（墨迹率 avg={avg:.2f} max={mx:.2f}，阈值 0.32/0.45）"
    if avg < 0.08:
        return False, f"笔画过稀（墨迹率 avg={avg:.2f}）"
    return True, f"墨迹率 avg={avg:.2f} max={mx:.2f}"


def check_font_file(path: str | Path) -> tuple[bool, str]:
    """按文件检查字库质量——**只读需要的字节**，不整读 2MB。

    字库有 65536 个字模，质量自检只需要 20 来个常用汉字，
    整读 2MB 在每次启动时纯属浪费。
    """
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError as exc:
        return False, f"无法读取（{exc}）"
    if size < 100_000:
        return False, f"字库太小（{size} 字节）"
    ratios: list[float] = []
    try:
        with p.open("rb") as fh:
            for ch in PROBE_CHARS:
                off = ord(ch) * BYTES_PER_GLYPH
                if off + BYTES_PER_GLYPH > size:
                    continue
                fh.seek(off)
                blob = fh.read(BYTES_PER_GLYPH)
                n = sum(1 for i in range(SIZE * SIZE)
                        if blob[i // 8] & (0x80 >> (i % 8)))
                ratios.append(n / (SIZE * SIZE))
    except OSError as exc:
        return False, f"读取失败（{exc}）"
    if len(ratios) < len(PROBE_CHARS) * 0.8:
        return False, f"常用汉字字模缺失（{len(ratios)}/{len(PROBE_CHARS)}）"
    avg = sum(ratios) / len(ratios)
    mx = max(ratios)
    if avg > 0.32 or mx > 0.45:
        return False, f"笔画粘连（墨迹率 avg={avg:.2f} max={mx:.2f}，阈值 0.32/0.45）"
    if avg < 0.08:
        return False, f"笔画过稀（墨迹率 avg={avg:.2f}）"
    return True, f"墨迹率 avg={avg:.2f} max={mx:.2f}"


def ensure_uc2(path: str | Path, font_path: str | None = None,
                log=print, factory_dirs=None) -> Path:
    """确保目标路径有一份可用的 16 点阵字库。

    优先级：

    1. **目标已存在且质量合格** -> 直接用（省掉几秒生成时间）；
    2. **发行包里有原厂字库** -> 复制过来（最清晰，且与真机一致）；
    3. **用系统字体现场生成**（宋体 -> 微软雅黑）-> 兜底。

    .. note::
       第 1 步会做**质量自检**：早期版本用「64px 粗体缩放」生成的字库
       笔画粘连成一团，用户界面上表现为「中文糊成一坨」。光看文件大小
       判断不出来（1310720 字节看着挺正常），必须抽查墨迹率。
    """
    p = Path(path)
    t0 = None
    try:
        import time
        t0 = time.perf_counter()
    except Exception:  # pragma: no cover
        pass

    # --- 1. 目标已存在？
    if p.is_file() and p.stat().st_size > 100_000:
        try:
            ok, why = check_font_file(p)
        except Exception:  # pragma: no cover
            ok, why = True, "读取失败，按合格处理"
        if ok:
            return p
        if log:
            log(f"[font] 现有字库 {p.name} 质量不合格（{why}），重新准备")

    # --- 2. 优先用原厂字库
    if factory_dirs:
        src = find_factory_font(factory_dirs)
        if src is not None:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                # shutil.copy 比 read_bytes+write 省一次 2MB 内存拷贝
                shutil.copyfile(src, p)
                if log:
                    log(f"[font] 已采用原厂字库 {src.name} -> {p.name}"
                        f"（{p.stat().st_size} 字节）")
                return p
            except OSError as exc:  # pragma: no cover
                if log:
                    log(f"[font] 复制原厂字库失败（{exc}），改为本地生成")

    # --- 3. 本地生成
    try:
        write_uc2(p, font_path)
    except Exception as exc:  # pragma: no cover
        if log:
            log(f"[font] 字库生成失败（应用界面可能显示不出中文）: {exc}")
        return p
    if log and t0 is not None:
        note = ""
        try:
            ok, why = check_font_file(p)
            note = f"，自检{'通过' if ok else '未通过'}（{why}）"
        except Exception:  # pragma: no cover
            pass
        log(f"[font] 已生成 16 点阵字库 {p.name} "
            f"（{p.stat().st_size} 字节，{time.perf_counter() - t0:.1f}s{note}）")
    return p
