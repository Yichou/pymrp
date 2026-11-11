# 自编译 mythroad 虚拟机：替代 cfunction.ext 的可行性结论

> 老板提问：**「目前启动 MRP 还必须依赖 cfunction.ext 吗？没有实现 MR 解释器吗？
> 可以用 mythroad.c 编译虚拟机，mythroad_mini.c 编译则不支持 mr 启动。」**
>
> 本文给出三个问题的确证答案 + 移植面量化 + 落地路径。
> 所有数字均可用 `tools/mythroad_check.sh` 与 `tools/port_scan.py` 复现。

---

## 一、结论速览

| 问题 | 答案 |
|---|---|
| 启动 MRP 还必须依赖 `cfunction.ext` 吗？ | **是，硬依赖。** 没有它就没有 MRP 加载器，一个应用也起不来。 |
| 没实现 MR 解释器吗？ | **解释器存在，但不在我们代码里** —— 它被编译进了 `cfunction.ext` 这个二进制。我们手写的是**宿主 API 层**（1502 行），这部分才是 bug 温床。 |
| 能用 mythroad.c 编译虚拟机吗？ | **能，而且是对的方向。** 源码开箱可编（47/50 文件语法通过，只缺 1 个宏）；平台接口 86 个，A 类必需 35 个。 |
| mini 版支持 mr 启动吗？ | **不支持**（与老板判断一致）。mini 的 `mr_start_dsm` 走 `_mr_intra_start("logo.ext")`，完整版才走 `_mr_intra_start(MR_START_FILE="start.mr")`。 |

---

## 二、架构真相：三层，而不是两层

之前我们一直以为「MRP 应用 = ARM 原生代码，宿主只提供 API」。**实际是三层**：

```
第 3 层  MRP 应用        start.mr = TOM(Lua 语法) 预编译字节码 + .bmp 资源
                          装在 MRPG 容器里（0xF0 固定头 + 条目表）
                              ▲
第 2 层  TOM 解释器       ref/mrpoid/mr/src/mr_*.c —— 这是**改名成 mr_ 前缀的 Lua 5.0**
                          （$Id: lcode.c,v 1.117 2003/04/03 13:35:34 roberto）
                              ▲
第 1 层  mythroad 宿主    mythroad.c —— mr_* API 实现、MRPG 解包、事件循环 mr_timer、
                          插件链 MRF_RunFile、内存模型 mr_mem_get/free
```

**`cfunction.ext` 就是第 1+2 层编译后的 ARM 二进制。** 证据（字符串级一一对应）：

| cfunction.ext 里的字符串 | 对应源码 |
|---|---|
| `_mr_c_function_new(%p, %d)  mr_c_function_P:%p` | `mythroad.c:6123` |
| `mr_unzip` | `mythroad.c:599`（MRPG 解包） |
| `attempt to use a closed file` | `src/lib/mr_iolib.c:106`（Lua io 库） |
| `error in error handling` | `src/mr_do.c:60`（Lua 运行时） |
| `DrawText x=%d: txt is nil!` / `GetSysInfo` / `RunFile` / `Exiting...` | `mythroad.c` 的 `MRF_*` 注册函数 |

容器格式也对得上：`cfunction.ext` 头 8 字节 = `MRPG` + `CMAP`，而 `dsm_gm.mrp`
头 = `MRPG` + 版本 + 总长 + 首段偏移，之后是 `u32 nameLen | name | u32 off | u32 csize | u32 rsv` 条目表。

### 我们自己写的那部分

`mrp_emu/mrp_emu/api/` 共 1847 行，是 **mythroad.c 里 `mr_*` 的替代实现**：

| 文件 | 行数 | 内容 |
|---|---|---|
| `api/impl.py` | 1502 | mr_* API 的 Python 实现（文件/网络/图形/声音/支付/userinfo…） |
| `api/mrtable.py` | 248 | mr_table 槽位表 |
| `api/dsmfuncs.py` | 97 | dsm_require_funcs 槽位表 |

