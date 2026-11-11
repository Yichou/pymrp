/* emu_crt.c —— 裸机 C 运行时（newlib 之外的最小替代）
 *
 * 覆盖 Lua 解释器与 mythroad 真正用到的那几个：
 *   _ctype_ 表、sprintf/snprintf/vsprintf、strcspn/strspn/strpbrk、
 *   strtod、qsort/bsearch（按需再补）。
 *
 * 不链接 newlib 是为了避免它的 printf 族牵出一串 syscall ——
 * 调试输出走我们自己的 mr_printf → 宿主钩子。
 */
#include "ctype.h"

#include <stdarg.h>
#include <stddef.h>

#include "mr.h"
#include "mrporting.h"

/* ==================================================================== ctype */

const unsigned short int _ctype_[256] = {
    /* 0x00-0x1f 全是控制字符 */
    _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C,
    _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C, _C,
    /* 0x20 空格 */
    _S | _B,
    _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P,
    /* 0x30-0x39 数字 */
    _D, _D, _D, _D, _D, _D, _D, _D, _D, _D, _P, _P, _P, _P, _P, _P,
    /* 0x40-0x5a @ A-Z */
    _P, _U | _X, _U | _X, _U | _X, _U | _X, _U | _X, _U | _X, _U,
    _U, _U, _U, _U, _U, _U, _U, _U,
    _U, _U, _U, _U, _U, _U, _U, _U,
    _U, _U, _U, _P, _P, _P, _P, _P,
    /* 0x5b-0x60 */
    _P, _P, _P, _P, _P, _P, _P, _P,
    /* 0x61-0x7a a-z */
    _L | _X, _L | _X, _L | _X, _L | _X, _L | _X, _L | _X, _L, _L,
    _L, _L, _L, _L, _L, _L, _L, _L,
    _L, _L, _L, _L, _L, _L, _L, _L,
    _L, _L, _L, _P, _P, _P, _P, _C,
    /* 0x7b-0xff */
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P,
    _P, _P, _P, _P, _P, _P, _P, _P
};

/* ==================================================================== 字符串 */

size_t strcspn(const char* s, const char* reject)
{
    const char* p = s;
    for (; *p; p++) {
        const char* r = reject;
        while (*r) {
            if (*r == *p) {
                return (size_t)(p - s);
            }
            r++;
        }
    }
    return (size_t)(p - s);
}

size_t strspn(const char* s, const char* accept)
{
    const char* p = s;
    for (; *p; p++) {
        const char* a = accept;
        int ok = 0;
        while (*a) {
            if (*a == *p) {
                ok = 1;
                break;
            }
            a++;
        }
        if (!ok) {
            break;
        }
    }
    return (size_t)(p - s);
}

char* strpbrk(const char* s, const char* accept)
{
    for (; *s; s++) {
        const char* a = accept;
        while (*a) {
            if (*a == *s) {
                return (char*)s;
            }
            a++;
        }
    }
    return 0;
}

double strtod(const char* s, char** end_ptr)
{
    double v = 0.0;
    int sign = 1;
    int any = 0;

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
        v = v * 10.0 + (double)(*s - '0');
        s++;
        any = 1;
    }
    if (*s == '.') {
        double scale = 0.1;
        s++;
        while (*s >= '0' && *s <= '9') {
            v += (double)(*s - '0') * scale;
            scale *= 0.1;
            s++;
            any = 1;
        }
    }
    if (any && (*s == 'e' || *s == 'E')) {
        int exp = 0;
        int esign = 1;
        const char* save = s;
        s++;
        if (*s == '-') {
            esign = -1;
            s++;
        } else if (*s == '+') {
            s++;
        }
        if (*s >= '0' && *s <= '9') {
            while (*s >= '0' && *s <= '9') {
                exp = exp * 10 + (*s - '0');
                s++;
            }
            while (exp--) {
                v = esign > 0 ? v * 10.0 : v / 10.0;
            }
        } else {
            s = save;
        }
    }
    if (!any) {
        s = end_ptr ? *end_ptr : s;
        if (end_ptr) {
            *end_ptr = (char*)s;
        }
        return 0.0;
    }
    if (end_ptr) {
        *end_ptr = (char*)s;
    }
    return sign > 0 ? v : -v;
}

/* ==================================================================== 格式化 */

