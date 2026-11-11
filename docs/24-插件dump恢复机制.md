# 插件调用失败：斯凯的「内存 dump / 恢复现场」机制

> 现象：调用冒泡浏览器插件（`mythroad/plugins/brwshell.mrp`）返回失败，
> 最终 `Invalid memory read @0x1C6826F4 (4B) PC=0x2F56BA` 崩溃。

老板提供的关键线索：**斯凯当年的做法是「MRP 运行过程中调用外部插件，会将
整个运行内存 dump 到内存卡，退出插件再恢复现场」**，日志里能看到
`mythroad/plugins/dump0` 的 open / close / remove。

本文记录这套机制的逆向结论与四个断点的修复。

---

## 一、机制全貌

### 1.1 三条独立的证据

| 来源 | 证据 |
|---|---|
| 用户日志 | `[fs] open 'mythroad/plugins/dump0' mode=0x1 -> 117` → `mr_close` → `mr_remove(mythroad/plugins/dump0) ret:0` |
| `cfunction.ext` 字符串表 | `plugins/dump%d`、`exRam:Alloc:addr:0x%x,len:%d`、`memory trace [start:0x%X]`、`memNode[%d]->P:0x%X`、`exRam:%dB required.` |
| `skyengine-v2` e2e | `fs.rmSync(ws.path('mythroad/plugins/dump0'), { force: true })` 出现在每个插件用例的**前置清理**与**后置断言**里 |

`plugins/dump%d` 在 **cfunction.ext**（ARM 侧 mythroad 实现）里，说明
**dump/恢复是 ext 自己的功能**，不是宿主做的。ext 内部维护一张
`memNode` 内存追踪表（`memNode[%d]->P:0x%X` / `->len` / `->next`），
切插件前把整张表的内容 dump 到 `plugins/dump%d`，插件退出后读回恢复。

日志里的 `dump0` 出现在**插件退出之后**（前面还有 `mr_closeNetwork`、
`mr_remove(mythroad/brw/exiterr)`），正是「读回 dump → 恢复现场 → 删除快照」
的收尾阶段。

### 1.2 dump 恢复的硬前提：地址必须恒定

dump 里记录的是**绝对地址**（`memNode[%d]->P:0x%X`）。恢复时按同一地址
写回，因此：

> **每轮 `mr_mem_get()` 必须返回同一块内存地址，否则恢复出来的指针全是野的。**

官方 `ref/mrpoid/mr/mythroad.c` 里内存生命周期严格配对：

```c
_mr_mem_init()                    // :626
    mr_mem_get(&Origin_LG_mem_base, &Origin_LG_mem_len)   // 申请

mr_stop_ex(freemem)               // :7266
    if (freemem) {
        mr_mem_free(Origin_LG_mem_base, Origin_LG_mem_len);  // :7364 释放
    }
```

重启链是 `mr_stop() → mr_stop_ex(TRUE) → _mr_intra_start() → _mr_mem_init()`，
所以「先 free 后 alloc」必须落回同一块。

---

## 二、四个断点

### 断点 1：`proxy.51mrp.com` / `proxy2.51mrp.com` 不在 DNS 映射里

日志里连续 4 次：

```
[net] DNS 失败 proxy.51mrp.com: [Errno 11001] getaddrinfo failed
```

浏览器插件链（`brwmain.ext` → `brwshell.ext` → `embrw`）要从这两个域名
下载组件。`skyengine-v2` 的**每个**插件 e2e 用例都显式传了：

```
dnsMap: "...;proxy.51mrp.com->159.75.119.124;proxy2.51mrp.com->159.75.119.124"
```

而我们的 `DEFAULT_DNS_MAP` 只有 3 条（`rop` / `spd` / `wap.skmeg.com`），
**恰好漏掉这两条** —— 这就是插件组件下载失败、进而「打开后立刻退回主界面」
的直接原因。

**修复**：`net.py` 的 `DEFAULT_DNS_MAP` 补齐为 5 条。

### 断点 2：`mr_stop_ex` 不释放 VM 内存，第二轮 `mem_get` 直接失败

上一轮修复把 `mr_stop_ex` 从「退出应用」改成了「停实例」，但**只置标志、
没释放内存**。官方语义里 `freemem != 0` 必须 `mr_mem_free`。

