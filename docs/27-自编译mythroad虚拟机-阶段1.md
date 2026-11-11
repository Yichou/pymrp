# 阶段 1：自编译 mythroad 虚拟机打通

> 老板批准**路线 A**（下载 ARM 工具链，交叉编译 mythroad.c）。
> 本文记录这一阶段的实际成果与踩过的坑。

---

## 一、成果：编译、装载、执行全通

```
$ cd tools/mythroad && make
[selfimpl] mythroad 自带实现 288 个平台符号
   text	   data	    bss	    dec	    hex	filename
  213548	   1056	 4612	 219216	  0x35838	mythroad_vm.elf

$ python tests/mythroad_probe.py
  [PASS] 有 PT_LOAD 段 / 链接基址 0x880000 / 镜像 214KB
  [PASS] 装载完成 / 版本号 1
  [PASS] 槽位数量合理 70 个 / 名字表与数量一致 / 槽位值 = 自身地址
  [PASS] host_api 表非空 9 项 / 地址都落在镜像内
  [PASS] 返回魔数 0x4D52564D（期望 0x4D52564D）
====================================================
全部通过
```

**关键判据**：`emu_self_test()` 在 Unicorn 里返回魔数 —— 证明镜像不只是能装，
而是真的能执行（栈、.bss、跳转都对）。

回归：老架构 22 个探针 + 新增 `mythroad_probe` 共 **23 个全绿**。

---

## 二、双向调用模型

```
┌──────────────── 宿主（Python）────────────────┐
│  文件/网络/按键/显示/定时  +  平台接口实现        │
└───────────▲────────────────────────┬──────────┘
            │ ② 宿主 → 虚拟机          │ ① 虚拟机 → 宿主
            │   emu_host_api 表          │   汇编 thunk 尾跳
            │   mr_event / mr_timer       │   → 钩子槽位
            │   mr_start_dsm              │   → UC_HOOK_CODE 拦截
┌───────────┴────────────────────────▼──────────┐
│      自编译 mythroad VM（ARM，链接 0x880000）   │
│   TOM 解释器 + mr_* 官方实现 + MRPG 解包        │
│   + 事件循环 mr_timer + 插件链 MRF_RunFile      │
└────────────────────────────────────────────────┘
```

### ① 虚拟机 → 宿主：汇编 thunk

每个平台接口一个 3 指令 thunk（`tools/mythroad/emu_stub.s`，由
`tools/gen_emu_stub.py` 生成）：

```asm
mr_open:
    ldr  ip, =emu_slot_mr_open   @ 取槽位变量的地址
    ldr  ip, [ip]                @ 再取槽位里存的钩子地址
    bx   ip
```

**为什么必须是汇编，不能用 C**：

1. **不改栈**。C 写的 thunk 会被 gcc 插入 prologue（push 寄存器/lr），
   栈指针一变，宿主按 AAPCS 读变参（`mr_printf(const char*, ...)`）的位置就全错。
2. **不改 LR**。`bx ip` 是尾跳，LR 保持调用者的返回地址，宿主 hook 完把
   PC 写回 LR 即返回，栈天然平衡（汇编没 push 过东西）。
3. 复用老 VM 的机制：`bridge.py` 的「槽位里写自身地址 + `UC_HOOK_CODE` 拦截」
   一个字都不用改。

### ② 宿主 → 虚拟机：host_api 表

`emu_host_api` 是一个函数指针数组，宿主通过 **ELF 符号表** 定位：

| 符号 | 用途 |
|---|---|
| `emu_host_api` | 9 个官方内部函数（mr_event / mr_timer / mr_start_dsm / mr_exit …） |
| `emu_slot_names` | 70 个平台接口的名字表（NULL 结尾） |
| `emu_self_test` | 自检函数 |
| `__heap_start` / `__heap_end` | mythroad 自有堆的边界 |
| `__stack_top` | 虚拟机栈顶 |

---

## 三、构建流程（关键：nm 自动判定官方已实现的接口）

```
1. 编译 mythroad.c + src/ + tomr/        -> obj/mr/**
2. nm 扫出已定义的 mr_/vm_/dsm_ 符号     -> selfimpl.txt   （288 个）
3. 按 selfimpl.txt 生成平台层 thunk       -> emu_stub.s / emu_slots.c
4. 编译 thunk + 移植层，链接              -> mythroad_vm.elf
```

