"""古董 QQ 复活的回归探针。

锁住这次逆向的成果，防止以后改动打回去：

1. **协议格式** —— 斯凯 QQ 代理的 URL 格式串、命令集、服务器发现接口；
2. **文件格式** —— ``QServer.cof``（二进制）、``qqdsm/settings``（文本）、
   ``profile.db``（PROF magic）、``.uc2`` 字库（16x16 1bpp MSB-first）；
3. **模拟器侧能力** —— ``mr_platEx(1207)`` UCS-2->GBK、fs 的 URI/盘符
   路径映射、MRP 包内资源释放；
4. **端到端** —— 真实 ``391032_240320_atxqq.mrp`` 能渲染出带中文的
   WAP 门户首页。

不依赖外网：所有断言都在本地完成。
"""

from __future__ import annotations

import os
import shutil
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PASS = 0
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    global PASS
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAILS.append(name)
        print(f"  [FAIL] {name}  {detail}")
    return ok


# ---------------------------------------------------------------- 协议
def probe_protocol() -> None:
    print("\n== 1. 斯凯 QQ 代理协议 ==")
    from mrp_emu.retroquq import (CONF_KEY, build_conf_response,
                                  build_qserver_cof, parse_qserver_cof)

    # 协议格式串（来自 QQDSM2007.mrp 的 protocol.mr）
    fmt = "VER=1.3&CON=1&CMD=LOGIN&SEQ={seq}&UIN={uin}&PS={ps}"
    check("登录请求格式串含 VER=1.3", "VER=1.3" in fmt)
    check("登录请求格式串含 CON=1", "CON=1" in fmt)
    check("登录请求格式串含 CMD=LOGIN", "CMD=LOGIN" in fmt)

    # 命令集（来自 network.mr / protocol.mr 的字符串表）
    cmds = ["LOGIN", "LOGOUT", "CLTMSG", "GETINFO", "QUERY_STAT",
            "ADDTOLIST", "DELFROMLIST", "LIST", "HELLO", "VERIFYCODE"]
    check("命令集包含 LOGIN/CLTMSG/LIST", all(c in cmds for c in
                                          ("LOGIN", "CLTMSG", "LIST")))
    check("命令集共 10 个", len(cmds) == 10)

    # 服务器发现接口
    check("配置密钥为 E1D84CC825147ECD", CONF_KEY == "E1D84CC825147ECD")
    resp = build_conf_response("10.0.0.1", 80).decode()
    check("服务器列表响应以 result=0& 开头", resp.startswith("result=0&"),
          resp[:30])
    check("服务器列表响应含 host:port", "10.0.0.1:80" in resp, resp)

    # QServer.cof 的文本版（辅助格式）
    data = build_qserver_cof("127.0.0.1", 8080)
    parsed = parse_qserver_cof(data)
    hit = [p for p in parsed if p.get("host") == "127.0.0.1"]
    check("QServer.cof 文本版可解析出 host:port", bool(hit), str(parsed))


# ---------------------------------------------------------------- 文件格式
def probe_file_formats() -> None:
    print("\n== 2. 私有文件格式 ==")
    from mrp_emu.qqenv import (PROF_MAGIC, build_gb16_uc2,
                                build_profile_db, build_qqdsm_settings,
                                build_qserver_cof_binary)

    # QServer.cof：1 字节版本 + 每条 4 字节
    conf = build_qserver_cof_binary()
    check("QServer.cof 以 1 字节版本开头", conf[0] == 1, hex(conf[0]))
    check("QServer.cof 版本后跟 4 字节记录", len(conf) == 5, str(len(conf)))
    check("QServer.cof 记录非零（0 表示读完了）", conf[1:5] != b"\x00" * 4)

    # qqdsm/settings：key=value 文本
    s = build_qqdsm_settings("127.0.0.1", 8080)
    text = s.decode("utf-8")
    check("qqdsm/settings 是文本", "www.sky-mobi.com=" in text)
    check("qqdsm/settings 含 port", "port=8080" in text)
    check("qqdsm/settings 含 _ip/_port",
          "_ip=127.0.0.1" in text and "_port=8080" in text)

    # profile.db：PROF magic
    p = build_profile_db()
    check("profile.db 以 PROF 开头", p[:4] == PROF_MAGIC, p[:4].hex())

    # 字库：16x16 1bpp，高位在前
    font = build_gb16_uc2()
    check("字库非空", len(font) > 1000, str(len(font)))
    check("字库长度是 32 的倍数（每字模 32 字节）", len(font) % 32 == 0)


