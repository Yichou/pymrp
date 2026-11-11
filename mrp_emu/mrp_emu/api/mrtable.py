"""mr_table —— MRP 侧的 143 个 API 槽位。

偏移量必须与 vmrp 的 mr_table_funcMap 完全一致：这些数字是编译进
cfunction.ext 里的，错一位就全线崩。
"""

from __future__ import annotations

from ..bridge import BridgeFunc
from ..consts import CODE_ADDRESS, MR_SUCCESS, SCREEN_BPP, SCREEN_HEIGHT, SCREEN_WIDTH
from . import impl


# ---------------------------------------------------------------- 数据槽
def _const(fn):
    """数据槽：init 时把计算出的值写进槽位（不是函数指针）。"""
    def init(vm, addr):
        vm.mem.set_u32(addr, fn(vm) & 0xFFFFFFFF)
    return init


def _str_slot(text: str):
    def init(vm, addr):
        p = vm.mem.malloc(len(text.encode("gbk", "replace")) + 1)
        if p:
            vm.mem.put_cstr(p, text)
        vm.mem.set_u32(addr, p)
    return init


# ---------------------------------------------------------------- 特殊函数
def _mr_c_function_new(ctx, vm):
    """ext 的入口回调：把自己的 helper 地址交回来，并领取参数结构体。"""
    helper_addr = ctx.arg(0)
    length = ctx.arg(1)
    vm.mr_extHelper_addr = helper_addr
    size = max(length, 32)
    vm.mr_c_function_P = ctx.mem.malloc(size)
    ctx.mem.memset(vm.mr_c_function_P, 0, size)
    # ext 约定：CODE_ADDRESS+4 存放 mr_c_function_P 指针
    ctx.mem.set_u32(CODE_ADDRESS + 4, vm.mr_c_function_P)
    vm.log(
        f"[ext] mr_c_function_new(helper=0x{helper_addr:X}, len={length}) "
        f"-> P@0x{vm.mr_c_function_P:X}"
    )
    ctx.ret(MR_SUCCESS)


def _mr_printf(ctx, vm):
    fmt = ctx.str_arg(0)
    nargs = max(0, fmt.count("%") - fmt.count("%%") * 2)
    args = [ctx.arg(1 + i) for i in range(nargs)]
    text = impl._fmt(fmt, args, ctx.mem)
    vm.app.log(f"[mrp] {text}")
    ctx.ret(MR_SUCCESS)


def _mem_get(ctx, vm):
    impl.dsm_mem_get(ctx, vm)


def _mem_free(ctx, vm):
    impl.dsm_mem_free(ctx, vm)


def F(pos: int, name: str, fn=None, init=None, note: str = "") -> BridgeFunc:
    if fn is None and init is None:
        fn = impl.get(name)
    return BridgeFunc(pos, name, fn, init, note)


