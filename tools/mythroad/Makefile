# mythroad 模拟器虚拟机 —— 交叉编译
#
# 产出：mythroad_vm.elf（ELF32 little-endian ARM，链接到 0x00880000）
#
# 依赖：ARM GNU Toolchain（arm-none-eabi）
#   默认路径 ../../tools/armtoolchain/arm-gnu-toolchain-13.2.Rel1-mingw-w64-i686-arm-none-eabi
#   可用 TOOLCHAIN=<dir> 覆盖
#
# 构建流程（关键：先编译 mythroad 本体，用 nm 查出它自己实现了哪些平台接口，
# 再据此生成 thunk —— 否则会 duplicate symbol）：
#   1. 编译 mythroad.c + src/ + tomr/  -> obj/mr/**
#   2. nm 扫出已定义的 mr_/vm_/dsm_ 符号 -> selfimpl.txt
#   3. 按 selfimpl.txt 生成平台层 thunk   -> emu_stub.s / emu_slots.c
#   4. 编译 thunk + 移植层，链接出 mythroad_vm.elf
#
# 用法：
#   make            # 完整构建
#   make clean

TOOLCHAIN ?= $(CURDIR)/../armtoolchain/arm-gnu-toolchain-13.2.Rel1-mingw-w64-i686-arm-none-eabi
CROSS     ?= $(TOOLCHAIN)/bin/arm-none-eabi-
CC        := $(CROSS)gcc
NM        := $(CROSS)nm
SIZE      := $(CROSS)size

MRDIR := $(CURDIR)/../../ref/mrpoid/mr
REPO  := $(CURDIR)/../..

# ARM926EJ-S + Thumb 互操作：MTK 26MHz 的经典核
ARCH := -mcpu=arm926ej-s -mthumb-interwork -marm

INC := -I$(CURDIR) \
       -I$(MRDIR) -I$(MRDIR)/include \
       -I$(MRDIR)/src -I$(MRDIR)/src/lib \
       -I$(MRDIR)/tomr/include -I$(MRDIR)/tomr/src

# MR_VERSION 是官方头文件里唯一缺的宏（mythroad.c:5342 / src/mr_api.c:868）
DEFS := -DMR_VERSION=0x0A01 -DMRP_UNDUMP_FLOAT_NUMBER=1

CFLAGS := $(ARCH) -O2 -ffreestanding -fno-builtin -fno-common -fno-strict-aliasing \
          $(INC) $(DEFS) -w
ASFLAGS := $(ARCH) $(INC)
LDFLAGS := -T mythroad.ld -nostartfiles -nostdlib \
           -Wl,--gc-sections -Wl,-Map=mythroad.map
# 库必须放在目标文件**之后**，否则链接器不会去解析 __aeabi_idiv 之类
LIBS := -lgcc

# ---------------------------------------------------------------- 源文件
# 排除：
#   *_brew.c        高通 BREW 平台专用（我们走 target/PC 路线）
#   src/lib/mr_iolib.c  通用 file 库，走标准 stdio，裸机不可用且宿主接不了
#   src/lib/mr_loadlib.c 动态库加载（Windows API，链接不过）
#   src/mr_tests.c  Lua 自测
#   src/mr_noparser.c 「无解析器」版本，与 mr_parser.c 二选一（重复定义）
MR_C := mythroad.c \
        src/mr_api.c src/mr_code.c src/mr_debug.c src/mr_do.c src/mr_dump.c \
        src/mr_func.c src/mr_gc.c src/mr_lex.c src/mr_mem.c \
        src/mr_object.c src/mr_opcodes.c src/mr_parser.c src/mr_state.c \
        src/mr_string.c src/mr_table.c src/mr_tm.c src/mr_undump.c \
        src/mr_vm.c src/mr_zio.c \
        src/lib/mr_auxiliar.c src/lib/mr_auxlib.c src/lib/mr_baselib.c \
        src/lib/mr_dblib.c src/lib/mr_iolib_target.c src/lib/mr_mathlib.c \
        src/lib/mr_socket_target.c src/lib/mr_strlib.c src/lib/mr_tablib.c \
        src/lib/mr_tcp_target.c \
        tomr/src/tomr_event.c tomr/src/tomr_is.c tomr/src/tomr_map.c \
        tomr/src/tomr_push.c tomr/src/tomr_to.c \
        mr_unzip.c mr_inflate.c mr_gb2312.c mr_graphics.c mr_pluto.c \
        mr_util.c mr_encode.c

EMU_C := emu_main.c emu_sys.c emu_slots.c emu_libc.c emu_crt.c

MR_OBJS := $(patsubst $(MRDIR)/%.c,obj/mr/%.o,$(addprefix $(MRDIR)/,$(MR_C)))
# mr_undump.c 用打过补丁的版本（number 常量按 4 字节 float 读）
MR_OBJS := $(filter-out obj/mr/src/mr_undump.o,$(MR_OBJS)) \
           obj/mr/patched/mr_undump.o
EMU_OBJS := $(patsubst %.c,obj/emu/%.o,$(EMU_C)) \
            obj/emu/emu_stub.o obj/emu/emu_jmp.o
OBJS := $(MR_OBJS) $(EMU_OBJS)

TARGET := mythroad_vm.elf
SELFIMPL := selfimpl.txt

.PHONY: all clean stub
all: $(TARGET)

# 1) mythroad 本体
obj/mr/%.o: $(MRDIR)/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

# 1.5) mr_undump 补丁：MRP 字节码的 number 常量是 4 字节 float
obj/mr/patched/mr_undump.o: $(REPO)/tools/patch_mr_undump.py $(MRDIR)/src/mr_undump.c
	@mkdir -p $(dir $@)
	@cd $(REPO) && python tools/patch_mr_undump.py \
	    --src $(MRDIR)/src/mr_undump.c --out tools/mythroad/patched_mr_undump.c
	$(CC) $(CFLAGS) -c patched_mr_undump.c -o $@

# 2) 用 nm 查出 mythroad 自己实现了哪些平台接口
$(SELFIMPL): $(MR_OBJS)
	@$(NM) $^ 2>/dev/null | grep -E " [TtWwDdBb] (mr_|vm_|dsm_)" \
	    | awk '{print $$3}' | sort -u > $@
	@echo "[selfimpl] mythroad 自带实现 $$(wc -l < $@) 个平台符号"

# 3) 生成平台层 thunk（排除官方已实现的）
emu_stub.s emu_slots.c: $(SELFIMPL) $(MRDIR)/mrporting.h \
                   $(REPO)/tools/gen_emu_stub.py
	@cd $(REPO) && python tools/gen_emu_stub.py \
	    --out-dir tools/mythroad --exclude-file tools/mythroad/$(SELFIMPL)

# 4) 移植层
obj/emu/%.o: %.c emu_port.h
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

obj/emu/%.o: %.s
	@mkdir -p $(dir $@)
	$(CC) $(ASFLAGS) -c $< -o $@

# 5) 链接
$(TARGET): $(OBJS) mythroad.ld
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)
	@$(SIZE) $@ || true

stub:
	@cd $(REPO) && python tools/gen_emu_stub.py --out-dir tools/mythroad

clean:
	rm -rf obj $(TARGET) mythroad.map $(SELFIMPL)
