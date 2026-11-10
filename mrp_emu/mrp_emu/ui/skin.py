"""皮肤系统：把整台功能机的几何/配色/键位抽成 JSON。

想换机型只改 JSON，不用碰代码。首次运行会自动写出一份默认的 MTK QVGA 直板机。

v2（导航区扁平化）：参考样式重排 —— 大圆形 D-pad 居中，四角是 58x50 的
大圆角方块（上排左右软键 / 下排拨号挂断），配色改为均匀深灰 + 纯色绿红。
机身因此加高 30px，数字键盘整体下移。v2.1 按老板新参考图把四角键从 59
压到 50px，上下两排中心保持不变。
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SKIN_NAME = "mtk_qvga.json"
SKIN_VERSION = 2


def _key(kid: str, label: str, rect, key: str, sub: str = "",
         style: str = "num", shape: str = "rect") -> dict:
    return {
        "id": kid, "label": label, "sub": sub, "rect": list(rect),
        "key": key, "style": style, "shape": shape,
    }


def build_default() -> dict:
    """一台典型的 MTK 平台 QVGA 直板机。坐标单位均为像素（1.0 缩放）。"""
    keys = [
        # 四角大圆角方块：上排软键、下排通话键，中间让给大圆盘
        _key("soft_l", "左软键", (22, 400, 58, 50), "SOFT_L", style="soft", shape="soft"),
        _key("soft_r", "右软键", (220, 400, 58, 50), "SOFT_R", style="soft", shape="soft"),
        _key("send", "拨号", (22, 470, 58, 50), "SEND", style="send"),
        _key("end", "挂断", (220, 470, 58, 50), "END", style="end"),
    ]

    # 4x3 数字键盘
    labels = [("1", ""), ("2", "ABC"), ("3", "DEF"),
              ("4", "GHI"), ("5", "JKL"), ("6", "MNO"),
              ("7", "PQRS"), ("8", "TUV"), ("9", "WXYZ"),
              ("*", ""), ("0", "+"), ("#", "")]
    x0, y0, kw, kh, gx, gy = 34, 542, 72, 26, 8, 6
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
        "version": SKIN_VERSION,
        "width": 300, "height": 690,
        "body": {
            "radius": 30,
            "top_color": [50, 54, 62],
            "bottom_color": [39, 42, 49],
            "edge_color": [66, 71, 81],
            "edge_width": 2,
            "speaker": [120, 22, 60, 6],
            "brand": "MTK",
            "brand_color": [176, 184, 196],
            "mic": [146, 676, 8, 3],
        },
        "screen": {"x": 30, "y": 60, "w": 240, "h": 320, "bezel": 6, "bezel_color": [16, 17, 20]},
        # 大圆盘：直径 124（占机身宽 41%），中心 OK 圆直径 46
        "nav": {"cx": 150, "cy": 461, "r": 62, "hole": 23},
        "palette": {
            # 数字键盘沿用原来的立体键帽
            "num_top": [66, 71, 80],
            "num_bottom": [44, 48, 56],
            "num_text": [232, 236, 243],
            "num_sub": [150, 158, 170],
            "num_radius": 9,
            # 四角按键：几乎纯色，只留极淡的上下明暗
            "soft_top": [58, 62, 71],
            "soft_bottom": [52, 56, 65],
            "soft_text": [154, 158, 167],
            "send_top": [74, 184, 97],
            "send_bottom": [64, 170, 87],
            "end_top": [204, 71, 57],
            "end_bottom": [190, 61, 49],
            "call_text": [240, 246, 242],
            "key_edge": [72, 77, 87],
            "key_radius": 9,
            # 圆盘
            "nav_ring": [52, 56, 64],
            "nav_inner": [70, 74, 83],
            "nav_face_top": [52, 56, 64],
            "nav_face_bottom": [38, 41, 48],
            "nav_edge": [62, 67, 76],
            "nav_arrow": [156, 161, 170],
            "arrow_radius": 0.725,
            "ok_top": [84, 88, 98],
            "ok_bottom": [68, 72, 81],
            "ok_edge": [92, 97, 107],
            "ok_text": [196, 200, 209],
            "highlight": [255, 240, 176],
            "backlight": [176, 200, 230],
            "press_glow": [214, 222, 234],
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
    skin = json.loads(p.read_text(encoding="utf-8"))
    # 老皮肤 JSON 缺新调色键时补齐，保证绘制代码不必到处写 .get 的默认值
    default = build_default()
    pal = skin.setdefault("palette", {})
    for k, v in default["palette"].items():
        pal.setdefault(k, v)
    return skin
