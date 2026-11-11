# 11 · PymRP 实现对照

本仓库 `mrp_emu/` 的实现现状。配套测试在 `tests/`，全部可通过。

## 1. 架构模块

```
mrp_emu/
├── consts.py            常量（键值/事件/文件/声音/内存布局）—— 以头文件为准
├── memory.py            8MB 内存 + first-fit 分配器 + 零拷贝共享 + GBK 容错 cstr
├── bridge.py            函数表 + UC_HOOK_CODE 拦截（syscall 机制核心）
├── vm.py                Unicorn 封装：run_code / 事件 / timer / r9 防御
│                        + 低地址 ROM 映射（0x0–CODE_ADDRESS）
├── fs.py                虚拟文件系统（路径沙箱 + 相对路径容错）
├── catalog.py           MRP 头解析 + 在线/本地索引 + safe_run_name 短名接管
├── gfx.py               RGB565 帧缓冲 + 紧凑位图 blit + DSM 脏矩形同步 + 字体缓存
├── app.py               App 门面（fs/gfx/audio 组装）+ shutdown_session 统一收尾
├── cli.py               主循环、键鼠输入、截图、统计、最小 SDL 初始化、启动打点
├── api/
│   ├── mrtable.py       mr_table 146 槽（111 函数 + 35 数据槽）
│   ├── dsmfuncs.py      dsm_require_funcs 51 槽（全实现）
│   └── impl.py          API 实现（真实现 + 礼貌占位）
├── audio/               声音子系统
│   ├── midi.py          SMF 解析（VLQ/running status/tempo map）+ iMelody
│   ├── synth.py         numpy 波表合成（GM 16 家族 + 鼓）
│   ├── wav.py           RIFF 解析 + 重采样
│   ├── stream.py        PCM 分段流（攒块/无缝拼接/积压丢弃）
│   ├── media.py         mr_platEx(201x~225x) 状态机
│   └── mixer.py         AudioEngine 门面 + md5 缓存 + 无音频设备快速跳过
└── ui/
    ├── skin.py          JSON 皮肤加载（v2 扁平化导航区几何/配色 + scaled_skin 整数倍缩放）
    ├── phone.py         MTK 直板机机身 + 触控命中 + 坐标直通 + 矢量重绘（scale=k）
    └── launcher.py      MTK 桌面 / 九宫格 / 游戏中心（240x320）
```

约 5500 行核心代码 + 1500 行测试。

## 2. API 覆盖度

| 表 | 槽位数 | 构成 | 状态 |
|---|---|---|---|
| `mr_table` | 146 | **111 个函数** + **35 个数据槽** | 函数全部有处理（真实现或占位）；数据槽启动时按 MAP_DATA 语义填值 |
| `dsm_require_funcs` | 51 | 回调/事件入口 | 全实现 |

> 数据槽 ≠ 函数：`mr_screenBuf`、`mr_soundOn`、`LG_mem_base` 这类是 ARM 侧直接读写的
> **全局变量**，由启动器填值或由实现回写，不经过函数调用。把它们当"未实现的函数"
> 是常见误判。

### 真实现（有完整行为）

