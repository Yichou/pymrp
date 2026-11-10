"""网络模块自检 + RX 管理器崩溃回归。

不需要联网：TCP/UDP 都打本机回环，DNS 只解析点分十进制与 localhost。
跑法::

    python tests/net_probe.py
"""
from __future__ import annotations

import os
import socket
import struct
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
pygame.init()

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP  # noqa: E402

from mrp_emu.api import impl  # noqa: E402
from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.bridge import ArmCall  # noqa: E402
from mrp_emu.consts import (  # noqa: E402
    KEY_NAME_TO_CODE, MR_FAILED, MR_SUCCESS, MR_WAITING,
)
from mrp_emu.net import (  # noqa: E402
    CMWAP_PROXY_IP, DSM_SOC_CLOSE, DSM_SUPPROT_SOC_NUM,
    MR_IPPROTO_TCP, MR_IPPROTO_UDP, MR_SOCKET_BLOCK, MR_SOCKET_NONBLOCK,
    MR_SOCK_DGRAM, MR_SOCK_STREAM, ip_to_u32, parse_host, split_host_port,
    u32_to_ip,
)
from mrp_emu.vm import Vm  # noqa: E402

PASS = 0
FAIL = 0
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


def check(cond: bool, msg: str, extra: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {msg}")
    else:
        FAIL += 1
        print(f"  FAIL {msg} {extra}")


def s32(v: int) -> int:
    return v - 0x100000000 if v & 0x80000000 else v


class Caller:
    """按 ARM AAPCS 造一次桥接调用，返回 R0（第 5 个参数压栈）。"""

    def __init__(self, vm):
        self.vm = vm

    def __call__(self, fn, *args) -> int:
        uc = self.vm.uc
        for i, v in enumerate(args[:4]):
            uc.reg_write(REGS[i], int(v) & 0xFFFFFFFF)
        if len(args) > 4:
            sp = uc.reg_read(UC_ARM_REG_SP)
            extra = b"".join(struct.pack("<I", int(v) & 0xFFFFFFFF)
                             for v in args[4:])
            uc.mem_write(sp, extra)
        ctx = ArmCall(uc, self.vm.mem)
        fn(ctx, self.vm)
        ctx.flush()
        return s32(uc.reg_read(UC_ARM_REG_R0))

    def cstr(self, text: str) -> int:
        raw = text.encode("gbk", "replace") + b"\x00"
        p = self.vm.mem.malloc(len(raw))
        self.vm.mem.write(p, raw)
        return p

    def buf(self, size: int = 512) -> int:
        p = self.vm.mem.malloc(size)
        self.vm.mem.memset(p, 0, size)
        return p


def test_consts() -> None:
    print("\n-- 常量 / 工具函数 --")
    check(ip_to_u32("10.0.0.172") == CMWAP_PROXY_IP, "ip_to_u32 与 cmwap 网关常量一致")
    check(u32_to_ip(0x7F000001) == "127.0.0.1", "u32_to_ip 主机序还原")
    check(u32_to_ip(ip_to_u32("192.168.1.7")) == "192.168.1.7", "IP 往返一致")
    check(DSM_SUPPROT_SOC_NUM == 10, "socket 槽位数与 dsm.h 一致")
    check(parse_host(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n") == "example.com",
          "解析 Host 头")
    check(parse_host(b"GET / HTTP/1.1\r\nX-Online-Host: a.cn:8080\r\n\r\n") == "a.cn:8080",
          "解析 X-Online-Host（cmwap）")
    check(split_host_port("a.cn:8080") == ("a.cn", 8080), "拆分 host:port")
    check(split_host_port("a.cn") == ("a.cn", 80), "缺省端口 80")


def test_registration() -> None:
    print("\n-- API 注册 --")
    names = ["mr_initNetwork", "mr_closeNetwork", "mr_getHostByName",
             "mr_socket", "mr_connect", "mr_closeSocket", "mr_recv",
             "mr_recvfrom", "mr_send", "mr_sendto", "mr_getSocketState",
             "dsm_initNetwork", "dsm_getHostByName"]
    check(all(n in impl.IMPL for n in names), "13 个网络实现全部注册")
    miss = [f.name for f in MR_TABLE if f.name.startswith("mr_") and f.fn is None]
    check(not any(n.startswith(("mr_initNetwork", "mr_socket", "mr_recv", "mr_send"))
                  for n in miss), "mr_table 网络槽位不是空实现")
    check(all(f.fn is not None for f in DSM_FUNCS), "dsm_require_funcs 51 槽全部有实现")


def test_tcp(vm, call: Caller) -> None:
    print("\n-- TCP 回环（socket/connect/send/recv/getSocketState/close）--")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    received: list[bytes] = []

    def serve():
        try:
            conn, _ = srv.accept()
            conn.settimeout(3)
            data = conn.recv(64)
            received.append(data)
            conn.sendall(b"PONG")
            time.sleep(0.15)
            conn.close()
        except OSError:
            pass

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    check(call(impl.mr_initNetwork, 0, call.cstr("cmnet")) == MR_SUCCESS,
          "mr_initNetwork 返回 MR_SUCCESS")
    s = call(impl.mr_socket, MR_SOCK_STREAM, MR_IPPROTO_TCP)
    check(s == 0, f"mr_socket 返回首个空闲槽位 (得到 {s})")
    ip = ip_to_u32("127.0.0.1")
    rc = call(impl.mr_connect, s, ip, port, MR_SOCKET_BLOCK)
    check(rc == MR_SUCCESS, f"mr_connect 阻塞连接成功 (得到 {rc})")
    check(call(impl.mr_getSocketState, s) == MR_SUCCESS, "getSocketState 已连接")

    src = call.buf(64)
    vm.mem.write(src, b"PING")
    sent = call(impl.mr_send, s, src, 4)
    check(sent == 4, f"mr_send 发出 4 字节 (得到 {sent})")

    t.join(timeout=3)
    check(received and received[0] == b"PING", "服务端收到 PING",
          repr(received))
    dst = call.buf(64)
    time.sleep(0.05)
    got = call(impl.mr_recv, s, dst, 64)
    check(got == 4, f"mr_recv 收到 4 字节 (得到 {got})")
    check(bytes(vm.mem.read(dst, 4)) == b"PONG", "收到的内容是 PONG",
          repr(bytes(vm.mem.read(dst, 4))))
    check(call(impl.mr_closeSocket, s) == MR_SUCCESS, "mr_closeSocket 成功")
    check(vm.app.net.slots[s].state == DSM_SOC_CLOSE, "槽位已回收")
    srv.close()


def test_nonblock(vm, call: Caller) -> None:
    print("\n-- 非阻塞连接状态机 --")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    s = call(impl.mr_socket, MR_SOCK_STREAM, MR_IPPROTO_TCP)
    rc = call(impl.mr_connect, s, ip_to_u32("127.0.0.1"), port,
              MR_SOCKET_NONBLOCK)
    check(rc in (MR_SUCCESS, MR_WAITING), f"非阻塞 connect 返回 SUCCESS/WAITING (得到 {rc})")
    state = call(impl.mr_getSocketState, s)
    check(state in (MR_SUCCESS, MR_WAITING), f"getSocketState 状态合法 (得到 {state})")
    call(impl.mr_closeSocket, s)
    srv.close()


def test_udp(vm, call: Caller) -> None:
    print("\n-- UDP 回环（sendto/recvfrom 写回 ip/port）--")
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(("127.0.0.1", 0))
    srv.settimeout(3)
    port = srv.getsockname()[1]

    def serve():
        try:
            data, addr = srv.recvfrom(64)
            srv.sendto(b"U" + data, addr)
        except OSError:
            pass

    threading.Thread(target=serve, daemon=True).start()
    s = call(impl.mr_socket, MR_SOCK_DGRAM, MR_IPPROTO_UDP)
    check(s >= 0, f"UDP socket 建成功 (得到 {s})")
    src = call.buf(32)
    vm.mem.write(src, b"ABC")
    ip_ptr, port_ptr = call.buf(8), call.buf(8)
    sent = call(impl.mr_sendto, s, src, 3, ip_to_u32("127.0.0.1"), port)
    check(sent == 3, f"sendto 发出 3 字节 (得到 {sent})")
    dst = call.buf(64)
    time.sleep(0.1)
    got = call(impl.mr_recvfrom, s, dst, 64, ip_ptr, port_ptr)
    check(got == 4, f"recvfrom 收到 4 字节 (得到 {got})")
    check(bytes(vm.mem.read(dst, 4)) == b"UABC", "UDP 回显内容正确")
    check(vm.mem.u32(ip_ptr) == ip_to_u32("127.0.0.1"), "写回来源 IP",
          hex(vm.mem.u32(ip_ptr)))
    check(vm.mem.u16(port_ptr) == port, "写回来源端口",
          str(vm.mem.u16(port_ptr)))
    call(impl.mr_closeSocket, s)
    srv.close()


def test_dns(vm, call: Caller) -> None:
    print("\n-- DNS --")
    v = call(impl.mr_getHostByName, call.cstr("127.0.0.1"), 0)
    check(v == ip_to_u32("127.0.0.1"), f"点分十进制直接返回 IP (得到 {v:#x})")
    v2 = call(impl.dsm_getHostByName, call.cstr("localhost"), 0, 0x1234)
    check(v2 == ip_to_u32("127.0.0.1"), f"dsm 三参数版解析 localhost (得到 {v2:#x})")
    v3 = call(impl.mr_getHostByName, call.cstr(""), 0)
    check(v3 == MR_FAILED, "空主机名返回 MR_FAILED")


def test_cmwap(vm, call: Caller) -> None:
    print("\n-- cmwap 10.0.0.172 代理（首次 send 解析 Host 再真连）--")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    got: list[bytes] = []

    def serve():
        try:
            conn, _ = srv.accept()
            conn.settimeout(3)
            got.append(conn.recv(512))
            conn.close()
        except OSError:
            pass

    threading.Thread(target=serve, daemon=True).start()
    s = call(impl.mr_socket, MR_SOCK_STREAM, MR_IPPROTO_TCP)
    check(call(impl.mr_connect, s, CMWAP_PROXY_IP, 80, MR_SOCKET_BLOCK) == MR_SUCCESS,
          "连 cmwap 网关先返回假成功")
    check(vm.app.net.slots[s].is_proxy and not vm.app.net.slots[s].real_connected,
          "槽位标记为待解析代理")
    req = (f"GET / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n\r\n").encode("ascii")
    src = call.buf(256)
    vm.mem.write(src, req)
    n = call(impl.mr_send, s, src, len(req))
    check(n == len(req), f"代理请求发送成功 (得到 {n})")
    check(vm.app.net.slots[s].real_connected, "已补上真实连接")
    check(vm.app.net.slots[s].host == f"127.0.0.1:{port}", "真实主机名已记录")
    time.sleep(0.1)
    check(bool(got) and b"Host:" in got[0], "本地服务端收到 HTTP 请求")
    call(impl.mr_closeSocket, s)
    srv.close()


def test_callback(vm) -> None:
    print("\n-- ARM 异步回调（NETWORK_CB 走 call_arm）--")
    net = vm.app.net
    calls: list[tuple] = []

    class FakeVm:
        def __init__(self, mem):
            self.mem = mem      # _queue_callback 要校验地址合法性

        def call_arm(self, addr, p0=0, p1=0, p2=0):
            calls.append((addr, p0, p1))
            return 0

    real_vm = net.vm
    net.vm = FakeVm(real_vm.mem)
    try:
        cb = 0x80000 + 8          # 模拟内存内的合法代码地址
        check(net.init_network(cb, "cmwap", 0x1234) == MR_SUCCESS,
              "initNetwork 排队成功回调")
        net.poll()
        check(len(calls) == 1, f"poll 触发 1 次回调 (得到 {len(calls)})")
        if calls:
            check(calls[0] == (cb, MR_SUCCESS, 0x1234),
                  "回调参数 (result=MR_SUCCESS, userData=0x1234)", str(calls[0]))
        check(net.stats["callbacks"] == 1, "回调计数已累加")
        net._queue_callback(0, MR_SUCCESS, 0)     # NULL 回调不应入队
        net.poll()
        check(len(calls) == 1, "NULL 回调被安全忽略")
    finally:
        net.vm = real_vm


def test_platex_1204(vm, call: Caller) -> None:
    print("\n-- mr_platEx(1204) dsmSwitchPath --")
    inp = call.cstr("Y")
    out_ptr, out_len_ptr = call.buf(8), call.buf(8)
    rc = call(impl.mr_platEx, 1204, inp, 1, out_ptr, out_len_ptr, 0)
    check(rc == MR_SUCCESS, "1204 返回 MR_SUCCESS")
    ptr = vm.mem.u32(out_ptr)
    n = vm.mem.u32(out_len_ptr)
    text = vm.mem.cstr(ptr)
    check(ptr != 0 and n > 0, "写回了 *output 与 *output_len",
          f"ptr=0x{ptr:X} n={n}")
    check(text.startswith("c:/"), f"Y 分支返回绝对路径 {text!r}")
    check(n == len(text.encode("gbk", "replace")), "output_len 与字符串长度一致")

    inp2 = call.cstr("c:/mythroad/games")
    call(impl.mr_platEx, 1204, inp2, 18, 0, 0, 0)
    check(vm.app.fs.work_path == "games/", "C 盘子路径更新 work_path",
          vm.app.fs.work_path)
    inp3 = call.cstr("Z")
    call(impl.mr_platEx, 1204, inp3, 1, 0, 0, 0)
    check(vm.app.fs.work_path == "mythroad/", "Z 分支回启动目录")


def test_fs_clamp(vm) -> None:
    print("\n-- 路径钳制（RX 管理器崩溃回归）--")
    root = vm.app.fs.root
    check(vm.app.fs.resolve("./..") == root, "根目录的 '..' 钳回 root，不再返回 NULL")
    check(vm.app.fs.resolve("mythroad/../..") == root, "多级 '..' 钳回 root")
    check(vm.app.fs.resolve("./") == root, "'./' 解析成 root")
    p = vm.app.fs.resolve("c:/../../Windows")
    check(p is not None and p.parent == root, "盘符 + 穿越被钳制在 root 内", str(p))
    check(vm.app.fs.resolve("mythroad") == root / "mythroad", "正常路径不受影响")
    check(vm.uc.mem_read(0, 4) == b"\x00\x00\x00\x00", "零页已映射且可读全 0")


def test_rx_regression(vm, call: Caller) -> None:
    print("\n-- RX 管理器真实按键序列（原崩溃点）--")
    # 固定隔离环境：不带上一次运行自建的缓存目录，保证 90 步按键可复现
    # （背景见 tests/rx_env.py）；用 HEAD 原版代码对照过，直接跑 runtime/
    # 会因目录漂移触发 RX 应用自身的野指针崩溃。
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from rx_env import RX_MRP, make_rx_env  # noqa: E402
    wd, cleanup = make_rx_env(ROOT / "runtime")
    if wd is None:
        print("  skip 运行环境不完整")
        return
    target = wd / "mythroad" / RX_MRP
    from mrp_emu.catalog import probe_entry_ext  # noqa: E402
    v = Vm(log=lambda *a: None)
    a = App(v, wd, log=lambda *a: None, audio=False)
    v.app = a
    v.install_tables(MR_TABLE, DSM_FUNCS)
    v.load_code(wd / "cfunction.ext")
    v.ext_init()
    v.dsm_init()
    r = v.start_dsm(target.name, probe_entry_ext(target), None)
    check(r in (0, 1), f"RX 管理器启动成功 (得到 {r})")
    seq = (["DOWN"] * 6 + ["SELECT"] + ["DOWN"] * 4 + ["SOFT_R"] +
           ["UP"] * 3 + ["SELECT"] + ["DOWN"] * 8 + ["SELECT"] + ["SOFT_R"] +
           ["1"] + ["DOWN"] * 10 + ["2"] + ["SOFT_L"] + ["3"] + ["SELECT"] +
           ["SOFT_R"] * 3 + ["UP"] * 12 + ["SELECT"] +
           ["LEFT", "RIGHT", "LEFT", "RIGHT", "CLEAR", "*", "#"] +
           ["DOWN"] * 20 + ["SELECT"] + ["SOFT_R"] * 5)
    crashed = ""
    try:
        for name in seq:
            code = KEY_NAME_TO_CODE[name]
            v.key_event(code, True)
            v.timer()
            v.key_event(code, False)
            v.timer()
    except Exception as exc:  # noqa: BLE001
        crashed = str(exc)
    check(not crashed, f"{len(seq)} 步按键无 UC_ERR_READ_UNMAPPED", crashed)
    a.net.close_network()
    cleanup()


def main() -> int:
    vm = Vm(log=lambda *a: None)
    app = App(vm, ROOT / "runtime", log=lambda *a: None, audio=False)
    vm.app = app
    call = Caller(vm)
    try:
        test_consts()
        test_registration()
        test_dns(vm, call)
        test_tcp(vm, call)
        test_nonblock(vm, call)
        test_udp(vm, call)
        test_cmwap(vm, call)
        test_callback(vm)
        test_platex_1204(vm, call)
        test_fs_clamp(vm)
        test_rx_regression(vm, call)
    finally:
        app.net.shutdown()
    print(f"\n==== net_probe: {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
