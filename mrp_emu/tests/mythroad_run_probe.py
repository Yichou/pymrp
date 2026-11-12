#!/usr/bin/env python3
"""自编译 mythroad VM 里真跑一个 MRP 应用。

这是阶段 2 的验收点：不是「能装载」，而是**官方 mythroad 运行时真的把
一个 MRP 应用跑起来了**（TOM 解释器执行 start.mr 字节码、应用调平台接口）。

检查项：
  1. 平台接口绑定情况（70 个槽位里绑了多少）
  2. mr_start_dsm_ex 返回值
  3. mythroad 自己分配的帧缓冲（mr_screenBuf）地址与内容
  4. 事件循环：mr_timer / mr_event 能否正常推进
  5. 帧缓冲里是否真的画上了东西（统计非零像素）

用法：
    python tests/mythroad_run_probe.py [mrp路径] [--dump 输出png]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mrp_emu.mythroad_app import MythroadApp          # noqa: E402
from mrp_emu.mythroad_port import bind_platform       # noqa: E402
from mrp_emu.mythroad_vm import MythroadVm            # noqa: E402

IMAGE = ROOT.parent / "tools" / "mythroad" / "mythroad_vm.elf"
WORKDIR = ROOT / "runtime"
FONT = WORKDIR / "mythroad" / "fonts" / "gb16.uc2"

FAILS: list[str] = []
LOGS: list[str] = []


def log(msg: str) -> None:
    LOGS.append(msg)
    if "--verbose" in sys.argv:
        print(msg)


def check(cond: bool, label: str, detail: str = "") -> bool:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILS.append(label)
    return cond


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mrp = Path(args[0]) if args else WORKDIR / "mythroad" / "dsm_gm.mrp"

    print("=== 自编译 mythroad VM：真实启动 MRP ===\n")
    print(f"镜像  : {IMAGE}")
    print(f"工作目录: {WORKDIR}")
    print(f"应用  : {mrp}")
    print(f"字库  : {FONT} ({'有' if FONT.is_file() else '无'})\n")

    if not IMAGE.is_file():
        print("找不到镜像，先编译：cd tools/mythroad && make")
        return 2

    # ---------------------------------------------------------- 装载
    vm = MythroadVm(IMAGE, log=log, font_path=FONT if FONT.is_file() else None)
    vm.debug_printf = "--printf" in sys.argv
    app = MythroadApp(vm, WORKDIR, log=log)
    vm.app = app

    bound, missing = bind_platform(vm)
    print(f"平台接口绑定: {len(bound)}/{len(vm.slot_names)}")
    if missing:
        print(f"  未绑定({len(missing)}): {' '.join(missing)}")
    check(len(bound) >= 60, "多数平台接口已绑定", f"{len(bound)} 个")

    # ---------------------------------------------------------- 启动
    # mythroad 用 mr_start_dsm_ex 的 "#<" 前缀指定包
    pack = f"#<{mrp.name}"
    rel = mrp.relative_to(WORKDIR).as_posix() if mrp.is_relative_to(WORKDIR) else mrp.name
    pack = f"#<{rel}"

    print("\n启动中...")
    try:
        r = vm.start_app(pack)
    except Exception as exc:                          # noqa: BLE001
        import traceback
        check(False, "启动未抛异常", str(exc))
        print("\n".join(traceback.format_exc().splitlines()[-14:]))
        print("\n".join(LOGS[-25:]))
        return 1
    print(f"  mr_start_dsm_ex({pack!r}, 'start.mr') -> {r}")
    check(r in (0, 1), "启动返回成功", f"r={r}")

    # ---------------------------------------------------------- 帧缓冲
    fb = vm.screen_buf_addr()
    check(fb != 0, "mythroad 已分配帧缓冲", f"0x{fb:X}")

    gfx = app.gfx.resolve()
    check(gfx.fb_addr == fb, "Gfx 绑定到 mythroad 的帧缓冲", f"0x{gfx.fb_addr:X}")

    # ---------------------------------------------------------- 画面内容
    if fb:
        raw = vm.mem.read(fb, gfx.size_bytes)
        nonzero = sum(1 for b in raw[0::2] if b) + sum(1 for b in raw[1::2] if b)
        check(nonzero > 0, "帧缓冲里有内容", f"非零字节 {nonzero}")
        if "--dump" in sys.argv:
            out = Path(sys.argv[sys.argv.index("--dump") + 1])
            try:
                import numpy as np
                from PIL import Image
                arr = np.frombuffer(raw, dtype="<u2").reshape(gfx.h, gfx.w)
                r = ((arr >> 11) & 0x1F) * 255 // 31
                g = ((arr >> 5) & 0x3F) * 255 // 63
                b = (arr & 0x1F) * 255 // 31
                Image.fromarray(np.stack([r, g, b], -1).astype("uint8")).save(out)
                print(f"  截图: {out}")
            except Exception as exc:                  # noqa: BLE001
                print(f"  截图失败: {exc}")

    # ---------------------------------------------------------- 事件循环
    print("\n事件循环...")
    timers = 0
    for i in range(5):
        try:
            v = vm.mr_timer()
        except Exception as exc:                      # noqa: BLE001
            check(False, "mr_timer 正常", str(exc))
            break
        timers += 1
    check(timers == 5, "mr_timer 连跑 5 次无异常", f"{timers}/5")

    # 按键
    try:
        k = vm.mr_event(0, 17, 0)     # MR_KEY_PRESS, 左软键
        check(True, "mr_event 送按键", f"ret={k}")
    except Exception as exc:                          # noqa: BLE001
        check(False, "mr_event 送按键", str(exc))

    # ---------------------------------------------------------- 结果
    print("\n平台接口调用序列 (前 40 个):")
    seq = vm.call_seq[:40]
    for i in range(0, len(seq), 8):
        print("   " + " ".join(seq[i:i + 8]))
    print(f"总计 {len(vm.call_seq)} 次调用")
    from collections import Counter
    print("按接口统计: " + ", ".join(
        f"{k}={v}" for k, v in Counter(vm.call_seq).most_common(12)))

    print("\n" + "=" * 56)
    if FAILS:
        print(f"失败 {len(FAILS)} 项: " + "; ".join(FAILS))
        if LOGS:
            print("\n--- 末尾日志 ---")
            print("\n".join(LOGS[-20:]))
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