MR_TABLE: list[BridgeFunc] = [
    # ---- 内存 / 字符串 ----
    # 槽位顺序说明（2026-11-10 核对）：
    #   0x000–0x040 与 mrpoid 官方 mr/mythroad.c::_mr_c_function_table[] 完全一致；
    #   从 0x048 起与官方**错位一格**——官方那里是 mr_sprintf，我们没有这一槽。
    #   我们的顺序是照 cfunction.ext 反推的（0x054/0x058 是 ext 里真实的空洞，
    #   所以放 reserve0/reserve1），且实测 4 个真实 MRP 从不调用 0x048 之后的槽位
    #   （应用走 DSM 层 51 槽；C 库由 ext 自己的 _mr_c_function_new 注册接管）。
    #   差异清单与风险见 tests/table_probe.py、docs/19。
    # 槽位顺序说明（2026-11-10 核对 mrpoid mythroad/mythroad.c 的
    # _mr_c_function_table，**这才是斯凯 mythroad 引擎给应用用的那张表**）：
    #   0x000–0x044 与官方完全一致（malloc…strlen…strstr…sprintf）；
    #   0x048 官方是 mr_atoi（我们也是 atoi）——注意 **mr 层**（mr/mythroad.c，
    #   给 MRP 应用用）那张表在 0x048 是 mr_sprintf，比 mythroad 层多一项，
    #   两张表不能混着比；
    #   0x054 官方是 NULL(reserve)；
    #   **0x058 官方是 mr_stop_ex**（此前我们留成空位 → 应用一调就跳地址 0），
    #   从这里往后的槽位与官方逐项对齐。
    F(0x000, "mr_malloc"),
    F(0x004, "mr_free"),
    F(0x008, "mr_realloc"),
    F(0x00C, "memcpy"),
    F(0x010, "memmove"),
    F(0x014, "strcpy"),
    F(0x018, "strncpy"),
    F(0x01C, "strcat"),
    F(0x020, "strncat"),
    F(0x024, "memcmp"),
    F(0x028, "strcmp"),
    F(0x02C, "strncmp"),
    F(0x030, "strcoll"),
    F(0x034, "memchr"),
    F(0x038, "memset"),
    F(0x03C, "strlen"),
    F(0x040, "strstr"),
    F(0x044, "sprintf"),
    F(0x048, "atoi"),
    F(0x04C, "strtoul"),
    F(0x050, "rand"),
    F(0x054, "reserve0", init=_const(lambda vm: 0)),   # 官方：NULL（保留）
    F(0x058, "mr_stop_ex"),                             # 官方：停止当前应用
    F(0x05C, "_mr_c_internal_table", init=_const(lambda vm: 0)),
    F(0x060, "_mr_c_port_table", init=_const(lambda vm: 0)),
    F(0x064, "_mr_c_function_new", fn=_mr_c_function_new),
    F(0x068, "mr_printf", fn=_mr_printf),
    F(0x06C, "mr_mem_get", fn=_mem_get),
    F(0x070, "mr_mem_free", fn=_mem_free),
    # ---- 图形 / 定时 / 系统 ----
    F(0x074, "mr_drawBitmap"),
    F(0x078, "mr_getCharBitmap", init=_const(lambda vm: 0)),
    F(0x07C, "mr_timerStart"),
    F(0x080, "mr_timerStop"),
    F(0x084, "mr_getTime"),
    F(0x088, "mr_getDatetime"),
    F(0x08C, "mr_getUserInfo"),
    F(0x090, "mr_sleep"),
    F(0x094, "mr_plat"),
    F(0x098, "mr_platEx"),
    F(0x09C, "mr_ferrno"),
    # ---- 文件 ----
    F(0x0A0, "mr_open"),
    F(0x0A4, "mr_close"),
    F(0x0A8, "mr_info"),
    F(0x0AC, "mr_write"),
    F(0x0B0, "mr_read"),
    F(0x0B4, "mr_seek"),
    F(0x0B8, "mr_getLen"),
    F(0x0BC, "mr_remove"),
    F(0x0C0, "mr_rename"),
    F(0x0C4, "mr_mkDir"),
    F(0x0C8, "mr_rmDir"),
    F(0x0CC, "mr_findStart"),
    F(0x0D0, "mr_findGetNext"),
    F(0x0D4, "mr_findStop"),
    # ---- 生命周期 / 外设 ----
    F(0x0D8, "mr_exit"),
    F(0x0DC, "mr_startShake"),
    F(0x0E0, "mr_stopShake"),
    F(0x0E4, "mr_playSound"),
    F(0x0E8, "mr_stopSound"),
    F(0x0EC, "mr_sendSms"),
    F(0x0F0, "mr_call"),
    F(0x0F4, "mr_getNetworkID"),
    F(0x0F8, "mr_connectWAP"),
    # ---- 菜单 / 控件 ----
    F(0x0FC, "mr_menuCreate"),
    F(0x100, "mr_menuSetItem"),
    F(0x104, "mr_menuShow"),
    F(0x108, "reserve", init=_const(lambda vm: 0)),
    F(0x10C, "mr_menuRelease"),
    F(0x110, "mr_menuRefresh"),
    F(0x114, "mr_dialogCreate"),
    F(0x118, "mr_dialogRelease"),
    F(0x11C, "mr_dialogRefresh"),
    F(0x120, "mr_textCreate"),
    F(0x124, "mr_textRelease"),
    F(0x128, "mr_textRefresh"),
    F(0x12C, "mr_editCreate"),
    F(0x130, "mr_editRelease"),
    F(0x134, "mr_editGetText"),
    F(0x138, "mr_winCreate"),
    F(0x13C, "mr_winRelease"),
    F(0x140, "mr_getScreenInfo"),
    # ---- 网络 ----
    F(0x144, "mr_initNetwork"),
    F(0x148, "mr_closeNetwork"),
    F(0x14C, "mr_getHostByName"),
    F(0x150, "mr_socket"),
    F(0x154, "mr_connect"),
    F(0x158, "mr_closeSocket"),
    F(0x15C, "mr_recv"),
    F(0x160, "mr_recvfrom"),
    F(0x164, "mr_send"),
    F(0x168, "mr_sendto"),
    # ---- 显示系统 ----
    F(0x16C, "mr_screenBuf", init=_const(lambda vm: vm.app.gfx.fb_addr)),
    F(0x170, "mr_screen_w", init=_const(lambda vm: SCREEN_WIDTH)),
    F(0x174, "mr_screen_h", init=_const(lambda vm: SCREEN_HEIGHT)),
    F(0x178, "mr_screen_bit", init=_const(lambda vm: SCREEN_BPP)),
    F(0x17C, "mr_bitmap", init=_const(lambda vm: 0)),
    F(0x180, "mr_tile", init=_const(lambda vm: 0)),
    F(0x184, "mr_map", init=_const(lambda vm: 0)),
    F(0x188, "mr_sound", init=_const(lambda vm: 0)),
    F(0x18C, "mr_sprite", init=_const(lambda vm: 0)),
    # ---- 打包文件名（mythroad 自己会填）----
    F(0x190, "pack_filename", init=_const(lambda vm: 0)),
    F(0x194, "start_filename", init=_const(lambda vm: 0)),
    F(0x198, "old_pack_filename", init=_const(lambda vm: 0)),
    F(0x19C, "old_start_filename", init=_const(lambda vm: 0)),
    F(0x1A0, "mr_ram_file", init=_const(lambda vm: 0)),
    F(0x1A4, "mr_ram_file_len", init=_const(lambda vm: 0)),
    F(0x1A8, "mr_soundOn", init=_const(lambda vm: 1)),
    F(0x1AC, "mr_shakeOn", init=_const(lambda vm: 1)),
    F(0x1B0, "LG_mem_base", init=_const(lambda vm: vm.mem.heap.base)),
    F(0x1B4, "LG_mem_len", init=_const(lambda vm: vm.mem.heap.size)),
    F(0x1B8, "LG_mem_end", init=_const(lambda vm: vm.mem.heap.base + vm.mem.heap.size)),
    F(0x1BC, "LG_mem_left", init=_const(lambda vm: vm.mem.heap.size - vm.mem.heap.in_use())),
    F(0x1C0, "mr_sms_cfg_buf", init=_const(lambda vm: 0)),
    # ---- 杂项 ----
    F(0x1C4, "mr_md5_init"),
    F(0x1C8, "mr_md5_append"),
    F(0x1CC, "mr_md5_finish"),
    F(0x1D0, "_mr_load_sms_cfg", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x1D4, "_mr_save_sms_cfg", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x1D8, "_DispUpEx", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x1DC, "_DrawPoint"),
    F(0x1E0, "_DrawBitmap"),
    F(0x1E4, "_DrawBitmapEx"),
    F(0x1E8, "DrawRect"),
    F(0x1EC, "_DrawText"),
    F(0x1F0, "_BitmapCheck"),
    F(0x1F4, "_mr_readFile"),
    F(0x1F8, "mr_wstrlen"),
    F(0x1FC, "mr_registerAPP"),
    F(0x200, "_DrawTextEx"),
    F(0x204, "_mr_EffSetCon", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x208, "_mr_TestCom", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x20C, "_mr_TestCom1", fn=lambda ctx, vm: ctx.ret(MR_SUCCESS)),
    F(0x210, "c2u"),
    F(0x214, "_mr_div"),
    F(0x218, "_mr_mod"),
    F(0x21C, "LG_mem_min", init=_const(lambda vm: vm.mem.heap.base)),
    F(0x220, "LG_mem_top", init=_const(lambda vm: 0)),
    F(0x224, "mr_updcrc"),
    F(0x228, "start_fileparameter", init=_const(lambda vm: 0)),
    F(0x22C, "mr_sms_return_flag", init=_const(lambda vm: 0)),
    F(0x230, "mr_sms_return_val", init=_const(lambda vm: 0)),
    F(0x234, "mr_unzip"),
    F(0x238, "mr_exit_cb", init=_const(lambda vm: 0)),
    F(0x23C, "mr_exit_cb_data", init=_const(lambda vm: 0)),
    F(0x240, "mr_entry"),
    F(0x244, "mr_platDrawChar"),
]

# 0x000..0x244 步长 4 = 146 项。数量由偏移连续性决定，不能凭印象取整。
assert len(MR_TABLE) == 146, f"mr_table 应有 146 项，实际 {len(MR_TABLE)}"
assert MR_TABLE[-1].pos == 0x244
