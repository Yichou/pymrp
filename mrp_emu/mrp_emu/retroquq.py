"""古董 QQ 的服务器列表配置（``QServer.cof``）生成与解析。

逆向来源
--------
``391032_240320_atxqq.mrp``（爱Q手机QQ，MTK WAP 版）包内的 WAP 引擎
``cfunction.ext``（gzip，解压后 340140 字节）在 ``0x4C328`` 附近有这组
字符串，它们构成了服务器的发现与连接流程：

.. code-block:: text

    http://%s/                 <- 用配置里的主机拼 HTTP 前缀
    %d                         <- 端口
    QServer.cof                <- 服务器列表配置文件名
    socket://                  <- 协议前缀（另有一套 socket 通道）
    auto.conf                  <- 配置文件内的子文件名
    %u                         <- QQ 号（UID）
    E1D84CC825147ECD           <- 16 位十六进制密钥（配置加解密用）
    http://conf.3g.qq.com/newConf/n   <- 在线拉取服务器列表
    result=0&                  <- 拉取成功的响应前缀
    http://activeqq.3g.qq.com/activeQQ/gkey2sid.jsp?s_ua=j2me&g_key=%s
                                <- 密钥换 SID（登录前置）

也就是说：``QServer.cof`` 里存的是**服务器地址列表**；真机上这个文件由
手机预置，或首次联网时从 ``conf.3g.qq.com/newConf/n`` 拉取
（响应形如 ``result=0&<服务器1>&<服务器2>...``）后落盘。

解析结果在客户端里被拼成 ``http://<host>/<port>``（``http://%s/`` + ``%d``），
另外还有 ``socket://<host>:<port>`` 的直连通道。

本模块负责：

* :func:`build_qserver_cof` —— 生成本地替代配置，指向本机复古服务端；
* :func:`parse_qserver_cof` —— 解析配置（供自检与调试）；
* :func:`build_conf_response` —— 生成 ``conf.3g.qq.com/newConf/n`` 的响应体。
"""

from __future__ import annotations

import re

# 客户端用来加解密配置的密钥（来自 cfunction.ext @0x4C360）
CONF_KEY = "E1D84CC825147ECD"

# 服务器列表项在配置里的分隔符（``result=0&`` 说明用 & 分隔）
ITEM_SEP = "&"

# 单条服务器描述：``<host>:<port>`` 或 ``<host>/<port>``
_ITEM_RE = re.compile(r"^(?P<host>[^:/&\s]+)[:/](?P<port>\d{1,5})$")


def build_qserver_cof(host: str, port: int,
                      name: str = "本地复古服务器",
                      extra: list[str] | None = None) -> bytes:
    """生成 ``QServer.cof`` 内容。

    客户端用 ``http://%s/`` + ``%d`` 拼 URL，所以配置项写成
    ``<host>:<port>`` 最直接。文件用 UTF-8 文本、逐行、CRLF 换行
    （客户端按行读，第一行是版本头）。
    """
    lines = [
        "VERSION=1",
        f"{name} {host}:{port}",
    ]
    for e in (extra or []):
        lines.append(e)
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def parse_qserver_cof(data: bytes) -> list[dict]:
    """解析 ``QServer.cof``，返回服务器列表。

    宽容处理：非 ``host:port`` 形式的行原样保留在 ``raw`` 字段里，
    这样自检能看到「客户端写了什么」而不用猜格式。
    """
    out: list[dict] = []
    text = data.decode("utf-8", "replace")
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        # 行首可能有 "名字 " 前缀
        parts = line.split()
        cand = parts[-1] if parts else ""
        m = _ITEM_RE.match(cand)
        if m:
            out.append({
                "host": m.group("host"),
                "port": int(m.group("port")),
                "name": " ".join(parts[:-1]) or None,
                "raw": line,
            })
        else:
            out.append({"host": None, "port": None, "name": None,
                        "raw": line})
    return out


def build_conf_response(host: str, port: int,
                        extra: list[str] | None = None) -> bytes:
    """生成 ``conf.3g.qq.com/newConf/n`` 的响应体。

    客户端认的前缀是 ``result=0&``，后面跟 ``&`` 分隔的服务器项。
    """
    items = [f"{host}:{port}"] + list(extra or [])
    return ("result=0&" + ITEM_SEP.join(items)).encode("utf-8")
