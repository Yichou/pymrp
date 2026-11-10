# 11 · PymRP 实现对照

本仓库 `mrp_emu/` 的实现现状。配套测试在 `tests/`，全部可通过。

## 1. 架构模块

```
mrp_emu/
├── consts.py            常量（键值/事件/文件/声音/内存布局）—— 以头文件为准
├── memory.py            8MB 内存 + first-fit 分配器 + 零拷贝共享
├── bridge.py            函数表 + UC_HOOK_CODE 拦截（syscall 机制核心）
├── vm.py                Unicorn 封装：run_code / 事件 / timer / r9 防御
├── fs.py                虚拟文件系统（路径沙箱 + 相对路径容错）
├── gfx.py               RGB565 帧缓冲 + 字体缓存
├── app.py               App 门面（fs/gfx/audio 组装）
├── cli.py               主循环、键鼠输入、截图、统计
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
│   └── mixer.py         AudioEngine 门面 + md5 缓存
└── ui/
    ├── skin.py          JSON 皮肤加载
    └── phone.py         MTK 直板机机身 + 触控命中 + 坐标直通
```

约 5300 行核心代码 + 1200 行测试。

## 2. API 覆盖度

| 表 | 槽位数 | 构成 | 状态 |
|---|---|---|---|
| `mr_table` | 146 | **111 个函数** + **35 个数据槽** | 函数全部有处理（真实现或占位）；数据槽启动时按 MAP_DATA 语义填值 |
| `dsm_require_funcs` | 51 | 回调/事件入口 | 全实现 |

> 数据槽 ≠ 函数：`mr_screenBuf`、`mr_soundOn`、`LG_mem_base` 这类是 ARM 侧直接读写的
> **全局变量**，由启动器填值或由实现回写，不经过函数调用。把它们当"未实现的函数"
> 是常见误判。

### 真实现（有完整行为）

内存、文件系统全套（含目录枚举）、RGB565 显示、定时器、时间日期、系统信息、
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

运行：`python tests/xxx.py`（全部无网络依赖，headless 可跑）。

## 5. 启动命令

```bash
pip install -r requirements.txt          # unicorn pygame numpy
python run.py                            # 自动找 runtime/mythroad/dsm_gm.mrp
python run.py runtime/mythroad/dsm_gm.mrp --workdir runtime   # 显式
python run.py --touch native             # 触摸坐标直通（默认）
python mrp_emu.pyz                       # 单文件版（需先 python build_pyz.py）
```

按键：方向键 / 回车=OK / F1,F2=软键 / Esc=挂机 / F12=截图。

## 6. 已知边界

- **网络已实现**（见 [13](13-网络模块与内存健壮性.md)）：IPv4 TCP/UDP、DNS、
  cmwap 代理、非阻塞 connect + `getSocketState`、可选 HTTP CONNECT 出站代理。
  但 2008 年前后的 MRP 服务器几乎全部下线，「接口通」不等于「有服务」；
  不支持 IPv6 / bind / listen；
- **`mr_getCharBitmap`** 未实现：依赖它的自绘文字应用会缺字（多数应用用内置 GB 字库，不受影响）；
- **MP3/AMR/M4A/AAC** 解码未做（需编解码库），明确返回失败并打日志；
- **运行时文件**（`cfunction.ext`、字库、游戏）不随源码分发在本仓库的 git 中——
  用 `python tools/fetch_runtime.py` 从 vmrp 发行包自动获取。

## 7. 二次开发指引

| 想做什么 | 看哪里 |
|---|---|
| 补一个 `mr_plat`/`mr_platEx` code | `api/impl.py` 的 `mr_plat`/`mr_platEx` 分支 + 对应手册页 |
| 加音频格式 | `audio/mixer.py` 的 play 分发 + 魔数判定（注意 [08 §1.5](08-陷阱清单.md#15-mr_sound_type-两版枚举冲突)） |
| 改键值映射 | `consts.py`（先读 [09 §4](09-常量速查.md#4-键值-️️最高危区)）+ 跑 `key_probe.py` |
| 换机型外观 | `runtime/skin.json`（几何/配色全外置） |
| 解包改资源 | `tools/mrp_pack.py` + [03 包格式](03-MRP包格式规范.md) |
