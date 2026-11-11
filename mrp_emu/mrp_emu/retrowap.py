"""古董 QQ（爱Q手机QQ / MTK WAP 版）的本地服务端。

背景
----
``391032_240320_atxqq.mrp`` 是腾讯 2010 年前后给 MTK 功能机做的
**WAP 架构** QQ 客户端：包内自带 WAP 浏览器引擎（``cfunction.ext``）、
WML 模板（``mtt_start.wml`` / ``mtt_config.wml`` / ``error1|2.wml``）与
图标资源，聊天入口是伪协议 ``mtt:qq``。

它启动时第一件事就是::

    GET http://info.3g.qq.com/g/s?aid=index&s_it HTTP/1.1
    Host: info.3g.qq.com
    User-Agent: MAUI WAP Browser
    Q-UA: SKYQQ10_GA/100019&MTKMTT_1/090001&SKY&152020&6225&V2

``Q-UA`` 里的 ``SKYQQ10_GA`` 说明当年走的是**斯凯的 QQ 代收费代理**
（斯凯服务器已停运）。2014 年腾讯关闭 3G 移动 QQ、运营商 WAP 网关退网，
所以这些域名现在全是死链：

* ``info.3g.qq.com`` -> 302 到 https 后失效
* ``3g.qq.com`` -> 502

**本模块提供一套本地替代服务端**：用 Python 起一个 HTTP 服务器，
按 WAP 协议返回 WML 页面，配合模拟器的 ``--dns-map`` 把
``info.3g.qq.com`` 等域名指向本机，就能让这台古董 QQ 重新跑起来。

三部分
------
1. :class:`WapServer` —— 线程化的 HTTP 服务器，记录全部请求，
   按路径查 :class:`RouteTable` 返回 WML。
2. :class:`RouteTable` —— 路径 -> WML 生成器的路由表，
   带「缺页兜底」：未知路径返回一张带导航的门户首页。
3. :func:`serve_forever` —— 命令行入口，便于单独起服务再让模拟器连。

协议要点（从 mrpoid 官方源码与包内 WML 逆向得到）
--------------------------------------------------
* 客户端用 **CMWAP**（``10.0.0.172``）做代理，所以发到网关的是
  **绝对 URL**（``GET http://host/path HTTP/1.1``）。本地服务端按普通
  origin-form 解析即可（模拟器的 WAP 代理会改写成 origin-form）。
* 响应必须是 ``text/vnd.wap.wml``，正文是 UTF-8 的 WML 1.1。
* 客户端会用 ``mr_platEx(1207, ...)``（UCS-2 -> GBK）转换路径，
  所以 WML 里引用的本地资源用 ASCII 相对路径最稳。
"""

from __future__ import annotations

import argparse
import json
import socket
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


# ---------------------------------------------------------------- WML 模板
WML_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE wml PUBLIC "-//WAPFORUM//DTD WML 1.1//EN" '
    '"http://www.wapforum.org/DTD/wml_1.1.xml">\n'
    "\n<wml>\n"
)

WML_FOOTER = "</wml>\n"


def wml(title: str, body: str, extra_head: str = "") -> str:
    """拼一张 WML 卡片。"""
    return (f'{WML_HEADER}<card title="{title}">\n{extra_head}{body}\n'
            f"{WML_FOOTER}")


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


@dataclass
class Request:
    """一次请求的完整记录（用于抓包分析与回归断言）。"""

    method: str
    target: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: bytes
    at: float = field(default_factory=time.time)

    def q(self, key: str, default: str = "") -> str:
        v = self.query.get(key)
        return v[0] if v else default

    def header(self, key: str, default: str = "") -> str:
        return self.headers.get(key.lower(), default)

    def brief(self) -> str:
        q = ("?" + "&".join(f"{k}={v[0]}" for k, v in self.query.items())
             if self.query else "")
        return f"{self.method} {self.path}{q}"


@dataclass
class Route:
    """一条路由：匹配路径 -> 生成 WML 正文。"""

    path: str
    handler: object                      # callable(Request) -> str
    name: str = ""


