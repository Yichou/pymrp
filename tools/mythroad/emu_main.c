/* emu_main.c —— 模拟器虚拟机入口
 *
 * 职责：
 *   1. 把宿主给的钩子基址写进各平台接口槽位
 *   2. 提供宿主可反向调用的函数表（emu_host_api）
 *   3. 提供镜像自描述头（emu_hdr），让 Python 侧一眼看清内存契约
 *
 * 注意：mr_event / mr_timer / mr_start_dsm / mr_stop 是 mythroad.c 自己
 * 实现的（官方逻辑），宿主要调它们时直接走 emu_host_api，不必绕钩子。
 */
#include "emu_port.h"


/* 链接脚本给出的符号（地址） */
extern char __stack_top[];

extern const struct emu_host_api emu_host_api;
extern const char* const emu_slot_names[];
extern const uint32 emu_slot_count;

/* ---------------------------------------------------------------- 自检 */

__attribute__((used))
uint32 emu_self_test(void)
{
    /* 返回魔数：Python 加载镜像后调一次，验证镜像可执行、栈可用 */
    return EMU_MAGIC;
}

uint32 emu_get_state(void)
{
    /* mythroad 的 mr_state 是 static，这里用接口探测代替：
     * 调一次 mr_timer，若不在运行态会返回 MR_IGNORE(1)。 */
    return (uint32)mr_timer();
}

/* -------------------------------------------------- 宿主可反向调用的表 */

__attribute__((section(".emu_keep"), used))
const struct emu_host_api emu_host_api = {
    (uint32 (*)(int16, int32, int32))mr_event,
    (uint32 (*)(void))mr_timer,
    (uint32 (*)(void))mr_exit,
    (uint32 (*)(const char*))mr_start_dsm,
    (uint32 (*)(void))mr_stop,
    (uint32 (*)(char**, uint32*))mr_mem_get,
    (uint32 (*)(char*, uint32))mr_mem_free,
    (uint32 (*)(void))emu_self_test,
    (uint32 (*)(void))emu_get_state
};

/* ---------------------------------------------------- 镜像自描述头 */

__attribute__((section(".emu_hdr")))
const struct emu_vm_hdr emu_hdr = {
    EMU_MAGIC,
    EMU_VERSION
};

/* ------------------------------------------------------------ 入口 */

/* 由 Python 侧调用：
 *   R0 = 钩子槽位基址（宿主分配，每个槽位 4 字节，槽位值 = 槽位自身地址）
 *   R1 = 入口文件名字符串在虚拟机内存里的地址
 * 返回 mr_start_dsm 的返回值。
 */
uint32 emu_vm_main(uint32 hook_base, uint32 entry_ptr)
{
    emu_bind_slots((void*)hook_base);
    if (entry_ptr == 0) {
        return 0xFFFFFFFFu;
    }
    return (uint32)mr_start_dsm((const char*)entry_ptr);
}
