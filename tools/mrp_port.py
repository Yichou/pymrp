#!/usr/bin/env python3
"""mrporting.h 平台接口解析器（共享库）。

`mrporting.h` 是官方给宿主预留的平台层接口面 —— mythroad.c 里所有
真正碰硬件/系统的东西都在这里以 `extern` 声明，官方实现放在真机 ROM 里。

本模块把这份声明解析成结构化清单，供两个工具使用：

* `tools/port_scan.py`  —— 量化移植面（A/B 分级）
* `tools/gen_emu_stub.py` —— 生成平台层 thunk 桩代码

两个坑：
1. 文件里有 `#if 0 ... #endif` 块，里面是**已取消**的接口
   （mr_start / mr_getAppList / mr_uninstall / mr_getAppInfo），
   必须整段跳过，否则会生成根本不存在的 stub。
2. 部分接口没有 `extern` 关键字（mr_start_dsm_ex / _B / _C），
   只按 `extern` 抓会漏。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PlatformApi:
    """mrporting.h 里的一个平台接口。"""

    name: str
    ret: str                 # 返回类型
    params: str              # 原始参数列表（含括号）
    arg_names: list[str]     # 解析后的形参名
    line: int                # 在头文件里的行号

    @property
    def param_types(self) -> list[str]:
        return _split_params(self.params)

    def prototype(self) -> str:
        """还原成 C 函数声明（用于生成 stub）。"""
        return f"{self.ret} {self.name}{self.params}"


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def _strip_if_zero(text: str) -> str:
    """去掉 `#if 0 ... #endif` 块（含嵌套的 #if/#endif 计数）。"""
    out: list[str] = []
    depth = 0          # >0 表示正在 #if 0 块内
    for line in text.split("\n"):
        st = line.strip()
        if depth == 0:
            m = re.match(r"#\s*if\s+0\b", st)
            if m:
                depth = 1
                continue
            out.append(line)
        else:
            # 块内仍需跟踪嵌套
            if re.match(r"#\s*if\b", st):
                depth += 1
            elif re.match(r"#\s*endif\b", st):
                depth -= 1
            elif re.match(r"#\s*else\b", st) and depth == 1:
                pass
    return "\n".join(out)


def _split_params(params: str) -> list[str]:
    """把 `(int16 type, int32 param1)` 拆成 ['int16 type', 'int32 param1']。"""
    inner = params.strip()
    if inner.startswith("("):
        inner = inner[1:]
    if inner.endswith(")"):
        inner = inner[:-1]
    if not inner.strip() or inner.strip() == "void":
        return []
    parts, depth, cur = [], 0, ""
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _arg_name(decl: str) -> str:
    """从 `const char* filename` 里取出 `filename`。"""
    d = decl.strip()
    # 去掉数组维度
    d = re.sub(r"\[[^\]]*\]", "", d)
    m = re.search(r"([A-Za-z_]\w*)\s*$", d)
    return m.group(1) if m else ""


_DECL_RE = re.compile(
    r"^\s*(?:extern\s+)?"
    r"(?P<ret>[A-Za-z_][\w\s\*]*?)\b(?P<name>(?:mr|vm|dsm)_[A-Za-z_]\w*)\s*"
    r"\((?P<params>[^;{)]*)\)\s*;",
    re.MULTILINE,
)


def parse_platform_apis(mrporting: str | Path) -> list[PlatformApi]:
    """解析 mrporting.h，返回平台接口清单（已跳过 #if 0 块）。"""
    p = Path(mrporting)
    text = _strip_if_zero(_strip_comments(p.read_text(encoding="utf-8",
                                                      errors="replace")))
    out: list[PlatformApi] = []
    for m in _DECL_RE.finditer(text):
        params = f"({m.group('params').strip()})"
        types = _split_params(params)
        out.append(PlatformApi(
            name=m.group("name"),
            ret=" ".join(m.group("ret").split()),
            params=params,
            arg_names=[_arg_name(t) for t in types],
            line=text[:m.start()].count("\n") + 1,
        ))
    # 去重（同名只留第一个）
    seen: set[str] = set()
    uniq: list[PlatformApi] = []
    for a in out:
        if a.name in seen:
            continue
        seen.add(a.name)
        uniq.append(a)
    return uniq


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent.parent / "ref" / "mrpoid" / "mr"
    apis = parse_platform_apis(root / "mrporting.h")
    print(f"平台接口 {len(apis)} 个：\n")
    for a in apis:
        print(f"  {a.prototype():70s}  # L{a.line}")