/* 输出缓冲器：写满就停（snprintf 语义） */
typedef struct {
    char* buf;
    size_t cap;        /* 容量（含结尾 NUL） */
    size_t len;        /* 已写长度 */
} out_buf_t;

static void ob_putc(out_buf_t* o, char c)
{
    if (o->buf && o->len + 1 < o->cap) {
        o->buf[o->len] = c;
    }
    o->len++;
}

static void ob_puts(out_buf_t* o, const char* s, int n)
{
    int i;
    for (i = 0; i < n; i++) {
        ob_putc(o, s[i]);
    }
}

static void ob_pad(out_buf_t* o, char c, int n)
{
    while (n-- > 0) {
        ob_putc(o, c);
    }
}

/* 无符号整数转字符串（base 2..16），返回长度 */
static int utoa(char* buf, unsigned long long v, unsigned base, int upper)
{
    const char* digits = upper ? "0123456789ABCDEF" : "0123456789abcdef";
    char tmp[72];
    int n = 0;
    int i;

    if (v == 0) {
        tmp[n++] = '0';
    }
    while (v > 0) {
        tmp[n++] = digits[v % base];
        v /= base;
    }
    for (i = 0; i < n; i++) {
        buf[i] = tmp[n - 1 - i];
    }
    buf[n] = 0;
    return n;
}

/* 浮点转字符串：定点 %f 风格，prec 位小数 */
static int ftoa_fixed(char* buf, double v, int prec)
{
    char tmp[512];
    int n = 0;
    int i;
    int neg = 0;
    unsigned long long ip;
    double fp;

    if (v < 0) {
        neg = 1;
        v = -v;
    }
    ip = (unsigned long long)v;
    fp = v - (double)ip;

    /* 小数部分 */
    for (i = 0; i < prec; i++) {
        fp *= 10.0;
        tmp[n++] = (char)('0' + (int)fp);
        fp -= (double)(int)fp;
    }
    while (n > 0 && tmp[n - 1] == '0' && prec > 0) {
        n--;                 /* 去掉多余的尾零 */
    }
    if (prec > 0) {
        n++;                 /* 小数点 */
        tmp[n - 1] = '.';
    }
    /* 整数部分（倒着写） */
    {
        char ib[32];
        int ilen = utoa(ib, ip, 10, 0);
        for (i = 0; i < ilen; i++) {
            tmp[n++] = ib[ilen - 1 - i];
        }
    }
    if (neg) {
        buf[0] = '-';
        for (i = 0; i < n; i++) {
            buf[i + 1] = tmp[n - 1 - i];
        }
        buf[n + 1] = 0;
        return n + 1;
    }
    for (i = 0; i < n; i++) {
        buf[i] = tmp[n - 1 - i];
    }
    buf[n] = 0;
    return n;
}

