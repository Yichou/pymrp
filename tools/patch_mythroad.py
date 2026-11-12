#!/usr/bin/env python3
"""给 mrpoid 的 `mythroad.c` 打移植补丁。

## 背景：斯凯扩展机制的加载入口

MRP 应用（TOM 字节码）会调用包内 `.ext` 里的 C 函数扩展自己。应用的
常量表里能直接看到这些名字：

| 应用 | 相关标识符 |
|---|---|
| `dsm_gm.mrp` | `c_load` |
| `gxrxd.mrp` | `_mr_c_load` |

而 mrpoid **自己并不注册这两个 Lua 全局**（`grep mrp_register mythroad.c`
里只有 `_com`/`_strCom` 等 81 个，没有 `c_load`）。它们是**平台（宿主）
注册**的 —— 老架构里那个 331KB 的宿主级 `cfunction.ext` 干的就是这件事。

本补丁把这两个入口注册进 mythroad 的 Lua 全局表，并提供两种实现：

* `MRP_C_LOAD_STUB`（默认）：桩实现，记录调用后返回 nil（相当于"扩展没找到"）。
  用来验证**应用没有 .ext 能不能继续跑** —— 这是决定后续工作量的分叉点。
* 真正实现：调用平台接口 `mr_c_function_load`（见 `mythroad.h:264`），
  由宿主负责读包内 `.ext`、加载其 ARM 代码段。

## 补丁位置

`mythroad.c` 里 `mrp_register(vm_state, "_com", MRF_TestCom);` 附近 ——
那里正在集中注册 Lua 全局。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ANCHOR = 'mrp_register(vm_state, "_com", MRF_TestCom);'
TOP_ANCHOR = '#include "mrporting.h"'

STUB = '''
/* ================= 【移植补丁】斯凯扩展加载入口 ================= */
#ifdef MRP_C_LOAD_STUB
/* 桩实现：只记录调用，返回 nil（= 扩展没找到）。
 * 用来验证「应用没有 .ext 能不能继续跑」—— 决定后续工作量。 */
static int MRF_c_load_stub(mrp_State* L)
{
   const char* nm = (const char*)mrp_tostring(L, 1);
   mr_printf("[c_load] stub called: %s", nm ? nm : "(null)");
   mrp_pushnil(L);
   return 1;
}
#else
/* 真正实现：交给平台的 mr_c_function_load（mythroad.h:264）。
 * 平台负责：读包内 .ext -> 解析 MRPG/CMAP -> 加载 ARM 代码 -> 调入口。 */
static int MRF_c_load(mrp_State* L)
{
   const char* nm = (const char*)mrp_tostring(L, 1);
   int32 code = (int32)mrp_tonumber(L, 1);
   int32 ret;

   mr_printf("[c_load] request: %s (code=%d)", nm ? nm : "(null)", (int)code);
   ret = mr_c_function_load(code);
   mr_printf("[c_load] mr_c_function_load -> %d", (int)ret);
   if (ret == MR_SUCCESS) {
      mrp_pushnumber(L, (mrp_Number)MR_SUCCESS);
   } else {
      mrp_pushnil(L);
   }
   return 1;
}
#endif
/* ================================================================ */
'''

REGISTER = '''
   /* 【移植补丁】注册斯凯扩展加载入口（平台提供的全局） */
#ifdef MRP_C_LOAD_STUB
   mrp_register(vm_state, "c_load", MRF_c_load_stub);
   mrp_register(vm_state, "_mr_c_load", MRF_c_load_stub);
#else
   mrp_register(vm_state, "c_load", MRF_c_load);
   mrp_register(vm_state, "_mr_c_load", MRF_c_load);
#endif
'''


def patch(text: str) -> tuple[str, bool]:
    if "移植补丁】斯凯扩展加载入口" in text:
        return text, False
    if ANCHOR not in text:
        # 锚点变了：退一步按 "mrp_register(vm_state, \"_com\"" 找
        m = re.search(r'mrp_register\(vm_state,\s*"_com"[^;]*;', text)
        if not m:
            raise SystemExit("找不到注册锚点，无法打补丁")
        anchor = m.group(0)
    else:
        anchor = ANCHOR

    # 1) 桩/真实现必须放在**文件作用域**（锚点所在的是函数体内部）
    if TOP_ANCHOR not in text:
        raise SystemExit("找不到顶部锚点，无法打补丁")
    text = text.replace(TOP_ANCHOR, TOP_ANCHOR + "\n" + STUB.strip("\n"), 1)
    # 2) 在锚点后插入注册
    text = text.replace(anchor, anchor + "\n" + REGISTER.strip("\n"), 1)
    return text, True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ref/mrpoid/mr/mythroad.c")
    ap.add_argument("--out", default="tools/mythroad/patched_mythroad.c")
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    text = src.read_text(encoding="utf-8", errors="replace")
    new, changed = patch(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(new, encoding="utf-8")
    print(f"[patch] {src} -> {out}  {'已打补丁' if changed else '无需补丁'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
