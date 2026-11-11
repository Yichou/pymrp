"""把 `api/impl.py` 的 mr_* 实现绑到自编译 mythroad VM 的钩子槽位上。

为什么能直接复用
----------------
`impl.py` 里每个平台接口的函数签名都是 ``fn(ctx, vm)``：

* ``ctx`` 是 `bridge.ArmCall` —— 按 AAPCS 从 R0-R3/栈读参数、写 R0 返回值；
  老 VM 与新 VM 的调用约定完全一致，所以同一份 ArmCall 通用。
* ``vm`` 提供 `.mem` / `.app` / `.exited` / `.instance_stopped` /
  `.alloc_vm_memory()` 等 —— `MythroadVm` 已实现同名接口。

接口名也一致：impl.py 里叫 `mr_open`、`mr_read`……，与
`mrporting.h` 的平台接口名逐字相同，按名字绑定即可。

命名差异只有两处，单独映射：
* ``mr_platDrawChar``（应用侧）↔ ``mr_platDrawCharReal``（平台侧）
* ``mr_drawText`` —— 应用侧叫 ``mr_drawText``，平台侧同名
"""

from __future__ import annotations

from typing import Callable

from .api import emu_platform, impl
from .bridge import ArmCall
from .mythroad_vm import MythroadVm

# 平台接口名 -> 实现名（只列不一致的）
ALIASES: dict[str, str] = {
    "mr_platDrawCharReal": "mr_platDrawChar",
}


def _make_handler(fn: Callable[..., None]) -> Callable[[MythroadVm], None]:
    def handler(vm: MythroadVm) -> None:
        call = ArmCall(vm.uc, vm.mem)
        try:
            fn(call, vm)
        except Exception as exc:                  # noqa: BLE001
            vm.log(f"[mvm] 平台接口异常: {exc}")
            call.ret(0xFFFFFFFF)
        call.flush()
    return handler


def bind_platform(vm: MythroadVm) -> tuple[list[str], list[str]]:
    """把 impl.py / emu_platform.py 的实现绑到 vm 的槽位表上。

    优先级：`emu_platform`（mythroad 专用）> `impl`（与老 VM 共用）。

    返回 (已绑定, 未实现) 两个接口名列表。
    """
    bound: list[str] = []
    missing: list[str] = []
    for name in vm.slot_names:
        target = ALIASES.get(name, name)
        fn = getattr(emu_platform, target, None)
        if fn is None or not callable(fn):
            fn = getattr(impl, target, None)
        if fn is None or not callable(fn):
            missing.append(name)
            continue
        vm.platform_handlers[name] = _make_handler(fn)
        bound.append(name)
    return bound, missing


def coverage_report(vm: MythroadVm) -> str:
    """覆盖情况报告。"""
    bound, missing = bind_platform(vm)
    lines = [
        f"平台接口 {len(vm.slot_names)} 个：已绑 {len(bound)}，"
        f"未实现 {len(missing)}",
    ]
    if missing:
        lines.append("未实现: " + " ".join(missing))
    return "\n".join(lines)
