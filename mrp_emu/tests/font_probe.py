#!/usr/bin/env python3
"""系统字库质量探针：防「中文糊成一坨」回归。

背景
----
2026-11-11 老板反馈「系统字体糊掉了」。根因不是模拟器 UI 字体，而是
DSM 层的**系统点阵字库** ``mythroad/system/gb16.uc2``：

* 应用（QQ 2007 等）启动第一件事就是 ``open("mythroad/system/gb16.uc2")``，
  运行时按 ``seek(id * 32)`` 取 16x16 的 1bpp 字模自己画中文；
* 我们早期用「64px 粗体渲染 -> smoothscale 缩到 16x16 -> 阈值化」生成这个
  字库，缩放让相邻笔画**互相渗透**，缩完再阈值化笔画就**粘死**了：
  「帐」「密」「录」糊成黑块。实测墨迹率 avg=0.37 / max=0.59；
* 而发行包里的原厂字库（``fonts/gb16.uc2``、``fonts/sky16.uc2``）是当年
  手工点阵字，清晰可辨，avg=0.24 / max=0.32。

本探针守住三件事：

1. 自造字库的**字形不粘连**（墨迹率在合理区间）；
2. 自造字库的**位序正确**（16x16、MSB-first、不因裁剪而错位）；
3. ``ensure_uc2`` **优先复用原厂字库**，且能**自动识别并替换**糊字库。

跑法::

    python tests/font_probe.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

FAILED = 0
PASSED = 0


def check(name: str, ok: bool, detail: str = "") -> bool:
    global FAILED, PASSED
    if ok:
        PASSED += 1
        print(f"  [ok]   {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}" + (f"  ({detail})" if detail else ""))
    return ok


def glyph_rows(data: bytes, ch: str) -> list[str]:
    """按运行时的位序把一个字模还原成 16 行 ASCII 点阵。"""
    from mrp_emu.fontgen import BYTES_PER_GLYPH
    cp = ord(ch)
    off = cp * BYTES_PER_GLYPH
    blob = data[off:off + BYTES_PER_GLYPH]
    if len(blob) < BYTES_PER_GLYPH:
        return []
    rows = []
    for y in range(16):
        row = []
        for x in range(16):
            n = y * 16 + x
            row.append("#" if blob[n // 8] & (0x80 >> (n % 8)) else ".")
        rows.append("".join(row))
    return rows


# ---------------------------------------------------------------- 1. 字形质量
def probe_glyph_quality() -> None:
    print("\n== 1. 自造字库的字形质量（不粘连） ==")
    from mrp_emu.fontgen import (PROBE_CHARS, build_uc2, check_font_file,
                                 check_font_quality, ink_ratio)

    data = build_uc2(include_gb=False)
    check("字库非空", len(data) > 100_000, f"{len(data)} 字节")
    check("字库长度是 32 的倍数（每字模 32 字节）", len(data) % 32 == 0)

    ok, why = check_font_quality(data)
    check("整体质量自检通过", ok, why)

    # 逐字看墨迹率：粘连 -> 明显偏高；缺笔画 -> 明显偏低
    bad = []
    for ch in PROBE_CHARS:
        r = ink_ratio(data, ch)
        if r < 0 or r > 0.45:
            bad.append(f"{ch}={r:.2f}")
    check("常用汉字墨迹率均在 0~0.45", not bad, ", ".join(bad))

    # 「中」是最好认的结构字：中列一竖贯穿 + 上下两横
    rows = glyph_rows(data, "中")
    check("取到「中」字模", len(rows) == 16, f"{len(rows)} 行")
    if rows:
        ink = sum(r.count("#") for r in rows)
        check("「中」有足量笔画（>=20 点）", ink >= 20, f"{ink} 点")
        mid = "".join(r[7] for r in rows)
        check("「中」中列有竖笔（>=4 点）", mid.count("#") >= 4, mid)
        widest = max(r.count("#") for r in rows)
        check("「中」有横向笔画（最宽行 >=6 点）", widest >= 6, str(widest))


# ---------------------------------------------------------------- 2. 位序
def probe_bit_order() -> None:
    print("\n== 2. 点阵位序（16x16 / MSB-first / 不因裁剪错位） ==")
    from mrp_emu.fontgen import BYTES_PER_GLYPH, build_uc2

    data = build_uc2(include_gb=False)
    for ch in "帐号密":
        rows = glyph_rows(data, ch)
        if not check(f"「{ch}」字模可取", len(rows) == 16):
            continue
        # 每行 16 个字符 —— 行宽错乱会直接在这里暴露
        widths = {len(r) for r in rows}
        check(f"「{ch}」每行都是 16 像素", widths == {16}, str(widths))
        # 字形不能顶满整格（说明没有被糊成实心方块）
        ink = sum(r.count("#") for r in rows)
        check(f"「{ch}」不是实心方块（<200 点）", ink < 200, f"{ink} 点")
        # 左右两半不能一模一样（说明位序没有左右翻转）
        left = "".join(r[:8] for r in rows)
        right = "".join(r[8:] for r in rows)
        check(f"「{ch}」左右不对称（位序未翻转）", left != right)

    # 空白区必须是全 0
    blank_cp = 0x0001
    off = blank_cp * BYTES_PER_GLYPH
    check("控制字符区是空白",
          data[off:off + BYTES_PER_GLYPH] == b"\x00" * BYTES_PER_GLYPH)


# ---------------------------------------------------------------- 3. 原厂复用
def probe_factory_reuse() -> None:
    print("\n== 3. ensure_uc2：优先原厂字库 + 自动替换糊字库 ==")
    from mrp_emu.fontgen import (ensure_uc2, find_factory_font,
                                 check_font_quality, check_font_file)

    td = Path(tempfile.mkdtemp(prefix="pymrp-fontprobe-"))
    try:
        myth = td / "mythroad"
        fonts = myth / "fonts"
        fonts.mkdir(parents=True)
        system = myth / "system"
        system.mkdir(parents=True)

        # 3a. 有原厂字库 -> 应该复制过去
        src = fonts / "gb16.uc2"
        # 造一个「合法但不真」的 2MB 文件：结构对但内容是糊的
        # （用真实的糊字库当样本，见 out/gb16_ours_backup.uc2）
        factory = _sample_factory_font()
        src.write_bytes(factory)
        found = find_factory_font([fonts, system])
        check("能发现原厂字库", found is not None and found.name == "gb16.uc2",
              str(found))

        target = system / "gb16.uc2"
        ensure_uc2(target, log=lambda *a: None,
                   factory_dirs=[fonts, system])
        check("目标字库已就位", target.is_file(),
              f"{target.stat().st_size if target.is_file() else 0} 字节")
        if target.is_file():
            ok, why = check_font_file(target)
            check("复制的字库质量合格", ok, why)
            ok2, why2 = check_font_quality(target.read_bytes())
            check("字节级自检与抽样自检结论一致", ok2 == ok,
                  f"抽样={ok} {why} / 全量={ok2} {why2}")
            check("内容与原厂一致", target.read_bytes() == factory)

        # 3b. 已存在一份「糊」字库 -> 应该被自动识别并替换
        target.write_bytes(_sample_blurry_font())
        ok_before, why_before = check_font_quality(target.read_bytes())
        check("样本糊字库确实不合格（对照）", not ok_before, why_before)
        msgs: list[str] = []
        ensure_uc2(target, log=lambda m: msgs.append(str(m)),
                   factory_dirs=[fonts, system])
        check("自动替换了糊字库",
              target.read_bytes() == factory,
              f"{target.stat().st_size} 字节")
        check("日志说明了重准备原因",
              any("不合格" in m or "原厂" in m for m in msgs),
              " | ".join(msgs[-2:]))
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _sample_factory_font() -> bytes:
    """取一份原厂字库样本；发行包里有就用真的，没有就造结构相同的。"""
    real = ROOT / "runtime" / "mythroad" / "fonts" / "gb16.uc2"
    if real.is_file():
        return real.read_bytes()
    from mrp_emu.fontgen import BYTES_PER_GLYPH
    # 造一个「稀疏但合法」的字库：每个字模只有几个点
    buf = bytearray()
    for cp in range(0x10000):
        b = bytearray(BYTES_PER_GLYPH)
        for k in range(4):
            b[k] = 0x88
        buf += b
    return bytes(buf)


def _sample_blurry_font() -> bytes:
    """取一份「笔画粘连」的糊字库样本；用早期版本备份，没有就现场造。"""
    backup = ROOT / "mrp_emu" / "out" / "gb16_ours_backup.uc2"
    for p in (backup, ROOT / "out" / "gb16_ours_backup.uc2"):
        if p.is_file():
            return p.read_bytes()
    # 现场造一个糊的：墨迹率拉满
    from mrp_emu.fontgen import BYTES_PER_GLYPH
    buf = bytearray()
    for cp in range(0x10000):
        buf += b"\xff" * BYTES_PER_GLYPH
    return bytes(buf)


# ---------------------------------------------------------------- 4. 端到端
def probe_end_to_end() -> None:
    print("\n== 4. 端到端：启动 QQ 时字库必须可用 ==")
    runtime = ROOT / "runtime"
    if not (runtime / "cfunction.ext").is_file():
        print("  [skip] 没有 runtime/cfunction.ext，跳过")
        return
    mrp = runtime / "mythroad" / "QQDSM2007.mrp"
    if not mrp.is_file():
        print("  [skip] 没有 QQDSM2007.mrp，跳过")
        return

    import subprocess
    py = sys.executable
    out = subprocess.run(
        [py, str(ROOT / "run.py"), "--workdir", str(runtime), str(mrp),
         "--headless", "--frames", "150",
         "--screenshot", str(ROOT / "out" / "font_probe_shot.png")],
        capture_output=True, text=True, timeout=240)
    combined = out.stdout + out.stderr
    check("启动未崩溃", out.returncode == 0, f"rc={out.returncode}")
    check("字库加载成功（无 font load fail）",
          "font load fail" not in combined,
          "".join(l for l in combined.splitlines() if "font" in l.lower())[:200])
    check("字库质量自检通过或已采用原厂",
          "质量不合格" not in combined or "原厂字库" in combined,
          "")


def main() -> int:
    print("=" * 60)
    print("系统字库质量探针")
    print("=" * 60)
    probe_glyph_quality()
    probe_bit_order()
    probe_factory_reuse()
    probe_end_to_end()
    print("\n" + "=" * 60)
    print(f"通过 {PASSED} 项，失败 {FAILED} 项")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
