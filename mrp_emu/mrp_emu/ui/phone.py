"""MTK 直板机外观：机壳、屏幕、五向导航、软键、数字键盘。

全部矢量绘制，几何来自皮肤 JSON。窗口里看到的就是一台功能机，
鼠标点哪颗键就是按哪颗键。
"""

from __future__ import annotations

import math

import pygame

from ..consts import KEY_NAME_TO_CODE
from ..gfx import get_font


class PhoneUI:
    def __init__(self, skin: dict) -> None:
        self.skin = skin
        self.w = skin["width"]
        self.h = skin["height"]
        self.screen_rect = pygame.Rect(
            skin["screen"]["x"], skin["screen"]["y"],
            skin["screen"]["w"], skin["screen"]["h"],
        )
        self.bezel = skin["screen"].get("bezel", 6)
        # 屏幕内部分辨率（MRP 坐标），与窗口上的像素尺寸无关
        self.screen_w = skin["screen"].get("w", 240)
        self.screen_h = skin["screen"].get("h", 320)
        self.nav = skin["nav"]
        self.palette = skin["palette"]
        self.keys = skin["keys"]
        self.pressed: set[str] = set()

        self._grad_cache: dict[tuple, pygame.Surface] = {}
        self._body = self._build_body()
        self._gloss = self._build_gloss()

    # ------------------------------------------------------------ 渐变工具
    def _grad(self, w: int, h: int, c1, c2, radius: int) -> pygame.Surface:
        key = (w, h, tuple(c1), tuple(c2), radius)
        cached = self._grad_cache.get(key)
        if cached is not None:
            return cached
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            pygame.draw.line(surf, col, (0, y), (w, y))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self._grad_cache[key] = surf
        return surf

    # ------------------------------------------------------------ 机身
    def _build_body(self) -> pygame.Surface:
        b = self.skin["body"]
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        body = self._grad(self.w, self.h, b["top_color"], b["bottom_color"], b["radius"])
        surf.blit(body, (0, 0))
        # 金属边框
        pygame.draw.rect(
            surf, b["edge_color"], (0, 0, self.w, self.h),
            width=b.get("edge_width", 2), border_radius=b["radius"],
        )
        # 顶部高光
        pygame.draw.line(surf, (88, 94, 104), (b["radius"], 1),
                         (self.w - b["radius"], 1), 1)
        return surf

    def _build_gloss(self) -> pygame.Surface:
        """屏幕玻璃反光：一条极淡的斜向高光。"""
        pad = self.bezel * 2
        w = self.screen_rect.w + pad
        h = self.screen_rect.h + pad
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(-h, w, 3):
            pts = [(i, 0), (i + 26, 0), (i + 26 - h // 3, h), (i - h // 3, h)]
            pygame.draw.polygon(surf, (255, 255, 255, 10), pts)
        fade = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            a = int(26 * (1 - y / max(1, h - 1)))
            pygame.draw.line(fade, (0, 0, 0, a), (0, y), (w, y))
        surf.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return surf

    # ------------------------------------------------------------ 按键绘制
    @staticmethod
    def _arrow(surf: pygame.Surface, x: float, y: float, angle: float,
               size: float, half: float, color) -> None:
        """以 (x,y) 为中心画一个朝 angle 方向的实心等腰三角。"""
        rad = math.radians(angle)
        ux, uy = math.cos(rad), math.sin(rad)
        px, py = -uy, ux
        back = size * 0.45
        tip = (x + size * ux, y + size * uy)
        a = (x - back * ux + half * px, y - back * uy + half * py)
        b = (x - back * ux - half * px, y - back * uy - half * py)
        pygame.draw.polygon(surf, color, [tip, a, b])

    def _draw_key(self, surf: pygame.Surface, key: dict, active: bool) -> None:
        x, y, w, h = key["rect"]
        style = key.get("style", "num")
        pal = self.palette

        if style == "num":
            c1, c2 = pal["num_top"], pal["num_bottom"]
            text_color = pal["num_text"]
            radius = pal.get("num_radius", 9)
        elif style == "soft":
            c1, c2 = pal["soft_top"], pal["soft_bottom"]
            text_color = pal["soft_text"]
            radius = pal.get("key_radius", 11)
        elif style == "send":
            c1, c2 = pal["send_top"], pal["send_bottom"]
            text_color = pal["call_text"]
            radius = pal.get("key_radius", 11)
        else:  # end
            c1, c2 = pal["end_top"], pal["end_bottom"]
            text_color = pal["call_text"]
            radius = pal.get("key_radius", 11)

        if active:
            c1 = [min(255, int(v * 1.10) + 12) for v in c1]
            c2 = [min(255, int(v * 1.08) + 10) for v in c2]

        # 扁平键面：极淡上下明暗，不再用黑描边
        surf.blit(self._grad(w, h, c1, c2, radius), (x, y))
        pygame.draw.rect(surf, pal["key_edge"], (x, y, w, h),
                         width=1, border_radius=radius)

        if style == "num":
            # 键盘背光轮廓
            pygame.draw.rect(
                surf, (46, 62, 84), (x + 2, y + 2, w - 4, h - 4),
                width=1, border_radius=radius - 2,
            )
            label = key["label"]
            sub = key.get("sub") or ""
            f_big = get_font("arial", 15, bold=True)
            img = f_big.render(label, True, text_color)
            dy = -4 if sub else 0
            surf.blit(img, (x + (w - img.get_width()) // 2, y + (h - img.get_height()) // 2 + dy))
            if sub:
                f_small = get_font("arial", 7)
                s = f_small.render(sub, True, pal["num_sub"])
                surf.blit(s, (x + (w - s.get_width()) // 2, y + h - 10))
        else:
            f = get_font("microsoftyahei", 13)
            img = f.render(key["label"], True, text_color)
            surf.blit(img, (x + (w - img.get_width()) // 2, y + (h - img.get_height()) // 2))

        if active:
            pygame.draw.rect(
                surf, pal["press_glow"], (x + 2, y + 2, w - 4, h - 4),
                width=1, border_radius=radius - 2,
            )

    def _draw_nav(self, surf: pygame.Surface, active_ids: set[str]) -> None:
        """扁平大圆盘：淡渐变盘面 + 四向实心三角 + 中央实心 OK 圆。"""
        pal = self.palette
        cx, cy, r = self.nav["cx"], self.nav["cy"], self.nav["r"]
        hole = self.nav["hole"]
        active = {k.split(":", 1)[1] for k in active_ids if k.startswith("nav:")}

        # 盘面：上略亮下略暗，只留一圈极淡边界，不做金属环
        face = self._grad(r * 2, r * 2,
                          pal["nav_face_top"], pal["nav_face_bottom"], r)
        surf.blit(face, (cx - r, cy - r))
        pygame.draw.circle(surf, pal["nav_edge"], (cx, cy), r, 1)

        # 四向箭头：距圆心 0.725r，与 OK 圆、盘沿都留足空隙
        arrow_r = r * pal.get("arrow_radius", 0.725)
        size = max(5.0, r * 0.12)
        half = size * 0.62
        dirs = {
            "UP": (0.0, -arrow_r, -90.0),
            "DOWN": (0.0, arrow_r, 90.0),
            "LEFT": (-arrow_r, 0.0, 180.0),
            "RIGHT": (arrow_r, 0.0, 0.0),
        }
        for name, (ox, oy, angle) in dirs.items():
            color = pal["highlight"] if name in active else pal["nav_arrow"]
            self._arrow(surf, cx + ox, cy + oy, angle, size, half, color)

        # 中央 OK：实心圆 + 淡边 + 浅色字
        ok_active = "SELECT" in active
        top, bottom = pal["ok_top"], pal["ok_bottom"]
        if ok_active:
            top = [min(255, int(v * 1.14) + 10) for v in top]
            bottom = [min(255, int(v * 1.12) + 8) for v in bottom]
        ok = self._grad(hole * 2, hole * 2, top, bottom, hole)
        surf.blit(ok, (cx - hole, cy - hole))
        pygame.draw.circle(surf, pal["ok_edge"], (cx, cy), hole, 1)
        f = get_font("arial", max(9, int(hole * 0.55)), bold=True)
        img = f.render("OK", True, pal["highlight"] if ok_active else pal["ok_text"])
        surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))

    # ------------------------------------------------------------ 合成
    def draw(self, screen_surface: pygame.Surface | None) -> pygame.Surface:
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        surf.blit(self._body, (0, 0))

        b = self.skin["body"]
        # 听筒
        sx, sy, sw, sh = b["speaker"]
        pygame.draw.rect(surf, (14, 15, 18), (sx, sy, sw, sh), border_radius=3)
        pygame.draw.rect(surf, (78, 84, 94), (sx, sy, sw, sh), width=1, border_radius=3)
        for i in range(sx + 6, sx + sw - 4, 6):
            pygame.draw.line(surf, (60, 66, 76), (i, sy + 2), (i, sy + sh - 2))
        # 品牌
        f = get_font("arial", 13, bold=True)
        img = f.render(b.get("brand", "MTK"), True, b.get("brand_color", (170, 178, 190)))
        surf.blit(img, ((self.w - img.get_width()) // 2, sy + sh + 7))

        # 屏幕凹槽 + 边框
        pad = self.bezel
        slot = pygame.Rect(self.screen_rect.x - pad, self.screen_rect.y - pad,
                           self.screen_rect.w + pad * 2, self.screen_rect.h + pad * 2)
        pygame.draw.rect(surf, (12, 13, 15), slot, border_radius=6)
        pygame.draw.rect(surf, (66, 72, 82), slot, width=1, border_radius=6)

        if screen_surface is not None:
            scaled = screen_surface
            if scaled.get_size() != (self.screen_rect.w, self.screen_rect.h):
                scaled = pygame.transform.smoothscale(
                    screen_surface, (self.screen_rect.w, self.screen_rect.h))
            surf.blit(scaled, self.screen_rect.topleft)
        else:
            pygame.draw.rect(surf, (8, 9, 11), self.screen_rect)

        # 屏幕内阴影
        pygame.draw.rect(surf, (0, 0, 0), self.screen_rect, width=2)
        surf.blit(self._gloss, slot.topleft)

        # 导航盘 + 按键
        self._draw_nav(surf, self.pressed)
        for key in self.keys:
            self._draw_key(surf, key, key["id"] in self.pressed)

        # 麦克风
        mx, my, mw, mh = b["mic"]
        for i in range(3):
            pygame.draw.circle(surf, (16, 17, 20), (mx + i * 4, my + mh // 2), 1)

        return surf

    # ------------------------------------------------------------ 命中测试
    def hit(self, pos: tuple[int, int]) -> str | None:
        """返回被点中的 key id（导航键返回 'nav:UP' 这类形式）。"""
        cx, cy, r = self.nav["cx"], self.nav["cy"], self.nav["r"]
        dx, dy = pos[0] - cx, pos[1] - cy
        dist = math.hypot(dx, dy)
        if dist <= self.nav["hole"]:
            return "nav:SELECT"
        if dist <= r:
            if abs(dx) > abs(dy):
                return "nav:RIGHT" if dx > 0 else "nav:LEFT"
            return "nav:DOWN" if dy > 0 else "nav:UP"

        for key in self.keys:
            x, y, w, h = key["rect"]
            if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                return key["id"]
        return None

    def key_code(self, key_id: str) -> int | None:
        """把皮肤里的键 id 翻译成 MRP 键值。"""
        if key_id.startswith("nav:"):
            return KEY_NAME_TO_CODE.get(key_id.split(":", 1)[1])
        for key in self.keys:
            if key["id"] == key_id:
                return KEY_NAME_TO_CODE.get(key["key"])
        return None

    def press(self, key_id: str) -> None:
        self.pressed.add(key_id)

    def release(self, key_id: str) -> None:
        self.pressed.discard(key_id)

    def key_at_name(self, name: str) -> str | None:
        """按 MRP 键名反查皮肤键 id（用于键盘映射）。"""
        for key in self.keys:
            if key["key"] == name:
                return key["id"]
        if name in ("UP", "DOWN", "LEFT", "RIGHT", "SELECT"):
            return f"nav:{name}"
        return None

    # ------------------------------------------------------------ 屏幕点击
    def screen_pos(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        """把窗口坐标换算成屏幕内坐标（240x320），不在屏幕内返回 None。"""
        r = self.screen_rect
        if not r.collidepoint(pos[0], pos[1]):
            return None
        sx = int((pos[0] - r.x) * self.screen_w / r.w)
        sy = int((pos[1] - r.y) * self.screen_h / r.h)
        return (max(0, min(self.screen_w - 1, sx)),
                max(0, min(self.screen_h - 1, sy)))

    def tap_to_key(self, sx: int, sy: int) -> str:
        """把屏幕上的点击位置翻译成一个键名。

        2008 年的 MTK 应用全部是按键驱动的，屏幕上没有可点击区域的概念，
        所以这里按「位置 -> 键」做空间映射，让鼠标点屏幕也能操作：

            顶部 1/4      上
            底部 1/4      下
            左边 1/5      左
            右边 1/5      右
            屏幕底部软键条 左/右软键
            其余（中央）   确定
        """
        w, h = self.screen_w, self.screen_h
        softbar = int(h * 0.92)          # 最底下 8% 是软键条

        if sy >= softbar:
            return "SOFT_L" if sx < w // 2 else "SOFT_R"
        if sx < w // 5:
            return "LEFT"
        if sx > w - w // 5:
            return "RIGHT"
        if sy < h // 4:
            return "UP"
        if sy > h * 3 // 4:
            return "DOWN"
        return "SELECT"
