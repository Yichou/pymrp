#!/usr/bin/env python3
"""自检：验证 ARM 执行、内存共享、桥接调用、图形输出。

不依赖任何 MRP 文件 —— 用硬编码 ARM 机器码直接调桥接槽位，
等于人工当了一次 cfunction.ext。
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.init()

from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.consts import CODE_ADDRESS  # noqa: E402
from mrp_emu.ui.phone import PhoneUI  # noqa: E402
from mrp_emu.ui.skin import build_default  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)


def main() -> int:
    logs: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="mrp_selftest_"))

    print("\n== 1. 函数表 ==")
    check("mr_table 146 项 (0x0..0x244)", len(MR_TABLE) == 146, f"实际 {len(MR_TABLE)}")
    check("dsm_require_funcs 51 项 (0x0..0xc8)", len(DSM_FUNCS) == 51, f"实际 {len(DSM_FUNCS)}")

    print("\n== 2. 引擎初始化 ==")
    vm = Vm(log=logs.append)
    app = App(vm, tmp, log=logs.append)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    for line in logs:
        print("      " + line)
    logs.clear()

    check("mr_table 基址在堆区", vm.mem.heap.base <= vm.mr_table < vm.mem.heap.base + vm.mem.heap.size,
          f"0x{vm.mr_table:X}")
    check("dsm 表基址在堆区", vm.mem.heap.base <= vm.dsm_funcs < vm.mem.heap.base + vm.mem.heap.size,
          f"0x{vm.dsm_funcs:X}")
    check("mr_screenBuf 槽位 == 帧缓冲", vm.mem.u32(vm.mr_table + 0x16C) == app.gfx.fb_addr,
          f"0x{vm.mem.u32(vm.mr_table + 0x16C):X}")
    check("mr_screen_w == 240", vm.mem.u32(vm.mr_table + 0x170) == 240)
    check("mr_screen_h == 320", vm.mem.u32(vm.mr_table + 0x174) == 320)
    check("dsm flags 已设置", vm.mem.u32(vm.dsm_funcs + 0xC8) == 2,
          f"= {vm.mem.u32(vm.dsm_funcs + 0xC8)}")

    print("\n== 3. ARM 执行 + 桥接调用（核心） ==")

    def run_arm(code_words: list[int], extra: list[int], stop_off: int) -> None:
        blob = b"".join(struct.pack("<I", w) for w in code_words + extra)
        addr = 0x90000
        vm.mem.write(addr, blob)
        vm.uc.emu_start(addr, addr + stop_off, 0, 0)

    # 调用 mr_malloc(64)
    slot_malloc = vm.mr_table + 0x00
    run_arm(
        [0xE3A00040,          # mov r0, #64
         0xE59F3004,          # ldr r3, [pc, #4]
         0xE12FFF33,          # blx r3
         0xEAFFFFFE],         # b .
        [slot_malloc],
        stop_off=0x0C,
    )
    ptr = vm.uc.reg_read(UC_ARM_REG_R0)
    check("mr_malloc(64) 返回有效指针", vm.mem.heap.base <= ptr < vm.mem.heap.base + vm.mem.heap.size,
          f"0x{ptr:X}")
    check("分配器记账正确", ptr in vm.mem.heap.used, f"size={vm.mem.heap.used.get(ptr)}")

    # 调用 mr_getScreenInfo(buf)
    outbuf = 0x90200
    slot_screen = vm.mr_table + 0x140
    run_arm(
        [0xE59F0008,          # ldr r0, [pc, #8]  -> outbuf
         0xE59F3008,          # ldr r3, [pc, #8]  -> slot
         0xE12FFF33,          # blx r3
         0xEAFFFFFE],
        [outbuf, slot_screen],
        stop_off=0x0C,
    )
    check("mr_getScreenInfo 写入宽度 240", vm.mem.u32(outbuf) == 240, f"= {vm.mem.u32(outbuf)}")
    check("mr_getScreenInfo 写入高度 320", vm.mem.u32(outbuf + 4) == 320, f"= {vm.mem.u32(outbuf + 4)}")

    # 调用 mr_getDatetime(buf)
    slot_dt = vm.mr_table + 0x88
    dtbuf = 0x90220
    run_arm(
        [0xE59F0008, 0xE59F3008, 0xE12FFF33, 0xEAFFFFFE],
        [dtbuf, slot_dt],
        stop_off=0x0C,
    )
    check("mr_getDatetime 年份合理", 2020 <= vm.mem.u16(dtbuf) <= 2100, f"= {vm.mem.u16(dtbuf)}")

    # 调用 mr_getTime()
    slot_time = vm.mr_table + 0x84
    run_arm(
        [0xE59F3004, 0xE12FFF33, 0xEAFFFFFE],
        [slot_time],
        stop_off=0x08,
    )
    ts = vm.uc.reg_read(UC_ARM_REG_R0)
    check("mr_getTime 返回 Unix 时间", ts > 1_700_000_000, f"= {ts}")

    print("\n== 4. 文件系统 ==")
    (tmp / "hello.dat").write_bytes(b"MRP" * 10)
    fh = app.fs.open("hello.dat", 0x01)
    check("open 成功", fh > 0, f"handle={fh}")
    data = app.fs.read(fh, 9)
    check("read 内容正确", data == b"MRPMRPMRP", f"={data!r}")
    app.fs.close(fh)
    check("getLen 正确", app.fs.get_len("hello.dat") == 30, f"={app.fs.get_len('hello.dat')}")
    check("info 识别为文件", app.fs.info("hello.dat") == 1)
    # 2026-11-10：语义改为「钳制在 root 内」而不是返回 NULL。
    # 返回 NULL 会让 ext 把空结果当 NULL 字符串交给 sprintf("%s")，
    # 在 Unicorn 里解引用地址 0 直接崩（RX 管理器实测）。
    _esc = app.fs.resolve("../../etc/passwd")
    check("沙箱把 ../ 钳制在 root 内",
          _esc is not None and _esc.is_relative_to(app.fs.root), str(_esc))

    print("\n== 5. 图形 ==")
    px = 0xF800  # 红
    buf = 0x90400
    vm.mem.write(buf, struct.pack("<H", px) * (10 * 10))
    app.gfx.draw_bitmap(buf, 5, 5, 10, 10)
    check("drawBitmap 生效", app.gfx.array()[5, 5] == px, f"={app.gfx.array()[5,5]:#06x}")
    app.gfx.fill_rect(0, 0, 240, 20, 0x001F)  # 蓝
    check("fill_rect 生效", app.gfx.array()[0, 0] == 0x001F)

    print("\n== 6. MTK 直板机渲染 ==")
    ui = PhoneUI(build_default())
    app.gfx.overlay_clear()
    app.gfx.status_bar("中国移动", "19:50")
    app.gfx.text_center("MRP 模拟器", 120, 140, (240, 246, 255), size=20)
    app.gfx.soft_keys("选项", "返回")
    frame = ui.draw(app.gfx.surface())
    check("画面尺寸正确", frame.get_size() == (300, 660), str(frame.get_size()))

    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    shot = out / "selftest_phone.png"
    pygame.image.save(frame, str(shot))
    check("截图已生成", shot.is_file(), f"{shot} ({shot.stat().st_size} 字节)")

    # 命中测试
    hit_nav = ui.hit((150, 438))
    hit_1 = ui.hit((70, 523)) if ui.keys else None
    check("导航盘命中", hit_nav == "nav:SELECT", str(hit_nav))
    k5 = [k for k in ui.keys if k["label"] == "5"][0]
    x, y, w, h = k5["rect"]
    check("数字键 5 命中", ui.hit((x + w // 2, y + h // 2)) == k5["id"])
    check("键值映射 5 -> 5", ui.key_code("k54") == 5 if "k54" in [k["id"] for k in ui.keys] else True)
    check("软键映射", ui.key_code("soft_l") == 17, str(ui.key_code("soft_l")))

    print("\n== 7. 摘要 ==")
    print("  " + app.report().replace("\n", "\n  "))

    if FAILS:
        print(f"\n失败 {len(FAILS)} 项: {', '.join(FAILS)}")
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
