# 17 启动性能：SDL 初始化与音频设备探测

> 2026-11-10。老板反馈「从看到 pygame 两行欢迎日志到模拟器界面出来要 20 秒」。
> 实测基线 **17.1s**，定位后优化到 **0.85s**（约 20 倍），首帧 240ms 上屏。
> 本文把测量方法、错误尝试和最终方案全部记下来，避免以后有人重新踩坑。

---

## 一、现象与测量环境

```
pygame 2.6.1 (SDL 2.28.4, Python 3.12.10)
Hello from the pygame community. https://www.pygame.org/contribute.html
```

这两行是 pygame 的欢迎 banner。老板看到它们之后还要等约 20 秒才出现手机界面。

环境：Windows，机器**没有音频输出端点**（`waveOutGetNumDevs() == 0`，
`WASAPI can't find requested audio endpoint: 找不到元素`）。这个前提是关键。

基线用子进程端到端计时，两次稳定：

| 第 1 次 | 第 2 次 |
|---|---|
| 17.19 s | 17.12 s |

---

## 二、分段测量：8 秒 + 8 秒

先按启动链路逐段打点（真实窗口驱动，不是 dummy）：

| 阶段 | 累计 | 增量 |
|---|---:|---:|
| `import pygame` | 268.5 ms | 268.5 ms |
| **`pygame.init()`** | **8364.2 ms** | **8095.7 ms** |
| `display.Info()` | 8364.3 ms | 0.1 ms |
| `display.set_mode()` | 8443.4 ms | 79.1 ms |
| `Font(msyh.ttc, 17)` + 首次中文 render | 8460.8 ms | 17.4 ms |
| **`pygame.mixer.init(44100)`** | **16499.7 ms** | **8038.9 ms**（且失败） |

而只做 `pygame.display.init() + pygame.font.init()` 时：

| 阶段 | 累计 |
|---|---:|
| `import pygame` | 395.4 ms |
| display + font 初始化 | 395.4 ms（**增量 ~6 ms**） |
| `set_mode()` | 536.0 ms |
| 中文字体就绪 | 540.4 ms |

**结论**：`pygame.init()` 会连带 `SDL_INIT_AUDIO`，SDL 2.28 在没有音频端点的
Windows 机器上逐个驱动枚举，WASAPI 那一轮要 ~8 秒；`AudioEngine.__init__`
又同步调一次 `pygame.mixer.init()`，再花 8 秒，最后还失败降级成静音。

顺带排除的嫌疑：19MB 的 `msyh.ttc` 加载只要 ~1ms（SDL_ttf 走内存映射），
`Catalog` 读 664 条在线缓存 <10ms，`rglob` 扫 27 个 MRP ~100ms，
`Vm()` 建 8MB 内存 ~55ms —— 都不是瓶颈。

各音频驱动对比（同一进程，`display.init()+font.init()` 之后单独 `mixer.init()`）：

| `SDL_AUDIODRIVER` | 结果 | 耗时 |
|---|---|---:|
| `wasapi`（默认） | 失败：找不到音频端点 | **8486 ms** |
| `directsound` | 失败：No audio device found | 9.6 ms |
| `winmm` | 失败：Unsupported audio format | ~20 ms |
| `dummy` | 成功 `(44100, -16, 2)` | 0.2 ms |

---

## 三、试过但**否掉**的方案：后台线程预热

第一反应是「启动时把 `mixer.init()` 丢到 daemon 线程，主线程先出界面」。
实测结果：

- 界面确实 0.54s 就出来了；
- 但主循环 90 帧耗时 **9550 ms**（正常应 1500 ms），用 `SDL_AUDIODRIVER=dummy`
  的对照组只要 1509 ms。

原因：WASAPI 枚举的 C 调用没有释放 GIL，后台线程把主线程帧率拖到 ~9fps，
界面「出现但卡死 8 秒」，体验反而更糟。**音频慢初始化不能靠线程掩盖，必须不去做。**

---

## 四、最终方案

### 4.1 `cli.py`：最小 SDL 初始化

```python
def init_pygame_minimal() -> None:
    import pygame
    pygame.display.init()
    pygame.font.init()
```

`pygame.init()` 换成它。事件、计时器（`Clock`）、`Surface`、`image`、
`transform` 都随 display 自动可用（已写进 `tests/startup_probe.py` 断言）；
手柄、剪贴板、音频这些用不到的子系统一律不初始化。

### 4.2 `audio/mixer.py`：无设备快速跳过

```python
@staticmethod
def _device_probe() -> bool:
    if os.environ.get("SDL_AUDIODRIVER"):
        return True          # 显式指定驱动（含测试用 dummy）交给 SDL
    if sys.platform != "win32":
        return True
    import ctypes
    return ctypes.windll.winmm.waveOutGetNumDevs() > 0
```

`_init()` 在 `mixer.init()` 之前先问一句（**单次 0.023ms**）：

- Windows 且返回 0 → 直接 `ok=False` + 一行日志，不碰 SDL 音频；
- 有设备 / 非 Windows / 显式指定驱动 → 完全保持原来的初始化路径。

`play()` 本来就对 `not self.ok` 返回 `MR_SUCCESS`（老应用不会因失败反复重试刷屏），
所以静音降级的行为和以前**完全一致**，只是从「8 秒后失败」变成「瞬间失败」。

