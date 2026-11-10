#!/usr/bin/env python3
"""自检：斯凯老域名覆写 + 内置 WAP 代理（对齐 open-skyengine/skyengine-v2）。

默认全部走本机回环，不需要联网。加 ``--online`` 才会去连复刻服务器
159.75.119.124:6009 做一次只读 GET 探针。

覆盖：
  1. --dns-map 解析（默认表 / 端口 / 大小写 / 尾点 / 非法格式）
  2. parse_proxy_request：绝对 URL 改写、Host/X-Online-Host、CONNECT
  3. getHostByName 覆写、IP 型 source 覆盖 cmwap 网关、端口覆写
  4. 真实 TCP 回环：绝对 URL 转发 + CONNECT 隧道 + 200 响应注入
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from mrp_emu.memory import MrpMemory  # noqa: E402
from mrp_emu.net import (  # noqa: E402
    CMWAP_PROXY_IP, DEFAULT_DNS_MAP, MR_IPPROTO_TCP, MR_SOCKET_BLOCK,
    MR_SOCK_STREAM, MR_SUCCESS, NetEngine, ip_to_u32, parse_dns_map,
    parse_proxy_request,
)

PASS = 0
FAIL = 0


def check(cond: bool, msg: str, extra: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {msg}")
    else:
        FAIL += 1
        print(f"  FAIL {msg}  {extra}")


class FakeVm:
    """只要 mem；不跑 ARM 回调，所以比真 Vm 轻。"""

    def __init__(self):
        self.mem = MrpMemory()


def fresh(dns_map=None, wap_proxy=True) -> NetEngine:
    return NetEngine(FakeVm(), log=lambda *a: None, dns_map=dns_map,
                     wap_proxy=wap_proxy, connect_timeout=1.0,
                     dns_timeout=0.5)


def put(net: NetEngine, data: bytes) -> int:
    p = net.vm.mem.malloc(max(1, len(data)))
    net.vm.mem.write(p, data)
    return p


def take(net: NetEngine, p: int, n: int) -> bytes:
    return bytes(net.vm.mem.read(p, n))


def wait_for(predicate, timeout=1.5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def start_server(handler):
    """起一个回环 TCP 服务器，每个连接交给 handler(conn, results)。"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)
    port = srv.getsockname()[1]
    results: list[bytes] = []
    done = threading.Event()

    def accept_loop():
        while not done.is_set():
            try:
                srv.settimeout(0.2)
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=handler, args=(conn, results),
                             daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    return srv, port, results, done


def http_handler(conn, results):
    conn.settimeout(1.5)
    buf = b""
    try:
        while b"\r\n\r\n" not in buf and len(buf) < 65536:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
        results.append(buf)
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                     b"Connection: close\r\n\r\nOK")
    except OSError:
        pass
    finally:
        conn.close()


def echo_handler(conn, results):
    conn.settimeout(1.5)
    try:
        data = conn.recv(4096)
        if data:
            results.append(data)
            conn.sendall(b"PONG")
    except OSError:
        pass
    finally:
        conn.close()


def test_parse() -> None:
    print("\n-- 1. DNS 映射解析 --")
    default = parse_dns_map(None)
    check(len(default) == 3, "默认表 3 条", str(default))
    check({m.source for m in default} ==
          {"rop.skymobiapp.com", "spd.skymobiapp.com", "wap.skmeg.com"},
          "默认覆盖 3 个斯凯老域名")
    check(all(m.address == "159.75.119.124" and m.port is None
              for m in default), "默认目标 159.75.119.124、不改端口")
    check(parse_dns_map("") == [], "传空字符串可清空覆写")
    m = parse_dns_map("SPD.SkyMobiApp.com.->127.0.0.1:8088")[0]
    check(m.source == "spd.skymobiapp.com", "源去尾点并小写", str(m))
    check(m.address == "127.0.0.1" and m.port == 8088, "目标支持 :PORT")
    for bad in ("abc", "a->999.1.1.1", "a->127.0.0.1:x", "a->1.2.3.4;a->5.6.7.8"):
        try:
            parse_dns_map(bad)
            ok = False
        except ValueError:
            ok = True
        check(ok, f"拒绝非法/重复映射 {bad!r}")
    check("159.75.119.124" in DEFAULT_DNS_MAP, "常量里内置复刻服务器 IP")


