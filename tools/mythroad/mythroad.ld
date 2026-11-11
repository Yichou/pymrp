/* mythroad.ld —— 模拟器虚拟机链接脚本
 *
 * 关键约定：**链接到固定绝对地址**。
 * Python 侧把编译出来的 ELF 原样加载到同一批地址，镜像里的绝对地址
 * （包括 thunk 里 `ldr ip, [emu_slot_xxx]` 的重定位结果）就全部有效，
 * 不需要任何运行期重定位。
 *
 * 内存分工（与 mrp_emu/mrp_emu/consts.py 保持一致）：
 *   0x000000 - 0x080000   低地址 ROM/RAM（现有）
 *   0x080000 - 0x180000   cfunction.ext + MRP 代码（现有）
 *   0x180000 - 0x280000   栈（现有）
 *   0x280000 - 0x880000   MRP 堆 6MB（现有）
 *   0x880000 - 0xA80000   【本虚拟机】镜像（代码+数据+bss）
 *   0xA80000 - 0xE80000   【本虚拟机】newlib 堆 4MB
 *   0xE80000              【本虚拟机】栈顶（向下生长 1MB）
 */
OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(emu_vm_main)

MEMORY
{
  VM  (rwx) : ORIGIN = 0x00880000, LENGTH = 0x00600000
}

SECTIONS
{
  . = 0x00880000;

  /* 镜像自描述头 —— Python 加载后偏移 0 就是它 */
  .emu_hdr : { KEEP(*(.emu_hdr)) }

  .text : {
    *(.text.emu_stub)        /* 生成的平台接口 thunk */
    *(.text*)
    *(.gnu.linkonce.t.*)
    *(.glue_7) *(.glue_7t)
  }

  /* 宿主要通过符号表访问的结构（emu_host_api / emu_slot_names），
   * 链接器看不到引用，会被 --gc-sections 删掉 —— 必须 KEEP。 */
  .emu_keep : { KEEP(*(.emu_keep)) }

  .rodata : { *(.rodata*) *(.gnu.linkonce.r.*) }

  .data : { *(.data*) *(.gnu.linkonce.d.*) }

  .bss (NOLOAD) : {
    __bss_start = .;
    *(.bss*) *(COMMON)
    . = ALIGN(4);
    __bss_end = .;
  }

  . = ALIGN(16);
  __heap_start = .;
  . += 0x00400000;           /* newlib 4MB 堆 */
  __heap_end = .;
  __heap_size = 0x00400000;  /* 常量符号：供 emu_hdr 静态初始化用 */

  __stack_top = 0x00E80000;  /* 栈顶（向下生长） */

  _end = .;

  /DISCARD/ : {
    *(.comment)
    *(.note*)
    *(.ARM.attributes)
    *(.ARM.exidx*)
    *(.ARM.extab*)
  }
}
