#!/usr/bin/env python3
"""槽位表一致性探针：我们的 mr_table 对齐斯凯 mythroad 官方 C 库表。

**关键：斯凯有两张 C 库表，别比错对象。**

| 表 | 出处 | 给谁用 | 0x044 | 0x048 |
|---|---|---|---|---|
| mythroad 层 | `mythroad/mythroad.c::_mr_c_function_table` | **斯凯 mythroad 引擎 / DSM 应用** | `mr_sprintf` | `mr_atoi` |
| mr 层 | `mr/mythroad.c::_mr_c_function_table` | MRP 应用（另一套栈） | `sprintf` | `mr_sprintf` |

mr 层比 mythroad 层**多一个 `mr_sprintf`**（0x048），所以整表往后差一格 ——
拿错表比，会得出「我们错位 112 项」的错误结论（2026-11-10 踩过）。

我们的 `cfunction.ext` 是 mythroad 引擎的扩展，所以**按 mythroad 层对齐**。
2026-11-10 补齐后，0x000–0x07C 与官方逐项一致（唯一补的是 0x058 的
`mr_stop_ex`，此前是空位 → 应用一调就跳地址 0）。

回归见 `tests/table_probe.py`、`tests/fmt_probe.py`，复盘见
`docs/19-sprintf与槽位表排查.md`。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mrp_emu.api import impl  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402

# mythroad/mythroad.c::_mr_c_function_table 前 32 项（斯凯 mythroad 引擎权威顺序）
OFFICIAL = [
    "mr_malloc", "mr_free", "mr_realloc", "mr_memcpy", "mr_memmove",
    "mr_strcpy", "mr_strncpy", "mr_strcat", "mr_strncat", "mr_memcmp",
    "mr_strcmp", "mr_strncmp", "mr_strcoll", "mr_memchr", "mr_memset",
    "mr_strlen", "mr_strstr", "mr_sprintf", "mr_atoi", "mr_strtoul",
    "mr_rand", "NULL", "mr_stop_ex", "_mr_c_internal_table",
    "_mr_c_port_table", "_mr_c_function_new", "mr_printf", "mr_mem_get",
    "mr_mem_free", "mr_drawBitmap", "mr_getCharBitmap", "mr_timerStart",
]

# mr 层那张表（mr/mythroad.c）的前 20 项，留作对照：它多一个 mr_sprintf
MR_LAYER = [
    "mr_malloc", "mr_free", "mr_realloc", "mr_memcpy", "mr_memmove",
    "mr_strcpy", "mr_strncpy", "mr_strcat", "mr_strncat", "mr_memcmp",
    "mr_strcmp", "mr_strncmp", "mr_strcoll", "mr_memchr", "mr_memset",
    "mr_strlen", "mr_strstr", "sprintf", "mr_sprintf", "atoi",
]

FAILS: list[str] = []
PASS = 0


def norm(name: str) -> str:
    """规范化函数名：去掉 mr_ / _ 前缀，便于跨层比较。"""
    return name.lower().lstrip("_").removeprefix("mr_")


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS
    if ok:
        PASS += 1
        print(f"  [PASS] {name}" + (f"  {detail}" if detail else ""))
    else:
        FAILS.append(name)
        print(f"  [FAIL] {name}  {detail}")


def main() -> int:
    ours = {f.pos: f.name for f in MR_TABLE}

    print("== 1. 0x000–0x07C 与 mythroad 官方逐项对齐 ==")
    mism = []
    for idx, name in enumerate(OFFICIAL):
        off = idx * 4
        o = ours.get(off, "<缺>")
        if name == "NULL":
            if o.startswith("reserve"):
                continue
            mism.append((off, name, o))
            continue
        if norm(o) != norm(name):
            mism.append((off, name, o))
    check(f"前 {len(OFFICIAL)} 项全部对齐", not mism, str(mism))

    print("\n== 2. 关键槽位 ==")
    check("0x044 = sprintf（官方 mr_sprintf）", ours.get(0x044) == "sprintf",
          str(ours.get(0x044)))
    check("0x048 = atoi（mythroad 层；mr 层才是 mr_sprintf）",
          ours.get(0x048) == "atoi", str(ours.get(0x048)))
    check("0x054 = 保留位（官方 NULL，数据槽 0）",
          ours.get(0x054, "").startswith("reserve"), str(ours.get(0x054)))
    check("0x058 = mr_stop_ex（此前是空位）", ours.get(0x058) == "mr_stop_ex",
          str(ours.get(0x058)))
    check("0x05C = _mr_c_internal_table", ours.get(0x05C) == "_mr_c_internal_table",
          str(ours.get(0x05C)))
    check("0x074 = mr_drawBitmap", ours.get(0x074) == "mr_drawBitmap",
          str(ours.get(0x074)))
    check("0x078 = mr_getCharBitmap", ours.get(0x078) == "mr_getCharBitmap",
          str(ours.get(0x078)))

    print("\n== 3. mr 层那张表的差异（说明为什么不能拿它比）==")
    diff = [(i * 4, a, ours.get(i * 4, "")) for i, a in enumerate(MR_LAYER)
            if norm(ours.get(i * 4, "")) != norm(a)]
    check("与 mr 层确有差异（两张表不是一回事）", len(diff) > 0, f"{len(diff)} 项")
    print("      mr 层 -> 我们（0x048 起分道扬镳）：")
    for off, a, b in diff[:6]:
        print(f"        0x{off:03X}  mr 层={a:<16} 我们={b}")

    print("\n== 4. mr_stop_ex 实现 ==")
    check("impl 里有 mr_stop_ex", impl.get("mr_stop_ex") is not None)
    check("mr_stop_ex 已挂到 0x058 槽位",
          any(f.pos == 0x058 and f.name == "mr_stop_ex" for f in MR_TABLE))

    print("\n== 5. mr_sprintf（mr 层 API）已实现 ==")
    check("impl 里有 mr_sprintf", impl.get("mr_sprintf") is not None)
    check("mr_sprintf 与 sprintf 同一实现",
          impl.get("mr_sprintf") is impl.get("sprintf"))

    print("\n== 6. 槽位总数 ==")
    check("mr_table 共 146 项", len(MR_TABLE) == 146, str(len(MR_TABLE)))

    print(f"\n== 摘要 ==  table_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