我们的堆只有 6MB（`MEMORY_MANAGER_SIZE`，与 vmrp 官方 `header/vmrp.h`
一致），而 `mem_get` 一次要 4MB —— 不释放的话第二轮 `mem_get` 返回 0，
插件根本起不来。

**修复**：`mr_stop_ex(freemem!=0)` → `vm.release_vm_memory()`。

### 断点 3：first-fit 堆不保证地址恒定

即使按官方语义释放了，普通 first-fit 堆在有碎片时也不保证同尺寸两次分配
落回同一地址。实测：

```
其他分配 0x280000, mem_get 0x299000
两轮都释放后再 mem_get -> 0x280000   与上轮一致? False
```

而 RX 管理器实际拿到的就是 `0x2A8168`（不是堆基址 `0x280000`），
说明 ext 启动时已有别的分配占了前面 —— 正是碎片场景。

**修复**：给 VM 内存**单独预留一块固定区域**（`Allocator.reserve()`），
不进入空闲链表，普通 `malloc` 抢不到它，每轮 `mem_get` 都从它发。

```python
# memory.py
def reserve(self, n: int) -> int:
    """预留一块固定地址的内存，返回 0 表示失败。"""
```

### 断点 4：`plugins/dump0` 解析到了错误的目录

上一轮修路径解析时，规则是「**仅当目标是文件**才采纳 `mythroad/` 回退」，
以免破坏 RX 管理器的浏览目录语义。但 dump 快照是**新建文件**——文件还不
存在，规则不生效：

```
plugins/dump0  -> plugins\dump0      ← 错！应是 mythroad\plugins\dump0
```

dump 写到了 `workdir/plugins/`，插件退出时按 `mythroad/plugins/dump%d`
读不回来 → 恢复失败 → 野指针 `0x1C6826F4`。

**修复**：采纳条件放宽为「目标是文件 **或** 目标是带子目录形态的新建文件
且父目录存在」，同时保持纯目录形态（`"."` / `"mythroad"` / `"plugins/"`）
不变：

```python
if ("/" in n and not n.endswith("/")
        and not ctarget.is_dir()
        and ctarget.parent.is_dir()):
    n = cand
    break
```

---

## 三、改动清单

| 文件 | 改动 |
|---|---|
| `net.py` | `DEFAULT_DNS_MAP` 补 `proxy.51mrp.com` / `proxy2.51mrp.com` |
| `api/impl.py` | `mr_stop_ex(freemem!=0)` 释放 VM 内存；`dsm_mem_get` 走预留区；`dsm_mem_free` 识别预留区 |
| `vm.py` | 新增 `alloc_vm_memory()` / `release_vm_memory()` / `vm_mem_reserved` |
| `memory.py` | `Allocator.reserve()` —— 预留固定地址，不进空闲链表 |
| `fs.py` | 相对路径解析：新建文件也落 `mythroad/` 下（dump 快照） |
| `tests/plugin_probe.py` | 新增 dump 路径、内存地址恒定、预留区、DNS 映射断言（47 项） |
| `tests/legacy_net_probe.py` | DNS 断言从 3 条更新为 5 条 |

---

## 四、验证

- 全套 **21 个探针 rc=0、0 失败**（`plugin_probe` 47 项 / `legacy_net_probe` 51 项）
- 6 个真实应用（QQ2007 / QQ2010 / 话费管家 / RX管理器 / 游戏中心 / opglqa）
  运行无异常
- pyz 已重打包（141.0 KB）

---

## 五、已知边界

**完整的「插件跑起来 → 退出 → 恢复上级现场」往返仍未在本地端到端复现。**
原因：

1. `brwshell` 插件链需要从 `proxy.51mrp.com` 下载组件 —— 域名映射已补，
   但能否从复刻服务端拿到当年的组件包，取决于对方是否还留着。
2. 触发插件的入口（游戏内广告条 → 浏览器）需要真实交互路径。

已定位并修复的是**机制层面的四个断点**（DNS 缺失、内存不释放、地址漂移、
dump 路径错误）。这四条恰好覆盖了用户日志里所有可见的失败征兆：
DNS 失败 → 组件下载不了 → 插件起不来 → 恢复时读不到 dump → 野指针崩溃。

建议老板在有网环境实测一遍「冒泡 → 点广告 → 浏览器 → 返回」，如果还有
问题，把新的日志给我 —— 特别关注 `plugins/dump%d` 的 open/close/read/write
序列和 `mem_get` 的地址。
