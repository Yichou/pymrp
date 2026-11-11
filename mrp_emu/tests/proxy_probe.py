"""斯凯 WAP 代理专项探针。

浏览器插件链（``plugins/brwcore.mrp`` 的 ``brwcore.ext``）把请求 POST 给
斯凯私有端点，代理地址来自真机运营商下发的 ``mythroad/ipaddr2.ini``：

===========================  ==========================================
字符串                       含义
===========================  ==========================================
``ipaddr2.ini``              代理地址缓存（``<host>:<port>``）
``proxy.51mrp.com``          默认代理域名（读不到 ini 时的回退）
``/page2`` ``/image`` ...    各类端点
``Nokia6681/2.0``            斯凯浏览器内核的固定 UA
``application/octet-stream`` 请求体类型（二进制协议）
===========================  ==========================================

本探针固化四条宿主侧语义：

1. ``mythroad/ipaddr2.ini`` 必须存在且内容是 ``<host>:<port>``；
2. 默认 DNS 映射必须覆盖 ``proxy.51mrp.com`` / ``proxy2.51mrp.com``
   （skyengine-v2 的每个插件 e2e 都显式传了这两条）；
3. 内置 WAP 代理必须能解析 ``POST /page2`` + ``Host:`` 形式并转发；
4. ini 里的域名要能被 DNS 映射解析到复刻服务端。
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def test_ipaddr_ini_format() -> None:
    print("\n-- ipaddr2.ini 内容格式（<host>:<port>）--")
    from mrp_emu.proxyenv import (build_ipaddr_ini, prepare_proxy_environment,
                                   IPADDR_INI, DEFAULT_PROXY_HOST)

    data = build_ipaddr_ini()
    text = data.decode("utf-8").strip()
    check("内容是 <host>:<port>", ":" in text, text)
    host, _, port = text.partition(":")
    check("host 是默认代理域名", host == DEFAULT_PROXY_HOST, host)
    check("port 是数字", port.isdigit(), port)
    check("以换行结尾", data.endswith(b"\n"), repr(data))

    with tempfile.TemporaryDirectory() as td:
        written = prepare_proxy_environment(td, log=lambda *a: None)
        check("生成了 1 个文件", len(written) == 1, str(written))
        p = Path(written[0]) if written else None
        check("文件名为 ipaddr2.ini",
              p is not None and p.name == IPADDR_INI, str(p))
        check("落在 mythroad/ 下",
              p is not None and p.parent.name == "mythroad", str(p))
        check("内容与 build_ipaddr_ini 一致",
              p is not None and p.read_bytes() == data)


def test_dns_mapping() -> None:
    print("\n-- 代理域名 DNS 映射 --")
    from mrp_emu.net import parse_dns_map, DEFAULT_DNS_MAP

    mapping = {m.source: m for m in parse_dns_map(DEFAULT_DNS_MAP)}
    for host in ("proxy.51mrp.com", "proxy2.51mrp.com"):
        m = mapping.get(host)
        check(f"{host} 在默认映射里", m is not None)
        check(f"{host} 指向复刻服务端",
              m is not None and m.address == "159.75.119.124", str(m))


def test_proxy_request_parsing() -> None:
    print("\n-- WAP 代理请求解析（POST /page2）--")
    from mrp_emu.net import parse_proxy_request

    req = (b"POST /page2 HTTP/1.1\r\n"
           b"Host: proxy.51mrp.com\r\n"
           b"User-Agent: Nokia6681/2.0\r\n"
           b"Accept: */*\r\n"
           b"Content-Type: application/octet-stream\r\n"
           b"Connection: Keep-Alive\r\n"
           b"Content-Length: 154\r\n\r\n" + b"\x00" * 154)
    r = parse_proxy_request(req)
    check("请求可解析", r is not None)
    if r:
        host, port, mode, outbound = r
        check("host = proxy.51mrp.com", host == "proxy.51mrp.com", host)
        check("port = 80", port == 80, str(port))
        check("mode = host（按 Host 头定位目标）", mode == "host", mode)
        check("转发内容保留了请求行",
              outbound.startswith(b"POST /page2 HTTP/1.1"), repr(outbound[:40]))
        check("转发内容保留了 body",
              len(outbound) == len(req), f"{len(outbound)} vs {len(req)}")

    # CONNECT 形式（另一种端点用法）
    r2 = parse_proxy_request(b"CONNECT example.com:443 HTTP/1.1\r\n\r\n")
    check("CONNECT 可解析", r2 is not None and r2[2] == "connect",
          str(r2[:3] if r2 else None))


def test_endpoints_and_ua() -> None:
    print("\n-- 斯凯端点与 UA --")
    from mrp_emu.proxyenv import SKY_ENDPOINTS, SKY_USER_AGENT

    for ep in ("/page2", "/image", "/mrp", "/res", "/sta", "/other"):
        check(f"端点 {ep} 已登记", ep in SKY_ENDPOINTS)
    check("UA 是 Nokia6681/2.0", SKY_USER_AGENT == "Nokia6681/2.0",
          SKY_USER_AGENT)


def main() -> int:
    print("=== 斯凯 WAP 代理 专项探针 ===")
    test_ipaddr_ini_format()
    test_dns_mapping()
    test_proxy_request_parsing()
    test_endpoints_and_ua()
    print(f"\n=== 摘要: proxy_probe {PASS} 项通过 / {FAIL} 项失败 ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