内存、文件系统全套（含目录枚举）、RGB565 显示（**两条 drawBitmap 路径分开**：
`mr_drawBitmap` 紧凑位图 / `dsm_drawBitmap` 全屏脏矩形同步，见 [06 §1.3](06-图形与图层专题.md#13-同名陷阱两条-drawbitmap-路径的-stride-不同a-级源码--实测)）、
定时器、时间日期、系统信息、
随机数、按键/触摸事件、`mr_playSound/stopSound`（MIDI 合成 + WAV + PCM 流）、
`mr_plat(102/103/1302)`、`mr_platEx(201x~216x, 222x~225x)` 状态机、UI 控件骨架、
**网络 socket 全家**（TCP/UDP/DNS/cmwap/非阻塞状态机/ARM 异步回调，见
[13 网络模块](13-网络模块与内存健壮性.md)）、`mr_platEx(1204)` 路径切换。

### 占位（返回失败/IGNORE，不崩溃）

MD5、短信、电话本、相机/录音、图层系统、图片解码、
`mr_getCharBitmap`（唯一未实现的常用函数）、天气/闹钟/NES。

### 数据槽填值示例

```
mr_screen_w = 240        mr_screen_h = 320       mr_screen_bit = 16
mr_soundOn  = 1          LG_mem_base/len/end     指向堆区
pack_filename / start_filename                       当前包名与入口
```

## 3. 桥接机制要点

- 槽位写**自身绝对地址**，`UC_HOOK_CODE` 只挂函数表所在页；
- 拦截时：参数读 `r0-r3`（第 5 个起走栈），返回值写 `r0`，`PC ← LR` 模拟 ret；
- `vm.ext_helper()` 进出保存/恢复 r9（防御）；`vm.call_arm()` 完整复刻
  `network_cb` 语义（保存 r9 → 切 `P->ER_RW` → 调用 → 恢复），供未来异步回调使用。

## 4. 测试体系

| 测试 | 断言数 | 验证什么 |
|---|---|---|
| `selftest.py` | ~20 | 硬编码 ARM 机器码调真实槽位：执行/内存/文件/图形/UI 命中 |
| `key_probe.py` | 26 | 常量表对齐、触控命中、键值翻译、按键后画面变化 |
| `touch_probe.py` | 11 | 触摸坐标经 `mr_event` 原样到达 `dsm_event` 内存 |
| `audio_probe.py` | 70 | MIDI/WAV 解析、合成、缓存、PCM 流、状态机、**ARM 端到端**、FFT 音准 |
| `r9_probe.py` / `r9_trace.py` | — | r9 状态探针与执行期采样证明 |
| `launch_probe.py` | — | 端到端：启动器 → 选推箱子 → 标题画面 |
| `gfx_probe.py` | 21 | DSM 脏矩形 stride 语义 + RX 花屏回归（隔离运行环境） |
| `net_probe.py` / `legacy_net_probe.py` | 57 / 51 | 回环网络、ARM 回调、DNS 覆写与 WAP 代理 |
| `cookie_probe.py` | 35 | 低地址 ROM 映射 / GBK 容错 / 安全运行名 / c2u / 真实曲奇 300 帧 |
| `skin_probe.py` | 50 | 导航区几何（v2.1 按键 58×50）/ 配色采样 / 命中 / 按下态 / 旧 JSON 兼容 |
| `startup_probe.py` | 24 | 最小 SDL 初始化、无声卡快速静音、端到端启动 <6s、首帧打点 |
| `exit_probe.py` | 23 | mr_exit 槽位、shutdown_session 三件套、幂等、cli 消费分支、端到端退出 |
| `crash_probe.py` | 15 | cli 无裸调 VM 调用、真实三国志崩溃捕获、崩溃后干净收尾、端到端崩溃隔离 |
| `rx_env.py`（helper） | — | 为 RX 回归构造固定隔离快照，排除应用自建缓存目录 |
| `fmt_probe.py` | 49 | sprintf 格式覆盖 / 宽度精度 / 浮点 / 长度修饰符 / **返回值字节数** / **ARM 机器码端到端（AAPCS 变参布局）** |
| `table_probe.py` | 14 | 我们的 mr_table 与 mythroad 官方表逐项对齐（0x000–0x07C）、mr_stop_ex、与 mr 层那张表的差异 |

运行：`python tests/xxx.py`（全部无网络依赖，headless 可跑）。
启动耗时诊断用 `PYMRP_TIMING=1 python run.py --frames 3`，
详见 [17](17-启动性能：SDL初始化与音频设备探测.md)。

## 5. 启动命令

```bash
pip install -r requirements.txt          # unicorn pygame numpy
python run.py                            # 自动找 runtime/mythroad/dsm_gm.mrp
python run.py runtime/mythroad/dsm_gm.mrp --workdir runtime   # 显式
python run.py --touch native             # 触摸坐标直通（默认）
python mrp_emu.pyz                       # 单文件版（需先 python build_pyz.py）
```

按键：方向键 / 回车=OK / **Ctrl=左软键、Alt=右软键**（F1,F2 为等价入口）/
Esc=挂机 / F12=截图。Ctrl+Q 退出窗口，AltGr 与 Ctrl+Shift 等组合不会误触发软键。

## 6. 已知边界

- **网络已实现**（见 [13](13-网络模块与内存健壮性.md)、[14](14-斯凯服务器复活：DNS覆写与WAP代理.md)）：
  IPv4 TCP/UDP、DNS 覆写表、cmwap/WAP 代理（绝对 URL 改写 + CONNECT 隧道）、
  非阻塞 connect + `getSocketState`、可选 HTTP CONNECT 出站代理。
  斯凯官方服务器已停运，但 open-skyengine 的复刻服务 `159.75.119.124`
  仍在线（实测 `POST /simpleDownload` 返回 200）；这是第三方服务，不保证长期可用。
  不支持 IPv6 / bind / listen；
- **`mr_getCharBitmap`** 未实现：依赖它的自绘文字应用会缺字（多数应用用内置 GB 字库，不受影响）；
- **MP3/AMR/M4A/AAC** 解码未做（需编解码库），明确返回失败并打日志；
- **运行时文件**（`cfunction.ext`、字库、游戏）不随源码分发在本仓库的 git 中——
  用 `python tools/fetch_runtime.py` 从 vmrp 发行包自动获取。
- **曲奇/冒泡类应用**还依赖 `mythroad/app240320/` 运行时资源包
  （`resmrp.mrp`、短名图标缓存、`rollmsg.dat`…）。真机由手机预置或首次联网下发，
  斯凯服务器停运后无法同步；缺了不影响主界面，但会打 `[fs] 打开失败`。
  详见 [15 §七](15-曲奇启动器崩溃复盘.md#七遗留仍缺的运行时资源不是模拟器的-bug)。

## 7. 二次开发指引

| 想做什么 | 看哪里 |
|---|---|
| 补一个 `mr_plat`/`mr_platEx` code | `api/impl.py` 的 `mr_plat`/`mr_platEx` 分支 + 对应手册页 |
| 加音频格式 | `audio/mixer.py` 的 play 分发 + 魔数判定（注意 [08 §1.5](08-陷阱清单.md#15-mr_sound_type-两版枚举冲突)） |
| 改键值映射 | `consts.py`（先读 [09 §4](09-常量速查.md#4-键值-️️最高危区)）+ 跑 `key_probe.py` |
| 换机型外观 / 改导航键样式 | `runtime/skin.json`（几何/配色全外置）+ [16 §五](16-皮肤系统与导航区扁平化.md#五自定义皮肤) |
| 解包改资源 | `tools/mrp_pack.py` + [03 包格式](03-MRP包格式规范.md) |
