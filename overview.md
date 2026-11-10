# MRP 模拟器（Python）— 任务总览

**任务**：参考 https://github.com/vmrp/vmrp ，用 Python 实现一个 MRP 模拟器，
UI 模拟 MTK 直板机。

## 结果：真实 MRP 已跑通 ✅

用 vmrp 官方发行包里的 `cfunction.ext`（ARM 版 mythroad 层）+ `dsm_gm.mrp`
启动器实测，应用菜单界面正常渲染（位图图标、GB 字库文字、软键条、列表高亮），
200ms 定时器与事件循环工作正常。

代码位置：`mrp_emu/`（工程根），截图在 `mrp_emu/out/`。

## 技术要点

- **MRP = ARM 机器码**：用 Unicorn（QEMU 内核）执行，与 vmrp 官方同方案；
  Python 的 8MB 模拟内存通过 `mem_map_ptr` 与引擎零拷贝共享。
- **桥接机制**（复刻 vmrp bridge.c）：两张函数表 146 + 51 槽位，每个槽位写入
  自身地址，ARM `blx` 进来被 `UC_HOOK_CODE` 拦截，用 R0-R3/栈当参数、R0 当
  返回值、PC←LR 模拟 ret —— 等于用可执行地址当 syscall 号，cfunction.ext 零修改。
- **内存布局与 vmrp 完全一致**：代码段 0x80000(1MB) / 栈 0x180000(1MB) / 堆 0x280000(6MB)。
- **UI**：pygame 矢量绘制的 MTK 直板机（机身渐变、五向导航、软键、12 键盘、
  听筒/麦克风、屏幕反光），几何外置为 JSON 皮肤可换机型；鼠标点击 + 键盘双输入。
- **文件系统**：MRP 的 open/read/write 全部沙箱在工作目录内，防路径穿越。

## 声音（2026-11-09 补完）

MRP 有两条完全不同的声音通路，都已实现，依据 SKYENGINE 官方移植手册
与原版 `mrporting.h` 校正过签名和常量。

**通路一：`mr_playSound(type, data, dataLen, loop)`** —— 一次给全量数据。
`data` 是模拟内存指针而非文件名。MIDI(0) 由自研 SMF 解析器 + numpy 波表
合成器处理（Windows 的 SDL2_mixer 没有 MIDI 解码器，只能自己合成），
WAV(1) 走 RIFF 解析 + 重采样，PCM(3) 走流式，MP3(2) 借 mixer.music。
合成结果按 md5 缓存，1.5 秒曲子渲染约 3~5ms。

**通路二：`mr_platEx(201x~216x)` 流媒体播放器** —— 有状态：初始化 / 加载
文件 / 加载缓冲 / 播放 / 暂停 / 继续 / 停止 / 查状态 / 定位 / 总时长 /
当前进度 / 释放，另有 222x~225x 多通道。`x` 是 `T_MEDIA_TYPE`（MIDI=1、
WAVE=2、MP3=3、AMR=4、PCM=5），状态机与手册 `PLAY_STATE` 一致。

**通路三：`mr_plat(102/103)`** —— PCM 环形缓冲直写，应用自己往内存里写，
驱动按时推进播放点。

不支持 AMR / AMR-WB / M4A / AAC 解码（需要专门编解码器），明确返回失败并
打日志，不假装成功。

## 验证

- `tests/selftest.py`：用硬编码 ARM 机器码直接调桥接槽位，验证 ARM 执行、
  参数/返回值传递、内存共享、文件系统、图形输出、UI 命中测试 —— 全部通过。
- `tests/audio_probe.py`：70 项断言。纯 Python 层测解析/合成/缓存/状态机，
  再用人工构造的 ARM 机器码调 `mr_playSound`(0x0E4)、`mr_plat`(0x094)、
  `mr_platEx`(0x098) 槽位，端到端确认「ARM 调用 → 宿主解码 → 渲染出非零
  PCM」。含 FFT 音高校验（A4 精确 440Hz，最大偏差 11 音分）。
- 实跑 `dsm_gm.mrp`：`start_dsm -> 0`，枚举 9 个游戏，read×214/seek×207，
  菜单界面截图正常。

## 使用

```bash
pip install -r requirements.txt
python tools/fetch_runtime.py             # 需联网，已下载过则用缓存
python run.py runtime/mythroad/dsm_gm.mrp # 启动器菜单（方向键+OK 选择游戏）
python run.py                             # 自动探测并进启动器
python run.py --audio off                 # 静音运行
python tests/selftest.py                  # 桥接自检
python tests/audio_probe.py               # 音频自检（70 项）
python tools/midi2wav.py --demo           # 生成 out/demo_tone.wav 可直接试听
```

## 边界与说明

- 游戏类 mrp（box.mrp 等）需经启动器菜单打开，直接 start_dsm 会报
  code=3006，这是斯凯包结构决定的（包内入口文件名不同），不是 bug。
- 网络/MD5/短信类 API 为占位（返回失败不崩溃），需要时在
  `api/impl.py` 补实现。
- 声音已完整实现三条通路，但 AMR/M4A/AAC 解码器不在范围内。
- 已实测注意：本机 `python` 命令是 3.13，依赖装在 3.12；`run.py` 会用
  当前解释器，若报缺依赖先 `pip install -r requirements.txt`。

## Git 仓库与知识库（2026-11-10）✅

- 源码已推送：**https://github.com/Yichou/pymrp.git**（main，362 文件 2.5 万行；
  ref//runtime//out 等版权物与大文件不入库，runtime 可用 fetch_runtime.py 重新获取）。
- `docs/` 知识库：SKYENGINE 手册 288 页全文整理（`docs/api/` 逐页保真 +
  `docs/api/topics/` 12 主题分册，零遗漏）+ 12 篇原理文档
  （00 体系总览 → 11 实现对照），入口 `docs/README.md`。
- **原创成果**：实测解出 MRP 包二进制格式（MRPG 头 / 条目表 / 独立 gzip 条目 /
  裸 RGB565 位图），并用「重打包 → 真实 mythroad 层加载渲染成功」闭环验证。
  工具 `mrp_emu/tools/mrp_pack.py` 支持 list/解包/替换重打包。
- 文档生成管线：`tools/extract_manual.py`（CHM→MD）与 `tools/build_docs.py`
  （主题聚合），手册更新后可一键重生成。
- 仓库 git 代理已固化 Clash 7890（local config），直接 git push 即可。
