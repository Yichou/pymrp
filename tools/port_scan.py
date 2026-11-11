#!/usr/bin/env python3
"""mythroad 平台层移植面扫描器。

回答一个问题：**如果不用现成的 cfunction.ext，而是自己用 mythroad.c
编译一个 MR 虚拟机，还差多少个函数要补？**

做法：
  1. 扫 mythroad.c + src/ + tomr/ 全部 .c，收集
       - 函数定义（`... name(...) {`）
       - 函数声明（`... name(...);`）
       - 函数调用（`name(`）
  2. 减去定义与声明，得到「被调用但本工程没有定义」的符号；
  3. 再减去 C 标准库白名单，剩下的就是**必须由宿主提供的平台层接口**。

输出：平台层 stub 清单（按来源分组），可直接当移植 TODO 用。

用法:
    python tools/port_scan.py [mr_dir]
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

# C 标准库 / 编译器内建：不需要我们实现
LIBC = {
    # string
    "memcpy", "memmove", "memset", "memcmp", "strlen", "strcpy", "strncpy",
    "strcmp", "strncmp", "strcat", "strncat", "strchr", "strrchr", "strstr",
    "strtok", "strspn", "strcspn", "strpbrk", "strerror", "strdup", "strcasecmp",
    "strncasecmp", "strtol", "strtoul", "strtod", "strtoulong", "atoi", "atol",
    "sprintf", "snprintf", "vsprintf", "vsnprintf", "printf", "fprintf",
    "sscanf", "scanf",
    # stdlib
    "malloc", "calloc", "realloc", "free", "exit", "abort", "atoi", "atof",
    "abs", "labs", "qsort", "bsearch", "rand", "srand", "getenv", "system",
    "strtol", "strtoul",
    # stdio
    "fopen", "fclose", "fread", "fwrite", "fseek", "ftell", "fflush",
    "fgets", "fputs", "fgetc", "fputc", "remove", "rename", "tmpfile",
    # math
    "sqrt", "pow", "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "log", "log10", "exp", "fabs", "floor", "ceil", "fmod", "frexp", "ldexp",
    "sinf", "cosf", "tanf", "sqrtf", "powf", "fabsf", "floorf", "ceilf",
    # ctype
    "isalpha", "isdigit", "isalnum", "isspace", "isupper", "islower",
    "isxdigit", "isprint", "ispunct", "toupper", "tolower",
    # time
    "time", "clock", "localtime", "gmtime", "mktime", "difftime",
    "strftime", "clock_gettime",
    # 其他常见
    "assert", "va_start", "va_arg", "va_end", "va_copy",
    "setjmp", "longjmp", "memfrob",
    # 编译器内建
    "__builtin_memcpy", "__builtin_memset", "__builtin_strlen",
    "__builtin_va_start", "__builtin_va_arg", "__builtin_va_end",
    "__builtin_expect", "__builtin_alloca",
}

# 关键字/伪函数，排除
NOT_A_FUNC = {
    "if", "for", "while", "switch", "return", "sizeof", "do", "else",
    "case", "defined", "typedef", "struct", "union", "enum", "static",
    "extern", "inline", "const", "volatile", "unsigned", "signed", "void",
    "char", "short", "int", "long", "float", "double", "register", "auto",
    "goto", "break", "continue", "default", "restrict", "asm", "__asm__",
    "MR_ERROR", "MR_SUCCESS",
}

# 宏定义出来的多参数宏，展开后不是函数
MACRO_LIKE = re.compile(r"^[A-Z][A-Z0-9_]*$")

DEF_RE = re.compile(
    r"^[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{", re.MULTILINE)
DECL_RE = re.compile(
    r"^[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*;", re.MULTILINE)
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
# 单行内定义（K&R 或同行 { ）
ONELINE_DEF_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\([^;{)]*\)\s*\{")
# 头文件里的行内声明
HDR_DECL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*;")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def collect(defs: set[str], decls: set[str], calls: dict[str, set[str]],
            text: str, source: str) -> None:
    text = strip_comments(text)
    # 去掉预处理指令行（宏定义可能带括号）
    lines = []
    for line in text.split("\n"):
        st = line.lstrip()
        if st.startswith("#"):
            # 宏定义行单独处理：函数式宏不算函数
            lines.append("")
        else:
            lines.append(line)
    body = "\n".join(lines)

    for m in DEF_RE.finditer(body):
        defs.add(m.group(1))
    for m in ONELINE_DEF_RE.finditer(body):
        defs.add(m.group(1))
    for m in DECL_RE.finditer(body):
        decls.add(m.group(1))
    for m in HDR_DECL_RE.finditer(body):
        decls.add(m.group(1))
    for m in CALL_RE.finditer(body):
        name = m.group(1)
        if name in NOT_A_FUNC or MACRO_LIKE.match(name):
            continue
        calls[name].add(source)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parent.parent / "ref" / "mrpoid" / "mr"

    sources: list[Path] = []
    for pat in ("mythroad.c", "src/*.c", "src/lib/*.c", "tomr/src/*.c"):
        sources += sorted(root.glob(pat))

    defs: set[str] = set()
    decls: set[str] = set()
    calls: dict[str, set[str]] = defaultdict(set)

    for p in sources:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        collect(defs, decls, calls, text, str(p.relative_to(root)))

    # 头文件里的声明也算“已声明”（内部库：include/ + tomr/）
    for p in sorted(root.glob("include/*.h")) + sorted(root.glob("tomr/include/*.h")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in HDR_DECL_RE.finditer(strip_comments(text)):
            decls.add(m.group(1))

    undefined = sorted(
        n for n in calls
        if n not in defs and n not in decls and n not in LIBC
    )

    print(f"扫描源文件 {len(sources)} 个")
    print(f"  函数定义 {len(defs)}  声明 {len(decls)}  调用符号 {len(calls)}")
    print(f"\n=== 需要宿主提供的平台层符号：{len(undefined)} 个 ===\n")
    by_src: dict[str, list[str]] = defaultdict(list)
    for n in undefined:
        for s in calls[n]:
            by_src[s].append(n)
    for s in sorted(by_src):
        uniq = sorted(set(by_src[s]))
        print(f"[{s}]  ({len(uniq)})")
        print("   " + " ".join(uniq))
        print()

    # 单独列出 mrporting.h 里官方声明的平台接口
    mp = root / "mrporting.h"
    if mp.is_file():
        text = strip_comments(mp.read_text(encoding="utf-8", errors="replace"))
        ext = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("extern"):
                m = re.search(r"\b([A-Za-z_]\w*)\s*\(", line)
                if m:
                    ext.append(m.group(1))
        ext_set = sorted(set(ext))
        # 本工程内已经有定义的（mythroad.c / src/ 里实现掉的）
        implemented = [e for e in ext_set if e in defs]
        todo = [e for e in ext_set if e not in defs]
        print(f"=== mrporting.h 官方平台接口：{len(ext_set)} 个 ===")
        print(f"  本工程已实现 {len(implemented)} 个：")
        print("   " + (" ".join(implemented) if implemented else "（无）"))
        print(f"\n  ** 必须由宿主实现 {len(todo)} 个 **")
        print("   " + " ".join(todo))
        print()
        # 平台接口的调用点分布：谁在用
        usage: dict[str, list[str]] = defaultdict(list)
        for e in todo:
            for s in sorted(calls.get(e, ())):
                usage[e].append(s)
        # 分类：被 mythroad/解释器内部调用 = VM 起不来就完蛋；
        #       只被 MRP 应用调用 = 可以先返回 MR_FAILED 后补
        internal, app_only = [], []
        for e in todo:
            srcs = usage.get(e, [])
            if any(s.startswith(("mythroad.c", "src/", "tomr/")) for s in srcs):
                internal.append(e)
            else:
                app_only.append(e)
        print(f"=== 分级：A 类（VM 内部必需，缺了就起不来）{len(internal)} 个 ===")
        print("   " + " ".join(internal))
        print(f"\n=== B 类（仅 MRP 应用调用，可后补）{len(app_only)} 个 ===")
        print("   " + " ".join(app_only))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