static int do_format(out_buf_t* o, const char* fmt, va_list ap)
{
    while (*fmt) {
        char c = *fmt++;
        if (c != '%') {
            ob_putc(o, c);
            continue;
        }
        /* 标志 */
        int left = 0, zero = 0, plus = 0, space = 0, alt = 0;
        for (;;) {
            if (*fmt == '-') { left = 1; fmt++; }
            else if (*fmt == '0') { zero = 1; fmt++; }
            else if (*fmt == '+') { plus = 1; fmt++; }
            else if (*fmt == ' ') { space = 1; fmt++; }
            else if (*fmt == '#') { alt = 1; fmt++; }
            else break;
        }
        /* 宽度 */
        int width = 0;
        if (*fmt == '*') {
            width = va_arg(ap, int);
            fmt++;
            if (width < 0) { left = 1; width = -width; }
        } else {
            while (*fmt >= '0' && *fmt <= '9') {
                width = width * 10 + (*fmt - '0');
                fmt++;
            }
        }
        /* 精度 */
        int prec = -1;
        if (*fmt == '.') {
            fmt++;
            prec = 0;
            if (*fmt == '*') {
                prec = va_arg(ap, int);
                fmt++;
            } else {
                while (*fmt >= '0' && *fmt <= '9') {
                    prec = prec * 10 + (*fmt - '0');
                    fmt++;
                }
            }
        }
        /* 长度修饰（忽略） */
        while (*fmt == 'l' || *fmt == 'h' || *fmt == 'z' || *fmt == 't') {
            fmt++;
        }
        char conv = *fmt ? *fmt++ : 0;
        char tmp[600];
        int len = 0;
        const char* text = tmp;
        int neg = 0;

        switch (conv) {
        case 'd':
        case 'i': {
            long v = (conv == 'i') ? (long)va_arg(ap, int) : va_arg(ap, long);
            unsigned long long uv;
            if (v < 0) { neg = 1; uv = (unsigned long long)(-(v + 1)) + 1ULL; }
            else uv = (unsigned long long)v;
            len = utoa(tmp, uv, 10, 0);
            break;
        }
        case 'u':
            len = utoa(tmp, (unsigned long long)va_arg(ap, unsigned long), 10, 0);
            break;
        case 'x':
            len = utoa(tmp, (unsigned long long)va_arg(ap, unsigned long), 16, 0);
            if (alt && len && tmp[0] != '0') {
                tmp[len++] = '0';
                tmp[len] = 0;
            }
            break;
        case 'X':
            len = utoa(tmp, (unsigned long long)va_arg(ap, unsigned long), 16, 1);
            break;
        case 'o':
            len = utoa(tmp, (unsigned long long)va_arg(ap, unsigned long), 8, 0);
            break;
        case 'c': {
            int v = va_arg(ap, int);
            tmp[0] = (char)v;
            tmp[1] = 0;
            len = 1;
            break;
        }
        case 's': {
            const char* s = va_arg(ap, const char*);
            if (!s) s = "(null)";
            if (prec >= 0) {
                len = 0;
                while (len < prec && s[len]) len++;
            } else {
                len = 0;
                while (s[len]) len++;
            }
            if (len > (int)sizeof(tmp) - 1) len = (int)sizeof(tmp) - 1;
            for (int k = 0; k < len; k++) tmp[k] = s[k];
            tmp[len] = 0;
            break;
        }
        case 'p': {
            void* v = va_arg(ap, void*);
            unsigned long long uv = (unsigned long long)(unsigned long)v;
            tmp[0] = '0';
            tmp[1] = 'x';
            len = 2 + utoa(tmp + 2, uv, 16, 0);
            tmp[len] = 0;
            break;
        }
        case 'f':
        case 'F':
        case 'e':
        case 'E':
        case 'g':
        case 'G': {
            double v = va_arg(ap, double);
            len = ftoa_fixed(tmp, v, prec >= 0 ? prec : 6);
            if ((conv == 'e' || conv == 'E' || conv == 'g' || conv == 'G')
                && prec < 0) {
                len = ftoa_fixed(tmp, v, 6);
            }
            break;
        }
        case '%':
            tmp[0] = '%';
            tmp[1] = 0;
            len = 1;
            break;
        case 0:
            continue;
        default:
            tmp[0] = '%';
            tmp[1] = conv;
            tmp[2] = 0;
            len = 2;
            break;
        }

        /* 符号前缀 */
        int prefix = 0;
        if (neg) {
            ob_putc(o, '-');
            prefix = 1;
        } else if (plus) {
            ob_putc(o, '+');
            prefix = 1;
        } else if (space) {
            ob_putc(o, ' ');
            prefix = 1;
        }
        int pad = width - len - prefix;
        if (!left && !zero) {
            ob_pad(o, ' ', pad);
        }
        ob_puts(o, text, len);
        if (left) {
            ob_pad(o, ' ', pad);
        } else if (zero) {
            /* 0 填充要放在符号之后：这里简化成空格 */
            ob_pad(o, ' ', 0);
        }
    }
    return (int)o->len;
}

int vsprintf(char* buf, const char* fmt, va_list ap)
{
    out_buf_t o;
    o.buf = buf;
    o.cap = (size_t)-1;
    o.len = 0;
    do_format(&o, fmt, ap);
    if (buf) {
        buf[o.len] = 0;
    }
    return (int)o.len;
}

int sprintf(char* buf, const char* fmt, ...)
{
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vsprintf(buf, fmt, ap);
    va_end(ap);
    return n;
}

int vsnprintf(char* buf, size_t cap, const char* fmt, va_list ap)
{
    out_buf_t o;
    o.buf = buf;
    o.cap = cap;
    o.len = 0;
    do_format(&o, fmt, ap);
    if (buf && cap) {
        buf[o.len < cap ? o.len : cap - 1] = 0;
    }
    return (int)o.len;
}

int snprintf(char* buf, size_t cap, const char* fmt, ...)
{
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = vsnprintf(buf, cap, fmt, ap);
    va_end(ap);
    return n;
}
