"""MTK 真机系统界面：开机 → 待机桌面 → 九宫格菜单 → 游戏中心。

这一层是**宿主 UI**（Python 直接画 240x320 的屏幕内容），不是 MRP 应用。
它输出一张 240x320 的 Surface 交给 PhoneUI 贴到机壳屏幕里，所以点击坐标
与 MRP 世界坐标一致，鼠标点图标和点游戏列表都是原生直觉操作。

页面:
    boot         开机动画
    home         待机桌面（信号/电量/时钟/壁纸/游戏中心快捷图标）
    menu         九宫格主菜单（游戏中心、应用列表、…）
    gamecenter   在线列表 / 本地列表（分页、搜索、下载进度、一键启动）
"""

from __future__ import annotations

import math
import time
from typing import Callable

import pygame

from ..gfx import get_font

W, H = 240, 320
SB_H = 18          # 状态栏
TB_H = 22          # 标题栏 18..40
TAB_Y, TAB_H = 40, 20
LIST_Y, LIST_END = 60, 282
ROW_H = 44
ROWS = (LIST_END - LIST_Y) // ROW_H          # 5 行
INFO_Y, INFO_H = 282, 18
SOFT_Y, SOFT_H = 300, 20

# 配色：2008 年 MTK 功能机常见的深蓝 + 橙色高亮
C_BG_TOP = (11, 32, 58)
C_BG_BOTTOM = (4, 14, 28)
C_TITLE_A = (20, 74, 132)
C_TITLE_B = (9, 40, 78)
C_ROW_A = (17, 46, 80)
C_ROW_B = (12, 34, 62)
C_SEL_A = (44, 112, 180)
C_SEL_B = (24, 74, 132)
C_TEXT = (238, 246, 255)
C_DIM = (146, 174, 205)
C_ACCENT = (255, 174, 58)
C_GREEN = (92, 214, 132)
C_RED = (240, 104, 96)
C_SOFT = (8, 26, 48)

ICON_COLORS = [
    (255, 158, 44), (66, 192, 122), (62, 155, 232),
    (155, 107, 232), (240, 96, 90), (58, 190, 198),
    (232, 132, 168), (150, 190, 70), (96, 132, 224),
]

MENU_ITEMS = [
    ("游戏中心", "game", 0),
    ("应用列表", "apps", 2),
    ("我的收藏", "star", 4),
    ("多媒体", "media", 1),
    ("通讯录", "book", 5),
    ("信息", "msg", 6),
    ("设置", "cfg", 8),
    ("日历", "cal", 3),
    ("工具箱", "tool", 7),
]


def _font(size: int, bold: bool = False, family: str = "microsoftyahei"):
    return get_font(family, size, bold)


def _fit(text: str, font, max_w: int) -> str:
    """按像素宽度截断，超长加省略号。"""
    if font.size(text)[0] <= max_w:
        return text
    out = ""
    for ch in text:
        if font.size(out + ch + "…")[0] > max_w:
            break
        out += ch
    return out + "…"


def _text(surf, text, x, y, size=12, color=C_TEXT, bold=False,
          align="left", family="microsoftyahei", max_w: int | None = None):
    f = _font(size, bold, family)
    s = _fit(str(text), f, max_w) if max_w else str(text)
    img = f.render(s, True, color)
    if align == "center":
        x -= img.get_width() // 2
    elif align == "right":
        x -= img.get_width()
    surf.blit(img, (x, y))
    return img.get_width()


def _vgrad(surf, rect, c1, c2):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        pygame.draw.line(surf, c, (x, y + i), (x + w, y + i))


def _panel(surf, rect, fill, border=None, radius=6, width=1):
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border, rect, width=width, border_radius=radius)


def _signal(surf, x, y, color=C_TEXT):
    for i in range(5):
        hh = 3 + i * 2
        pygame.draw.rect(surf, color if i < 4 else (70, 92, 120),
                         (x + i * 4, y + 11 - hh, 3, hh))


def _battery(surf, x, y, level=0.75, color=C_TEXT):
    pygame.draw.rect(surf, color, (x, y, 16, 8), width=1)
    pygame.draw.rect(surf, color, (x + 16, y + 2, 2, 4))
    pygame.draw.rect(surf, color, (x + 2, y + 2, int(12 * level), 4))


