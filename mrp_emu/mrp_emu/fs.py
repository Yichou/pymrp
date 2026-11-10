"""MRP 虚拟文件系统。

vmrp 的做法是直接 open() 宿主文件（mrp 已经被工具解开到 mythroad 目录）。
这里同样如此，但加了一层路径沙箱：所有访问都被限制在 root 目录内，
防止 MRP 里写死 "../.." 之类的路径跑到沙箱外面。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .consts import (
    MR_FAILED,
    MR_FILE_CREATE,
    MR_FILE_RDONLY,
    MR_FILE_RDWR,
    MR_FILE_WRONLY,
    MR_IS_DIR,
    MR_IS_FILE,
    MR_IS_INVALID,
    MR_SEEK_CUR,
    MR_SEEK_END,
    MR_SEEK_SET,
    MR_SUCCESS,
)

DRIVE_PREFIXES = ("a:", "A:", "c:", "C:", "e:", "E:", "fs:/", "/")


class VirtualFs:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.handles: dict[int, dict] = {}
        self.dirs: dict[int, list[str]] = {}
        self.counter = 0
        self.dir_counter = 0
        self.readonly = False
        # mr_platEx(1204) dsmSwitchPath 维护的逻辑工作路径（相对 root，以 / 结尾）
        self.work_path = ""

    # ------------------------------------------------------------ 路径
    def resolve(self, name: str, must_exist: bool = False) -> Path | None:
        n = name.replace("\\", "/").strip()
        for p in DRIVE_PREFIXES:
            if n.lower().startswith(p.lower()):
                n = n[len(p):]
                break
        n = n.lstrip("/")
        # "."/".." 归一化后**钳制在 root 内**：真机上根目录的 ".." 仍是根目录。
        # 这里若返回 None，ext 会把空结果当 NULL 字符串交给内部 sprintf("%s")，
        # 直接解引用地址 0 —— RX 管理器浏览根目录时的崩溃就是这么来的。
        parts: list[str] = []
        for seg in n.split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(seg)
        target = (self.root.joinpath(*parts) if parts else self.root).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            # 软链接等极少数情况仍可能越界，钳回 root 而不是给 NULL
            target = self.root
        if must_exist and not target.exists():
            return None
        return target

    # ------------------------------------------------------------ 打开/读写
    def open(self, name: str, mode: int) -> int:
        if self.readonly and mode & (MR_FILE_WRONLY | MR_FILE_RDWR | MR_FILE_CREATE):
            return 0
        path = self.resolve(name)
        if path is None:
            return 0

        if mode & MR_FILE_RDWR:
            flags = "r+b" if path.exists() else "w+b"
        elif mode & MR_FILE_WRONLY:
            flags = "r+b" if path.exists() else "wb"
        else:
            flags = "rb"

        if mode & MR_FILE_CREATE:
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            fh = open(path, flags)
        except OSError as exc:
            print(f"[fs] 打开失败 {name}: {exc}")
            return 0

        self.counter += 1
        self.handles[self.counter] = {"fp": fh, "path": path, "name": name}
        return self.counter

    def close(self, f: int) -> int:
        h = self.handles.pop(f, None)
        if not h:
            return MR_FAILED
        try:
            h["fp"].close()
        except OSError:
            return MR_FAILED
        return MR_SUCCESS

    def close_all(self) -> int:
        """关掉所有还开着的文件句柄与目录句柄。

        应用退出（mr_exit）或崩溃收尾时必须调：漏掉的句柄会让文件描述符
        一直占着，应用再开文件会拿到新句柄号，旧数据悬在内存里。
        返回关掉的句柄数。
        """
        n = len(self.handles)
        for f in list(self.handles.keys()):
            try:
                self.close(f)
            except Exception:
                self.handles.pop(f, None)
        for d in list(self.dirs.keys()):
            try:
                self.closedir(d)
            except Exception:
                pass
        self.dirs.clear()
        return n

    def read(self, f: int, length: int) -> bytes:
        h = self.handles.get(f)
        if not h:
            return b""
        try:
            return h["fp"].read(length)
        except OSError:
            return b""

    def write(self, f: int, data: bytes) -> int:
        h = self.handles.get(f)
        if not h:
            return MR_FAILED
        try:
            return h["fp"].write(data)
        except OSError:
            return MR_FAILED

    def seek(self, f: int, pos: int, method: int) -> int:
        h = self.handles.get(f)
        if not h:
            return MR_FAILED
        whence = {MR_SEEK_SET: os.SEEK_SET, MR_SEEK_CUR: os.SEEK_CUR, MR_SEEK_END: os.SEEK_END}
        try:
            h["fp"].seek(pos, whence.get(method, os.SEEK_SET))
        except (OSError, ValueError):
            return MR_FAILED
        return MR_SUCCESS

    def get_len(self, name: str) -> int:
        path = self.resolve(name, must_exist=True)
        if path is None or not path.is_file():
            return -1
        return path.stat().st_size

    def read_all(self, name: str) -> bytes | None:
        path = self.resolve(name, must_exist=True)
        if path is None or not path.is_file():
            return None
        return path.read_bytes()

    # ------------------------------------------------------------ 元信息
    def info(self, name: str) -> int:
        path = self.resolve(name)
        if path is None or not path.exists():
            return MR_IS_INVALID
        return MR_IS_DIR if path.is_dir() else MR_IS_FILE

    def remove(self, name: str) -> int:
        path = self.resolve(name, must_exist=True)
        if path is None or path.is_dir():
            return MR_FAILED
        try:
            path.unlink()
            return MR_SUCCESS
        except OSError:
            return MR_FAILED

    def rename(self, old: str, new: str) -> int:
        src = self.resolve(old, must_exist=True)
        dst = self.resolve(new)
        if src is None or dst is None:
            return MR_FAILED
        try:
            src.replace(dst)
            return MR_SUCCESS
        except OSError:
            return MR_FAILED

    def mkdir(self, name: str) -> int:
        path = self.resolve(name)
        if path is None:
            return MR_FAILED
        path.mkdir(parents=True, exist_ok=True)
        return MR_SUCCESS

    def rmdir(self, name: str) -> int:
        path = self.resolve(name, must_exist=True)
        if path is None:
            return MR_FAILED
        try:
            shutil.rmtree(path)
            return MR_SUCCESS
        except OSError:
            return MR_FAILED

    # ------------------------------------------------------------ 目录枚举
    def opendir(self, name: str) -> int:
        path = self.resolve(name, must_exist=True)
        if path is None or not path.is_dir():
            return 0
        try:
            names = [".", ".."] + [p.name for p in sorted(path.iterdir())]
        except OSError:
            return 0
        self.dir_counter += 1
        self.dirs[self.dir_counter] = names
        return self.dir_counter

    def readdir(self, f: int) -> str | None:
        names = self.dirs.get(f)
        if not names:
            return None
        return names.pop(0)

    def closedir(self, f: int) -> int:
        return MR_SUCCESS if self.dirs.pop(f, None) is not None else MR_FAILED

    def find_start(self, pattern: str, buf_len: int) -> tuple[int, str | None]:
        """mr_findStart：返回 (句柄, 首个匹配项)。"""
        base = pattern.replace("\\", "/")
        folder, _, pat = base.rpartition("/")
        if not pat:
            pat, folder = "*", ""
        path = self.resolve(folder or ".", must_exist=True)
        if path is None or not path.is_dir():
            return MR_FAILED, None
        try:
            items = [p.name for p in sorted(path.iterdir())
                     if _glob_match(pat, p.name)]
        except OSError:
            return MR_FAILED, None
        self.dir_counter += 1
        h = self.dir_counter
        self.dirs[h] = items
        first = items[0] if items else None
        if first is None:
            self.dirs.pop(h, None)
            return MR_FAILED, None
        items.pop(0)
        return h, first

    def find_next(self, h: int) -> str | None:
        names = self.dirs.get(h)
        if not names:
            return None
        return names.pop(0) if names else None

    def find_stop(self, h: int) -> int:
        return MR_SUCCESS if self.dirs.pop(h, None) is not None else MR_FAILED

    # ------------------------------------------------------------ 调试
    def dump(self, limit: int = 40) -> str:
        items = sorted(self.root.rglob("*"))[:limit]
        return "\n".join(
            f"  {'D' if p.is_dir() else 'F'} {p.relative_to(self.root)} "
            f"{'' if p.is_dir() else p.stat().st_size}"
            for p in items
        )


def _glob_match(pattern: str, name: str) -> bool:
    """只支持 * 和 ?，够 MRP 用了。"""
    import re
    regex = "^" + "".join(
        ".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern
    ) + "$"
    return re.match(regex, name, re.IGNORECASE) is not None
