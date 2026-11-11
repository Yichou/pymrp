/* emu_libc.c —— 标准 C 库与 mrporting.h 里的封装
 *
 * 裸机（-nostdlib）下没有 libc，所以这里自带一份最小实现：
 *
 *   1. 标准 C 函数：memcpy/memset/strlen/strcmp…（gcc 即使加了
 *      -fno-builtin 也仍会为结构体赋值生成 memset/memcpy 调用）
 *   2. mrporting.h 声明的 mr_mem / mr_str 封装（真机由平台提供）
 *   3. vm_mem / vm_strlen（MEMCPY/MEMMOVE/MEMSET 宏的落点）
 *
 * 为什么不链接 newlib：newlib 的 printf 族会牵出一串 syscall，
 * 而我们自己已经有 mr_printf 走宿主钩子。
 */
#include <stddef.h>

#include "mr.h"
#include "mrporting.h"

/* ==================================================================== 标准 C */

void* memcpy(void* dst, const void* src, size_t n)
{
    unsigned char* d = (unsigned char*)dst;
    const unsigned char* s = (const unsigned char*)src;
    while (n--) {
        *d++ = *s++;
    }
    return dst;
}

void* memmove(void* dst, const void* src, size_t n)
{
    unsigned char* d = (unsigned char*)dst;
    const unsigned char* s = (const unsigned char*)src;
    if (d == s || n == 0) {
        return dst;
    }
    if (d < s) {
        while (n--) {
            *d++ = *s++;
        }
    } else {
        d += n;
        s += n;
        while (n--) {
            *--d = *--s;
        }
    }
    return dst;
}

void* memset(void* dst, int ch, size_t n)
{
    unsigned char* d = (unsigned char*)dst;
    unsigned char c = (unsigned char)ch;
    while (n--) {
        *d++ = c;
    }
    return dst;
}

int memcmp(const void* lhs, const void* rhs, size_t n)
{
    const unsigned char* a = (const unsigned char*)lhs;
    const unsigned char* b = (const unsigned char*)rhs;
    while (n--) {
        if (*a != *b) {
            return (int)*a - (int)*b;
        }
        a++;
        b++;
    }
    return 0;
}

void* memchr(const void* s, int ch, size_t n)
{
    const unsigned char* p = (const unsigned char*)s;
    unsigned char c = (unsigned char)ch;
    while (n--) {
        if (*p == c) {
            return (void*)p;
        }
        p++;
    }
    return 0;
}

size_t strlen(const char* s)
{
    const char* p = s;
    while (*p) {
        p++;
    }
    return (unsigned long)(p - s);
}

char* strcpy(char* dst, const char* src)
{
    char* d = dst;
    while ((*d++ = *src++) != 0) {
    }
    return dst;
}

char* strncpy(char* dst, const char* src, size_t n)
{
    char* d = dst;
    while (n > 0 && *src) {
        *d++ = *src++;
        n--;
    }
    while (n-- > 0) {
        *d++ = 0;
    }
    return dst;
}

char* strcat(char* dst, const char* src)
{
    char* d = dst;
    while (*d) {
        d++;
    }
    while ((*d++ = *src++) != 0) {
    }
    return dst;
}

char* strncat(char* dst, const char* src, size_t n)
{
    char* d = dst;
    while (*d) {
        d++;
    }
    while (n > 0 && *src) {
        *d++ = *src++;
        n--;
    }
    *d = 0;
    return dst;
}

int strcmp(const char* lhs, const char* rhs)
{
    while (*lhs && *lhs == *rhs) {
        lhs++;
        rhs++;
    }
    return (int)(unsigned char)*lhs - (int)(unsigned char)*rhs;
}

int strncmp(const char* lhs, const char* rhs, size_t n)
{
    while (n > 0 && *lhs && *lhs == *rhs) {
        lhs++;
        rhs++;
        n--;
    }
    if (n == 0) {
        return 0;
    }
    return (int)(unsigned char)*lhs - (int)(unsigned char)*rhs;
}

int strcoll(const char* lhs, const char* rhs)
{
    return strcmp(lhs, rhs);
}

char* strchr(const char* s, int ch)
{
    char c = (char)ch;
    for (;; s++) {
        if (*s == c) {
            return (char*)s;
        }
        if (*s == 0) {
            return 0;
        }
    }
}

char* strrchr(const char* s, int ch)
{
    char c = (char)ch;
    const char* last = 0;
    for (;; s++) {
        if (*s == c) {
            last = s;
        }
        if (*s == 0) {
            break;
        }
    }
    return (char*)last;
}