**之前修的那些 bug 全部出在这里**：支付后野指针（`mr_getUserInfo` 字段错位）、
插件返回退桌面（`mr_stop_ex` 语义）、`sprintf` 浮点变参（AAPCS）、
`mr_plat` 未知 code 行为…… 因为我们在**猜**官方语义，而不是**用**官方语义。

---

## 三、为什么自编译 mythroad 是对的方向

自编译后，第 1、2 层换成官方实现，带来四个直接收益：

1. **API 语义 100% 官方** —— 不用再猜 `mr_getUserInfo` 布局、`mr_stop_ex` 语义。
2. **解释器自带** —— TOM 字节码（`start.mr`）由 `mrp_open`/`mrp_dofile` 执行，
   不再依赖别人编译好的二进制。
3. **插件链天然对齐** —— `mr_timer` → `MR_STATE_RESTART` → `MRF_RunFile` →
   `mr_stop_ex` → `mr_mem_get/free` 就是斯凯那套 dump/恢复现场的底座，
   我们手写的 `app_stack` 模拟可以退休。
4. **MRP 容器解包官方化** —— `mr_unzip` + `_mr_intra_start` 取代我们手写的装载逻辑。

**代价**：mythroad.c 的 `mr_*` 大量是 `extern`（官方就把它设计成平台层），
要我们补实现。但这些实现在我们 `api/impl.py` 里**已经有了**，只是宿主换了个人。

---

## 四、移植面量化（实测）

### 4.1 源码可编译性

```
$ bash tools/mythroad_check.sh
通过: 47    失败: 3
失败文件:
  - src/lib/mr_iolib_brew.c     ← 高通 BREW 平台专用，不需要
  - src/lib/mr_socket_brew.c    ← 同上
  - src/lib/mr_tcp_brew.c       ← 同上
```

* 唯一需要补的宏：**`MR_VERSION`**（`mythroad.c:5342`、`src/mr_api.c:868` 各用一次）
* `mythroad.c` 9679 行，`src/` + `tomr/` 约 45 个文件
* **没有 ARM 交叉编译器**：本机 `arm-none-eabi-gcc` / `armcc` 全缺；
  msys64 有 mingw32 gcc（15.2.0），但沙箱禁止 gcc 落盘，只能做 `-fsyntax-only` 体检

### 4.2 平台接口清单（`tools/port_scan.py`）

`mrporting.h` 官方平台接口共 **86 个**，本工程已实现 9 个（`mr_event`/`mr_timer`/
`mr_start_dsm`/`mr_stop`/`mr_pauseApp`/`mr_resumeApp`/`mr_registerAPP`/
`mr_newSIMInd`/`mr_smsIndiaction`），**待实现 77 个**：

| 分级 | 数量 | 判据 | 名单 |
|---|---|---|---|
| **A 类：VM 内部必需** | **35** | 被 mythroad.c / src/ 内部调用，缺了 VM 起不来 | `mr_open` `mr_close` `mr_read` `mr_write` `mr_seek` `mr_info` `mr_remove` `mr_drawText` `mr_drawBitmap` `mr_getScreenBuf` `mr_bufToScreen` `mr_platDrawCharReal` `mr_getCharBitmap` `mr_printf` `mr_playSound` `mr_stopSound` `mr_sleep` `mr_getTime` `mr_getDatetime` `mr_getUserInfo` `mr_getScreenInfo` `mr_mem_free` `mr_exit` `mr_plat` `mr_platEx` `mr_call` `mr_connectWAP` `mr_closeNetwork` `mr_getHostByName` `mr_getNetworkID` `mr_sendSms` `mr_startShake` `mr_getLen` `mr_asyn_read` `mr_asyn_write` |
| **B 类：仅 MRP 应用调用** | **42** | 只被 app 通过 mr_table 调，可先返回 `MR_FAILED` 后补 | `mr_mem_get` `mr_mem_get_ex` `mr_save_mrp*` `mr_start` `mr_timerStart/Stop` `mr_uninstall` `mr_getAppList` `mr_initNetwork` `mr_connect` `mr_socket` `mr_send/recv/sendto/recvfrom` `mr_closeSocket` `mr_findStart/GetNext/Stop` `mr_rename` `mr_mkDir` `mr_rmDir` `mr_ferrno` `mr_dialog*` `mr_edit*` `mr_menu*` `mr_text*` `mr_win*` `mr_stopShake` |

