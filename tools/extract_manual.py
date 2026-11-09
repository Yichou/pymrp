"""把 SKYENGINE 手册解包后的文本规范化为 Markdown。

输入: ref/sky/txt/*.txt  (CHM 解包 + GBK 转码后的纯文本)
输出: docs/api/*.md       逐页规范页
      docs/api/INDEX.md   全量索引
      build/manual_index.json  供后续分类脚本使用的结构化数据
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ref" / "sky" / "txt"
OUT = ROOT / "docs" / "api"
BUILD = ROOT / "build"

SECTIONS = (
    "Description", "Parameters", "Return Value", "Remarks", "Example", "See Also",
    "背景", "特性", "平台结构示意图",
)
NOISE = {"|", "SKYENGINE API", "参考手册", "SKYENGINE 参考手册"}


def cells(line: str) -> list[str]:
    """把一行按 '|' 结尾的单元格拆开。"""
    s = line.rstrip()
    if not s.endswith("|"):
        return []
    parts = [p.strip() for p in s[:-1].split("|")]
    return [p for p in parts]


def parse(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.rstrip() for ln in raw.splitlines()]
    lines = [ln for ln in lines if ln.strip()]

    title = lines[0].strip() if lines else path.stem
    body = lines[1:]

    # 找到第一个段标题的位置，之前的内容是「原型」区
    def sec_of(ln: str) -> str | None:
        t = ln.strip().rstrip(":").rstrip("：")
        for s in SECTIONS:
            if t.lower() == s.lower() or t == s:
                return s
        return None

    first_sec = next((i for i, ln in enumerate(body) if sec_of(ln)), None)
    if first_sec is None:
        proto_lines, rest = body, []
    else:
        proto_lines, rest = body[:first_sec], body[first_sec:]

    proto_parts = []
    for ln in proto_lines:
        t = ln.strip().rstrip("|").strip()
        for junk in ("SKYENGINE API", "参考手册", "SKYENGINE"):
            t = t.replace(junk, "").strip()
        if t and t not in NOISE and t != "|":
            proto_parts.append(t)
    proto = re.sub(r"\s+", " ", " ".join(proto_parts)).strip()

    # 按段切分
    sections: dict[str, list[str]] = {}
    cur: str | None = None
    for ln in rest:
        s = sec_of(ln)
        if s:
            cur = s
            sections.setdefault(cur, [])
            continue
        if cur:
            sections[cur].append(ln)

    # 参数表
    params: list[list[str]] = []
    if "Parameters" in sections:
        rows: list[list[str]] = []
        pending: list[str] = []
        for ln in sections["Parameters"]:
            c = cells(ln)
            if c:
                rows.extend(c)
                continue
            # 非单元格行，作为说明文字另记
            if ln.strip() not in NOISE:
                pending.append(ln.strip())
        if rows and rows[:1]:
            ncol = 1
            # 用 header 名推断列数
            hdr_names = {"Name", "Type", "Description", "类型", "名称", "说明"}
            cnt = 0
            for r in rows:
                cnt += 1
                if r in hdr_names and cnt >= 2:
                    break
            ncol = max(1, min(3, cnt if cnt >= 2 else 2))
            for i in range(0, len(rows), ncol):
                chunk = rows[i:i + ncol]
                if all(c in hdr_names for c in chunk):
                    continue
                params.append(chunk)
        if pending:
            sections.setdefault("Parameters__note", []).extend(pending)

    def text(key: str) -> str:
        ls = [ln for ln in sections.get(key, []) if ln.strip() not in NOISE]
        out: list[str] = []
        for ln in ls:
            c = cells(ln)
            out.append(" ".join(c) if c else ln.strip())
        return "\n".join(out).strip()

    return {
        "file": path.name,
        "title": title,
        "proto": proto,
        "params": params,
        "desc": text("Description"),
        "ret": text("Return Value"),
        "remarks": text("Remarks"),
        "example": text("Example"),
        "see": text("See Also"),
        "extra": {k: text(k) for k in ("背景", "特性", "平台结构示意图") if k in sections},
        "param_note": text("Parameters__note"),
    }


def slug(title: str, fname: str) -> str:
    """稳定 slug：mr_plat/mr_platEx 用 code 号，其余用函数名。

    不能依赖 ' - ' 分割副标题 —— 手册里有 'mr_plat(1016) -初始化' 这种没有空格的写法。
    """
    m = re.match(r"(mr_platEx|mr_plat)\s*\(\s*([^)]+?)\s*\)", title)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    t = re.split(r"\s+-\s*| -", title)[0].strip()
    t = re.sub(r"[()（）\s]+", "-", t).strip("-")
    t = re.sub(r"[^\w\-.]+", "", t)
    return t or fname.replace(".txt", "")


def md_of(d: dict) -> str:
    out = [f"# {d['title']}", ""]
    if d["proto"]:
        out += ["```c", d["proto"], "```", ""]
    if d["desc"]:
        out += ["## 说明", "", d["desc"], ""]
    if d["params"]:
        out += ["## 参数", ""]
        ncol = len(d["params"][0])
        head = ["参数", "类型", "说明"][:ncol] if ncol == 3 else ["参数", "说明"][:ncol]
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + "---|" * ncol)
        for row in d["params"]:
            out.append("| " + " | ".join(row) + " |")
        out.append("")
    if d["param_note"]:
        out += [d["param_note"], ""]
    if d["ret"]:
        out += ["## 返回值", "", d["ret"], ""]
    if d["remarks"]:
        out += ["## 备注", "", d["remarks"], ""]
    if d["example"]:
        out += ["## 示例", "", "```c", d["example"], "```", ""]
    if d["see"]:
        out += ["## 相关", "", d["see"], ""]
    return "\n".join(out)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    pages = []
    for p in sorted(SRC.glob("*.txt")):
        if p.name.startswith("$$"):
            continue
        d = parse(p)
        d["slug"] = slug(d["title"], p.name)
        pages.append(d)
        (OUT / f"{d['slug']}.md").write_text(md_of(d), encoding="utf-8")

    # 索引
    idx = ["# SKYENGINE API 全量索引", "",
           f"共 {len(pages)} 页，由 `ref/sky`（CHM 解包文本）自动规范化生成，内容保真。", "",
           "| 页面 | 原型 | 一句话说明 |", "|---|---|---|"]
    for d in pages:
        desc = (d["desc"] or "").split("\n")[0][:70]
        proto = d["proto"].replace("|", "\\|")[:90]
        idx.append(f"| [{d['title'].split(' - ')[0]}]({d['slug']}.md) | `{proto}` | {desc} |")
    (OUT / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    (BUILD / "manual_index.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pages={len(pages)}  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