**为什么必须先 nm 再生成**：mythroad.c 自己实现了 `mr_timer`、`mr_event`、
`mr_start_dsm`、`mr_save_mrp`、`mr_platDrawChar`、`mr_wstrlen` 等 **288 个**
`mr_*` 符号。再给它们生成 thunk 就是 duplicate symbol。
手工维护这个清单一定会漏 —— 第一次手工列了 12 个，链接直接报重复定义。

---

## 四、踩过的坑（全部有解，按踩坑顺序）

| # | 现象 | 根因 | 解法 |
|---|---|---|---|
| 1 | `initializer element is not constant` | 跨翻译单元的 `const uint32` 在 C 里**不是**常量表达式 | 不把它放进结构体初始化；改从符号表读 |
| 2 | 同上（另一个版本） | 链接脚本符号（`__heap_start = .`）的**地址**是链接期才知道的值 | 堆/栈边界改为从符号表读 |
| 3 | 符号表里找不到 `emu_host_api` | `--gc-sections` 认为没人引用它就删了 —— 而引用者只有宿主 | 加 `.emu_keep : { KEEP(*(.emu_keep)) }` 段 + `__attribute__((used))` |
| 4 | `emu_slot_names` 突然消失 | 生成器改了但 Makefile 没把它列为依赖，产物是旧的 | 生成器加进依赖；强制重新生成 |
| 5 | `multiple definition of 'mr_X_init'` | `mr_noparser.c` 与 `mr_parser.c` 二选一 | 排除 `mr_noparser.c` |
| 6 | `multiple definition of 'mr_save_mrp'` | mythroad.c 自己实现了它，nm 清单没覆盖 | 改用 nm 自动判定（第 3 节） |
| 7 | `undefined reference to '__aeabi_idiv'` | ARM 硬件无除法指令，gcc 生成 libgcc 调用 | 链接 `-lgcc`，且**必须放在目标文件之后** |
| 8 | `emu_crt.c` 报"stray '\343'" | **注释里写了 `mr_mem*/mr_str*`**，其中的 `*/` 提前闭合了块注释 | 注释里禁止出现 `*/`（反复踩了 3 次） |
| 9 | `emu_crt.o` 内容是 C 不是汇编 | `emu_crt.c` 和 `emu_crt.s` 生成**同一个 .o**，make 认为已完成 | 改名 `emu_jmp.s` |
| 10 | `conflicting types for 'memcpy'` | ARM32 的 `size_t` 是 `unsigned int`，我写成了 `unsigned long` | 全部改用 `size_t` |
| 11 | `undefined reference to '_ctype_'` | `<ctype.h>` 来自 newlib | 自带 `ctype.h` + `_ctype_` 表 |
| 12 | `undefined reference to 'setjmp/longjmp'` | Lua 的 protected call 依赖它；官方 `mr_setjmp.s` 是全局寄存器保存版，不是标准 per-call | 自写 `emu_jmp.s`（AAPCS 标准版） |
| 13 | Python 解析符号表找不到符号 | ELF32 的 `sh_entsize` 在偏移 **36**，我读成了 28（`sh_info`） | 改偏移 |

---

## 五、源码取舍（编译期发现）

| 文件 | 取舍 | 原因 |
|---|---|---|
| `src/lib/mr_iolib_target.c` | **用** | 走 `mr_open`/`mr_read` 平台接口，宿主能完整接管文件层 |
| `src/lib/mr_iolib.c` | 排除 | 走标准 stdio，裸机不可用且宿主接不了 |
| `src/lib/mr_*_brew.c`（3 个） | 排除 | 高通 BREW 平台专用 |
| `src/lib/mr_loadlib.c` | 排除 | 动态库加载（Windows API，链接不过） |
| `src/mr_noparser.c` | 排除 | 与 `mr_parser.c` 重复定义 |
| `src/mr_tests.c` | 排除 | Lua 自测 |
| `src/lib/mr_socket_target.c` / `mr_tcp_target.c` | **用** | 网络走平台接口，宿主可接管 |
| `tomr/src/*.c`（5 个） | **用** | TOM 运行时 |

