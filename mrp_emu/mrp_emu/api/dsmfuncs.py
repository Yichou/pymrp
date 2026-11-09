"""dsm_require_funcs —— 平台提供给 mythroad 层的 52 个函数。

顺序与 mythroad/include/dsm.h 的 DSM_REQUIRE_FUNCS 结构体字段一一对应。
注意这里的名字不带 mr_ 前缀，但实现与 mr_table 里的是同一套，靠 ALIAS 复用。
"""

from __future__ import annotations

from ..bridge import BridgeFunc
from . import impl

# dsm 名 -> impl 里的实现名
ALIAS = {
    "test": "test",
    "log": "log",
    "exit": "exit",
    "srand": "srand",
    "rand": "rand",
    "mem_get": "mem_get",
    "mem_free": "mem_free",
    "timerStart": "mr_timerStart",
    "timerStop": "mr_timerStop",
    "get_uptime_ms": "get_uptime_ms",
    "getDatetime": "mr_getDatetime",
    "sleep": "mr_sleep",
    "open": "mr_open",
    "close": "mr_close",
    "read": "mr_read",
    "write": "mr_write",
    "seek": "mr_seek",
    "info": "mr_info",
    "remove": "mr_remove",
    "rename": "mr_rename",
    "mkDir": "mr_mkDir",
    "rmDir": "mr_rmDir",
    "opendir": "opendir",
    "readdir": "readdir",
    "closedir": "closedir",
    "getLen": "mr_getLen",
    "drawBitmap": "mr_drawBitmap",
    "getHostByName": "mr_getHostByName",
    "initNetwork": "mr_initNetwork",
    "mr_closeNetwork": "mr_closeNetwork",
    "mr_socket": "mr_socket",
    "mr_connect": "mr_connect",
    "mr_getSocketState": "mr_getSocketState",
    "mr_closeSocket": "mr_closeSocket",
    "mr_recv": "mr_recv",
    "mr_send": "mr_send",
    "mr_recvfrom": "mr_recvfrom",
    "mr_sendto": "mr_sendto",
    "mr_startShake": "mr_startShake",
    "mr_stopShake": "mr_stopShake",
    "mr_playSound": "mr_playSound",
    "mr_stopSound": "mr_stopSound",
    "mr_dialogCreate": "mr_dialogCreate",
    "mr_dialogRelease": "mr_dialogRelease",
    "mr_dialogRefresh": "mr_dialogRefresh",
    "mr_textCreate": "mr_textCreate",
    "mr_textRelease": "mr_textRelease",
    "mr_textRefresh": "mr_textRefresh",
    "mr_editCreate": "mr_editCreate",
    "mr_editRelease": "mr_editRelease",
    "mr_editGetText": "mr_editGetText",
}

_ORDER = [
    (0x00, "test"), (0x04, "log"), (0x08, "exit"), (0x0C, "srand"), (0x10, "rand"),
    (0x14, "mem_get"), (0x18, "mem_free"),
    (0x1C, "timerStart"), (0x20, "timerStop"), (0x24, "get_uptime_ms"),
    (0x28, "getDatetime"), (0x2C, "sleep"),
    (0x30, "open"), (0x34, "close"), (0x38, "read"), (0x3C, "write"),
    (0x40, "seek"), (0x44, "info"), (0x48, "remove"), (0x4C, "rename"),
    (0x50, "mkDir"), (0x54, "rmDir"),
    (0x58, "opendir"), (0x5C, "readdir"), (0x60, "closedir"), (0x64, "getLen"),
    (0x68, "drawBitmap"),
    (0x6C, "getHostByName"), (0x70, "initNetwork"), (0x74, "mr_closeNetwork"),
    (0x78, "mr_socket"), (0x7C, "mr_connect"), (0x80, "mr_getSocketState"),
    (0x84, "mr_closeSocket"), (0x88, "mr_recv"), (0x8C, "mr_send"),
    (0x90, "mr_recvfrom"), (0x94, "mr_sendto"),
    (0x98, "mr_startShake"), (0x9C, "mr_stopShake"),
    (0xA0, "mr_playSound"), (0xA4, "mr_stopSound"),
    (0xA8, "mr_dialogCreate"), (0xAC, "mr_dialogRelease"), (0xB0, "mr_dialogRefresh"),
    (0xB4, "mr_textCreate"), (0xB8, "mr_textRelease"), (0xBC, "mr_textRefresh"),
    (0xC0, "mr_editCreate"), (0xC4, "mr_editRelease"), (0xC8, "mr_editGetText"),
]

DSM_FUNCS: list[BridgeFunc] = [
    BridgeFunc(pos, name, impl.get(ALIAS.get(name, name)))
    for pos, name in _ORDER
]

# 0x00..0xc8 步长 4 = 51 项，与 DSM_REQUIRE_FUNCS 结构体字段数一致
assert len(DSM_FUNCS) == 51, f"dsm_require_funcs 应有 51 项，实际 {len(DSM_FUNCS)}"
