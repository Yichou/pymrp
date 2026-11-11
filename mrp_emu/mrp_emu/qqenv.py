"""古董 QQ 的运行环境准备器。

背景
----
2014 年腾讯关闭 3G 移动 QQ、运营商 WAP 网关退网后，这些老应用缺的不只是
「服务器地址」，还有一堆**真机预置的私有资源**：

======================  ==========================================
文件                    作用
======================  ==========================================
``QQ2010/QServer.cof``  服务器列表（决定连哪个 QQ 网关）
``QQ2010/profile.db``  账号库（``PROF`` magic 的二进制格式）
``system/gb16.uc2``    16 点阵字库（MTK 的 .uc2 格式）
``qqdsm/settings``     老版 QQ 的服务器地址（key=value 文本）
``qqdsm/info``         老版 QQ 的账号信息
======================  ==========================================

本模块按已逆向出的格式生成这些文件的**最小可用版本**，让古董 QQ 能在
模拟器里跑起来（界面 + 本地复古服务端）。

已逆向出的格式
--------------
``qqdsm/settings``（老版 ``QQDSM2007.mrp``）
    **纯文本**，整个文件一次读完。按 ``key=value`` 逐行，键名来自
    ``common.mr`` 的字符串表：``www.sky-mobi.com`` / ``port`` /
    ``_ip`` / ``_port``。

``QQ2010/QServer.cof``（新版 ``391032_240320_atxqq.mrp``）
    **二进制**：1 字节版本号，随后每条服务器记录 4 字节，
    读满 4 字节返回 0 表示结束（``mr_read(fd, buf, 4)``）。

``profile.db``
    ``PROF`` magic（4 字节）+ 0x80 偏移处的数据块。格式未完全逆出，
    这里只写一个最小 magic 头，让应用走「首次运行」分支而不是
    「读取已有账号」分支。

``system/gb16.uc2``
    MTK 字库：16x16 点阵，GB2312 码位索引。我们生成一个空字库
    （有合法头，字符为空），保证应用不会因为缺文件而中止。

参考
----
逆向过程与证据见 ``docs/20-古董QQ复活.md``。
"""

from __future__ import annotations

from pathlib import Path

# 2010 版 QQ 的服务器列表文件名与所在目录
Q2010_DIR = "QQ2010"
Q2010_CONF = "QServer.cof"
Q2010_PROFILE = "profile.db"

# 老版 QQ 的配置目录
QQDSM_DIR = "qqdsm"
QQDSM_SETTINGS = "settings"
QQDSM_INFO = "info"

# 系统字库
FONT_DIR = "system"
FONT_GB16 = "gb16.uc2"

# profile.db 的 magic
PROF_MAGIC = b"PROF"


def build_qserver_cof_binary(servers: list[tuple[str, int]] | None = None,
                             version: int = 1) -> bytes:
    """生成 2010 版 QQ 的 ``QServer.cof``。

    格式：``u8 版本`` + 每条服务器 ``u32``（服务器编号）。
    客户端按 ``mr_read(fd, buf, 4)`` 逐条读，读到 0 字节就结束。

    .. note::
       这里存的是**服务器编号**而不是 IP —— 客户端拿到编号后会去
       ``conf.3g.qq.com`` 之类的服务换取真实地址（斯凯那套
       ``result=0&...`` 协议）。本地复古服务器直接给编号 1 即可，
       由 :mod:`mrp_emu.retrowap` 接管后续所有 HTTP 交互。
    """
    servers = servers or [(f"srv{i}", 80) for i in range(1)]
    out = bytearray([version & 0xFF])
    for _name, port in servers:
        # 客户端把 4 字节读成一个整数；这里用端口作为编号的低位，
        # 保证非零（0 会被当成「读完了」）。
        out += (port & 0xFFFFFFFF).to_bytes(4, "little")
    return bytes(out)


def build_qqdsm_settings(host: str, port: int) -> bytes:
    """生成老版 QQ 的 ``qqdsm/settings``（key=value 文本）。"""
    lines = [
        f"www.sky-mobi.com={host}",
        f"port={port}",
        f"_ip={host}",
        f"_port={port}",
    ]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def build_profile_db() -> bytes:
    """生成最小可用的 ``profile.db``。

    结构：``PROF`` magic + 预留 0x80 偏移的数据块。
    """
    return PROF_MAGIC + b"\x00" * 0x80


def build_gb16_uc2() -> bytes:
    """生成一个可用的 16 点阵字库（MTK .uc2）。

    用系统字体渲染 16x16 点阵（1bpp，高位在前，偏移 = id * 32），
    这样应用的中文界面才能真正显示出来，而不是一片空白。
    详见 :mod:`mrp_emu.fontgen`。
    """
    try:
        from .fontgen import build_uc2
        return build_uc2()
    except Exception:  # pragma: no cover - 字体不可用时退回空字库
        # 最小合法结构：偏移表全零 + 少量字模数据
        return b"\x00" * (96 * 2) + b"\x00" * 32


def prepare_qq_environment(workdir: str | Path,
                           host: str = "127.0.0.1",
                           port: int = 8080,
                           log=print) -> list[Path]:
    """把古董 QQ 需要的运行环境文件准备好，返回写出的文件列表。

    同时准备新旧两个 QQ 客户端的配置，互不影响。
    """
    workdir = Path(workdir)
    written: list[Path] = []

    def put(rel: str, data: bytes) -> None:
        path = workdir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() == data:
            return
        path.write_bytes(data)
        written.append(path)

    put(f"mythroad/{Q2010_DIR}/{Q2010_CONF}",
        build_qserver_cof_binary())
    put(f"mythroad/{Q2010_DIR}/{Q2010_PROFILE}", build_profile_db())
    put(f"mythroad/{QQDSM_DIR}/{QQDSM_SETTINGS}",
        build_qqdsm_settings(host, port))
    put(f"mythroad/{QQDSM_DIR}/{QQDSM_INFO}", b"")

    # 字库：内容大且生成慢，走 ensure_uc2（已存在就跳过）
    try:
        from .fontgen import ensure_uc2
        ensure_uc2(workdir / "mythroad" / FONT_DIR / FONT_GB16, log=log)
    except Exception as exc:  # noqa: BLE001
        if log:
            log(f"[qq-env] 字库准备失败: {exc}")

    if written and log:
        log(f"[qq-env] 已准备 {len(written)} 个 QQ 运行环境文件"
            f"（指向 {host}:{port}）")
    return written
