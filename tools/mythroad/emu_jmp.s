/* emu_crt.s —— 裸机需要的汇编支持
 *
 * setjmp / longjmp —— Lua 的错误恢复靠这两个（mr_do.c 的 protected call）。
 * 官方 mr_setjmp.s 是「全局寄存器保存」版本（MR_REG 单槽），而 Lua 用的是
 * 标准 per-call jmp_buf，所以这里按 AAPCS 自己实现一份。
 *
 * jmp_buf 布局（标准做法）：
 *   [0 .. 35]   r4-r11 + lr（9 个寄存器）
 *   [36 .. 39]  sp
 */
    .syntax unified
    .arm
    .text

    .global setjmp
    .type setjmp, %function
setjmp:
    stmia   r0!, {r4-r11, lr}     @ 保存被调用者保存寄存器 + 返回地址
    str    r0, [r0, #-4]!         @ 记下当时的 sp
    mov    r0, #0                 @ setjmp 直接返回 0
    bx     lr
    .size setjmp, .-setjmp

    .global longjmp
    .type longjmp, %function
longjmp:
    ldr    r2, [r0, #-4]!         @ 取回 sp
    ldmia  r2!, {r4-r11, lr}      @ 恢复寄存器（lr = 原返回地址）
    mov    r1, #0
    mov    r0, #1                 @ longjmp 之后 setjmp 返回 1
    bx     lr
    .size longjmp, .-longjmp

    .section .note.GNU-stack,"",%progbits
