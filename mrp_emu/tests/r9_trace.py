"""证明 fixR9 机制在我们模拟器里真实生效。

方法：装一个 UC_HOOK_CODE，在执行期间采样 r9，看它是否在
「mythroad 顶层值(0)」和「ext 的 ER_RW 基址」之间来回切换。

如果能看到两个不同的值交替出现 —— 说明 cfunction.ext 里那套
asm_* + fixR9_begin/end 的 ARM 汇编桩正在正常工作，
宿主(Python)完全不需要插手 r9。
"""

import os
import sys
from collections import Counter

os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R9  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.consts import CODE_ADDRESS, KEY_NAME_TO_CODE  # noqa: E402
from mrp_emu.vm import Vm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(ROOT, "runtime")


def main():
    cfunc = os.path.join(RUNTIME, "cfunction.ext")
    if not os.path.isfile(cfunc):
        print("缺少 runtime/cfunction.ext")
        return 1

    vm = Vm(log=lambda m: None)
    app = App(vm, RUNTIME, log=lambda m: None)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)

    # 采样器：记录执行过程中 r9 出现过哪些值、以及伴随的 PC 区间
    seen = Counter()
    samples = 0
    budget = 400_000

    def on_code(uc, address, size, ud):
        nonlocal samples
        if samples >= budget:
            return
        samples += 1
        seen[uc.reg_read(UC_ARM_REG_R9)] += 1

    vm.load_code(cfunc)
    vm.ext_init()
    vm.dsm_init()

    uc = vm.uc
    uc.hook_add(UC_HOOK_CODE, on_code, None, CODE_ADDRESS, CODE_ADDRESS + 0x100000)

    sel = KEY_NAME_TO_CODE["SELECT"]
    vm.key_event(sel, True)
    vm.key_event(sel, False)
    for _ in range(20):
        vm.timer()

    p = vm.mr_c_function_P
    er_rw = vm.mem.u32(p)
    er_len = vm.mem.u32(p + 4)

    print(f"采样指令数 : {samples}")
    print(f"P          : 0x{p:08X}")
    print(f"P->ER_RW   : 0x{er_rw:08X} (len 0x{er_len:X})")
    print(f"r9 取值分布: ")
    for val, cnt in seen.most_common(8):
        mark = ""
        if val == er_rw:
            mark = "  <== ext 的 SB（RW 段基址）"
        elif val == 0:
            mark = "  <== mythroad 顶层值"
        print(f"  0x{val:08X} : {cnt:>8} 次{mark}")

    distinct = [v for v in seen if v not in (0, er_rw)]
    print()
    if er_rw in seen and 0 in seen:
        print("✅ r9 在 mythroad 层与 ext 层之间来回切换 —— fixR9 汇编桩正常工作")
        print("   宿主(Python)无需介入 r9 管理。")
    elif distinct:
        print(f"⚠️  出现意料之外的 r9 值: {[hex(v) for v in distinct]}")
    else:
        print("⚠️  未观察到切换，可能本次执行没走到跨层调用")
    return 0


if __name__ == "__main__":
    sys.exit(main())
