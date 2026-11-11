#!/usr/bin/env python3
"""自编译 mythroad 虚拟机的装载自检。

验证清单：
  1. ELF 能解析、段能装进 Unicorn
  2. 镜像自描述头 magic/version 正确
  3. 钩子名字表能读出，槽位地址写对
  4. host_api 表能读出，地址落在镜像内
  5. emu_self_test() 返回魔数（证明镜像可执行、栈可用）

用法：
    python tests/mythroad_probe.py [镜像路径]
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mrp_emu.elfload import parse_elf32            # noqa: E402
from mrp_emu.mythroad_vm import (                  # noqa: E402
    EMU_MAGIC, HOOK_BASE, VM_BASE, MythroadVm,
)

DEFAULT_IMAGES = [
    ROOT.parent / "tools" / "mythroad" / "mythroad_vm.elf",
    ROOT / "runtime" / "mythroad_vm.elf",
]

FAILS: list[str] = []


def check(cond: bool, label: str, detail: str = "") -> bool:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILS.append(label)
    return cond


def find_image() -> Path | None:
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        return p if p.is_file() else None
    for p in DEFAULT_IMAGES:
        if p.is_file():
            return p
    return None


def main() -> int:
    img = find_image()
    if img is None:
        print("找不到 mythroad_vm.elf")
        print("  先编译：cd tools/mythroad && make")
        print("  默认查找：")
        for p in DEFAULT_IMAGES:
            print(f"    {p}")
        return 2

    print(f"=== mythroad 虚拟机装载自检: {img} ===\n")

    # 1. ELF 结构
    print("1) ELF 结构")
    e = parse_elf32(img)
    check(len(e.segments) > 0, "有 PT_LOAD 段", f"{len(e.segments)} 个")
    check(e.load_base == VM_BASE, "链接基址符合约定",
          f"0x{e.load_base:X}（期望 0x{VM_BASE:X}）")
    size_kb = (e.load_end - e.load_base) // 1024
    check(size_kb < 2048, "镜像大小在预算内", f"{size_kb}KB")

    # 2. 装载
    print("\n2) 装载进 Unicorn")
    try:
        vm = MythroadVm(img)
    except Exception as exc:                      # noqa: BLE001
        check(False, "装载", str(exc))
        return 1
    check(True, "装载完成")
    check(vm.version == 1, "版本号", str(vm.version))

    # 3. 钩子表
    print("\n3) 钩子表")
    check(vm.n_slots > 50, "槽位数量合理", f"{vm.n_slots} 个")
    check(len(vm.slot_names) == vm.n_slots,
          "名字表与数量一致", f"{len(vm.slot_names)}")
    # 注意：mr_drawText / mr_bufToScreen / mr_getScreenBuf 在 mrporting.h 里
    # 位于 #if 0 块内（"厂商屏幕缓冲模式"专用），mythroad 走的是
    # mr_platDrawCharReal / mr_drawBitmap 直接画进屏幕缓冲，所以不在槽位表里。
    missing = [n for n in ("mr_open", "mr_read", "mr_write",
                           "mr_playSound", "mr_getUserInfo", "mr_mem_get",
                           "mr_drawBitmap", "mr_platDrawCharReal")
               if n not in vm.slot_names]
    check(not missing, "关键接口都在槽位表里",
          "缺 " + ", ".join(missing) if missing else "")
    # 槽位值必须是自身地址
    bad = []
    for i, name in enumerate(vm.slot_names):
        a = HOOK_BASE + i * 4
        if struct.unpack("<I", vm.uc.mem_read(a, 4))[0] != a:
            bad.append(name)
    check(not bad, "槽位值 = 自身地址", f"异常 {bad[:3]}" if bad else "")

    # 4. host_api
    print("\n4) host_api（宿主可反向调用的官方函数）")
    check(bool(vm.host_api), "表非空", f"{len(vm.host_api)} 项")
    bad = [k for k, v in vm.host_api.items()
           if not (e.load_base <= v < e.load_end)]
    check(not bad, "地址都落在镜像内",
          f"越界 {bad}" if bad else "")
    for k in ("mr_event", "mr_timer", "mr_start_dsm"):
        check(k in vm.host_api and vm.host_api[k] != 0,
              f"{k} 可调用", f"0x{vm.host_api.get(k, 0):X}")

    # 5. 执行
    print("\n5) 执行自检函数")
    try:
        v = vm.self_test()
    except Exception as exc:                      # noqa: BLE001
        check(False, "调用 self_test", str(exc))
        v = 0
    check(v == EMU_MAGIC, "返回魔数", f"0x{v:X}（期望 0x{EMU_MAGIC:X}）")

    print("\n" + "=" * 52)
    if FAILS:
        print(f"失败 {len(FAILS)} 项: " + "; ".join(FAILS))
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
