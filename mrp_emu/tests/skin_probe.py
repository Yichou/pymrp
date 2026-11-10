#!/usr/bin/env python3
"""皮肤探针：导航键区域扁平化样式回归。

背景（2026-11-10）：老板给了一张导航区参考图 —— 深灰底、大圆形 D-pad、
四角大圆角方块（左/右软键、绿拨号、红挂断）、中心实心 OK 圆。这里验证：

1. 几何比例与参考图一致（圆盘直径/按键高≈2.1、OK/圆盘≈0.37、圆盘/机身宽≈0.41）；
2. 圆盘与四角按键、数字键盘互不重叠且都在机身内；
3. 渲染像素配色对齐参考采样（#292C33 / #383C45 / #46B45D / #C84335）；
4. 命中测试在新几何下仍然正确（中心/四向/盘外/四角/数字键）；
5. 按下态有可见但不刺眼的反馈；
6. 旧版皮肤 JSON（缺新调色键）能自动补齐、不抛异常。

用法：python tests/skin_probe.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

pygame.init()

from mrp_emu.ui.phone import PhoneUI  # noqa: E402
from mrp_emu.ui.skin import build_default, load_skin  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  {detail}" if detail else ""))
    if cond:
        PASS += 1
    else:
        FAIL += 1


def near(actual, want, tol: int = 18) -> bool:
    return all(abs(int(a) - int(b)) <= tol for a, b in zip(actual, want))


def main() -> int:
    print("== 1. 几何与参考图比例 ==")
    skin = load_skin(ROOT / "runtime" / "skin.json")
    ui = PhoneUI(skin)
    nav = skin["nav"]
    cx, cy, r, hole = nav["cx"], nav["cy"], nav["r"], nav["hole"]
    corners = {k["id"]: k for k in skin["keys"][:4]}

    check("皮肤版本为 2", skin.get("version") == 2, f"={skin.get('version')}")
    check("机身高度 >= 680（容纳大圆盘）", skin["height"] >= 680, f"={skin['height']}")
    check("屏幕仍是 240x320", (skin["screen"]["w"], skin["screen"]["h"]) == (240, 320))
    check("圆盘直径 > 110px", 2 * r > 110, f"={2*r}")
    check("圆盘直径/按键高 ≈ 2.1",
          abs(2 * r / corners["soft_l"]["rect"][3] - 2.1) < 0.15,
          f"={2*r/corners['soft_l']['rect'][3]:.3f}")
    check("OK 圆/圆盘 ≈ 0.37", abs(hole / r - 0.375) < 0.05, f"={hole/r:.3f}")
    check("圆盘/机身宽 ≈ 0.40", abs(2 * r / skin["width"] - 0.40) < 0.05,
          f"={2*r/skin['width']:.3f}")
    check("四角按键接近正方形",
          all(abs(k["rect"][2] - k["rect"][3]) <= 4 for k in corners.values()),
          str([k["rect"][2:] for k in corners.values()]))

    # 圆盘位于左右两列按键之间
    lx, ly, lw, lh = corners["soft_l"]["rect"]
    rx, ry, rw, rh = corners["soft_r"]["rect"]
    check("圆盘不压左列按键", cx - r > lx + lw, f"圆盘左 {cx-r} > 按键右 {lx+lw}")
    check("圆盘不压右列按键", cx + r < rx, f"圆盘右 {cx+r} < 按键左 {rx}")
    check("上排与下排按键不重叠", ly + lh < corners["send"]["rect"][1],
          f"{ly+lh} < {corners['send']['rect'][1]}")

    # 所有按键都在机身内
    out_of_body = [k["id"] for k in skin["keys"]
                   if k["rect"][0] < 0 or k["rect"][1] < 0
                   or k["rect"][0] + k["rect"][2] > skin["width"]
                   or k["rect"][1] + k["rect"][3] > skin["height"]]
    check("所有按键都在机身内", not out_of_body, str(out_of_body))
    num_top = min(k["rect"][1] for k in skin["keys"][4:])
    check("数字键盘在导航区下方", num_top > cy + r, f"键盘顶 {num_top} > 圆盘底 {cy+r}")

    print("\n== 2. 渲染配色采样（对齐参考图）==")
    surf = ui.draw(None)
    check("机身尺寸正确", surf.get_size() == (skin["width"], skin["height"]),
          str(surf.get_size()))
    arr = pygame.surfarray.array3d(surf)  # [x, y, rgb]

    def px(x, y):
        return tuple(int(v) for v in arr[x, y])

    samples = [
        ("导航区背景 #292C33", (10, cy), (41, 44, 51)),
        ("左软键底色 #383C45", (lx + 12, ly + 12), (56, 60, 69)),
        ("右软键底色", (rx + 12, ry + 12), (56, 60, 69)),
    ]
    sx, sy, sw, sh = corners["send"]["rect"]
    ex, ey, ew, eh = corners["end"]["rect"]
    samples += [
        ("拨号绿 #46B45D", (sx + 12, sy + 12), (70, 180, 93)),
        ("挂断红 #C84335", (ex + 12, ey + 12), (200, 67, 53)),
        ("圆盘上部偏亮", (cx - 24, cy - 22), (48, 52, 60)),
        ("OK 圆比圆盘亮", (cx - 12, cy - 8), (76, 80, 90)),
    ]
    for name, pos, want in samples:
        got = px(*pos)
        check(name, near(got, want, 22), f"{pos}={got} 期望≈{want}")
    check("OK 圆明显亮于圆盘", sum(px(cx - 12, cy - 8)) > sum(px(cx - 24, cy - 22)) + 40,
          f"{px(cx-12,cy-8)} vs {px(cx-24,cy-22)}")
    # 绿红确实带色，不是灰块
    g = px(sx + 12, sy + 12)
    e = px(ex + 12, ey + 12)
    check("拨号按键偏绿", g[1] > g[0] + 60 and g[1] > g[2] + 50, str(g))
    check("挂断按键偏红", e[0] > e[1] + 80 and e[0] > e[2] + 90, str(e))

    print("\n== 3. 命中测试（新几何）==")
    cases = [
        ("中心 OK", (cx, cy), "nav:SELECT"),
        ("上", (cx, cy - int(r * 0.8)), "nav:UP"),
        ("下", (cx, cy + int(r * 0.8)), "nav:DOWN"),
        ("左", (cx - int(r * 0.8), cy), "nav:LEFT"),
        ("右", (cx + int(r * 0.8), cy), "nav:RIGHT"),
        ("圆盘外", (cx, cy + r + 6), None),
    ]
    for name, pos, want in cases:
        got = ui.hit(pos)
        check(f"{name} -> {want}", got == want, f"={got}")
    for kid, k in corners.items():
        x, y, w, h = k["rect"]
        check(f"{kid} 命中", ui.hit((x + w // 2, y + h // 2)) == kid)
    k5 = next(k for k in skin["keys"] if k["label"] == "5")
    x, y, w, h = k5["rect"]
    check("数字键 5 命中", ui.hit((x + w // 2, y + h // 2)) == k5["id"])
    check("键值映射不变", ui.key_code("soft_l") == 17 and ui.key_code("nav:SELECT") == 20)
    check("屏幕坐标换算不变", ui.screen_pos((150, 220)) == (120, 160),
          str(ui.screen_pos((150, 220))))

    print("\n== 4. 按下态反馈 ==")
    base = pygame.surfarray.array3d(ui.draw(None)).astype(int)
    for kid in corners:
        ui.press(kid)
    ui.press("nav:UP")
    ui.press("nav:SELECT")
    pressed = pygame.surfarray.array3d(ui.draw(None)).astype(int)
    diff = np.abs(base - pressed).sum(axis=2)
    for kid, k in corners.items():
        x, y, w, h = k["rect"]
        region = diff[x:x + w, y:y + h]
        check(f"{kid} 按下有反馈", int((region > 12).sum()) > 30,
              f"变化像素 {int((region > 12).sum())}")
        check(f"{kid} 按下不过曝", int(pressed[x:x + w, y:y + h].max()) < 250,
              f"峰值 {int(pressed[x:x+w,y:y+h].max())}")
    ok_region = diff[cx - hole:cx + hole, cy - hole:cy + hole]
    check("OK 按下有反馈", int((ok_region > 12).sum()) > 20,
          f"变化像素 {int((ok_region > 12).sum())}")
    ui.release("soft_l")
    ui.release("soft_r")
    ui.release("send")
    ui.release("end")
    ui.release("nav:UP")
    ui.release("nav:SELECT")

    print("\n== 5. 旧皮肤 JSON 兼容 ==")
    with tempfile.TemporaryDirectory(prefix="pymrp-skin-") as td:
        old = build_default()
        for k in ("nav_face_top", "nav_face_bottom", "nav_edge", "ok_top",
                  "ok_bottom", "ok_edge", "ok_text", "soft_text", "call_text",
                  "key_edge", "key_radius", "num_radius", "arrow_radius",
                  "press_glow"):
            old["palette"].pop(k, None)
        old.pop("version", None)
        p = Path(td) / "legacy.json"
        p.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
        loaded = load_skin(p)
        check("缺失调色键已补齐", all(k in loaded["palette"] for k in
              ("nav_face_top", "ok_top", "soft_text", "key_radius")))
        try:
            legacy_ui = PhoneUI(loaded)
            legacy_ui.draw(None)
            check("旧皮肤仍能渲染", True)
        except Exception as exc:  # pragma: no cover
            check("旧皮肤仍能渲染", False, repr(exc))

    print(f"\nskin_probe: {PASS} PASS / {FAIL} FAIL")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