> 注意 `mr_mem_get` / `mr_mem_get_ex` 落在 B 类 —— 它们不是 mythroad 内部调用，
> 而是**给斯凯插件链用的**。这正是 `docs/24` 里 dump/恢复机制依赖的入口，
> 自编译后由官方实现接管，地址恒定问题自动消失。

---

## 五、落地路径

### 阶段 0：取得 ARM 交叉编译器（**当前唯一硬门槛**）

| 方案 | 产物 | 优点 | 缺点 |
|---|---|---|---|
| **A. ARM GNU Toolchain**（arm-none-eabi，~200MB） | bare-metal ELF | 与真机同构，MRP 应用若有 ARM 汇编段也能跑 | 需下载；newlib 的 sbrk/malloc 要接我们的 Python 堆 |
| B. x86 编译 + ctypes | `mythroad.dll` | 快（TOM 解释器原生速度，比 Unicorn 快数十倍），无需下载 | MRP 应用若含 ARM 原生段则跑不了；事件模型要改成 Python 主动调 C |

> **倾向 A**：现有 `bridge.py` 的「槽位里写自身地址 + `UC_HOOK_CODE` 拦截」机制
> 可以原样复用 —— 自编译的 mythroad VM 当 ARM 二进制加载进 Unicorn，
> Python 侧桥接逻辑几乎不动。
> **需要老板确认**：能否下载 ~200MB 的 ARM 工具链（当前沙箱拦了 pip 下载）。

### 阶段 1：平台层 stub（ARM 侧 thunk）

`mrporting.h` 的 77 个待实现接口，在 C 侧写成**尾调用 thunk**：

```c
/* 槽位里写自身地址（沿用 bridge.py 的机制），Python 用 UC_HOOK_CODE 拦截 */
#define EMU_THUNK(slot) \
    __asm__ volatile("ldr ip, %0\n\t bx ip\n\t" :: "m"(slot) : "ip","cc","memory")

int32 mr_open(const char* fn, uint32 mode) { EMU_THUNK(g_slot_mr_open); return 0; }
```

`bx ip` 不改 LR → Python hook 读到的 LR 就是调用者返回地址 → hook 里
`PC = LR` 即完成返回；参数 R0-R3 原样传下去，Python 侧读法与现在完全一致。

### 阶段 2：替换启动链路

```
现在:  load_code(cfunction.ext) → ext_init() → dsm_init() → start_dsm(app, "start.mr")
改后:  load_code(mythroad_vm.elf) → vm_init() → mr_start_dsm(app, "start.mr")
```

`cli.py` 里 `runtime` 参数的语义从「cfunction.ext 路径」改为「VM 二进制路径」，
其余事件循环（`vm.event()` / `vm.timer()` / `vm.touch_event()`）保持不变。

### 阶段 3：语义对齐与回归

* 现有 22 个探针全部要重跑（`api/impl.py` 的实现会被官方版本取代，
  探针断言要从「我们以为的语义」改成「官方语义」）
* `docs/19`（sprintf/槽位表）、`docs/22`（宿主接口语义）、`docs/24`（dump 恢复）
  三篇的结论要按官方实现复核 —— **可能会推翻我们之前的某些"修复"**

### 阶段 4：新旧并存

保留 `cfunction.ext` 作为可切换后端（`--backend ext|mythroad`），
新后端稳定后再切换默认。

---

## 六、两个决定路线选择的实证发现（2026-11-11 追加）

### 6.1 MRP 应用本体是纯字节码，不含 ARM 指令

`start.mr` 的头 16 字节：

