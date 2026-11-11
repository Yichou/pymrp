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


def _glyph_mask(font, ch: str):
    """渲染一个字，返回 16x16 的布尔墨迹矩阵（True = 有笔画）。

    做法：用**大字号**（4 倍）在 64x64 的不透明黑底画布上渲染白字，
    再缩到 16x16。

    两个坑：

    * **字号太小**：16px 字号下宋体的汉字只有 ~10px 宽，细笔画在缩放
      时被阈值吃掉，「网」会整个消失、「输」只剩两个方块。必须先用
      64px 渲染再缩。
    * **不要用 SRCALPHA**：半透明画布经 ``smoothscale`` 后 alpha 被平均，
      中心 alpha 也只剩 ~111，阈值很难定。用不透明黑底白字，
      缩放后的灰度就是「覆盖率」，取 50% 灰即半笔画，天然带抗锯齿。
    """
    try:
        import pygame
    except ImportError:  # pragma: no cover
        return None

    big = pygame.Surface((SIZE * 4, SIZE * 4))
    big.fill((0, 0, 0))
    try:
        # 用大字号渲染，保证细笔画在缩放后仍然存在；
        # 加粗一档：宋体的细横/细竖缩到 16px 后只剩 1 个点，
        # 看起来像虚线，真机字库是粗宋体/仿宋，点更实。
        big_font = _big_font(font)
        surf = big_font.render(ch, True, (255, 255, 255))
    except Exception:  # pragma: no cover
        return None
    big.blit(surf, ((SIZE * 4 - surf.get_width()) // 2,
                    (SIZE * 4 - surf.get_height()) // 2))
    small = pygame.transform.smoothscale(big, (SIZE, SIZE))

    try:
        import numpy as np
        buf = np.frombuffer(small.get_buffer(), dtype=np.uint8)
        arr = buf.reshape(SIZE, SIZE, 4)
        gray = arr[:, :, 0].astype(np.uint16) + arr[:, :, 1] + arr[:, :, 2]
        return gray > 384          # 三通道和 > 384 即平均灰度 > 128
    except Exception:  # pragma: no cover - 没有 numpy 时退回逐像素
        mask = [[False] * SIZE for _ in range(SIZE)]
        for y in range(SIZE):
            for x in range(SIZE):
                r, g, b, _a = small.get_at((x, y))
                mask[y][x] = (r + g + b) > 384
        return mask


_BIG_FONTS: dict = {}
_FONT_PATH: str | None = None


def _big_font(font):
    """拿到 4 倍字号的**粗体**大字体（按原字体的路径重建）。

    字号必须够大：16px 下宋体的汉字只有 ~10px 宽，缩放时细笔画会被
    阈值吃掉（「网」整个消失、「输」只剩两个方块）。先用 64px 渲染再缩。
    """
    import pygame
    f = _BIG_FONTS.get(id(font))
    if f is None:
        try:
            f = pygame.font.Font(_FONT_PATH, SIZE * 4) if _FONT_PATH \
                else pygame.font.Font(None, SIZE * 4)
            f.set_bold(True)
        except Exception:  # pragma: no cover
            f = font
        _BIG_FONTS[id(font)] = f
    return f


def _fit_mask(mask, size: int = SIZE):
    """字形墨迹矩阵 -> 居中放到 16x16 画布上。

    大字号（64px）渲染后字形已经基本占满 64x64 画布，缩到 16x16 时
    就是最终字模，**不需要再裁剪放大**——之前那一步会把字形撑成方块
    （「输」变成两个实心方块、「网」整个消失）。

    这里只做居中：字形若小于整格就补边，不缩放。
    """
    try:
        import numpy as np
        arr = np.asarray(mask, dtype=bool)
        ys, xs = np.nonzero(arr)
        if len(ys) == 0:
            return arr
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        sub = arr[y0:y1 + 1, x0:x1 + 1]
        h, w = sub.shape
        if h >= size or w >= size:
            # 已经够大，居中裁剪
            oy = max(0, (h - size) // 2)
            ox = max(0, (w - size) // 2)
            return sub[oy:oy + size, ox:ox + size]
        out = np.zeros((size, size), dtype=bool)
        oy = (size - h) // 2
        ox = (size - w) // 2
        out[oy:oy + h, ox:ox + w] = sub
        return out
    except ImportError:  # pragma: no cover
        return mask


def _mask_to_bytes(mask) -> bytes:
    """16x16 布尔矩阵 -> 1bpp 字模（高位在前）。"""
    buf = bytearray(BYTES_PER_GLYPH)
    try:
        import numpy as np
        arr = np.asarray(mask, dtype=bool)
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
    """把一个字符渲染成 16x16 的 1bpp 字模（高位在前）。"""
    mask = _glyph_mask(font, ch)
    if mask is None:
        return b"\x00" * BYTES_PER_GLYPH
    return _mask_to_bytes(_fit_mask(mask))


def _render_glyphs(font, chars: list[str]) -> list[bytes]:
    """批量渲染一串字符的字模。"""
    out: list[bytes] = []
    blank = b"\x00" * BYTES_PER_GLYPH
    for ch in chars:
        mask = _glyph_mask(font, ch)
        if mask is None:
            out.append(blank)
            continue
        out.append(_mask_to_bytes(_fit_mask(mask)))
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
    """
    import pygame
    pygame.init()

    global _FONT_PATH
    path = font_path
    if path is None:
        for cand in FONT_CANDIDATES:
            if Path(cand).is_file():
                path = cand
                break
    if path is None:
        return b"\x00" * BYTES_PER_GLYPH
    _FONT_PATH = path

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


def ensure_uc2(path: str | Path, font_path: str | None = None,
                log=print) -> Path:
    """确保字库存在；已存在且大小合理就跳过（生成要 ~10 秒）。

    字库内容只跟系统字体有关，字体没变就不用重生成。
    """
    p = Path(path)
    if p.is_file() and p.stat().st_size > 100_000:
        return p
    t0 = None
    try:
        import time
        t0 = time.perf_counter()
    except Exception:  # pragma: no cover
        pass
    try:
        write_uc2(p, font_path)
    except Exception as exc:  # pragma: no cover
        if log:
            log(f"[font] 字库生成失败（应用界面可能显示不出中文）: {exc}")
        return p
    if log and t0 is not None:
        log(f"[font] 已生成 16 点阵字库 {p.name} "
            f"（{p.stat().st_size} 字节，{time.perf_counter() - t0:.1f}s）")
    return p
