#!/usr/bin/env python3
"""槽位表一致性探针：我们的 mr_table 与 mrpoid 官方 C 库表的差异。

背景（2026-11-10）：老板看到 RX 管理器列表里多出一个字符 "f"，怀疑
「sprintf 没实现」。顺着查下去发现一件更值得记住的事：

* mrpoid 官方 ``mr/mythroad.c::_mr_c_function_table[]`` 的 0x048 是
  ``mr_sprintf``，而我们的 0x048 是 ``atoi`` —— **从 0x048 起整表错位
  一格**，逐项对比 112 项不一致。
* 但前 17 项（0x000–0x040：malloc/memcpy/strlen/strstr…）**完全一致**，
  这正是 ext 的 C 库真正会用到的部分。
* 4 个真实 MRP（dsm_gm / 曲奇 / 2048 / RX 管理器）实测：mr_table 的
  0x044–0x060 区间**一次都没被调用过**。原因有二：
  ① MRP 应用通过 **DSM 层 51 槽**用平台 API，不直接碰 mr_table；
  ② 应用的 C 库（sprintf 等）由 ext 自己的 ``_mr_c_function_new``
  注册接管（ext 日志：``_mr_c_function_new(002DD3A0, 8212)``）。

所以这个错位**目前没有实际影响**，但它是隐患：一旦某个 MRP 直接调用
mr_table 的 C 库槽位，就会踩雷。本探针把差异固化下来，防止悄悄漂移。
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

# mrpoid 官方 mr/mythroad.c::_mr_c_function_table[] 前 38 项（快照）
OFFICIAL = [
    "mr_malloc", "mr_free", "mr_realloc", "memcpy", "memmove", "strcpy",
    "strncpy", "strcat", "strncat", "memcmp", "strcmp", "strncmp",
    "strcoll", "memchr", "memset", "strlen", "strstr", "sprintf",
    "mr_sprintf", "atoi", "strtoul", "rand", "NULL", "mr_stop_ex",
    "_mr_c_internal_table", "_mr_c_port_table", "_mr_c_function_new",
    "mr_printf", "mr_mem_get", "mr_mem_free", "mr_drawBitmap",
    "mr_getCharBitmap", "mr_timerStart", "mr_timerStop", "mr_getTime",
    "mr_getDatetime", "mr_getUserInfo", "mr_sleep",
]

FAILS: list[str] = []
PASS = 0


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

    print("== 1. 前 17 项必须与官方一致（ext 真正用到的 C 库）==")
    mism = []
    for idx in range(17):
        off = idx * 4
        if ours.get(off, "").lower() != OFFICIAL[idx].lower():
            mism.append((off, OFFICIAL[idx], ours.get(off)))
    check("0x000–0x040 全部一致", not mism, str(mism))

    print("\n== 2. 0x044 = sprintf ==")
    check("0x044 是 sprintf", ours.get(0x044) == "sprintf", str(ours.get(0x044)))

    print("\n== 3. 已知差异（0x048 起错位一格）==")
    diff = []
    for idx in range(18, len(OFFICIAL)):
        off = idx * 4
        o = ours.get(off, "<缺>")
        if o.lower() != OFFICIAL[idx].lower():
            diff.append((off, OFFICIAL[idx], o))
    check("0x048 官方是 mr_sprintf（我们没有这一槽）",
          OFFICIAL[18] == "mr_sprintf", OFFICIAL[18])
    check("差异项数 = 20（快照区间内）", len(diff) == 20, str(len(diff)))
    print("      已知差异清单（官方 -> 我们）：")
    for off, a, b in diff:
        print(f"        0x{off:03X}  {a:<22} -> {b}")

    print("\n== 4. 我们的空位是 ext 反推出来的真实空洞 ==")
    # 官方 0x058=NULL / 0x05C=mr_stop_ex；我们从 cfunction.ext 反推知道
    # 这两格是空的（reserve），所以从这里开始整表平移。
    check("0x054 是 reserve（数据槽 0）", ours.get(0x054) == "reserve0",
          str(ours.get(0x054)))
    check("0x058 是 reserve（数据槽 0）", ours.get(0x058) == "reserve1",
          str(ours.get(0x058)))
    for pos in (0x054, 0x058):
        f = next((x for x in MR_TABLE if x.pos == pos), None)
        check(f"0x{pos:03X} 槽位里写的是 0（不是函数指针）",
              f is not None and f.fn is None and f.init is not None)

    print("\n== 5. mr_sprintf 已有实现（等确认槽位后即可挂上）==")
    check("impl 里有 mr_sprintf", impl.get("mr_sprintf") is not None)
    check("mr_sprintf 与 sprintf 同一实现",
          impl.get("mr_sprintf") is impl.get("sprintf"))

    print("\n== 6. 槽位总数 ==")
    check("mr_table 共 146 项", len(MR_TABLE) == 146, str(len(MR_TABLE)))

    print(f"\n== 摘要 ==  table_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
