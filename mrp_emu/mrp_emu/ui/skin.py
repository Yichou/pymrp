"""皮肤系统：把整台功能机的几何/配色/键位抽成 JSON。

想换机型只改 JSON，不用碰代码。首次运行会自动写出一份默认的 MTK QVGA 直板机。
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SKIN_NAME = "mtk_qvga.json"


def _key(kid: str, label: str, rect, key: str, sub: str = "",
         style: str = "num", shape: str = "rect") -> dict:
    return {
        "id": kid, "label": label, "sub": sub, "rect": list(rect),
        "key": key, "style": style, "shape": shape,
    }


def build_default() -> dict:
    """一台典型的 MTK 平台 QVGA 直板机。坐标单位均为像素（1.0 缩放）。"""
    keys = [
        # 软键
        _key("soft_l", "左软键", (34, 392, 72, 24), "SOFT_L", style="soft", shape="soft"),
        _key("soft_r", "右软键", (194, 392, 72, 24), "SOFT_R", style="soft", shape="soft"),
        # 通话键（绿 / 红）
        _key("send", "拨号", (34, 476, 72, 24), "SEND", style="send"),
        _key("end", "挂断", (194, 476, 72, 24), "END", style="end"),
    ]

    # 4x3 数字键盘
    labels = [("1", ""), ("2", "ABC"), ("3", "DEF"),
              ("4", "GHI"), ("5", "JKL"), ("6", "MNO"),
              ("7", "PQRS"), ("8", "TUV"), ("9", "WXYZ"),
              ("*", ""), ("0", "+"), ("#", "")]
    x0, y0, kw, kh, gx, gy = 34, 510, 72, 26, 8, 6
    for i, (lab, sub) in enumerate(labels):
        col, row = i % 3, i // 3
        keys.append(_key(
            f"k{lab.strip('#*') or 'x'}{i}",
            lab, (x0 + col * (kw + gx), y0 + row * (kh + gy), kw, kh),
            lab, sub=sub,
        ))

    return {
        "name": "MTK QVGA 直板机",
        "device": "MTK6225 / 240x320",
        "width": 300, "height": 660,
        "body": {
            "radius": 30,
            "top_color": [58, 63, 72],
            "bottom_color": [30, 33, 39],
            "edge_color": [96, 102, 112],
            "edge_width": 2,
            "speaker": [120, 22, 60, 6],
            "brand": "MTK",
            "brand_color": [176, 184, 196],
            "mic": [146, 646, 8, 3],
        },
        "screen": {"x": 30, "y": 60, "w": 240, "h": 320, "bezel": 6, "bezel_color": [16, 17, 20]},
        "nav": {"cx": 150, "cy": 438, "r": 38, "hole": 15},
        "palette": {
            "num_top": [72, 77, 86],
            "num_bottom": [46, 50, 58],
            "num_text": [232, 236, 243],
            "num_sub": [150, 158, 170],
            "soft_top": [60, 65, 74],
            "soft_bottom": [38, 41, 48],
            "send_top": [70, 160, 96],
            "send_bottom": [40, 116, 66],
            "end_top": [186, 78, 74],
            "end_bottom": [130, 44, 42],
            "nav_ring": [88, 94, 104],
            "nav_inner": [40, 43, 50],
            "nav_arrow": [206, 213, 224],
            "highlight": [255, 232, 150],
            "backlight": [120, 190, 255],
        },
        "keys": keys,
    }


def load_skin(path: str | Path | None = None) -> dict:
    if path is None:
        return build_default()
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(build_default(), ensure_ascii=False, indent=2), encoding="utf-8")
        return build_default()
    return json.loads(p.read_text(encoding="utf-8"))