class RouteTable:
    """路径路由表。

    匹配规则：精确路径优先，其次按前缀最长匹配（``/g/channels/`` 之类）。
    未命中时走 :attr:`fallback`。
    """

    def __init__(self, fallback=None) -> None:
        self.routes: list[Route] = []
        self.fallback = fallback or self.portal_home

    def add(self, path: str, handler, name: str = "") -> None:
        self.routes.append(Route(path, handler, name or path))

    def match(self, req: Request):
        best = None
        best_len = -1
        for r in self.routes:
            if r.path == req.path:
                return r
            if req.path.startswith(r.path) and len(r.path) > best_len:
                best, best_len = r, len(r.path)
        return best

    # -- 内置页面 --------------------------------------------------------
    def portal_home(self, req: Request) -> str:
        """门户首页（等价于当年的 ``/g/s?aid=index``）。

        结构照抄包内 ``mtt_start.wml``：搜索框 + 图标行 + 分类链接。
        链接全部指向本地 ``/g/...`` 路径，不依赖任何外网域名。
        """
        rows = [
            ("腾讯", "/g/s?aid=index", "首页"),
            ("新闻", "/g/channels/news.jsp", "资讯"),
            ("体育", "/g/channels/sports.jsp", "体育"),
            ("社区", "/g/channels/community.jsp", "社区"),
            ("音乐", "/g/channels/music.jsp", "音乐"),
            ("图书", "/g/channels/book.jsp", "书城"),
        ]
        links = " | ".join(
            f'<a href="{esc(p)}">{esc(n)}</a>' for n, p, _ in rows)
        body = (
            '<mttblock bgcolor="#123456">\n'
            '<input src="icon_url.gif" value="" alt="输入网址" '
            'maxlength="255" id="InputUrl_9984" format="a" align="fill" />\n'
            '<input src="icon_search.gif" value="" alt="搜索" '
            'maxlength="255" id="Search_9984" format="m" align="fill" />\n'
            "</mttblock>\n"
            "<p align=\"center\">\n"
            f"{links}\n"
            "</p>\n"
            "<p>【本地复古服务器】这是替代已停运腾讯 3G QQ 的本地 WAP 服务端。\n"
            "<br/>当前路径："
            f"{esc(req.path)}\n</p>\n"
            "<p><a href=\"mtt:qq\">进入 QQ 聊天</a></p>\n"
        )
        return wml("腾讯手机版首页", body)

    def qq_login(self, req: Request) -> str:
        """QQ 登录页（``mtt:qq`` 伪协议对应的落地页）。

        腾讯原来把聊天入口挂在 ``mtt:qq`` 上，由客户端本地处理；
        这里给一个普通的 WML 表单，提交到 ``/qq/login``。
        """
        body = (
            '<p align="center"><b>QQ 登录（本地复古服务器）</b></p>\n'
            "<p>原腾讯 3G QQ 已于 2014 年停止服务，这里用本地服务器替代。\n"
            "<br/>协议格式沿用斯凯 QQ 代理："
            "<code>VER=1.3&amp;CON=1&amp;CMD=LOGIN&amp;SEQ=n"
            "&amp;UIN=qq&amp;PS=xxx</code></p>\n"
            '<form method="get" action="/qq/login">\n'
            'QQ号：<input type="text" name="UIN" value="" maxlength="12"/>\n'
            "<br/>密码：<input type=\"text\" name=\"PS\" value=\"\" "
            "maxlength=\"32\"/>\n"
            "<br/><input type=\"submit\" value=\"登录\"/>\n"
            "</form>\n"
        )
        return wml("QQ登录", body)

    def qq_result(self, req: Request) -> str:
        """QQ 登录结果页。"""
        uin = req.q("UIN", "")
        body = (
            f"<p align=\"center\"><b>欢迎，{esc(uin)}</b></p>\n"
            "<p>已连上本地复古 QQ 服务器。</p>\n"
            "<p>好友列表：\n<br/>• 小明（在线）\n<br/>• 老板（离线）\n</p>\n"
            '<p><a href="/qq/chat">进入聊天</a></p>\n'
            '<p><a href="/g/s?aid=index">返回首页</a></p>\n'
        )
        return wml("QQ好友列表", body)

    def channel(self, name: str) -> str:
        """一个分类页（新闻/体育/社区…）。"""
        def handler(req: Request) -> str:
            body = (
                f'<p align="center"><b>{esc(name)}</b></p>\n'
                "<p>这里是「" + esc(name) + "」频道的本地占位页。\n"
                "<br/>原服务器已停运，内容由本地复古服务器生成。</p>\n"
                '<p><a href="/g/s?aid=index">返回首页</a></p>\n'
            )
            return wml(name, body)
        return handler