```
1b 4d 52 50 80 01 0a 00 00 00 40 73 74 61 72 74 2e 6d 72 ...
└─ ESC "MRP" ─┘ └版本┘ └格式┘  └"start.mr" 字符串常量┘
```

即 **Lua 5.1 预编译字节码**（`\x1bLua` 被改成 `\x1bMRP`），由 `src/mr_undump.c` 加载。

对照检查：

* `src/mr_lex.c` / `mr_parser.c` / `mr_code.c` 里**没有任何 `asm` 支持** →
  TOM 脚本无法内联 ARM 汇编 → **.mr 段里不存在 ARM 指令**
* `sfc.bin` / `*.bin`（RX 管理器 197 段里 55 个 .bin）经抽样是**字模/精灵数据**，
  不是代码

**结论：MRP 应用本体是纯数据（TOM 字节码），理论上 x86 也能跑。**

### 6.2 但包内 `cfunction.ext` 是真 ARM 码 —— 决定性未知项

`opglqa.mrp` 包内的 `cfunction.ext`（19872 字节）头：

```
4d 52 50 47 43 4d 41 50 | 10 40 2d e9 | ...
└──── MRPG "CMAP" ────┘ └ARM: push {r4,lr}┘
```

**CMAP 段里是真 ARM 机器码**，和我们运行时根目录那个 331520 字节的
`cfunction.ext` 同类（后者是斯凯固件版，MRP 应用自带的这个是应用精简版）。

| 若 | 后果 |
|---|---|
| 包内 .ext 的 ARM 段**会被执行** | **路线 B（x86 + ctypes）不可行**，必须走路线 A（ARM 交叉编译 + Unicorn） |
| 包内 .ext 的 ARM 段**从不执行**（真机 ROM 自带 mythroad，属冗余） | 路线 B 可行，且性能更好 |

**已查明的事实（2026-11-11）**：在**当前模拟器里**，包内 `.ext` 从不执行。

* `release.py:37` 的 `CODE_EXTS = (".mr", ".ext", ".mid", ".mel", ".dat", ".bin")`
  把 `.ext` 归为代码类 → **不释放**到工作目录
* `cli.py:465` 的 `v.load_code(runtime)` 加载的始终是**运行时根目录那个
  331520 字节的宿主级 `cfunction.ext`**，不是包内那份
* 实证：6 个真实 MRP 应用全部跑通，而包内 `.ext` 从未被装载过

**残留未知**：真机上 mythroad 是否会自动执行包内 `.ext`（斯凯固件里
`cfunction.ext` 是固件的一部分，MTK ROM 自带 mythroad，两者可能重复）。

**验证方法（一行日志）**：在 `vm.py` 的 `ext_init()` 前后打印当前加载的
ext 文件路径与大小，看 MRP 启动时用的是包内那份还是运行时根目录那份；
再在 `cli.py` 加载应用时检查包内 `cfunction.ext` 有没有被取出装载。

> 风险已收窄：**路线 A 对两种情况都成立**，路线 B 只在"包内 .ext 从不执行"
> 时可用。**默认按路线 A 规划。**

---

## 七、风险

| 风险 | 量级 | 缓解 |
|---|---|---|
| MRP 应用含 ARM 原生段 | **已排除**（TOM 无内联汇编，.bin 是数据） | — |
| 包内 cfunction.ext 的 ARM 段被执行 | **未知**（见 6.2） | 一行日志即可查清；按最坏情况走 ARM 路线 |
| mythroad 的屏幕/字体/声音语义与真机有偏差 | 中 | A 类接口逐个对照真机行为 |
| 之前基于"猜的语义"做的修复被官方语义推翻 | 中 | 阶段 3 回归全部探针，允许改断言 |
| 工具链下载被网络策略阻断 | 高（当前） | 老板授权 / 离线拷贝 arm-none-eabi |

---

## 八、复现命令

```bash
bash tools/mythroad_check.sh          # 源码语法体检（47/50）
python tools/port_scan.py             # 平台接口分级清单（86 / 35 / 42）
```
