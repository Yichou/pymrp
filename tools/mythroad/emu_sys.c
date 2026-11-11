/* emu_sys.c —— newlib 需要的最小 syscall 桩
 *
 * mythroad 自带堆管理器（mr_malloc/mr_free/mr_realloc），底层只要平台
 * 给一块 mr_mem_get 内存，所以这里**不需要**实现 malloc。
 *
 * 但 mythroad.c 与改名版 Lua 里仍会用到标准 C 字符串/内存函数，
 * 这些由 arm-none-eabi 的 newlib 提供；newlib 又要求我们补几个
 * syscall（_sbrk / _write / _read ...），这里给最简实现。
 */
#include "mr.h"

#include <sys/stat.h>
#include <sys/types.h>

/* 链接脚本给出的堆区 */
extern char __heap_start[];
extern char __heap_end[];

static char* heap_cur = 0;

/* newlib 的 malloc 若被间接引用（部分 C 库构造路径会），走这里 */
void* _sbrk(int incr)
{
    char* prev;

    if (heap_cur == 0) {
        heap_cur = __heap_start;
    }
    prev = heap_cur;
    heap_cur += incr;
    if (heap_cur > __heap_end) {
        heap_cur = prev;
        return (void*)-1;      /* 分配失败 */
    }
    return prev;
}

/* 调试输出：mythroad 的 mr_printf 已经走宿主钩子，这里只是 newlib
 * printf 族的兜底，丢进环形缓冲，宿主想看可以再挖。 */
#define EMU_OUTBUF 4096
static char out_buf[EMU_OUTBUF];
static uint32 out_pos = 0;

int _write(int fd, const char* buf, int len)
{
    int i;
    (void)fd;
    for (i = 0; i < len; i++) {
        out_buf[out_pos] = buf[i];
        out_pos = (out_pos + 1) % EMU_OUTBUF;
    }
    return len;
}

int _read(int fd, char* buf, int len)
{
    (void)fd; (void)buf; (void)len;
    return 0;               /* EOF */
}

int _close(int fd)
{
    (void)fd;
    return -1;
}

int _fstat(int fd, struct stat* st)
{
    (void)fd;
    st->st_mode = S_IFCHR;
    return 0;
}

int _isatty(int fd)
{
    (void)fd;
    return 1;
}

int _lseek(int fd, int off, int whence)
{
    (void)fd; (void)off; (void)whence;
    return 0;
}

void _exit(int code)
{
    (void)code;
    for (;;) {
        /* 宿主侧靠看 PC 停在栈顶来发现退出，不允许真退出 */
    }
}

/* newlib-nano 需要 */
void _init(void) {}
void _fini(void) {}