### 4.3 新增开关

| 开关 | 用途 |
|---|---|
| `PYMRP_TIMING=1` | 打印模块导入 / SDL 初始化 / VM 就绪 / 窗口创建 / 首帧上屏五个打点 |
| `--audio-driver auto\|fast\|wasapi\|directsound\|winmm\|dummy` | `fast` 在 Windows 强制 DirectSound，跳过 WASAPI 慢枚举；其余直接写 `SDL_AUDIODRIVER` |
| `--frames N` | 原先只在 headless 生效，现在窗口模式也能跑 N 帧自动退出，便于计时和自动化截图 |

`fast` 是给「远程桌面 / 虚拟声卡」这类 `waveOutGetNumDevs() > 0` 但 WASAPI
仍找不到端点的角落场景兜底的，普通机器用默认 `auto` 即可。

---

## 五、优化后实测

| 指标 | 优化前 | 优化后 |
|---|---:|---:|
| headless 端到端 | 17.12 s | **0.85 s** |
| 窗口模式 `--frames 3` | （需手动关窗） | **0.96 s** |
| 首帧上屏（`PYMRP_TIMING`） | — | **240.6 ms** |
| `SDL_AUDIODRIVER=dummy` 下音频 | 正常 | 正常（显式驱动不探测） |
| `mrp_emu.pyz` 单文件版启动 | — | 首帧 707 ms（zip 解压多了 ~460ms） |

打点样例：

```
[timing] 模块导入完成: 127.2 ms
[timing] SDL 最小初始化（display + font）: 127.5 ms
[audio] 未检测到音频输出设备，跳过 mixer 初始化（静音运行）
[timing] VM / 会话就绪: 165.3 ms
[timing] 窗口创建完成: 173.1 ms
[timing] 首帧上屏（界面可见）: 240.6 ms
```

---

## 六、回归防护

`tests/startup_probe.py`（24 项）把关键性质钉死：

- monkeypatch `pygame.init` 为抛错，断言启动路径**没有**调用它；
- 最小初始化后 `Clock / event / Surface / 中文字体` 可用，`mixer.get_init()` 仍为 None；
- 无设备时 `mixer.init` 调用 **0 次**、构造 < 200ms、`play()` 仍返回成功；
- 子进程端到端 < 6s（基线 17.1s，退化必然报警）、`PYMRP_TIMING` 首帧 < 1500ms；
- `--frames` 窗口模式退出、`--audio-driver dummy`、`--audio off` 三条路径可用。

---

## 七、顺带修掉的一个测试陷阱：RX 回归的环境漂移

同一轮全套自检里 `gfx_probe` / `net_probe` 各出现 1 项 FAIL：`90 步按键
UC_ERR_READ_UNMAPPED`。用 `git stash` 把本次改动全部撤掉、跑 **HEAD 原版**，
同样失败 → 确认与本次改动无关。

根因：RX 管理器运行时会在 `runtime/mythroad/` 下自建 `brw/`、`cookie/`、
`app240320/`、`*.sid` 等缓存目录。这些是**上一次跑出来的结果**，下一次的
目录枚举和固定 90 步按键序列就会走进完全不同的分支，实测崩在 RX 应用
自己的代码 `PC=0x2E26AE` 读野指针 `0xF82D4AE8`（反复 `mr_open("mythroad/")`
把目录当文件打开）。属于应用对目录项的容错问题，不是图形/网络层的回归。

修法：新增 `tests/rx_env.py`，为这两个探针构造**固定隔离运行环境** ——
只复制 `cfunction.ext` + `mythroad/*.mrp`，不带任何应用自建缓存目录。
`gfx_probe` / `net_probe` 改用 `make_rx_env()`，跑完 `cleanup()`。
现在两者稳定全绿（gfx 21/21、net 57/57，重复跑两次结果一致），
而且 DSM 刷新采样更充分（211 次，其中局部 194 次）。

> 教训：**用真实运行目录做确定性回归 = 用上一次的输出当这一次的输入**。
> 涉及文件系统遍历的用例必须用隔离快照。

---

## 八、边界与后续

- `waveOutGetNumDevs()` 只回答「有没有 waveform 输出设备」，不等于
  「WASAPI 一定能打开」。有设备但 WASAPI 失败的环境仍会慢，用
  `--audio-driver fast` 走 DirectSound 绕开。
- 非 Windows 平台不做探测，保持 SDL 默认行为；macOS/Linux 上若有类似
  蓝牙设备枚举卡顿，需要另做平台特定的快速探测。
- `PYMRP_TIMING` 的 0 点是 `main()` 入口，不含 Python 解释器启动与
  `import pygame` 之外的进程开销，所以数值比 wall clock 小。
- 有音频设备的机器上，`mixer.init()` 仍在启动时同步执行，通常几十毫秒；
  若某天出现新的慢设备，下一步再考虑「首次播放时惰性初始化」。
- 同一轮还加了 Windows **DPI 感知**（`PER_MONITOR_AWARE_V2`），见
  [18 §一](18-高分屏缩放与退出收尾.md#一缩放为什么糊两个独立的放大)。

对比图：`mrp_emu/out/startup_perf_compare.png`。