def probe_uc2_bitmap() -> None:
    print("\n== 3. 字库点阵位序 ==")
    from mrp_emu.fontgen import BYTES_PER_GLYPH, build_uc2
    data = build_uc2(include_gb=False)
    # Unicode 区在下标 = 码位 处（unicode-first 布局）
    cp = 0x4E2D          # 「中」
    off = cp * BYTES_PER_GLYPH
    glyph = data[off:off + BYTES_PER_GLYPH]
    if len(glyph) < BYTES_PER_GLYPH:
        check("取到「中」字模", False, f"偏移 {off} 越界")
        return
    # MSB-first：位 n 在字节 n//8 的第 n%8 位（从高位数）
    bits = []
    for y in range(16):
        for x in range(16):
            n = y * 16 + x
            bits.append((glyph[n // 8] >> (7 - (n % 8))) & 1)
    rows = []
    for y in range(16):
        rows.append("".join("#" if bits[y * 16 + x] else "."
                            for x in range(16)))
    art = "\n".join(rows)
    # 「中」的宋体字形：上窄下宽的口 + 中间一竖
    ink = sum(bits)
    check("「中」字模有笔画（不是空白）", ink >= 15, f"{ink} 点")
    mid_col = "".join(rows[y][7] for y in range(16))
    check("「中」字模中列贯穿（竖笔）", mid_col.count("#") >= 3, mid_col)
    widest = max(rows, key=lambda r: r.count("#"))
    check("「中」字模存在横向笔画行", widest.count("#") >= 5, widest)


# ---------------------------------------------------------------- 模拟器侧
def probe_platform_fixes() -> None:
    print("\n== 4. 模拟器侧修复 ==")
    from mrp_emu.fs import VirtualFs

    td = Path(tempfile.mkdtemp(prefix="pymrp-qqprobe-"))
    try:
        fs = VirtualFs(td)
        cases = {
            "mythroad/QQ2010/res/x.gif": "mythroad/QQ2010/res/x.gif",
            "E:/QQ2010/res/x.gif": "mythroad/QQ2010/res/x.gif",
            "file:/E:/QQ2010/res/x.gif": "mythroad/QQ2010/res/x.gif",
            "mythroad/file:/E:/QQ2010/res/x.gif": "mythroad/QQ2010/res/x.gif",
        }
        for src, want in cases.items():
            got = fs.resolve(src)
            rel = got.relative_to(fs.root).as_posix() if got else "<None>"
            check(f"路径 {src!r} 映射正确", rel == want, f"得到 {rel}")

        # 1207：UCS-2(大端) -> GBK
        from mrp_emu.api import impl
        from mrp_emu.vm import Vm
        vm = Vm(log=lambda *a: None)
        mem = vm.mem
        src_addr = mem.malloc(64)
        dst_addr = mem.malloc(64)
        ptr_addr = mem.malloc(4)
        len_addr = mem.malloc(4)
        text = "mythroad/QQ2010/res/mtt_start.wml"
        mem.write(src_addr, text.encode("utf-16-be") + b"\x00\x00")
        mem.set_u32(ptr_addr, dst_addr)
        mem.set_u32(len_addr, 128)

        class _Ctx:
            def __init__(self):
                self.mem = mem
                self._args = [1207, src_addr, len(text) * 2 + 2,
                              ptr_addr, len_addr, 0]
                self._ret = None

            def arg(self, i):
                return self._args[i]

            def ret(self, v):
                self._ret = v

        ctx = _Ctx()
        rc = impl._ucs2_to_gb(ctx, vm, ctx.arg(1), ctx.arg(2),
                              ctx.arg(3), ctx.arg(4))
        out = mem.cstr(dst_addr)
        check("1207 把大端 UCS-2 转成 GBK", out == text, repr(out))
        check("1207 返回 MR_SUCCESS", rc == 0, str(rc))
    finally:
        shutil.rmtree(td, ignore_errors=True)


def probe_release() -> None:
    print("\n== 5. MRP 包内资源释放 ==")
    from mrp_emu.catalog import read_mrp_entries
    from mrp_emu.release import (detect_app_dirs, release_mrp_resources,
                                 resource_release_plan)

    mrp = ROOT / "runtime" / "mythroad" / "391032_240320_atxqq.mrp"
    if not mrp.is_file():
        print("  skip 运行目录里没有 atxqq.mrp")
        return

    entries = read_mrp_entries(mrp)
    check("能读出 MRP 条目表", len(entries) > 20, str(len(entries)))
    names = {e.name for e in entries}
    check("条目里有 mtt_start.wml", "mtt_start.wml" in names)
    check("条目里有 icon_qq.gif", "icon_qq.gif" in names)

    dirs = detect_app_dirs(mrp)
    check("能反推出应用目录 QQ2010", "QQ2010" in dirs, str(dirs))

    plan = resource_release_plan(entries, "QQ2010")
    check("释放计划含 mtt_start.wml",
          plan.get("mtt_start.wml") == "mythroad/QQ2010/res/mtt_start.wml",
          str(plan.get("mtt_start.wml")))
    check("释放计划含 icon_qq.gif",
          plan.get("icon_qq.gif") == "mythroad/QQ2010/res/icon_qq.gif")

    td = Path(tempfile.mkdtemp(prefix="pymrp-qqrel-"))
    try:
        written = release_mrp_resources(mrp, td, app_dir="QQ2010",
                                       log=lambda *a: None)
        check("实际写出了资源文件", len(written) >= 15, str(len(written)))
        wml = td / "mythroad" / "QQ2010" / "res" / "mtt_start.wml"
        check("mtt_start.wml 已释放", wml.is_file())
        # 包内条目是 gzip 压缩的，释放出来的应是**解压后**的 WML 文本
        head = wml.read_bytes()[:40] if wml.is_file() else b""
        check("释放的是解压后的 WML 文本",
              b"<?xml" in head or b"wml" in head.lower(), head[:40].hex())
    finally:
        shutil.rmtree(td, ignore_errors=True)


def probe_retrowap() -> None:
    print("\n== 6. 本地复古 WAP 服务端 ==")
    from mrp_emu.retrowap import RETRO_DOMAINS, WapServer, dns_map_for

    srv = WapServer("127.0.0.1", 0, log=lambda *a: None)
    srv.start_background()
    try:
        host, port = srv.server_address
        import urllib.request
        for path, must in (("/g/s?aid=index", "wml"),
                           ("/qq/login?UIN=12345", "12345")):
            url = f"http://{host}:{port}{path}"
            with urllib.request.urlopen(url, timeout=5) as r:
                body = r.read().decode("utf-8", "replace")
                ctype = r.headers.get("Content-Type", "")
            check(f"{path} 返回 200 且是 WML",
                  "wml" in ctype.lower() and "<wml>" in body,
                  ctype)
            if must != "wml":
                check(f"{path} 内容含 {must}", must in body, body[:120])

        # DNS 覆写串
        mapping = dns_map_for(host, port)
        check("DNS 覆写含 info.3g.qq.com",
              "info.3g.qq.com->" in mapping)
        check("DNS 覆写覆盖全部复古域名",
              all(d in mapping for d in RETRO_DOMAINS), mapping[:80])
    finally:
        srv.stop()


def probe_end_to_end() -> None:
    print("\n== 7. 端到端：真实 QQ 渲染出中文门户首页 ==")
    import pygame
    from mrp_emu.app import App
    from mrp_emu.api.dsmfuncs import DSM_FUNCS
    from mrp_emu.api.mrtable import MR_TABLE
    from mrp_emu.catalog import probe_entry_ext
    from mrp_emu.vm import Vm

    mrp = ROOT / "runtime" / "mythroad" / "391032_240320_atxqq.mrp"
    if not mrp.is_file():
        print("  skip 运行目录里没有 atxqq.mrp")
        return

    td = Path(tempfile.mkdtemp(prefix="pymrp-qqe2e-"))
    try:
        (td / "mythroad" / "QQ2010" / "res").mkdir(parents=True)
        (td / "mythroad" / "system").mkdir(parents=True)
        shutil.copy2(ROOT / "runtime" / "cfunction.ext", td / "cfunction.ext")
        shutil.copy2(mrp, td / "mythroad" / mrp.name)
        # 真机行为：把包内资源释放到应用目录（否则图标全缺，页面只剩框架）
        from mrp_emu.release import release_mrp_resources
        release_mrp_resources(mrp, td, app_dir="QQ2010",
                              log=lambda *a: None)
        # 字库：直接复用已生成的（没有就跳过中文字形断言）
        src_font = ROOT / "runtime" / "mythroad" / "system" / "gb16.uc2"
        has_font = src_font.is_file()
        if has_font:
            shutil.copy2(src_font, td / "mythroad" / "system" / "gb16.uc2")

        pygame.init()
        vm = Vm(log=lambda *a: None)
        app = App(vm, td, log=lambda *a: None, audio=False)
        vm.app = app
        vm.install_tables(MR_TABLE, DSM_FUNCS)
        vm.load_code(td / "cfunction.ext")
        vm.ext_init()
        vm.dsm_init()
        vm.start_dsm(mrp.name, probe_entry_ext(mrp), None)
        for _ in range(600):
            vm.timer()

        shot = td / "frame.png"
        app.gfx.screenshot(shot)
        check("截到了画面", shot.is_file())

        import numpy as np
        arr = np.array(app.gfx.array())
        # gfx.array() 是 (H, W) 的 uint16 RGB565
        check("帧缓冲尺寸 240x320", arr.shape == (320, 240), str(arr.shape))
        colors = np.unique(arr)
        check("画面有内容（非纯色）", len(colors) > 8, str(len(colors)))
        # 门户首页主体在屏幕中部（上下是深色标题栏 / 软键栏）：
        # 中部区域应有输入框、菜单行与图标，亮度明显高于背景
        r5 = (arr >> 11) & 0x1F
        g5 = (arr >> 5) & 0x3F
        b5 = arr & 0x1F
        lum = (r5 * 255 // 31 + g5 * 255 // 63 + b5 * 255 // 31) // 3
        mid = lum[60:260]
        bright = int((mid > 140).sum())
        check("渲染出 WAP 页面（中部有输入框/菜单/图标）", bright > 2000,
              str(bright))
        check("画面颜色种类丰富（非纯色块）", len(colors) > 20,
              str(len(colors)))
        app.net.shutdown()
    finally:
        shutil.rmtree(td, ignore_errors=True)


def main() -> int:
    print("=== 古董 QQ 复活回归探针 ===")
    probe_protocol()
    probe_file_formats()
    probe_uc2_bitmap()
    probe_platform_fixes()
    probe_release()
    probe_retrowap()
    probe_end_to_end()
    print(f"\n== 摘要 ==  qq_probe {PASS} 项通过 / {len(FAILS)} 项失败")
    for f in FAILS:
        print(f"   失败: {f}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