裸机不链 newlib（printf 族会牵出一串 syscall），改为自带最小 CRT：
`emu_crt.c`（`_ctype_` 表 / `sprintf` / `strcspn` / `strtod`）+ `emu_libc.c`
（标准 C 字符串与内存函数）+ `emu_jmp.s`（setjmp/longjmp）。

---

## 六、平台接口账目

```
mrporting.h 平台接口          104 个
 ├─ 官方自己实现（nm 扫出）    ~34 个   → 不生成 thunk
 ├─ C 侧实现（libc 封装）      21 个   → emu_libc.c
 └─ 需要宿主补齐               70 个   → 汇编 thunk + Python 钩子
```

Python 侧已有实现的复用情况（`api/impl.py` + `api/emu_platform.py`）：

* `api/impl.py` 的 51 个 `mr_xxx(ctx, vm)` **签名与平台接口名逐字相同**，
  按名字直接绑定即可（`mythroad_port.py`）。
* `api/emu_platform.py` 补的是老架构用不到、但 mythroad 内部必需的那批：
  `mr_mem_get`/`mr_mem_get_ex`/`mr_mem_free`（堆的底座）、`mr_printf`、
  `mr_getNetworkID`、`mr_sendSms`、`mr_call`、`mr_connectWAP`、
  异步文件与系统菜单/对话框（回 `MR_FAILED`，我们用自绘 UI）。

---

## 七、关键确认：字节码兼容

自编译 VM 能不能加载真实 MRP 应用，取决于 mrpoid 的 undump 与应用字节码格式是否一致。已核实：

* `src/mr_undump.h:21` → `#define MRP_SIGNATURE "\033MRP"`，
  与应用 `start.mr` 的头 `\x1bMRP` **完全一致** ✅
* `mr_undump.c` 的 `LoadHeader` 里 `if (version > VERSION) { }` 是**空分支** ——
  比解释器新的字节码版本跳过全部 size 检查 ✅
* `LoadFunction` 的字段顺序是 **Lua 5.1 布局**
  （source → lineDefined → nups → numparams → is_vararg → maxstacksize →
  lines → locvars → upvalues → constants → code）✅
* 应用 `start.mr` 的头字节 `1b 4d 52 50 80 01 0a 00 00 00 40` ✅

结论：**mrpoid 的解释器能直接加载这些 MRP 应用的字节码**。

---

## 八、下一步（阶段 2）

要把一个真实 MRP 在新 VM 里跑起来，还差三件事：

1. **图形层接线**：`mr_platDrawCharReal` / `mr_drawBitmap` 要写进我们的屏幕缓冲；
   真机是「厂商屏幕缓冲模式」，所以 `mr_drawText` / `mr_bufToScreen` /
   `mr_getScreenBuf` 三个接口在 `mrporting.h` 里是 `#if 0`（官方注释：
   "当使用厂商屏幕缓冲时使用的接口"）—— **我们正是这种模式**。
   而 mythroad 走 `mr_platDrawCharReal` 逐字画进缓冲，不需要刷新接口 ✅
   字模格式已从官方手册确认：**1bpp，每行紧凑排列**，与原厂
   `fonts/gb16.uc2`（16×16，每行 2 字节，恰好对齐）兼容 ✅
2. **文件系统接线**：`mr_open`/`mr_read`/`mr_write` 走 `api/impl.py`，
   底层接 `fs.py`；`mr_mem_get` 给 mythroad 的那块内存要**地址恒定**
   （斯凯 dump/恢复的前提，`MythroadVm.alloc_vm_memory` 已实现）。
3. **事件循环接线**：`cli.py` 增加 `--backend mythroad` 分支，
   保留 `cfunction.ext` 作为可切换后端做 A/B 对照。

---

## 九、复现命令

```bash
# 一次性：取工具链（364MB，16 路并行）
bash tools/armtoolchain/fetch.sh

# 构建（需要 msys2 的 make）
cd tools/mythroad && PATH=/c/msys64/usr/bin:/c/msys64/mingw32/bin:$PATH make

# 装载自检
cd mrp_emu && python tests/mythroad_probe.py
```
