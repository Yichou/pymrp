"""图形层：RGB565 帧缓冲 + 叠加层。

MRP 的屏幕就是一块 240x320 的 RGB565 内存。真机上它是系统显存，
这里由 Python 分配，并把地址写进 mr_table 的 mr_screenBuf 槽位，
于是 MRP 侧 ldr 到的指针直接指向这块内存 —— 它怎么画，我们就怎么读。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pygame

from .consts import SCREEN_HEIGHT, SCREEN_WIDTH


# ---------------------------------------------------------------- 颜色工具
def rgb565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def from565(v: int) -> tuple[int, int, int]:
    r = ((v >> 11) & 0x1F) * 255 // 31
    g = ((v >> 5) & 0x3F) * 255 // 63
    b = (v & 0x1F) * 255 // 31
    return r, g, b


BLACK = rgb565(0, 0, 0)
WHITE = rgb565(255, 255, 255)

# ---------------------------------------------------------------- 字体
# 不用 pygame.font.match_font / SysFont：在部分 Windows 上它们枚举字体注册表
# 时会因非字符串值抛出 TypeError。直接探测字体文件更稳。
_FONT_CANDIDATES: dict[str, list[str]] = {
    "microsoftyahei": [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ],
    "simhei": ["C:/Windows/Fonts/simhei.ttf"],
    "simsun": ["C:/Windows/Fonts/simsun.ttc"],
    "arial": [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}

_font_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}


def get_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    key = (name.lower(), size, bold)
    cached = _font_cache.get(key)
    if cached is not None:
        return cached

    font: pygame.font.Font | None = None
    for path in _FONT_CANDIDATES.get(name.lower(), []):
        if Path(path).is_file():
            try:
                font = pygame.font.Font(path, size)
                break
            except (OSError, pygame.error):
                continue
    if font is None:
        font = pygame.font.Font(None, size)
    if bold:
        font.set_bold(True)
    _font_cache[key] = font
    return font


class Gfx:
    def __init__(self, mem, fb_addr: int | None = None) -> None:
        """``fb_addr`` 为 None 时自己分配帧缓冲。

        自编译 mythroad VM 那条路上，帧缓冲是 **mythroad 自己分配的**
        （全局变量 ``mr_screenBuf``），我们只能绑定上去 —— 见
        ``mythroad_vm.MythroadVm.screen_buf_addr``。
        """
        self.mem = mem
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT
        self.size_bytes = self.w * self.h * 2

        if fb_addr is None:
            self.fb_addr = mem.malloc(self.size_bytes)
            mem.memset(self.fb_addr, 0, self.size_bytes)
        else:
            self.fb_addr = fb_addr
            self.owns_fb = False
        self.owns_fb = True if fb_addr is None else False

        self.overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 0))
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}
        self.frames = 0

    # ------------------------------------------------------------ 帧缓冲
    def raw(self) -> bytes:
        return self.mem.read(self.fb_addr, self.size_bytes)

    def array(self) -> np.ndarray:
        """返回 (h, w) 的 uint16 视图（只读快照）。"""
        return np.frombuffer(self.raw(), dtype="<u2").reshape(self.h, self.w)

    def clear(self, color: int = BLACK) -> None:
        px = np.full(self.w * self.h, color, dtype="<u2")
        self.mem.write(self.fb_addr, px.tobytes())

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        arr = self.array().copy()
        arr[y0:y1, x0:x1] = color
        self.mem.write(self.fb_addr, arr.tobytes())

    # ------------------------------------------------------------ MRP drawBitmap
    def draw_bitmap(self, bmp_addr: int, x: int, y: int, w: int, h: int) -> None:
        """对应 guiDrawBitmap：把一段 RGB565 位图贴到屏幕，带裁剪。"""
        if w <= 0 or h <= 0 or not self.mem.valid(bmp_addr, w * h * 2):
            return
        sx0, sy0 = max(0, -x), max(0, -y)
        dx0, dy0 = max(0, x), max(0, y)
        cw = min(w - sx0, self.w - dx0)
        ch = min(h - sy0, self.h - dy0)
        if cw <= 0 or ch <= 0:
            return

        src = np.frombuffer(self.mem.read(bmp_addr, w * h * 2), dtype="<u2").reshape(h, w)
        dst = self.array().copy()
        dst[dy0:dy0 + ch, dx0:dx0 + cw] = src[sy0:sy0 + ch, sx0:sx0 + cw]
        self.mem.write(self.fb_addr, dst.tobytes())

    def refresh_rect(self, buf_addr: int, x: int, y: int,
                     w: int, h: int) -> bool:
        """把离屏「全屏缓冲」的脏矩形同步到帧缓冲（DSM 刷屏语义）。

        来源：mrpoid ``dsm.c::mr_drawBitmap`` -> ``emulator.c::emu_bitmapToscreen``

        .. code-block:: c

            for (i = y; i <= y1; i++)
                memcpy(p + sw*i + x, data + sw*i + x, w*2);

        也就是说 ``bmp`` 是 **240x320 整屏缓冲的基址**，源行跨度是屏宽
        （不是 ``w``），x/y 既是源矩形起点也是目标位置。mythroad/DSM 把 UI
        画在自己的离屏缓冲里，滚动列表时只同步变脏的那几行。

        这里若按紧凑 ``w x h`` 位图去读，就会把屏幕左上角（标题栏）贴到
        y=61/90/119 的列表行上 —— 正是 RX 管理器「重复标题栏 + 蓝色斜纹」
        花屏的根因。整屏刷新 (0,0,240,320) 时两种语义恰好等价，所以静止
        首帧正常、一滚动就花，非常有迷惑性。

        返回 True 表示按全屏 stride 同步成功；源缓冲不足整屏时退化成
        :meth:`draw_bitmap` 的紧凑语义并返回 False（兼容个别 DSM 变体）。
        """
        W, H = self.w, self.h
        if not buf_addr or w <= 0 or h <= 0:
            return False
        if buf_addr == self.fb_addr:
            return True                      # 源就是屏幕本身，内容已在屏上

        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return False
        if not self.mem.valid(buf_addr, W * H * 2):
            self.draw_bitmap(buf_addr, x, y, w, h)
            return False

        rows = y1 - y0
        span = rows * W * 2
        src = np.frombuffer(self.mem.read(buf_addr + y0 * W * 2, span),
                            dtype="<u2").reshape(rows, W)
        dst = np.frombuffer(self.mem.read(self.fb_addr + y0 * W * 2, span),
                            dtype="<u2").reshape(rows, W).copy()
        dst[:, x0:x1] = src[:, x0:x1]
        self.mem.write(self.fb_addr + y0 * W * 2, dst.tobytes())
        return True

    # ------------------------------------------------------------ 渲染
    def surface(self) -> pygame.Surface:
        a = self.array()
        r = (((a >> 11) & 0x1F) << 3).astype(np.uint8)
        g = (((a >> 5) & 0x3F) << 2).astype(np.uint8)
        b = ((a & 0x1F) << 3).astype(np.uint8)
        rgb = np.dstack((r, g, b))
        surf = pygame.image.frombuffer(rgb.tobytes(), (self.w, self.h), "RGB")
        surf.blit(self.overlay, (0, 0))
        self.frames += 1
        return surf

    # ------------------------------------------------------------ 叠加层
    def overlay_clear(self) -> None:
        self.overlay.fill((0, 0, 0, 0))

    def font(self, name: str, size: int) -> pygame.font.Font:
        return get_font(name, size)

    def text(self, txt: str, x: int, y: int, color=(255, 255, 255),
             size: int = 12, font: str = "microsoftyahei", shadow: bool = True) -> None:
        f = self.font(font, size)
        if shadow:
            s = f.render(txt, True, (0, 0, 0))
            self.overlay.blit(s, (x + 1, y + 1))
        img = f.render(txt, True, color)
        self.overlay.blit(img, (x, y))

    def text_right(self, txt: str, right: int, y: int, color=(255, 255, 255),
                   size: int = 12, font: str = "microsoftyahei") -> None:
        f = self.font(font, size)
        img = f.render(txt, True, color)
        self.overlay.blit(img, (right - img.get_width(), y))

    def text_center(self, txt: str, cx: int, y: int, color=(255, 255, 255),
                    size: int = 12, font: str = "microsoftyahei") -> None:
        f = self.font(font, size)
        img = f.render(txt, True, color)
        self.overlay.blit(img, (cx - img.get_width() // 2, y))

    def status_bar(self, title: str = "中国移动", time_str: str = "") -> None:
        """MTK 风格状态栏：左侧运营商，右侧信号/电量/时间。"""
        pygame.draw.rect(self.overlay, (28, 32, 38, 235), (0, 0, self.w, 18))
        self.text(title, 4, 2, (230, 236, 245), size=12)
        if time_str:
            self.text_right(time_str, self.w - 26, 2, (230, 236, 245), size=12)
        # 信号格
        for i in range(4):
            hgt = 3 + i * 2
            pygame.draw.rect(self.overlay, (150, 220, 160),
                             (self.w - 22 + i * 4, 14 - hgt, 3, hgt))
        # 电量
        pygame.draw.rect(self.overlay, (200, 205, 210), (self.w - 6, 5, 5, 9), 1)
        pygame.draw.rect(self.overlay, (150, 220, 160), (self.w - 5, 6, 3, 7))

    def soft_keys(self, left: str = "", right: str = "") -> None:
        """底部左右软键提示条。"""
        pygame.draw.rect(self.overlay, (28, 32, 38, 235), (0, self.h - 18, self.w, 18))
        if left:
            self.text(left, 6, self.h - 17, (235, 240, 250), size=12)
        if right:
            self.text_right(right, self.w - 6, self.h - 17, (235, 240, 250), size=12)

    # ------------------------------------------------------------ 导出
    def screenshot(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self.surface(), str(p))
        return p
