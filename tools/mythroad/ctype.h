/* ctype.h —— 裸机自带的 ctype（覆盖 newlib 版）
 *
 * newlib 的 ctype.h 会引入 __ctype_b_loc 之类的符号，裸机下不想牵出
 * 一整条依赖链，这里自己提供表与宏。
 *
 * 标志位沿用 POSIX 惯例：
 *   _U upper  _L lower  _D digit  _C cntrl
 *   _P punct  _S space  _X xdigit _B blank
 */
#ifndef _EMU_CTYPE_H
#define _EMU_CTYPE_H

extern const unsigned short int _ctype_[256];

#define _U 0x0100
#define _L 0x0200
#define _D 0x0400
#define _C 0x0800
#define _P 0x1000
#define _S 0x2000
#define _X 0x4000
#define _B 0x8000

#define isalpha(c)  ((_ctype_[(unsigned char)(c)] & (_U | _L)) != 0)
#define isupper(c)  ((_ctype_[(unsigned char)(c)] & _U) != 0)
#define islower(c)  ((_ctype_[(unsigned char)(c)] & _L) != 0)
#define isdigit(c)  ((_ctype_[(unsigned char)(c)] & _D) != 0)
#define isalnum(c)  ((_ctype_[(unsigned char)(c)] & (_U | _L | _D)) != 0)
#define isspace(c)  ((_ctype_[(unsigned char)(c)] & _S) != 0)
#define isblank(c)  ((_ctype_[(unsigned char)(c)] & _B) != 0)
#define iscntrl(c)  ((_ctype_[(unsigned char)(c)] & _C) != 0)
#define isprint(c)  ((_ctype_[(unsigned char)(c)] & (_U | _L | _D | _P | _S)) != 0)
#define isgraph(c)  ((_ctype_[(unsigned char)(c)] & (_U | _L | _D | _P)) != 0)
#define ispunct(c)  ((_ctype_[(unsigned char)(c)] & _P) != 0)
#define isxdigit(c) ((_ctype_[(unsigned char)(c)] & _X) != 0)

#define tolower(c) ((unsigned char)(c) >= 'A' && (unsigned char)(c) <= 'Z' \
                    ? (unsigned char)(c) + 32 : (unsigned char)(c))
#define toupper(c) ((unsigned char)(c) >= 'a' && (unsigned char)(c) <= 'z' \
                    ? (unsigned char)(c) - 32 : (unsigned char)(c))

#endif /* _EMU_CTYPE_H */
