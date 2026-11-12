# 阶段 2：官方 mythroad 接管应用 —— 打通到 TOM 解释器

> 阶段 1 只能证明「镜像能装载、能执行」。阶段 2 要证明**官方的 mythroad
> 运行时真的接手了一个 MRP 应用**。本文记录实际结果与最后一个缺口。

---

## 一、现在能做到什么

自编译 VM 里启动 `dsm_gm.mrp` 的真实调用序列：

```
mr_getScreenInfo          -> 返回 240x320
mr_open  'mythroad/dsm_gm.mrp' -> 成功（宿主文件系统）
mr_read / mr_seek / mr_read / mr_read / mr_close   -> 读 MRPG 容器
mr_mem_get                -> 预留 2048KB（地址恒定区）
                        mythroad 在这之上分配自己的堆
mr_screenBuf 分配          -> 0x9B58D8（153600 字节 = 240x320x2 RGB565）
mr_platEx(1001)            -> 未实现（真机"第二缓冲"申请，回落到自己分配）
mrp_dofile("start.mr")    -> TOM 解释器执行应用字节码 ✅
```

**证据链**：mythroad 打印了 `dealevent is nil!` —— 这条调试串来自
`mythroad.c:7524` 的 `mr_event` 事件分发分支，说明**控制流已经进入了
Lua 层的全局表查找**，也就是 TOM 解释器确实在跑应用的字节码。

平台接口绑定 **70/70**。

---

## 二、决定性根因：number 常量是 4 字节 float

### 现象

应用启动到一半崩在 mythroad 的堆里：

```
Invalid instruction (UC_ERR_INSN_INVALID) PC=0x9DDE98 LR=0x9DDE20
```

PC/LR 都落在 mythroad 自己的堆（0x9B58D8 起）—— 说明解释器把**堆里的
数据当成了函数地址**去调用。

### 定位方法

用 Python 按 mrpoid 的 `LoadFunction` 布局手工解析 `start.mr`：

```
按 double 读:  [8] num 8.1569518204705e-311   [9] nil   [10] ?? type83   ← 全乱
按 float  读:  [8] num 0.0   [9] str 'ShowQQmainlist'  [10] str 'LoginStatus'  ← 完全可读
```

常量表从**第一个数字常量**起整体错位 4 字节。

### 为什么解释器会读错

`src/mr_undump.c` 的 `LoadHeader` 有一段 size 检查：

```c
if (version > VERSION_50) {
    /* 空 —— 新版本跳过全部 size 检查 */
} else {
    TESTSIZE(sizeof(mrp_Number), "number");
    ...
}
```

MRP 应用的字节码头是 `\x1bMRP` + version `0x80`，而 `VERSION_50 = 0x50`，
**0x80 > 0x50 → 检查被跳过**。于是解释器按 `mrp_Number = double`（8 字节）
读，而应用（斯凯平台的编译器产物）写的是 **4 字节 float**。

### 修复

`tools/patch_mr_undump.py` —— 构建时给 `src/mr_undump.c` 打补丁
（**不改参考源码**，补丁版生成到 `tools/mythroad/patched_mr_undump.c`）：

```c
static mrp_Number LoadNumber (LoadState* S)
{
#ifdef MRP_UNDUMP_FLOAT_NUMBER
   float f;
   LoadBlock(S,&f,sizeof(f));
   return (mrp_Number)f;      /* float -> double 精确转换 */
#else
   ...原样...
#endif
}
```

解释器**内部**仍用 double 运算，只有常量表的**存储宽度**变了；
运行时算出来的数字走 `mr_pushnumber`（double），不受影响。

### 验证

补丁后用 Python 完整解析（含子函数列表）三个应用：

```
QQDSM2007.mrp    结束偏移 6396/6396   ✅ 完全匹配
dsm_gm.mrp       结束偏移 37230/37230 ✅ 完全匹配
gxrxd.mrp        结束偏移 5509/5509   ✅ 完全匹配
```

**字节码布局 100% 对上了** —— 剩下的崩溃与格式无关。

---

## 三、最后一个缺口：斯凯扩展机制（`c_load` / `_mr_c_load`）

把应用常量表里"像函数名的标识符"与 mythroad 注册的 81 个全局函数对比：

| 应用 | 需要的、mythroad **没有**注册的 |
|---|---|
| `dsm_gm.mrp` | `c_load`、`showDialog`、`checkFile`、`runAppFunc`…（部分是应用自定义） |
| `gxrxd.mrp` | **`_mr_c_load`**、`dealevent`、`dealtimer`…（部分是应用自定义） |
| `QQDSM2007.mrp` | 应用自定义为主 |