def test_request_parse() -> None:
    print("\n-- 2. WAP 代理请求解析 --")
    rel = (b"POST /simpleDownload HTTP/1.1\r\n"
           b"Host: spd.skymobiapp.com:6009\r\n"
           b"Content-Length: 4\r\n\r\nABCD")
    r = parse_proxy_request(rel)
    check(r is not None and r[:3] == ("spd.skymobiapp.com", 6009, "host"),
          "相对路径 + Host", str(r))
    check(r is not None and r[3] == rel, "相对路径请求原样转发")

    abs_req = (b"GET http://service.test/resource?id=7 HTTP/1.1\r\n"
               b"Host: service.test\r\nProxy-Connection: Keep-Alive\r\n\r\n")
    r = parse_proxy_request(abs_req)
    check(r is not None and r[:3] == ("service.test", 80, "absolute"),
          "绝对 URL 解析出 authority", str(r))
    out = r[3] if r else b""
    check(out.startswith(b"GET /resource?id=7 HTTP/1.1\r\n"),
          "绝对 URL 改写成 origin-form", repr(out[:60]))
    check(b"Host: service.test" in out, "保留 Host 头")
    check(b"Proxy-Connection" not in out, "剥掉 Proxy-Connection")

    abs_port = (b"GET http://service.test:8123/x HTTP/1.1\r\n\r\n")
    r = parse_proxy_request(abs_port)
    check(r is not None and r[1] == 8123 and b"Host: service.test:8123" in r[3],
          "绝对 URL 带端口时自动补 Host", str(r))

    conn = b"CONNECT wap.skmeg.com:6009 HTTP/1.1\r\nProxy-Connection: Keep-Alive\r\n\r\n"
    r = parse_proxy_request(conn)
    check(r is not None and r[:3] == ("wap.skmeg.com", 6009, "connect"),
          "CONNECT 解析", str(r))
    check(r is not None and r[3] == b"", "CONNECT 头不转发给上游")
    check(parse_proxy_request(b"GET /x HTTP/1.1\r\n\r\n") is None,
          "没有任何 Host 信息时放弃")


def test_mapping() -> None:
    print("\n-- 3. 域名 / IP 覆写路由 --")
    net = fresh()
    want = ip_to_u32("159.75.119.124")
    check(net.get_host_by_name("spd.skymobiapp.com") == want,
          "getHostByName 老域名走覆写表")
    check(net.get_host_by_name("SPD.SkyMobiApp.com.") == want,
          "大小写 + 尾点不敏感")
    check(net.get_host_by_name("10.0.0.172") == CMWAP_PROXY_IP,
          "点分 IP 不受影响")
    check(net.resolve_target("wap.skmeg.com", 6009) ==
          ("159.75.119.124", 6009), "resolve_target 保留原端口")
    check(net.find_mapping("example.com") is None, "无关域名不覆写")
    net2 = fresh(dns_map="spd.skymobiapp.com->127.0.0.1:8088")
    check(net2.resolve_target("spd.skymobiapp.com", 6009) ==
          ("127.0.0.1", 8088), "映射端口优先于请求端口")


def test_absolute_forward() -> None:
    print("\n-- 4. 回环实测：cmwap 假连接 + 绝对 URL 改写 --")
    srv, port, results, done = start_server(http_handler)
    try:
        net = fresh(dns_map=f"service.test->127.0.0.1:{port}")
        s = net.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
        check(s >= 0, "拿到 socket 槽位")
        rc = net.connect(s, CMWAP_PROXY_IP, 80, MR_SOCKET_BLOCK)
        check(rc == MR_SUCCESS, "connect(10.0.0.172) 返回成功（假连接）")
        slot = net.slots[s]
        check(slot.is_proxy and not slot.real_connected, "进入 WAP 代理假连接态")

        req = (b"GET http://service.test/resource?id=7 HTTP/1.1\r\n"
               b"Host: service.test\r\nProxy-Connection: Keep-Alive\r\n\r\n")
        n = net.send(s, put(net, req), len(req))
        check(n == len(req), "send 返回原始请求长度", f"n={n}")
        check(slot.real_connected and slot.peer == ("127.0.0.1", port),
              "真实连到 dns-map 目标", str(slot.peer))
        check(wait_for(lambda: bool(results)), "本地服务端收到请求")
        got = results[0] if results else b""
        check(got.startswith(b"GET /resource?id=7 HTTP/1.1\r\n"),
              "上游收到 origin-form", repr(got[:60]))
        check(b"Host: service.test" in got and b"Proxy-Connection" not in got,
              "Host 保留、Proxy-Connection 已剥")
        check(b"http://service.test" not in got, "绝对 URL 已移除")

        buf = put(net, b"\0" * 256)
        n = wait_for_n(net, s, buf, 256)
        check(n > 0 and b"200 OK" in take(net, buf, n),
              "MRP 侧 recv 拿到 200 响应", repr(take(net, buf, max(n, 0))[:60]))
    finally:
        done.set()
        srv.close()


