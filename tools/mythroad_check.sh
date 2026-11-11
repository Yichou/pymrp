#!/usr/bin/env bash
# mythroad 源码可编译性体检
#
# 用途：验证 ref/mrpoid/mr 里的官方 MR 运行时源码能否在当前环境编译，
#       以及要补哪些平台层接口（配合 tools/port_scan.py）。
#
# 本机现状（2026-11-11）：
#   * 没有 ARM 交叉编译器（arm-none-eabi-gcc / armcc 全缺）
#   * 有 msys64 的 mingw32 gcc，但沙箱禁止 gcc 落盘（只能 -fsyntax-only）
#   * 因此本脚本做**语法体检**，不做链接/产物生成
#
# 用法: bash tools/mythroad_check.sh [mr_dir]

set -u
MR_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)/ref/mrpoid/mr}"
GCC="${GCC:-/c/msys64/mingw32/bin/gcc.exe}"
[ -x "$GCC" ] || GCC=gcc
export PATH="/c/msys64/mingw32/bin:/c/msys64/usr/bin:$PATH"

INC="-I. -Iinclude -Isrc -Isrc/lib -Itomr/include -Itomr/src"
DEF="-DMR_VERSION=0x0A01 -w"

cd "$MR_DIR" || exit 1
echo "=== mythroad 源码语法体检 ==="
echo "目录: $MR_DIR"
echo "编译器: $GCC ($($GCC --version | head -1))"
echo

pass=0; fail=0; failed=""
for f in mythroad.c src/*.c src/lib/*.c tomr/src/*.c \
         mr_unzip.c mr_inflate.c mr_gb2312.c mr_graphics.c \
         mr_pluto.c mr_util.c mr_encode.c mr_readfileforplat.c; do
    [ -f "$f" ] || continue
    if $GCC -fsyntax-only $DEF $INC "$f" 2>/dev/null; then
        pass=$((pass+1))
    else
        fail=$((fail+1)); failed="$failed $f"
    fi
done

echo "通过: $pass    失败: $fail"
if [ -n "$failed" ]; then
    echo "失败文件:"
    for f in $failed; do echo "  - $f"; done
    echo
    echo "（*_brew.c 是高通 BREW 平台专用，本项目走 target/PC 路线，不需要）"
fi
exit 0