关键那个是 **`_mr_c_load` / `c_load`** —— 它的语义是「加载包内 `.ext`
的 C 函数」。在 mrpoid 里：

* `mythroad.h:264` → `extern int32 mr_c_function_load(int32 code);`
  —— **平台接口**，真机上由 ROM 实现
* `mythroad.c:6478` → `mr_load_c_function = mr_c_function_load;`
  只在 `#ifdef MR_C_TEST` + `#ifdef SDK_MOD` 下生效（`mr_sdk(800)` 分支）
* `_mr_c_load` / `c_load` 这两个 Lua 全局**在 mrpoid 里根本没注册**
  → 说明是**宿主（平台）注册的**

也就是说：**老架构里那个 331KB 的宿主级 `cfunction.ext`，干的就是这件事**
（它内含 c_load 机制 + ARM 扩展代码）。

### 要补的三件事

1. **定义 `MR_C_TEST` + `SDK_MOD`**，让 `mr_sdk(800)` 分支启用
   （`MR_C_TEST` 在 mythroad.c 里只出现 1 次，影响面很小；
   `SDK_MOD` 12 处，其中 2 处是注释掉的）
2. **实现 `mr_c_function_load` 平台接口**：读包内 `.ext` → 解析 MRPG/CMAP 段
   → 把 ARM 代码加载进 VM 空间 → 返回入口
3. **注册 `c_load` / `_mr_c_load` Lua 全局**（在 `emu_main.c` 里用
   `mrp_register` 做）

好消息：第 2 步的"在 Unicorn 里执行 ARM 代码"能力**我们已经有了**
（老架构一直在用），缺的只是把 `.ext` 里的 CMAP 段加载进来。

---

## 四、阶段 2 的新增/修改

| 文件 | 作用 |
|---|---|
| `tools/patch_mr_undump.py` | 给 `mr_undump.c` 打 float-number 补丁（不动 ref 源码） |
| `tools/mythroad/Makefile` | 集成补丁规则；`-DMRP_UNDUMP_FLOAT_NUMBER=1`；newlib 堆 4MB→1MB（给宿主腾地方） |
| `tools/mythroad/emu_main.c` | 入口改成 `mr_start_dsm_ex("#<包名", "start.mr")` |
| `tools/mythroad/mythroad.ld` | newlib 堆缩到 1MB，宿主分配区扩到约 3.8MB |
| `mrp_emu/mythroad_vm.py` | 哨兵返回点（`emu_start` 的 until）、`screen_buf_addr()`、`glyph_ptr()`、`start_app()`、调用统计 |
| `mrp_emu/mythroad_app.py` | 新架构的宿主上下文（`LazyGfx` 惰性绑定 mythroad 的帧缓冲） |
| `mrp_emu/mythroad_port.py` | 70 个平台接口按名字绑定（`emu_platform` 优先于 `impl`） |
| `mrp_emu/api/emu_platform.py` | 补 `mr_mem_get`/`mr_printf`/`mr_getCharBitmap`/`mr_platDrawCharReal` 等 |
| `mrp_emu/gfx.py` | `Gfx(mem, fb_addr=...)` 支持绑定外部帧缓冲 |
| `mrp_emu/tests/mythroad_run_probe.py` | 真启动 MRP 的探针（启动/帧缓冲/事件循环/调用序列） |

---

## 五、阶段 2 踩的坑

| 现象 | 根因 |
|---|---|
| `emu_start(addr, 0, 0, 1)` 只跑一条指令 | count=1；自检函数因为第一条指令恰好是 `mov r0` 才"碰巧"返回魔数 —— 阶段 1 的通过是**假阳性**，已改用哨兵地址 |
| `'list' object is not callable` | `Allocator` 的方法是 `free_block`，`free` 是空闲链表这个 list |
| `mr_mem_get failed!` | newlib 堆占 4MB，宿主只剩 1.87MB，凑不出 2MB 的应用堆 → 堆缩到 1MB |
| 返回值 458752（=钩子区基址） | 同上第一条 —— emu_start 提前返回，R0 是垃圾 |
| 包名不生效（总加载 `*A`） | `mr_start_dsm` 不接受普通文件名，必须用 `mr_start_dsm_ex` 的 `#<` 前缀 |
| 注释里的 `mr_mem*/mr_str*` | `*/` 提前闭合块注释（阶段 1 也踩了 3 次，这次又踩） |

---

## 六、复现

```bash
cd tools/mythroad && PATH=/c/msys64/usr/bin:/c/msys64/mingw32/bin:$PATH make
cd mrp_emu && python tests/mythroad_run_probe.py --verbose
```
