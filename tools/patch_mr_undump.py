#!/usr/bin/env python3
"""给 mrpoid 的 `src/mr_undump.c` 打一个补丁。

## 为什么需要

MRP 应用的字节码里，**number 常量按 4 字节 float 存储**（斯凯平台的编译器
产物）。而 mrpoid 的解释器默认 `mrp_Number = double`（8 字节）。

`mr_undump.c` 的 `LoadHeader` 里本来有一段大小检查：

```c
if (version > VERSION_50) {
    /* 空 —— 新版本跳过全部 size 检查 */
} else {
    TESTSIZE(sizeof(mrp_Number), "number");
    x = LoadNumber(S);
    if ((long)x != (long)tx) mr_G_runerror(...);
}
```

应用的字节码头是 `\\x1bMRP` + version `0x80`，**0x80 > VERSION_50(0x50)**，
于是这段检查被跳过 —— 解释器按 8 字节 double 读常量表，
而应用写的是 4 字节 float。

**后果**：常量表从第一个数字常量起整体错位 4 字节，后面的字符串常量、
函数指针全部读成垃圾 → 解释器把垃圾当函数地址去调用 →
`Invalid instruction`，PC 落在 mythroad 堆里。

实测（用 Python 按两种宽度解析同一个 `start.mr`）：

```
按 double:  [8] num 8.1569518204705e-311   [9] nil   [10] ?? type83   ← 全乱
按 float :  [8] num 0.0  [9] str 'ShowQQmainlist'  [10] str 'LoginStatus'  ← 完全可读
```

## 补丁内容

只改 `LoadNumber`：按 4 字节 float 读，转成 double 返回。

* 解释器**内部**仍然用 double 运算（`mrp_Number` 不变），
  只有**常量表的存储宽度**变了 —— 预编译常量里的 float 转 double 是精确的 ✅
* 运行时算出来的数字走 `mr_pushnumber`（double），不受影响 ✅

用编译期宏 `MRP_UNDUMP_FLOAT_NUMBER` 控制，方便回退。

## 用法

```bash
python tools/patch_mr_undump.py \
    --src ref/mrpoid/mr/src/mr_undump.c \
    --out tools/mythroad/patched_mr_undump.c
```
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ORIG = """static mrp_Number LoadNumber (LoadState* S)
{
   mrp_Number x;
   LoadBlock(S,&x,sizeof(x));
   return x;
}"""

PATCHED = """static mrp_Number LoadNumber (LoadState* S)
{
#ifdef MRP_UNDUMP_FLOAT_NUMBER
   /* 【移植补丁】MRP 字节码里 number 常量按 4 字节 float 存储（斯凯编译器
    * 的产物），而解释器内部用 double。LoadHeader 里那段 sizeof 检查在
    * version > VERSION_50 时被跳过（应用头是 \\x1bMRP + 0x80），于是按 8 字节
    * 读会把常量表整体错位 4 字节 —— 后面全是垃圾，解释器会把垃圾当函数
    * 指针调用，直接崩在堆里。
    * 这里按 float 读再转 double：float -> double 是精确转换，数值不变。 */
   float f;
   LoadBlock(S,&f,sizeof(f));
   return (mrp_Number)f;
#else
   mrp_Number x;
   LoadBlock(S,&x,sizeof(x));
   return x;
#endif
}"""


def patch(text: str) -> tuple[str, bool]:
    if "MRP_UNDUMP_FLOAT_NUMBER" in text:
        return text, False          # 已经打过
    if ORIG not in text:
        # 源码被上游改过：退一步按函数体特征匹配
        import re
        pat = re.compile(
            r"static mrp_Number LoadNumber \(LoadState\* S\)\s*\{.*?\n\}",
            re.S)
        m = pat.search(text)
        if not m:
            raise SystemExit("找不到 LoadNumber，无法打补丁")
        return text[:m.start()] + PATCHED + text[m.end():], True
    return text.replace(ORIG, PATCHED), True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ref/mrpoid/mr/src/mr_undump.c")
    ap.add_argument("--out", default="tools/mythroad/patched_mr_undump.c")
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