char* strstr(const char* haystack, const char* needle)
{
    size_t nl = strlen(needle);
    if (nl == 0) {
        return (char*)haystack;
    }
    for (; *haystack; haystack++) {
        if (*haystack == *needle && strncmp(haystack, needle, nl) == 0) {
            return (char*)haystack;
        }
    }
    return 0;
}

int atoi(const char* s)
{
    int sign = 1;
    int v = 0;
    while (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r') {
        s++;
    }
    if (*s == '-') {
        sign = -1;
        s++;
    } else if (*s == '+') {
        s++;
    }
    while (*s >= '0' && *s <= '9') {
        v = v * 10 + (*s - '0');
        s++;
    }
    return v * sign;
}

long strtol(const char* s, char** end_ptr, int base)
{
    long v = 0;
    int sign = 1;
    while (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r') {
        s++;
    }
    if (*s == '-') {
        sign = -1;
        s++;
    } else if (*s == '+') {
        s++;
    }
    if (base == 0) {
        if (*s == '0' && (s[1] == 'x' || s[1] == 'X')) {
            base = 16;
            s += 2;
        } else if (*s == '0') {
            base = 8;
        } else {
            base = 10;
        }
    } else if (base == 16 && *s == '0' && (s[1] == 'x' || s[1] == 'X')) {
        s += 2;
    }
    for (;;) {
        int d;
        if (*s >= '0' && *s <= '9') {
            d = *s - '0';
        } else if (*s >= 'a' && *s <= 'z') {
            d = *s - 'a' + 10;
        } else if (*s >= 'A' && *s <= 'Z') {
            d = *s - 'A' + 10;
        } else {
            break;
        }
        if (d >= base) {
            break;
        }
        v = v * base + d;
        s++;
    }
    if (end_ptr) {
        *end_ptr = (char*)s;
    }
    return v * sign;
}

unsigned long strtoul(const char* s, char** end_ptr, int base)
{
    return (unsigned long)strtol(s, end_ptr, base);
}

int abs(int v)
{
    return v < 0 ? -v : v;
}

long labs(long v)
{
    return v < 0 ? -v : v;
}

/* 简易随机数（线性同余），够 mythroad 用了 */
static uint32 rand_state = 1;

int rand(void)
{
    rand_state = rand_state * 1103515245UL + 12345UL;
    return (int)((rand_state >> 16) & 0x7FFF);
}

void srand(unsigned int seed)
{
    rand_state = seed;
}

/* ==================================================================== 封装 */

void* mr_memcpy(void* dst, const void* src, uint32 n)
{
    return memcpy(dst, src, n);
}

void* mr_memmove(void* dst, const void* src, uint32 n)
{
    return memmove(dst, src, n);
}

void* mr_memset(void* dst, int ch, uint32 n)
{
    return memset(dst, ch, n);
}

int mr_memcmp(const void* lhs, const void* rhs, uint32 n)
{
    return memcmp(lhs, rhs, n);
}

void* mr_memchr(const void* s, int ch, uint32 n)
{
    return memchr(s, ch, n);
}

void* mr_strcpy(char* dst, const char* src)
{
    return strcpy(dst, src);
}

char* mr_strncpy(char* dst, const char* src, uint32 n)
{
    return strncpy(dst, src, n);
}

char* mr_strcat(char* dst, const char* src)
{
    return strcat(dst, src);
}

char* mr_strncat(char* dst, const char* src, uint32 n)
{
    return strncat(dst, src, n);
}

int mr_strcmp(const char* lhs, const char* rhs)
{
    return strcmp(lhs, rhs);
}

int mr_strncmp(const char* lhs, const char* rhs, uint32 n)
{
    return strncmp(lhs, rhs, n);
}

int mr_strcoll(const char* lhs, const char* rhs)
{
    return strcoll(lhs, rhs);
}

int mr_strlen(const char* s)
{
    return (int)strlen(s);
}

char* mr_strstr(const char* haystack, const char* needle)
{
    return strstr(haystack, needle);
}

int mr_atoi(const char* s)
{
    return atoi(s);
}

unsigned long mr_strtoul(const char* s, char** end_ptr, int base)
{
    return strtoul(s, end_ptr, base);
}

int mr_rand(void)
{
    return rand();
}

/* ------------------------------------------------- MEMCPY/MEMMOVE/MEMSET 宏落点 */

void* vm_memcpy(void* dst, const void* src, uint32 n)
{
    return memcpy(dst, src, n);
}

void* vm_memmove(void* dst, const void* src, uint32 n)
{
    return memmove(dst, src, n);
}

void* vm_memset(void* dst, int ch, uint32 n)
{
    return memset(dst, ch, n);
}

int vm_strlen(const char* s)
{
    return (int)strlen(s);
}