# ---------------------------------------------------------------- 服务器
class _Handler(BaseHTTPRequestHandler):
    server_version = "PymrpRetroWap/1.0"
    sys_version = ""

    # 静音默认的 stderr 日志，改用我们的记录器
    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        pass

    def _dispatch(self, method: str) -> None:
        server: "WapServer" = self.server.retro  # type: ignore[attr-defined]
        raw_target = self.path
        parsed = urlparse(raw_target)
        path = parsed.path or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        headers = {k.lower(): v for k, v in self.headers.items()}
        req = Request(method, raw_target, path, query, headers, body)
        server.record(req)

        route = server.routes.match(req)
        try:
            content = route.handler(req) if route else server.routes.fallback(req)
        except Exception as exc:  # noqa: BLE001
            server.log(f"[wap] 处理 {req.brief()} 出错: {exc}")
            content = wml("出错了", "<p>本地服务器内部错误。</p>\n")

        raw = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/vnd.wap.wml; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:      # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:     # noqa: N802
        self._dispatch("POST")

    def do_HEAD(self) -> None:     # noqa: N802
        self._dispatch("HEAD")


class WapServer(ThreadingHTTPServer):
    """线程化的 WAP 服务器（一个连接一个线程，模拟器是同步阻塞的）。"""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host: str = "127.0.0.1", port: int = 8080,
                 routes: RouteTable | None = None,
                 log=print) -> None:
        super().__init__((host, port), _Handler)
        self.retro = self                       # type: ignore[assignment]
        self.routes = routes or build_routes()
        self.requests: list[Request] = []
        self.log = log
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def record(self, req: Request) -> None:
        with self._lock:
            self.requests.append(req)
        self.log(f"[wap] {req.method} {req.brief()} "
                 f"UA={req.header('user-agent')!r} "
                 f"Q-UA={req.header('q-ua')!r}")

    def start_background(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self.serve_forever, name="retro-wap", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            self.shutdown()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.server_close()
        except Exception:  # noqa: BLE001
            pass
        self._thread = None

    def dump_json(self) -> str:
        with self._lock:
            data = [
                {"method": r.method, "path": r.path,
                 "query": {k: v for k, v in r.query.items()},
                 "headers": r.headers,
                 "body_len": len(r.body)}
                for r in self.requests
            ]
        return json.dumps(data, ensure_ascii=False, indent=2)


def build_routes() -> RouteTable:
    """默认路由表。"""
    rt = RouteTable()
    rt.add("/g/s", lambda req: rt.portal_home(req), "portal")
    rt.add("/g/channels/", lambda req: rt.channel("频道")(req), "channels")
    rt.add("/qq/login", lambda req: rt.qq_result(req), "qq-login")
    rt.add("/qq/chat", lambda req: rt.qq_result(req), "qq-chat")
    rt.add("/mtt/qq", lambda req: rt.qq_login(req), "mtt-qq")
    rt.add("/", lambda req: rt.portal_home(req), "root")
    return rt


# 腾讯 3G WAP 门户的全部域名（来自包内 mtt_start.wml）。
# 这些域名现在都是死链，本地服务端统一接管。
RETRO_DOMAINS = (
    "info.3g.qq.com",
    "3g.qq.com",
    "misc.3g.qq.com",
    "gp.3g.qq.com",
    "res.3g.qq.com",
    "jwt.3g.qq.com",
    "music33.3g.qq.com",
    "ebook.3g.qq.com",
    "wap.3g.qq.com",
    "wap.3g.cn",
    "z.qq.com",
    "w.mail.qq.com",
)


def dns_map_for(host: str, port: int,
                extra: str | None = None) -> str:
    """生成给 ``--dns-map`` 用的覆写串。

    把腾讯 3G 门户的全部域名指向本地复古服务端。``extra`` 里原有的
    斯凯域名覆写会保留（拼在后面，同一 host 后者不覆盖前者）。
    """
    parts = [f"{d}->{host}:{port}" for d in RETRO_DOMAINS]
    if extra:
        parts.extend(x for x in extra.split(";") if x.strip())
    return ";".join(parts)


def serve_forever(host: str = "127.0.0.1", port: int = 8080) -> None:
    """命令行入口：单独起一个本地 WAP 服务器。"""
    srv = WapServer(host, port)
    print(f"[wap] 古董 QQ 本地服务端已启动: http://{host}:{port}/")
    print("[wap] 模拟器侧用 --dns-map "
          f"'info.3g.qq.com->{host}:{port}' 接管")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[wap] 停止")
    finally:
        srv.stop()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="古董 QQ（爱Q手机QQ）本地 WAP 服务端")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args(argv)
    serve_forever(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
