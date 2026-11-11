#!/usr/bin/env python3
"""生成 mythroad 平台层 thunk 桩（汇编）。

背景
----
`mrporting.h` 是官方留给宿主的平台接口面：mythroad.c 里所有真正碰
硬件/系统的东西都在这里 extern 声明，官方实现烧在真机 ROM 里。

我们要自己编译一个 mythroad 虚拟机，就必须在宿主侧补齐这些接口。
做法是给每个接口生成一个**汇编 thunk**：

    mr_open:
        ldr ip, [emu_slot_mr_open]   ; 取宿主分配的槽位地址
        bx ip                        ; 尾跳过去（LR 不变）

为什么必须用汇编而不是 C
------------------------
1. **不改栈**：C 写的 thunk 会被 gcc 插入 prologue（push 寄存器/lr），
   栈指针一变，宿主侧按 AAPCS 读变参（`mr_printf(const char*, ...)`）
   的位置就全错了。汇编 thunk 一个字节都不动栈。
2. **LR 不变**：尾跳 `bx ip` 不改 LR，宿主 hook 完把 PC 写回 LR 即
   直接返回调用者，栈天然平衡（汇编没 push 过东西）。
3. **不与 gcc 序言打架**：省掉「PC=LR 后要不要再 pop」的纠结。

生成物
------
* `emu_stub.s`  —— 91 个 thunk（每接口一个）
* `emu_slots.c` —— 槽位变量 + 名字表（名字表用于宿主侧按名字对齐）

用法:
    python tools/gen_emu_stub.py [--out-dir build/mythroad]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mrp_port import PlatformApi, parse_platform_apis   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MR_DIR = ROOT / "ref" / "mrpoid" / "mr"

# mythroad.c / src/ 自己实现了这些 —— 再定义会 duplicate symbol
SELF_IMPLEMENTED = {
    "mr_timer", "mr_event", "mr_stop", "mr_start_dsm", "mr_start_dsm_ex",
    "mr_start_dsmB", "mr_start_dsmC", "mr_pauseApp", "mr_resumeApp",
    "mr_registerAPP", "mr_newSIMInd", "mr_smsIndiaction",
}

# 标准 C 库封装 —— 由 emu_libc.c 在 C 侧直接实现（转发给 newlib）。
# 走 Python hook 的话每次 memcpy 都要跨一次引擎，太慢。
LIBC_WRAPPERS = {
    "mr_memcpy", "mr_memmove", "mr_memset", "mr_memcmp", "mr_memchr",
    "mr_strcpy", "mr_strncpy", "mr_strcat", "mr_strncat", "mr_strcmp",
    "mr_strncmp", "mr_strcoll", "mr_strlen", "mr_strstr", "mr_atoi",
    "mr_strtoul", "mr_rand",
    # vm_* 是 MEMCPY/MEMMOVE/MEMSET 宏的落点，同样在 C 侧实现
    "vm_memcpy", "vm_memmove", "vm_memset", "vm_strlen",
}


def collect_self_implemented() -> set[str]:
    """扫描 mythroad 源码，确认哪些平台接口官方自己实现了。"""
    found: set[str] = set()
    pattern = re.compile(
        r"^[A-Za-z_][\w\s\*]*?\b(mr_[A-Za-z_]\w*)\s*\([^;{]*\)\s*\{",
        re.MULTILINE,
    )
    for rel in ("mythroad.c", "src/mr_api.c", "src/mr_mem.c"):
        p = MR_DIR / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
        for m in pattern.finditer(text):
            found.add(m.group(1))
    return found


def gen_stub_s(apis: list[PlatformApi]) -> str:
    out: list[str] = []
    out.append("/* 由 tools/gen_emu_stub.py 生成，请勿手改。")
    out.append(" *")
    out.append(" * mythroad 平台层 thunk：每个官方平台接口一个。")
    out.append(" * 尾跳到宿主分配的钩子槽位，不改栈、不改 LR。")
    out.append(" */")
    out.append("")
    out.append("    .syntax unified")
    out.append("    .arm")
    out.append("    .text")
    out.append("")
    for a in apis:
        out.append(f"    .global {a.name}")
        out.append(f"    .type {a.name}, %function")
        out.append(f"{a.name}:")
        out.append(f"    ldr  ip, =emu_slot_{a.name}   @ 取槽位变量的地址")
        out.append("    ldr  ip, [ip]                @ 再取槽位里存的钩子地址")
        out.append("    bx   ip")
        out.append(f"    .size {a.name}, .-{a.name}")
        out.append("")
    out.append('    .section .note.GNU-stack,"",%progbits')
    return "\n".join(out) + "\n"


def gen_slots_c(apis: list[PlatformApi]) -> str:
    out: list[str] = []
    out.append("/* 由 tools/gen_emu_stub.py 生成，请勿手改。 */")
    out.append('#include "emu_port.h"')
    out.append("")
    out.append("/* 每个平台接口一个槽位变量：运行时由宿主填入钩子地址 */")
    for a in apis:
        out.append(f"void* emu_slot_{a.name};")
    out.append("")
    out.append("/* 名字表：宿主侧按名字建立钩子槽位，顺序必须与 emu_stub.s 一致 */")
    out.append('__attribute__((section(".emu_keep"), used))')
    out.append("const char* const emu_slot_names[] = {")
    for a in apis:
        out.append(f'    "{a.name}",')
    out.append("    0")
    out.append("};")
    out.append("")
    out.append('__attribute__((section(".emu_keep"), used))')
    out.append("const uint32 emu_slot_count = "
               f"{len(apis)};")
    out.append("")
    out.append("/* 把宿主给的钩子基址写进每个槽位变量。")
    out.append(" * 顺序必须与 emu_slot_names 一致 —— 宿主按同样的顺序建槽位，")
    out.append(" * 两边靠名字对齐。 */")
    out.append("void emu_bind_slots(void* hook_base)")
    out.append("{")
    out.append("    uint32 i = 0;")
    for a in apis:
        out.append(f"    emu_slot_{a.name} =")
        out.append(f"        (void*)((uint32)hook_base + (i++) * (uint32)sizeof(void*));")
    out.append("}")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(ROOT / "build" / "mythroad"))
    ap.add_argument("--exclude-file", default=None,
                    help="nm 扫出的「官方已实现」符号清单（每行一个）")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    apis = parse_platform_apis(MR_DIR / "mrporting.h")
    self_impl = collect_self_implemented() | SELF_IMPLEMENTED
    if args.exclude_file:
        p = Path(args.exclude_file)
        if p.is_file():
            names = {ln.strip() for ln in
                     p.read_text(encoding="utf-8").splitlines() if ln.strip()}
            self_impl |= names
    todo = [a for a in apis
            if a.name not in self_impl and a.name not in LIBC_WRAPPERS]

    (out_dir / "emu_stub.s").write_text(gen_stub_s(todo), encoding="utf-8")
    (out_dir / "emu_slots.c").write_text(gen_slots_c(todo), encoding="utf-8")

    print(f"平台接口总数     : {len(apis)}")
    print(f"官方自己实现     : {len(self_impl & {a.name for a in apis})}"
          f"  ({', '.join(sorted(self_impl & {a.name for a in apis}))})")
    print(f"需要宿主补齐     : {len(todo)}")
    print(f"  -> {out_dir / 'emu_stub.s'}")
    print(f"  -> {out_dir / 'emu_slots.c'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