class Launcher:
    """系统 UI 状态机。耗时操作全部委托给 Catalog 的后台线程。"""

    def __init__(self, catalog, log=print, start_page: str = "boot") -> None:
        self.cat = catalog
        self.log = log
        self.page = start_page
        self.boot_t = 0.0
        self.tab = 0                 # 0=在线 1=本地
        self.sel = 0
        self.top = 0
        self.menu_sel = 0
        self.search = ""
        self.searching = False
        self.toast_text = ""
        self.toast_left = 0.0
        self.t = 0.0
        self.on_launch: Callable[[object], None] | None = None
        self.on_exit: Callable[[], None] | None = None
        self._bg: dict[str, pygame.Surface] = {}
        self._icon_cache: dict[tuple, pygame.Surface] = {}
        self.cat.start_refresh()     # 首次启动就在后台把在线列表拉回来
        self.cat.scan_local()

    # ------------------------------------------------------------ 导航
    def go(self, page: str) -> None:
        self.page = page
        self.searching = False
        if page == "gamecenter":
            self.sel = 0
            self.top = 0
            self.cat.start_refresh()   # 缓存命中会立刻返回，不会重复联网

    def toast(self, text: str, seconds: float = 2.2) -> None:
        self.toast_text = text
        self.toast_left = seconds

    # ------------------------------------------------------------ 列表数据
    def items(self) -> list:
        src = self.cat.online_items if self.tab == 0 else self.cat.local_items
        q = self.search.strip().lower()
        if q:
            src = [m for m in src
                   if q in m.label.lower() or q in m.file.lower()
                   or q in m.vendor.lower() or q in m.desc.lower()]
        return src

    def current(self):
        items = self.items()
        if not items:
            return None
        return items[max(0, min(self.sel, len(items) - 1))]

    def _scroll(self, delta: int) -> None:
        items = self.items()
        if not items:
            return
        self.sel = max(0, min(len(items) - 1, self.sel + delta))
        if self.sel < self.top:
            self.top = self.sel
        elif self.sel >= self.top + ROWS:
            self.top = self.sel - ROWS + 1

    # ------------------------------------------------------------ 事件
    def tick(self, dt: float) -> None:
        self.t += dt
        if self.page == "boot":
            self.boot_t += dt
            if self.boot_t > 1.5:
                self.go("home")
        if self.toast_left > 0:
            self.toast_left -= dt

        for kind, payload in self.cat.poll():
            if kind == "online_cached":
                pass                      # 命中本地 JSON 缓存，静默
            elif kind == "online_ready":
                self.toast(f"在线列表已更新 · {payload} 个应用")
            elif kind == "online_error":
                self.toast(f"在线列表获取失败：{str(payload)[:28]}")
            elif kind == "download_ready":
                item = self._by_file(str(payload))
                if item is not None and self.on_launch:
                    self.toast(f"启动 {item.label}")
                    self.on_launch(item)
            elif kind == "download_error":
                name, err = payload
                self.toast(f"下载失败：{str(err)[:26]}", 3.0)

    def _by_file(self, name: str):
        for m in self.cat.online_items:
            if m.file == name:
                return m
        for m in self.cat.local_items:
            if m.file == name:
                return m
        return None

    def open_current(self) -> None:
        item = self.current()
        if item is None:
            return
        if item.source == "online":
            p = self.cat.get_progress(item.file)
            if p.get("state") == "downloading":
                self.toast("正在下载，请稍候…")
                return
            if self.cat.find_local_file(item.file):
                item.downloaded = True
                item.path = str(self.cat.find_local_file(item.file))
                if self.on_launch:
                    self.on_launch(item)
                return
            self.toast(f"正在下载 {item.label}…", 3.0)
            self.cat.start_download(item)
        else:
            if self.on_launch:
                self.on_launch(item)

    def handle_text(self, ch: str) -> None:
        if self.searching and ch.isprintable() and len(self.search) < 24:
            self.search += ch
            self.sel = 0
            self.top = 0

    def handle_key(self, name: str) -> bool:
        """返回 True 表示该按键已被系统 UI 消费（不要转给虚拟机）。"""
        if self.page == "boot":
            self.go("home")
            return True

        if self.page == "home":
            if name == "SOFT_L" or name == "SELECT":
                self.go("menu")
            elif name == "SOFT_R":
                self.go("gamecenter")
            elif name == "END":
                if self.on_exit:
                    self.on_exit()
            elif name in ("*", "0"):
                self.toast("PymRP · MTK6225 · 240x320")
            return True

        if self.page == "menu":
            if name == "UP":
                self.menu_sel = (self.menu_sel - 3) % 9
            elif name == "DOWN":
                self.menu_sel = (self.menu_sel + 3) % 9
            elif name == "LEFT":
                self.menu_sel = (self.menu_sel - 1) % 9
            elif name == "RIGHT":
                self.menu_sel = (self.menu_sel + 1) % 9
            elif name in ("SELECT", "SOFT_L"):
                self._activate_menu(self.menu_sel)
            elif name in ("END", "SOFT_R", "CLEAR"):
                self.go("home")
            elif name == "*":
                self.go("gamecenter")
            return True

        # ---- 游戏中心
        if self.searching:
            if name == "CLEAR" or name == "BACKSPACE":
                self.search = self.search[:-1]
                self.sel = self.top = 0
            elif name in ("SELECT", "ENTER"):
                self.searching = False
                self.open_current()
            elif name == "END":
                self.searching = False
                self.search = ""
                self.sel = self.top = 0
            elif name in ("UP", "DOWN"):
                self._scroll(-1 if name == "UP" else 1)
            return True

        if name == "UP":
            self._scroll(-1)
        elif name == "DOWN":
            self._scroll(1)
        elif name == "LEFT":
            self.tab = 0
            self.sel = self.top = 0
        elif name == "RIGHT":
            self.tab = 1
            self.sel = self.top = 0
        elif name == "9":
            self._scroll(-ROWS)
        elif name == "3":
            self._scroll(ROWS)
        elif name in ("SELECT", "SOFT_L", "ENTER"):
            self.open_current()
        elif name in ("*", "#"):
            self.searching = True
            self.search = ""
            self.sel = self.top = 0
            self.toast("输入关键字过滤，按确定搜索")
        elif name in ("END", "SOFT_R", "CLEAR"):
            self.go("menu")
        return True

    def _activate_menu(self, idx: int) -> None:
        label = MENU_ITEMS[idx][0]
        if idx == 0:
            self.go("gamecenter")
        elif idx == 1:
            # 真实 MRP 启动器（应用列表），交给宿主直接启动
            if self.on_launch:
                from ..catalog import MrpMeta
                p = self.cat.find_local_file("dsm_gm.mrp")
                if p:
                    self.on_launch(MrpMeta(
                        file="dsm_gm.mrp", title="应用列表", vendor="杭州斯凯",
                        source="local", path=str(p), size=p.stat().st_size,
                        downloaded=True))
                else:
                    self.toast("运行环境里没有 dsm_gm.mrp")
        else:
            self.toast(f"「{label}」功能开发中")

    def handle_click(self, sx: int, sy: int) -> bool:
        """屏幕坐标点击。返回是否消费。"""
        if self.page == "boot":
            self.go("home")
            return True
        if self.page == "home":
            if sy >= SOFT_Y:
                self.go("menu" if sx < W // 2 else "gamecenter")
            elif 96 <= sy <= 176:      # 中央快捷图标区
                self.go("gamecenter")
            else:
                self.go("menu")
            return True
        if self.page == "menu":
            if sy >= SOFT_Y:
                if sx < W // 2:
                    self._activate_menu(self.menu_sel)
                else:
                    self.go("home")
                return True
            if TAB_Y <= sy < 266:
                gx, gy = (sx - 8) // 74, (sy - 44) // 74
                if 0 <= gx < 3 and 0 <= gy < 3:
                    idx = gy * 3 + gx
                    self.menu_sel = idx
                    self._activate_menu(idx)     # 单击图标直接打开
                return True
            return True

        # 游戏中心
        if sy < TAB_Y + TAB_H:
            if sy >= TAB_Y:            # Tab 条
                self.tab = 0 if sx < W // 2 else 1
                self.sel = self.top = 0
            elif sx > 190:             # 标题栏放大镜
                self.searching = True
                self.search = ""
                self.toast("输入关键字过滤")
            return True
        if sy >= SOFT_Y:
            if sx < W // 2:
                self.open_current()
            else:
                self.go("menu")
            return True
        if LIST_Y <= sy < LIST_END:
            row = (sy - LIST_Y) // ROW_H
            idx = self.top + row
            items = self.items()
            if 0 <= idx < len(items):
                self.sel = idx
                self.open_current()               # 单击列表项 = 直接玩
            return True
        return True

    # ------------------------------------------------------------ 背景
    def _background(self, page: str) -> pygame.Surface:
        cached = self._bg.get(page)
        if cached is not None:
            return cached
        s = pygame.Surface((W, H))
        _vgrad(s, (0, 0, W, H), C_BG_TOP, C_BG_BOTTOM)
        if page == "home":
            _vgrad(s, (0, SB_H, W, 170), (26, 86, 152), (10, 38, 74))
            # 远山 / 光晕
            pygame.draw.circle(s, (78, 158, 214), (186, 76), 30)
            pygame.draw.circle(s, (120, 190, 236), (186, 76), 18)
            for i in range(3):
                pts = [(0, 176), (0, 158 + i * 6)]
                for x in range(0, W + 20, 20):
                    pts.append((x, 150 + i * 12 + 10 * math.sin(x / 33 + i)))
                pts += [(W, 196), (W, 300), (0, 300)]
                pygame.draw.polygon(s, (9 + i * 5, 34 + i * 8, 62 + i * 10), pts)
            _vgrad(s, (0, 236, W, 64), (6, 20, 38), (3, 10, 22))
        elif page == "menu":
            for i in range(0, W, 6):
                pygame.draw.line(s, (12, 34, 60), (i, 40), (i, SOFT_Y))
        self._bg[page] = s
        return s

    def _status_bar(self, s) -> None:
        _vgrad(s, (0, 0, W, SB_H), (10, 42, 78), (6, 24, 48))
        _signal(s, 6, 3)
        _text(s, "中国移动", 32, 3, 10, (198, 220, 244))
        _text(s, time.strftime("%H:%M"), 186, 2, 12, C_TEXT, True,
              family="arial")
        _battery(s, 218, 5, 0.72)

    def _title_bar(self, s, title: str, right: str = "") -> None:
        _vgrad(s, (0, SB_H, W, TB_H), C_TITLE_A, C_TITLE_B)
        pygame.draw.line(s, (78, 144, 206), (0, SB_H + TB_H - 1),
                         (W, SB_H + TB_H - 1))
        _text(s, title, 8, SB_H + 3, 13, C_TEXT, True)
        if right:
            _text(s, right, W - 9, SB_H + 5, 10, C_DIM, align="right")

    def _soft_bar(self, s, left: str, right: str) -> None:
        _vgrad(s, (0, SOFT_Y, W, SOFT_H), (16, 52, 92), C_SOFT)
        pygame.draw.line(s, (60, 106, 158), (0, SOFT_Y), (W, SOFT_Y))
        _text(s, left, 7, SOFT_Y + 3, 11, C_TEXT)
        _text(s, right, W - 7, SOFT_Y + 3, 11, C_TEXT, align="right")

    def _info_bar(self, s, text: str) -> None:
        _vgrad(s, (0, INFO_Y, W, INFO_H), (10, 30, 54), (6, 20, 38))
        pygame.draw.line(s, (42, 80, 124), (0, INFO_Y), (W, INFO_Y))
        _text(s, text, 6, INFO_Y + 2, 10, C_DIM, max_w=W - 12)

    # ------------------------------------------------------------ 图标
    def _icon(self, kind: str, color, size: int = 40,
              active: bool = False) -> pygame.Surface:
        key = (kind, tuple(color), size, active)
        hit = self._icon_cache.get(key)
        if hit is not None:
            return hit
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        r = 9
        top = tuple(min(255, int(c * 1.18) + 22) for c in color)
        bot = tuple(max(0, int(c * 0.72)) for c in color)
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size),
                         border_radius=r)
        grad = pygame.Surface((size, size), pygame.SRCALPHA)
        for y in range(size):
            t = y / max(1, size - 1)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            pygame.draw.line(grad, c, (0, y), (size, y))
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        s.blit(grad, (0, 0))
        w = (255, 255, 255)
        cx, cy = size // 2, size // 2
        if kind == "game":                       # 手柄
            pygame.draw.rect(s, w, (cx - 13, cy - 6, 26, 13), border_radius=6)
            pygame.draw.circle(s, w, (cx - 14, cy + 1), 5)
            pygame.draw.circle(s, w, (cx + 14, cy + 1), 5)
            pygame.draw.line(s, color, (cx - 9, cy), (cx - 3, cy), 2)
            pygame.draw.line(s, color, (cx - 6, cy - 3), (cx - 6, cy + 3), 2)
            pygame.draw.circle(s, color, (cx + 7, cy - 2), 2)
            pygame.draw.circle(s, color, (cx + 10, cy + 2), 2)
        elif kind == "apps":
            for dx, dy in ((-8, -8), (2, -8), (-8, 2), (2, 2)):
                pygame.draw.rect(s, w, (cx + dx, cy + dy, 6, 6), border_radius=1)
        elif kind == "star":
            pts = []
            for i in range(10):
                a = math.radians(-90 + i * 36)
                rr = 13 if i % 2 == 0 else 5.5
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            pygame.draw.polygon(s, w, pts)
        elif kind == "media":
            pygame.draw.polygon(s, w, [(cx - 7, cy - 10), (cx + 11, cy),
                                      (cx - 7, cy + 10)])
        elif kind == "book":
            pygame.draw.rect(s, w, (cx - 10, cy - 11, 20, 22), 2, border_radius=2)
            pygame.draw.circle(s, w, (cx, cy - 3), 4, 2)
            pygame.draw.arc(s, w, (cx - 7, cy + 1, 14, 10), 3.14, 6.28, 2)
        elif kind == "msg":
            pygame.draw.ellipse(s, w, (cx - 12, cy - 9, 24, 17))
            pygame.draw.polygon(s, w, [(cx - 8, cy + 5), (cx - 12, cy + 12),
                                      (cx - 2, cy + 7)])
        elif kind == "cfg":
            pygame.draw.circle(s, w, (cx, cy), 9, 3)
            for i in range(8):
                a = i * math.pi / 4
                pygame.draw.line(s, w, (cx + 11 * math.cos(a), cy + 11 * math.sin(a)),
                                 (cx + 14 * math.cos(a), cy + 14 * math.sin(a)), 2)
        elif kind == "cal":
            pygame.draw.rect(s, w, (cx - 11, cy - 10, 22, 20), 2, border_radius=2)
            pygame.draw.line(s, w, (cx - 11, cy - 4), (cx + 11, cy - 4), 2)
            for dx in (-6, 0, 6):
                pygame.draw.line(s, w, (cx + dx, cy - 12), (cx + dx, cy - 7), 2)
        else:  # tool
            pygame.draw.rect(s, w, (cx - 10, cy - 3, 20, 7), border_radius=3)
            pygame.draw.circle(s, w, (cx - 7, cy), 6, 2)
        if active:
            pygame.draw.rect(s, C_ACCENT, (0, 0, size, size), width=2,
                             border_radius=r)
        self._icon_cache[key] = s
        return s

    # ------------------------------------------------------------ 各页
    def _draw_boot(self, s) -> None:
        _vgrad(s, (0, 0, W, H), (238, 245, 252), (186, 210, 236))
        pygame.draw.ellipse(s, (24, 92, 164), (58, 92, 124, 54))
        pygame.draw.ellipse(s, (255, 255, 255), (66, 100, 108, 38))
        _text(s, "MTK", W // 2, 103, 28, (24, 76, 140), True,
              align="center", family="arial")
        _text(s, "PymRP", W // 2, 162, 20, (32, 62, 100), True, align="center")
        _text(s, "Mythroad 应用模拟器", W // 2, 190, 11, (92, 118, 148),
              align="center")
        _panel(s, (50, 232, 140, 7), (198, 214, 232), radius=3)
        k = min(1.0, self.boot_t / 1.5)
        if k > 0:
            _panel(s, (50, 232, int(140 * k), 7), (28, 110, 190), radius=3)
        _text(s, "正在启动…", W // 2, 250, 10, (100, 126, 156), align="center")
        _text(s, "按任意键跳过", W // 2, 282, 9, (140, 160, 184), align="center")

    def _draw_home(self, s) -> None:
        self._status_bar(s)
        now = time.localtime()
        week = "星期" + "一二三四五六日"[now.tm_wday]
        _text(s, time.strftime("%H:%M"), W // 2, 42, 40, C_TEXT, True,
              align="center", family="arial")
        _text(s, f"{now.tm_mon}月{now.tm_mday}日  {week}", W // 2, 90, 12,
              (198, 222, 246), align="center")
        _text(s, "中国移动", W // 2, 108, 10, (150, 190, 226), align="center")

        # 游戏中心快捷图标
        bx, by, bw, bh = 72, 126, 96, 58
        _panel(s, (bx, by, bw, bh), (14, 46, 84), (72, 130, 190), radius=9)
        s.blit(self._icon("game", ICON_COLORS[0], 32), (bx + 6, by + 12))
        _text(s, "游戏中心", bx + 44, by + 12, 11, C_TEXT, True)
        _text(s, "在线 / 本地", bx + 44, by + 30, 9, C_DIM)
        _text(s, "左软键 菜单   ·   右软键 游戏中心", W // 2, 216, 10,
              (170, 200, 230), align="center")
        _text(s, "PymRP  ·  MTK6225  ·  240x320", W // 2, 268, 9,
              (110, 146, 184), align="center")
        self._soft_bar(s, "菜单", "游戏")

    def _draw_menu(self, s) -> None:
        self._status_bar(s)
        self._title_bar(s, "主菜单", "1/1")
        for i, (label, kind, color_idx) in enumerate(MENU_ITEMS):
            gx, gy = i % 3, i // 3
            x, y = 8 + gx * 74, 44 + gy * 74
            active = i == self.menu_sel
            if active:
                _panel(s, (x - 2, y - 2, 72, 72), (36, 84, 140),
                       C_ACCENT, radius=10, width=2)
            s.blit(self._icon(kind, ICON_COLORS[color_idx], 40, active),
                   (x + 15, y + 4))
            _text(s, label, x + 34, y + 48, 10,
                  C_ACCENT if active else C_TEXT, active, align="center")
        name = MENU_ITEMS[self.menu_sel][0]
        self._info_bar(s, f"{self.menu_sel + 1}/9  {name}   ·   方向键选择，确定打开")
        self._soft_bar(s, "打开", "返回")

    def _draw_gamecenter(self, s) -> None:
        self._status_bar(s)
        state = self.cat.online_state
        dot = C_GREEN if state == "ready" else C_ACCENT if state == "loading" else C_RED
        self._title_bar(s, "游戏中心", "按*搜索")
        pygame.draw.circle(s, dot, (206, SB_H + 11), 4)
        pygame.draw.circle(s, (255, 255, 255), (206, SB_H + 11), 4, 1)

        # Tab
        _vgrad(s, (0, TAB_Y, W, TAB_H), (12, 36, 64), (8, 24, 46))
        for i, label in enumerate(("① 在线列表", "② 本地列表")):
            x0 = 4 + i * 116
            if i == self.tab:
                _panel(s, (x0, TAB_Y + 2, 112, TAB_H - 3),
                       (34, 96, 158), (96, 160, 220), radius=5)
            _text(s, label, x0 + 56, TAB_Y + 4, 11,
                  C_TEXT if i == self.tab else C_DIM, i == self.tab,
                  align="center")
        pygame.draw.line(s, (40, 84, 132), (0, TAB_Y + TAB_H - 1),
                         (W, TAB_Y + TAB_H - 1))

        items = self.items()
        # 列表背景
        for r in range(ROWS):
            y = LIST_Y + r * ROW_H
            if r % 2 == 0:
                _vgrad(s, (0, y, W, ROW_H), C_ROW_A, C_ROW_B)
            else:
                _vgrad(s, (0, y, W, ROW_H), (13, 38, 68), (10, 30, 56))

        if not items:
            msg = ("正在后台获取在线列表…" if self.tab == 0 and state == "loading"
                   else "在线列表获取失败，按左软键重试" if self.tab == 0
                   and state == "error"
                   else "没有找到应用，按 * 搜索或切换列表")
            _text(s, msg, W // 2, LIST_Y + 74, 11, C_DIM, align="center")
            if self.tab == 0 and state == "error":
                _text(s, self.cat.online_message[:26], W // 2, LIST_Y + 94,
                      9, C_RED, align="center")
        else:
            f_title = _font(12, True)
            f_sub = _font(9)
            for r in range(ROWS):
                idx = self.top + r
                if idx >= len(items):
                    break
                m = items[idx]
                y = LIST_Y + r * ROW_H
                active = idx == self.sel
                if active:
                    _vgrad(s, (0, y + 1, W - 4, ROW_H - 2), C_SEL_A, C_SEL_B)
                    pygame.draw.rect(s, C_ACCENT, (0, y + 1, 3, ROW_H - 2))
                # 图标
                color = ICON_COLORS[(m.appid or idx) % len(ICON_COLORS)]
                _panel(s, (7, y + 6, 30, 30), color, radius=6)
                ch = (m.label.strip() or "?")[0]
                _text(s, ch, 22, y + 11, 15, (255, 255, 255), True,
                      align="center")
                # 文本
                tc = C_TEXT if active else (216, 232, 248)
                _text(s, m.label, 43, y + 5, 12, tc, active, max_w=150)
                _text(s, m.subtitle, 43, y + 22, 9,
                      (188, 214, 238) if active else C_DIM, max_w=150)
                # 右侧状态
                p = self.cat.get_progress(m.file) if m.source == "online" else {}
                state = p.get("state")
                if state == "downloading":
                    pct = int(100 * p.get("done", 0) / max(1, p.get("total") or 1))
                    _text(s, f"{pct}%", W - 7, y + 5, 10, C_ACCENT, align="right")
                    pygame.draw.rect(s, (30, 64, 104), (W - 50, y + 26, 42, 3))
                    pygame.draw.rect(s, C_ACCENT,
                                     (W - 50, y + 26, max(1, int(42 * pct / 100)), 3))
                elif state == "error":
                    _text(s, "失败", W - 7, y + 8, 9, C_RED, align="right")
                elif m.downloaded or m.source == "local":
                    pygame.draw.line(s, C_GREEN, (W - 23, y + 20), (W - 18, y + 25), 2)
                    pygame.draw.line(s, C_GREEN, (W - 18, y + 25), (W - 9, y + 12), 2)
                else:
                    pygame.draw.rect(s, C_DIM, (W - 18, y + 12, 4, 8))
                    pygame.draw.polygon(s, C_DIM, [(W - 23, y + 19),
                                                   (W - 11, y + 19),
                                                   (W - 17, y + 26)])
                pygame.draw.line(s, (26, 58, 96), (43, y + ROW_H - 1),
                                 (W - 5, y + ROW_H - 1))

            # 滚动条
            if len(items) > ROWS:
                track = LIST_END - LIST_Y
                thumb = max(16, track * ROWS // len(items))
                pos = LIST_Y + int((track - thumb) * self.top /
                                   max(1, len(items) - ROWS))
                pygame.draw.rect(s, (26, 56, 92), (W - 4, LIST_Y, 3, track))
                pygame.draw.rect(s, C_ACCENT, (W - 4, pos, 3, thumb))

        # 信息条
        if self.searching:
            info = f"搜索: {self.search}_   （CLEAR 删除 / 确定 打开）"
        elif state == "loading" and self.tab == 0:
            info = "后台获取在线列表… 首次需联网，之后读本地缓存"
        else:
            total = len(items)
            where = f"{self.sel + 1}/{total}" if total else "0/0"
            tag = "在线" if self.tab == 0 else "本地"
            info = f"{tag} · {where} · 上下选择 左右切页 · * 搜索"
            p = self.cat.get_progress(self.current().file) if self.current() else {}
            if p.get("state") == "downloading":
                pct = int(100 * p.get("done", 0) / max(1, p.get("total") or 1))
                info = f"下载 {p.get('done', 0) // 1024}K / {(p.get('total') or 1) // 1024}K  {pct}%"
        self._info_bar(s, info)
        self._soft_bar(s, "打开", "返回")

    # ------------------------------------------------------------ 输出
    def surface(self) -> pygame.Surface:
        if self.page == "boot":
            s = pygame.Surface((W, H))
            self._draw_boot(s)
        else:
            s = self._background(self.page).copy()
            if self.page == "home":
                self._draw_home(s)
            elif self.page == "menu":
                self._draw_menu(s)
            else:
                self._draw_gamecenter(s)

        if self.toast_left > 0 and self.toast_text:
            f = _font(10)
            tw = min(W - 20, f.size(self.toast_text)[0] + 20)
            box = ((W - tw) // 2, 246, tw, 24)
            _panel(s, box, (18, 34, 54), C_ACCENT, radius=6)
            _text(s, self.toast_text, W // 2, 252, 10, C_TEXT,
                  align="center", max_w=tw - 12)
        return s