def wait_for_n(net, s, buf, size) -> int:
    end = time.monotonic() + 1.5
    while time.monotonic() < end:
        n = net.recv(s, buf, size)
        if n > 0:
            return n
        time.sleep(0.02)
    return 0


def test_connect_tunnel() -> None:
    print("\n-- 5. 回环实测：CONNECT 隧道 --")
    srv, port, results, done = start_server(echo_handler)
    try:
        net = fresh(dns_map=f"wap.skmeg.com->127.0.0.1:{port}")
        s = net.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
        net.connect(s, CMWAP_PROXY_IP, 80, MR_SOCKET_BLOCK)
        req = (b"CONNECT wap.skmeg.com:6009 HTTP/1.1\r\n"
               b"Proxy-Connection: Keep-Alive\r\n\r\n")
        n = net.send(s, put(net, req), len(req))
        check(n == len(req), "CONNECT 首包被代理消化")
        check(net.slots[s].tunnel, "进入隧道模式")
        buf = put(net, b"\0" * 256)
        n = wait_for_n(net, s, buf, 256)
        got = take(net, buf, n) if n > 0 else b""
        check(got == b"HTTP/1.1 200 Connection Established\r\n\r\n",
              "MRP 先收到代理生成的 200", repr(got))
        n2 = net.send(s, put(net, b"PING"), 4)
        check(n2 == 4, "隧道内 PING 透传")
        n3 = wait_for_n(net, s, buf, 256)
        check(take(net, buf, n3) == b"PONG", "隧道内收到 PONG")
        check(wait_for(lambda: bool(results)) and results[0] == b"PING",
              "上游只收到 PING，没收到 CONNECT 头", str(results))
    finally:
        done.set()
        srv.close()


def test_ip_mapping() -> None:
    print("\n-- 6. 显式映射 10.0.0.172 覆盖 WAP 代理 --")
    srv, port, results, done = start_server(http_handler)
    try:
        net = fresh(dns_map=f"10.0.0.172->127.0.0.1:{port}")
        s = net.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
        rc = net.connect(s, CMWAP_PROXY_IP, 80, MR_SOCKET_BLOCK)
        slot = net.slots[s]
        check(rc == MR_SUCCESS and not slot.is_proxy,
              "不再走假连接代理", f"rc={rc} proxy={slot.is_proxy}")
        check(slot.peer == ("127.0.0.1", port), "直连映射地址+端口",
              str(slot.peer))
        req = (b"POST /simpleDownload HTTP/1.1\r\n"
               b"Host: spd.skymobiapp.com:6009\r\n"
               b"Content-Length: 0\r\n\r\n")
        n = net.send(s, put(net, req), len(req))
        check(n == len(req), "请求原样发出")
        check(wait_for(lambda: bool(results)) and
              b"Host: spd.skymobiapp.com:6009" in results[0],
              "上游收到的 Host 保持老域名不变")
    finally:
        done.set()
        srv.close()

    # 规则 3：getHostByName 返回的 IP 命中带端口映射时补端口
    srv2, port2, _, done2 = start_server(http_handler)
    try:
        net2 = fresh(dns_map=f"service.test->127.0.0.1:{port2}")
        ip2 = net2.get_host_by_name("service.test")
        s2 = net2.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
        net2.connect(s2, ip2, 80, MR_SOCKET_BLOCK)
        check(net2.slots[s2].peer == ("127.0.0.1", port2),
              "connect(映射IP, 80) 自动改成映射端口",
              str(net2.slots[s2].peer))
    finally:
        done2.set()
        srv2.close()

    # 关掉 WAP 代理后，网关不再被接管
    net3 = fresh(dns_map="", wap_proxy=False)
    s3 = net3.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
    net3.connect(s3, CMWAP_PROXY_IP, 80, MR_SOCKET_BLOCK)
    check(not net3.slots[s3].is_proxy, "wap-proxy=off 时不接管 10.0.0.172")


