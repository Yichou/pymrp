/* emu_port.h —— mythroad 模拟器移植层公共头
 *
 * 定位
 * ----
 * 官方 mythroad.c 把所有碰硬件/系统的东西都声明在 mrporting.h 里，
 * 真机上由 ROM 提供实现。我们自己编译 mythroad 虚拟机时，就在这里
 * 定义「宿主 ↔ 虚拟机」的契约：
 *
 *   虚拟机 → 宿主 ： 平台接口 thunk（emu_stub.s），尾跳到钩子槽位
 *   宿主 → 虚拟机 ： emu_host_api 表（Python 直接调虚拟机内部函数）
 *
 * 内存约定
 * --------
 * 镜像链接到固定地址（见 mythroad.ld），Python 侧把裸镜像原样加载到
 * 同一地址，所以镜像里的绝对地址全部有效，不需要重定位。
 */
#ifndef EMU_PORT_H
#define EMU_PORT_H

#include "mr.h"
#include "mrporting.h"

/* 镜像自描述头：放在镜像偏移 0，Python 加载后第一件事就是读它 */
#define EMU_MAGIC        0x4D52564Du    /* 'MRVM' */
#define EMU_VERSION      1u

/* 镜像自描述头。
 *
 * 只放**编译期常量**字段：链接脚本符号（地址）的值在链接期才知道，
 * 拿来做静态初始化会报 "initializer element is not constant"。
 * 运行时才需要的信息（host_api 表、槽位名字表、堆/栈边界）由宿主
 * 通过 **ELF 符号表** 查 emu_host_api / emu_slot_names / emu_self_test，
 * 以及 emu_hdr_heap_base / emu_hdr_heap_size / emu_hdr_stack_top 这几个
 * 专门导出的常量符号。
 */
struct emu_vm_hdr {
    uint32 magic;            /* EMU_MAGIC */
    uint32 version;          /* EMU_VERSION */
};


/* 宿主可以主动调用的虚拟机内部函数 */
struct emu_host_api {
    uint32 (*mr_event)(int16 type, int32 param1, int32 param2);
    uint32 (*mr_timer)(void);
    uint32 (*mr_exit)(void);
    uint32 (*mr_start_dsm)(const char* entry);
    uint32 (*mr_stop)(void);
    uint32 (*mr_mem_get)(char** mem_base, uint32* mem_len);
    uint32 (*mr_mem_free)(char* mem, uint32 mem_len);
    uint32 (*self_test)(void);
    uint32 (*get_state)(void);
};

/* 槽位变量 / 名字表（emu_slots.c，生成物） */
extern const char* const emu_slot_names[];
extern const uint32 emu_slot_count;
void emu_bind_slots(void* hook_base);

/* 入口（emu_main.c） */
uint32 emu_vm_main(uint32 hook_base, uint32 entry_ptr);
uint32 emu_self_test(void);

#endif /* EMU_PORT_H */
