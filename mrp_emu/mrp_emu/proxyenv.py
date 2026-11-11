"""斯凯 WAP 代理的运行环境准备器。

背景
----
2008-2014 年斯凯（SkyMobi）的 MRP 应用走的是**运营商 WAP 网关**：
应用不直连目标服务器，而是把请求 POST 给网关上的一个斯凯私有端点，
由网关代为取回内容再回给应用。

浏览器插件链（``plugins/brwcore.mrp`` 的 ``brwcore.ext``）是这套协议的
典型实现。从它的字符串表能完整还原协议：

===========================  ==========================================
字符串                       含义
===========================  ==========================================
``ipaddr2.ini``              代理地址缓存文件（读 ``<host>:<port>``）
``proxy.51mrp.com``          回退用的默认代理域名
``%d.%d.%d.%d``              DNS 解析结果格式化成 IP
``%s:%d``                    请求行 ``Host:`` 的拼接格式
``/page2``                   主内容端点（POST 统计/正文）
``/image`` ``/mrp``          图片 / MRP 资源端点
``/res`` ``/sta`` ``/other`` 其它资源与状态端点
``POST``                     请求方法
``Host:``                    请求头
``User-Agent:``              请求头
``Nokia6681/2.0``            UA（斯凯浏览器内核的固定 UA）
``Accept: */*``              请求头
``Content-Type:``            请求头
``application/octet-stream`` 请求体类型（二进制协议）
``Connection: Keep-Alive``   连接复用
``Content-Length:``          请求体长度
===========================  ==========================================

代理地址的解析顺序（``brwcore.ext`` 里的实际逻辑）：

1. 读 ``mythroad/ipaddr2.ini``，按 ``<host>:<port>`` 解析；
   真机上这是运营商/服务端下发的地址缓存。
2. 读不到（``mr_open`` 返回 0）-> 回退到默认域名 ``proxy.51mrp.com``，
   再 DNS 解析成 IP。

本模块做的事
------------
生成 ``mythroad/ipaddr2.ini``，让第 1 步就能拿到地址。这样不必依赖
"读不到再回退"那条路径，日志里也就不会出现
``mr_open(mythroad/ipaddr2.ini,1) fd is: 0``。

写入的地址就是复刻服务端的地址 —— 配合 :data:`mrp_emu.net.DEFAULT_DNS_MAP`
里 ``proxy.51mrp.com->159.75.119.124`` 的映射，请求会正确落到复刻机。

参考
----
逆向证据见 ``docs/25-斯凯WAP代理.md``；协议实现见
``ref/skyengine-v2/crates/skyengine-core/src/wap_proxy.rs``。
"""

from __future__ import annotations

from pathlib import Path

# 代理地址缓存（真机由运营商下发）
IPADDR_INI = "ipaddr2.ini"

# 浏览器插件链引用的默认代理域名
DEFAULT_PROXY_HOST = "proxy.51mrp.com"
DEFAULT_PROXY_PORT = 80

# brwcore.ext 用到的端点
SKY_ENDPOINTS = (
    "/page2",
    "/image",
    "/mrp",
    "/res",
    "/sta",
    "/other",
)

# 斯凯浏览器内核的固定 UA
SKY_USER_AGENT = "Nokia6681/2.0"


def build_ipaddr_ini(host: str = DEFAULT_PROXY_HOST,
                     port: int = DEFAULT_PROXY_PORT) -> bytes:
    """生成 ``ipaddr2.ini``（代理地址缓存）。

    格式：``<host>:<port>``，一行，末尾换行。``brwcore.ext`` 用
    ``sscanf("%s:%s")`` 之类的写法解析它。

    host 写域名（``proxy.51mrp.com``）而不是 IP：域名的解析交给
    :mod:`mrp_emu.net` 的 DNS 映射表，映射到复刻服务端；写死 IP 则
    换服务端时得改文件。
    """
    return f"{host}:{port}\n".encode("utf-8")


def prepare_proxy_environment(workdir: str | Path,
                              host: str = DEFAULT_PROXY_HOST,
                              port: int = DEFAULT_PROXY_PORT,
                              log=print) -> list[Path]:
    """把斯凯 WAP 代理需要的文件准备好，返回写出的文件列表。

    生成的 ``ipaddr2.ini`` 让浏览器插件链的 ``brwcore.ext`` 直接
    拿到代理地址，省掉"读不到再回退"的路径。
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

    put(f"mythroad/{IPADDR_INI}", build_ipaddr_ini(host, port))

    if written and log:
        log(f"[proxy-env] 已准备斯凯代理地址缓存 {host}:{port} "
            f"（{written[0].name}）")
    return written