def test_online() -> None:
    print("\n-- 8. 在线探针：复刻服务器 159.75.119.124 --")
    proxy = os.environ.get("PYMRP_NET_PROXY", "")
    net = fresh()
    net.connect_timeout = 8.0
    if proxy:                      # 直连不通时可让 TCP 走 Clash 的 CONNECT
        net.http_proxy = proxy
    ip = net.get_host_by_name("spd.skymobiapp.com")
    check(ip == ip_to_u32("159.75.119.124"), "老域名解析到复刻服务器")
    s = net.socket(MR_SOCK_STREAM, MR_IPPROTO_TCP)
    rc = net.connect(s, ip, 6009, MR_SOCKET_BLOCK)
    check(rc == MR_SUCCESS, "TCP 连上 159.75.119.124:6009", f"rc={rc}")
    if rc == MR_SUCCESS:
        # 实测：GET 会被 DNSPod 未备案拦截页 302，POST /simpleDownload
        # 才是斯凯真实 CGI（skyengine-v2 e2e 也是这条），返回 200。
        # 只发空 body，不构造 TLV，不会真正下载插件。
        req = (b"POST /simpleDownload HTTP/1.1\r\n"
               b"Host: spd.skymobiapp.com:6009\r\n"
               b"Content-Length: 0\r\nConnection: close\r\n\r\n")
        n = net.send(s, put(net, req), len(req))
        check(n == len(req), "POST /simpleDownload 请求发出")
        buf = put(net, b"\0" * 512)
        n2 = wait_for_n(net, s, buf, 512)
        body = take(net, buf, n2) if n2 > 0 else b""
        check(body.startswith(b"HTTP/1.") and b" 200 " in body[:32],
              "复刻 CGI 返回 HTTP 200", repr(body[:80]))
    net.close_network()


def test_cli_wiring() -> None:
    """CLI -> App -> NetEngine 的参数贯通（独立子进程，避免二次 init SDL）。"""
    print("\n-- 7. CLI 参数贯通 --")
    import subprocess
    import textwrap

    code = textwrap.dedent(f"""
        import contextlib, io, os, sys
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        sys.path.insert(0, {str(ROOT)!r})
        import pygame
        pygame.init(); pygame.display.set_mode((300, 660))
        from mrp_emu import net
        seen = {{}}
        orig = net.NetEngine.__init__
        def spy(self, *a, **kw):
            seen['dns_map'] = kw.get('dns_map')
            seen['wap_proxy'] = kw.get('wap_proxy')
            return orig(self, *a, **kw)
        net.NetEngine.__init__ = spy
        from mrp_emu.cli import main
        with contextlib.redirect_stdout(io.StringIO()), \\
                contextlib.redirect_stderr(io.StringIO()):
            main(['--boot', 'home', '--workdir', {str(ROOT / 'runtime')!r},
                  '--headless', '--frames', '1', '--audio', 'off',
                  '--dns-map', 'a.cn->1.2.3.4:8080', '--wap-proxy', 'off'])
        print('SEEN=' + repr(seen))
    """)
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT),
                       env=dict(os.environ, SDL_VIDEODRIVER="dummy"),
                       capture_output=True, text=True, timeout=90)
    line = next((x for x in (r.stdout or "").splitlines()
                 if x.startswith("SEEN=")), "")
    seen = {}
    if line:
        try:
            import ast
            seen = ast.literal_eval(line[5:])
        except (ValueError, SyntaxError):
            pass
    check(seen.get("dns_map") == "a.cn->1.2.3.4:8080",
          "--dns-map 传到 NetEngine", str(seen))
    check(seen.get("wap_proxy") is False,
          "--wap-proxy off 传到 NetEngine", str(seen))


def main() -> int:
    online = "--online" in sys.argv
    test_parse()
    test_request_parse()
    test_mapping()
    test_absolute_forward()
    test_connect_tunnel()
    test_ip_mapping()
    test_cli_wiring()
    if online:
        test_online()
    else:
        print("\n-- 8. 在线探针已跳过（加 --online 才会连 159.75.119.124）--")
    print(f"\n==== legacy_net_probe: {PASS} passed, {FAIL} failed ====")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
