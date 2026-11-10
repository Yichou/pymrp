# MRP 模拟器（Python 实现，UI 模拟 MTK 直板机）

用 **Python + Unicorn** 复刻 [vmrp](https://github.com/vmrp/vmrp) 的 MRP 模拟器。
`.mrp` 里是 ARM 机器码，不是脚本 —— 本项目用 QEMU 的 CPU 核心（unicorn）执行它们，
Python 负责实现 mythroad 层需要的 198 个平台 API，并用 pygame 画出一台可点击的
MTK 直板机。

## 快速开始

```bash
pip install -r requirements.txt
python tools/fetch_runtime.py    # 抓取 vmrp 官方运行时（含 cfunction.ext + 9 个游戏）
python run.py                    # 直接进 dsm_gm 启动器菜单（自动探测，推荐）
```

Windows 双击 `run.bat` 效果同上。等价的显式写法：

```bash
python run.py runtime/mythroad/dsm_gm.mrp --workdir runtime
```

`--workdir` 必须是 `runtime`，因为 `dsm_gm.mrp` 内部用相对路径
`mythroad/xxx.mrp` 去枚举游戏，工作目录错了就会看到空列表。

想直接跑某个游戏也可以指定文件（多数游戏仍需经启动器打开，见下）：

```bash
python run.py runtime/mythroad/box.mrp   # 推箱子
```

## 单文件运行（.pyz）

```bash
python build_pyz.py        # 打包 mrp_emu.pyz（约 37 KB，纯代码）
python mrp_emu.pyz         # 双击 run_pyz.bat 同效
```

- `.pyz` 只含代码，**runtime/（cfunction.ext + 字库 + 游戏）不打包**，
  和 pyz 放同一目录或当前目录即可，也支持 `--workdir` 指定。
- 第三方依赖（unicorn / pygame / numpy）需要 `pip install -r requirements.txt`。
- 重新打包前改代码，跑 `python build_pyz.py` 即可，秒级完成。

## 运行真实 MRP 前的必要准备

MRP 的启动链路是：

```
cfunction.ext (ARM 版 mythroad 层，331KB)
        │  由它解析 .mrp 包、加载包内 ext、调度事件与绘制
        ▼
dsm_gm.mrp (启动器) ──► 选择游戏 ──► mrc_init / mrc_event / mrc_timer
```

所以除了 `.mrp` 本身，还需要 `cfunction.ext` 和 mythroad 的资源文件。
`tools/fetch_runtime.py` 会从 vmrp 官方发行包里解出 `cfunction.ext`、
GB16 字库和 9 个经典游戏（推箱子、俄罗斯方块、雪人兄弟等）到 `runtime/`。

入口名自动判断：`dsm_gm.mrp` 用 `start.mr`，其它 mrp 用 `cfunction.ext`；
也可以 `--ext start.mr` 手动指定。

> 注意：游戏类 mrp（如 box.mrp）一般要经启动器菜单打开，直接
> `start_dsm(box.mrp)` 会报 `read file cfunction.ext err code=3006`，
> 这是斯凯的包结构决定的，不是模拟器 bug。

## 键位

> 点屏幕时，屏幕坐标会通过 `mr_event(MR_MOUSE_DOWN/UP/MOVE, x, y)` **原样**
> 送进虚拟机，与 vmrp 的 `main.c` 完全一致（不做任何按键模拟）。
> 大多数 2008 年的 MTK 应用并不处理触摸事件，点了没反应是应用自身的限制。
> 若想用鼠标点屏幕来操作这类老应用，可加 `--touch nav`（可选辅助，非默认）。

| 实体键 | 鼠标 | 键盘 |
|---|---|---|
| 左软键 | 点击 | **左 Ctrl** / 右 Ctrl / F1 |
| 右软键 | 点击 | **右 Alt** / 左 Alt / F2 |
| 五向导航 | 点击 | 方向键 |
| OK | 点导航中心 | 回车 |
| 拨号 / 挂断 | 点击 | — / Esc |
| 数字键盘 | 点击 | 0-9、`*`、`#` |
| 清除 | — | Backspace |

> 左右两个 Ctrl 都是左软键、左右两个 Alt 都是右软键（双手握持时更顺手），
> F1/F2 保留为等价入口。修饰键本身有 KEYDOWN/KEYUP，所以**长按软键**也支持。
> Windows 的 `AltGr`（右 Alt）会同时伪造一个左 Ctrl，已自动识别并忽略，
> 不会一次按出左右两个软键；`Ctrl+Shift` / `Ctrl+Win` 等组合也不当软键。
> `Ctrl+Q` 仍是退出窗口（退出前会先松开已按下的软键）；
> `Alt+F4` / `Alt+Tab` 是系统级快捷键，会被 Windows 抢走，用 F2 或点机壳代替。

按 F12 或 `--screenshot 输出.png` 截图；`--stats` 在退出时打印 API 调用统计。
`python tests/keymap_probe.py` 可验证这套映射（37 项，含真实按键送达虚拟机）。

## 声音

MRP 有两条完全不同的声音通路，都已实现。签名与常量以 SKYENGINE 官方
移植手册（`SKYENGINE API 参考手册.chm`）和原版 `mrporting.h` 为准。

### 1. mr_playSound —— 一次性给全量数据

```c
int32 mr_playSound(int type, const void *data, uint32 dataLen, int32 loop);
```

`data` 是**模拟内存里的指针，不是文件名**——应用总是先 `mr_open`/`mr_read`
把音频读进内存再传过来。`type` 见 `MR_SOUND_TYPE`：

| type | 含义 | 模拟器 |
|---|---|---|
| 0 | MIDI | 内置 SMF 解析 + 波表合成 |
| 1 | WAV | RIFF 解析，8/16/24/32bit，自动重采样 |
| 2 | MP3 | 走 `pygame.mixer.music`，解码失败则静默 |
| 3 | PCM（8K） | 分段流式，见下 |
| 4 | M4A；老枚举里是 PCM | 按 PCM 处理 |
| 5 / 6 | AMR / AMR-WB | 编解码不在模拟范围，返回失败 |

> 枚举有历史包袱：老版 `mrporting.h` 是 5 个值（AMR=3、PCM=4），vmrp 是
> 7 个值（PCM=3、M4A=4）。两边在 3/4 上打架，所以用数据头判定——AMR 一定
> 以 `#!AMR` 开头，其余按 8K 裸 PCM 处理。

MIDI 是重点。Windows 上 SDL2_mixer 没有 MIDI 解码器，所以自己写了解析器
（`audio/midi.py`）和波表合成器（`audio/synth.py`）：按 GM 音色家族选波形
与 ADSR 包络，鼓通道走噪声/低频扫频。合成结果按 md5 缓存，同一段音乐只
渲染一次（1.5 秒的曲子实测 3~5ms）。也支持 iMelody（`.imy`，MTK 老铃声）。

### 2. mr_platEx 201x~216x —— 有状态的流媒体播放器

这才是"流媒体"那条路：一台按音频类型分路的播放器，应用自己控制播放、
暂停、定位、查进度。

| code | 功能 |
|---|---|
| 201x | 设备初始化 |
| 202x | 加载文件（input = 文件名指针） |
| 203x | 加载内存缓冲（`LOAD_AUDIO_DATA_REQ`） |
| 204x | 播放（`struct{cb, loop, block}`） |
| 205x / 206x | 暂停 / 继续 |
| 207x | 停止 |
| 208x | 关闭设备 |
| 209x | 查状态（返回 `MR_PLAT_VALUE_BASE + PLAY_STATE`） |
| 210x / 211x | 定位（秒 / 字节偏移） |
| 212x | 总时长（写 `T_MEDIA_TIME{int32 pos}`） |
| 213x / 215x | 当前进度 |
| 216x | 释放 |
| 222x~225x | 多通道加载/播放/停止/释放（只支持 WAV、MIDI） |

`x` 是 `T_MEDIA_TYPE`：MIDI=1、WAVE=2、MP3=3、AMR=4、PCM=5、M4A=6。
所以 `2011` 是初始化 MIDI 设备，`2042` 是播放 WAVE。

状态机与手册的 `PLAY_STATE` 一致：IDLE(1001) → INITED(1002) →
LOADED(1003) → PLAYING(1004) / PAUSED(1005)。

不用 `pygame.mixer.music` 的原因：它是全局单例，pause/resume/seek 会和
`mr_playSound` 打架，而且 MIDI 在上面根本没有解码器。这里自己持有 PCM
数组 + 专用 Channel，seek 就是重新切片播放，行为可控且跨平台一致。

### 3. mr_plat(102/103) —— PCM 环形缓冲直写

最底层的模式：应用自己往内存里写 PCM，每写一段调 `mr_plat(102, addr)`
告诉驱动位置，驱动按时推进播放点，应用再用 `mr_plat(103)` 查回来算还剩
多少空间可写。

### 开关

```bash
python run.py --audio on         # 强制开启
python run.py --audio off        # 完全静音
python run.py --pcm-rate 16000   # PCM 流采样率（默认 8000，见 mrporting.h 的 //8K）
python run.py --audio-driver fast   # Windows 走 DirectSound，跳过 WASAPI 慢枚举
```

没有音频设备时自动降级为静音，但 API 仍返回成功——老应用遇到失败会反复
重试，把日志刷爆。

**启动性能**：程序只初始化 `display` + `font` 两个 SDL 子系统，并先用
winmm 快速判断有没有音频输出端点；无声卡时不会去调 `pygame.init()` /
`mixer.init()`（这两者在 SDL 2.28 上各要卡 8 秒）。诊断开关：

```bash
PYMRP_TIMING=1 python run.py --frames 3   # 打印各阶段耗时，跑 3 帧自动退出
```

`--frames N` 在窗口模式也生效（便于计时与自动化截图）；设计依据见
`docs/17-启动性能：SDL初始化与音频设备探测.md`。

## 架构

```
mrp_emu/
├── consts.py          内存布局 / 事件码 / 键值（对齐 vmrp）
├── memory.py          8MB 模拟内存（unicorn 零拷贝共享）+ first-fit 分配器
├── vm.py              Unicorn ARM 引擎：加载 cfunction.ext、mr_extHelper、事件泵
├── bridge.py          函数表机制：槽位地址 = syscall 号，UC_HOOK_CODE 拦截
├── fs.py              沙箱文件系统（mrp 的 open/read/write 全部限制在工作目录）
├── gfx.py             RGB565 帧缓冲 + 系统字体叠加层
├── api/
│   ├── impl.py        平台 API 实现（内存/文件/图形/时间/系统…）
│   ├── mrtable.py     mr_table：146 个槽位，偏移与 vmrp 完全一致
│   └── dsmfuncs.py    dsm_require_funcs：51 个槽位（mythroad 的平台接口）
├── ui/
│   ├── skin.py        机身皮肤（JSON，可自定义机型；v2 扁平化导航区）
│   ├── phone.py       MTK 直板机矢量绘制 + 键盘命中测试
│   └── launcher.py    MTK 桌面 / 九宫格 / 游戏中心
├── cli.py             主循环
└── tools/fetch_runtime.py
```

### 桥接原理（与 vmrp 相同）

1. 在模拟内存里放两张"函数表"，每个槽位 4 字节；
2. 每个槽位里写入**它自己的地址** —— MRP 侧 `ldr` 出地址后 `blx` 过去；
3. PC 落在槽位上时被 `UC_HOOK_CODE` 拦截，Python 用 R0-R3/栈当参数、
   R0 当返回值，最后把 PC 改成 LR 模拟函数返回。

等于用"可执行地址"当 syscall 号，因此 **cfunction.ext 不需要任何修改**。

### 内存布局（与 vmrp 一致，不可改动）

| 区域 | 地址 | 大小 |
|---|---|---|
| 代码段（cfunction.ext） | 0x80000 | 1MB |
| 栈 | 0x180000 | 1MB |
| 堆（my_mallocExt） | 0x280000 | 6MB |

### r9(SB) 寄存器切换

r9 是 ARM 的静态基址寄存器，在 MRP 体系里指向「当前 ext 的全局变量区」
（`mr_c_function_P->start_of_ER_RW`）。跨层切换由 **cfunction.ext 内部的
`asm_*` 汇编桩**（`mythroad/fixR9.c` + `genR9R10.js` 生成）自己完成，
它们是真实的 ARM 指令，在本模拟器里照常执行——宿主不需要替它切换。

宿主侧只负责两件事（已实现在 `vm.py`）：

1. `_mr_c_function_new` 把 P 写到 `CODE_ADDRESS+4`，ext 的 fixR9 机制靠
   `*(mr_c_function_load - 4)` 找回上一级的 P；
2. 凡是**从宿主直接跳进 ARM 的回调**（不经 `mr_extHelper` 的路径，例如
   未来的网络异步回调），必须手动保存/改写/恢复 r9 —— 用 `vm.call_arm()`，
   它对应 vmrp 的 `bridge_dsm_network_cb` 语义。

实测见 `tests/r9_trace.py`：ARM 执行期间 r9 恒等于 `P->ER_RW`
（12k+ 条指令采样零偏差），切换完全在 ARM 侧闭环。

## 自检

```bash
python tests/selftest.py
python tests/audio_probe.py       # 声音全链路
python tests/key_probe.py         # 按键与触摸
python tests/net_probe.py         # 网络 57 项（回环 TCP/UDP/DNS/cmwap/回调）
python tests/gfx_probe.py         # 图形 21 项（DSM 脏矩形语义 + RX 花屏回归，隔离运行环境）
python tests/cookie_probe.py      # 曲奇 35 项（低地址映射/GBK 容错/短名/c2u/真实 300 帧）
python tests/skin_probe.py        # 皮肤 50 项（导航区几何/配色采样/命中/按下态/旧 JSON 兼容）
python tests/startup_probe.py     # 启动 24 项（最小 SDL 初始化/无声卡静音/端到端 <6s）
python tests/exit_probe.py        # 退出 23 项（mr_exit 收尾：停声音/关 socket/关句柄/回桌面）
python tests/crash_probe.py       # 崩溃 15 项（MRP 野指针隔离：崩溃不带走模拟器）
python tests/fmt_probe.py        # 格式化 44 项（sprintf 格式覆盖/浮点/长度修饰符/返回值字节数）
python tests/table_probe.py      # 槽位表 11 项（与 mrpoid 官方表的差异清单）
python tests/legacy_net_probe.py  # DNS 覆写 / WAP 代理 51 项（纯回环）
python tests/legacy_net_probe.py --online   # 55 项，含复刻服务器只读探针
python tests/rx_gfx_trace.py      # 诊断工具：RX 90 步按键的绘图调用与离屏缓冲导出
```

> 换机型外观编辑 `runtime/skin.json` 即可（几何/配色/键位全外置）；删掉该文件
> 会自动重建默认皮肤。设计依据与自定义约束见 `docs/16-皮肤系统与导航区扁平化.md`。

> **高分屏缩放**：程序已做 Windows DPI 感知（PER_MONITOR_AWARE_V2），并把机壳
> 改成**整数倍矢量重绘**（不是拉伸成品图），所以 `--scale 2` 下文字与圆盘是
> 物理像素级锐利的。`--scale` 只认整数倍；非整数倍缩放必然糊。
> 见 `docs/18-高分屏缩放与退出收尾.md`。

> 图形花屏排查用 `tests/rx_gfx_trace.py`：无窗口跑真实 RX 管理器，产出
> `out/rx_trace_*_calls.txt`（全部桥接调用与 `drawBitmap` 参数）、
> `*_dsmbuf.png`（DSM 离屏全屏缓冲）与逐帧截图。
> 加 `PYMRP_FROM_PYZ=1` 可从 `mrp_emu.pyz` 加载代码复测打包产物。

`selftest.py` 用硬编码 ARM 机器码直接调用桥接槽位，验证：ARM 执行、内存
共享、参数/返回值传递、文件系统、图形输出、UI 命中测试。

`audio_probe.py` 分两层验证音频：纯 Python 层测解析/合成/缓存/状态机，
再用人工构造的 ARM 机器码调 `mr_playSound`(0x0E4)、`mr_plat`(0x094)、
`mr_platEx`(0x098) 三个槽位，端到端确认"ARM 调用 → 宿主解码 → 渲染出
非零 PCM"整条链路。

## 已实现 / 未实现

- **已实现**：内存管理、字符串、文件系统（含目录枚举）、RGB565 显示、
  定时器、时间日期、系统信息、随机数、按键事件、**声音全链路**
  （mr_playSound / mr_platEx 流媒体播放器 / mr_plat PCM 环形缓冲）、
  **网络全链路**（TCP/UDP/DNS/cmwap/WAP 代理/CONNECT 隧道/ARM 异步回调）
  等约 130 项。
- **占位（返回失败但不崩溃）**：MD5、短信、电话本、相机/图层/图片解码、
  `mr_getCharBitmap`、菜单/控件类。需要时在 `api/impl.py` 里补。
- **明确不支持**：AMR / AMR-WB / M4A / AAC 解码器。这些需要专门的编解码
  实现（AMR 是语音编码，不是通用音频），不在模拟范围内，调用时返回失败
  并打日志，不会假装成功。

## 网络与已停运的斯凯服务器

斯凯官方服务器全停了，但老 MRP 的流量可以接回来。默认行为：

```bash
python run.py                                          # 默认已接管 3 个老域名 + 内置 WAP 代理
python run.py --dns-map ""                             # 清空覆写，按系统 DNS
python run.py --dns-map "spd.skymobiapp.com->127.0.0.1:8088"  # 指到自己的复刻服务
python run.py --dns-map "10.0.0.172->159.75.119.124:13230"    # 网关直连、绕开代理
python run.py --wap-proxy off                          # 不接管 10.0.0.172
python run.py --net-proxy http://127.0.0.1:7890        # TCP 出站走 Clash（可选）
```

默认把 `rop/spd.skymobiapp.com`、`wap.skmeg.com` 覆写到
`159.75.119.124`（open-skyengine 的复刻服务，2026-11-10 实测在线）；
MRP 连 `10.0.0.172` 旧 cmwap 网关时由内置 WAP 代理接管，支持绝对 URL
改写、`Host` / `X-Online-Host` 和 `CONNECT` 隧道。完整逆向见
`../docs/14-斯凯服务器复活：DNS覆写与WAP代理.md`。

> 该 IP 是第三方服务，不是本项目资产；随时可能下线或改策略。
> 我们只做客户端接管，服务端 CGI 不在本项目范围。

## 已知边界

- 必须自备 `cfunction.ext`（斯凯的 mythroad 层，见上文获取方式）。
- unicorn 2.x 才支持 `mem_map_ptr`（零拷贝共享内存）；旧版本自动回退到
  手动同步模式，速度会慢一些。
- 屏幕分辨率固定 240×320（RGB565）。要改分辨率需要连 `cfunction.ext`
  的假设一起改，不是改一个常量就行。
