"""r9(SB) 探针：验证进入子 ext 后 r9 / mr_c_function_P / mr_extHelper 是否被改写。

背景：r9 = 静态基址寄存器 = ext 模块的全局变量区基址。
mythroad 官方（fixR9.c）用 asm_* 汇编桩在每次跨层调用时切换并恢复 r9/r10。
本脚本用来确认「宿主 Python 侧」是否也需要做同样的事。
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.consts import KEY_NAME_TO_CODE  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(ROOT, "runtime")
CFUNC = os.path.join(RUNTIME, "cfunction.ext")


def snap(vm, tag):
    r9 = vm.read_r9()
    p = vm.mr_c_function_P
    sb_of_p = vm.mem.u32(p) if p else 0
    rw_len = vm.mem.u32(p + 4) if p else 0
    print(
        f"{tag:<12} r9=0x{r9:08X} helper=0x{vm.mr_extHelper_addr:08X} "
        f"P=0x{p:08X} P->ER_RW=0x{sb_of_p:08X} P->ER_RW_len=0x{rw_len:X} "
        f"{'  <== r9 与 P->ER_RW 一致' if r9 == sb_of_p and sb_of_p else '  <== 不一致！'}"
    )


def main():
    if not os.path.isfile(CFUNC):
        print(f"缺少 {CFUNC}，先跑 tools/fetch_runtime.py")
        return 1

    vm = Vm(log=lambda m: None)
    app = App(vm, RUNTIME, log=lambda m: None)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)

    vm.load_code(CFUNC)
    vm.ext_init()
    snap(vm, "ext_init")
    ok = vm.dsm_init()
    print(f"DSM_INIT -> {ok}")
    snap(vm, "dsm_init")

    r = vm.start_dsm("dsm_gm.mrp", "start.mr", None)
    print(f"start_dsm -> {r}")
    snap(vm, "start_dsm")

    # 跑几十次 timer，让启动器把菜单画出来
    for i in range(30):
        vm.timer()
    snap(vm, "timer x30")

    # 按下 SELECT 进入第一个游戏
    sel = KEY_NAME_TO_CODE["SELECT"]
    before = (vm.read_r9(), vm.mr_extHelper_addr, vm.mr_c_function_P)
    print(f"\n>>> 发送 SELECT 键（{sel}）尝试启动子游戏")
    try:
        vm.key_event(sel, True)
        vm.key_event(sel, False)
    except Exception as exc:  # noqa: BLE001
        print(f"按键异常: {exc}")
        return 1
    snap(vm, "after SELECT")

    for i in range(40):
        vm.timer()
    snap(vm, "timer x40")

    after = (vm.read_r9(), vm.mr_extHelper_addr, vm.mr_c_function_P)
    print()
    if before == after:
        print("结论：r9 / helper / P 在进入子 ext 后未变化 —— 子 ext 加载完全发生在 ARM 侧")
    else:
        print("结论：发生了变化 —— 宿主侧必须做 r9/P 的保存与恢复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
