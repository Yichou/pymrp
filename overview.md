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

## MTK 真机桌面与游戏中心（2026-11-10）

启动画面改成真正的 MTK 直板机系统界面：开机动画 → 待机桌面（信号/时钟/壁纸）
→ 九宫格菜单 → 游戏中心图标 → ① 在线列表 / ② 本地列表 → 点一行直接开玩，
挂机键回桌面。

- **在线列表 664 个应用**：首次进后台拉 `vmrp.github.io/public/data.txt`
  （站点自己从 MRP 里读出的标题/开发商/描述 NDJSON，362 KB）+ 目录清单，
  落盘 `runtime/cache/online_index.json`，7 天缓存；不逐个下载上百 MB 的包。
- **本地列表**：只读每个 `.mrp` 前 0xF0 字节解头（0x1C 标题 / 0x58 厂商 /
  0x80 描述 / 0x44 appid），字段长度与官方 `.mpr` 编写指南逐字节吻合。
- **一键启动**：在线项按需下载到 `runtime/mythroad/` → 重建干净 VM →
  `start_dsm()`。实测下载的 `2048.mrp` 直接渲染出「开始游戏 / 退出游戏」菜单。
- **重要纠错**：所有 MRP 入口都是 `start.mr`，此前「普通应用用
  `cfunction.ext`」的结论是错的，传错会报 `exit de is nil / init failed`。
  CLI 已改为读包内条目表自动判断并支持换入口重试（`docs/03 §9`）。
- 网络自动读系统代理（Clash 7890），直连失败会探测常见本地代理端口。
- 说明见 [docs/12](docs/12-启动界面与游戏中心.md)，自检
  `tests/launcher_probe.py` 34 项全过（含真实点击 → 启动 → 挂机返回）。

## 使用

```bash
pip install -r requirements.txt
python tools/fetch_runtime.py             # 需联网，已下载过则用缓存
python run.py                             # 开机 → 待机桌面 → 游戏中心
python run.py --boot gamecenter            # 开机直接进游戏中心
python run.py --refresh                    # 强制刷新在线索引
python run.py runtime/mythroad/box.mrp     # 跳过桌面，单跑一个 MRP
python run.py --audio off                 # 静音运行
python tests/selftest.py                  # 桥接自检
python tests/audio_probe.py               # 音频自检（70 项）
python tests/launcher_probe.py             # 桌面/列表/点击启动（35 项）
python tests/net_probe.py                  # 网络（57 项）+ RX 崩溃回归
python tests/keymap_probe.py               # Ctrl/Alt 软键映射（37 项）
python tools/midi2wav.py --demo           # 生成 out/demo_tone.wav 可直接试听
```

## Ctrl / Alt 软键映射（2026-11-10）

| 实体键 | 键盘 |
|---|---|
| 左软键 | **左 Ctrl** / 右 Ctrl / F1 |
| 右软键 | **右 Alt** / 左 Alt / F2 |

`cli.py::_key_name()` 把四个修饰键直接翻译成 `SOFT_L` / `SOFT_R`，
与 F1/F2 走同一条 `press_key()` 链路，游戏里和系统桌面里都生效；
修饰键自身有 KEYDOWN/KEYUP，长按软键也支持。

防误触：Windows 的 AltGr（右 Alt 同时伪造一个左 Ctrl）、`Ctrl+Shift`、
`Ctrl+Win` 组合一律不当软键；`Ctrl+Q` 退出窗口前会先释放按住的软键。
`Alt+F4` / `Alt+Tab` 是系统级快捷键，会被 Windows 抢走，用 F2 代替。
新增 `tests/keymap_probe.py` 37 项全过，含「真实 pygame 事件 → VM 收到
左右软键 press/release」与桌面模式验证。

## 边界与说明

- 早期记录「游戏类 mrp 直接 start_dsm 会报 code=3006，必须经启动器」
  **已被证伪**：真实原因是入口 ext 传错。现在 `box.mrp / tetris.mrp /
  2048.mrp / 火柴谜题 / 丧尸杀戮` 等均可单文件直启，返回 0。
- 部分 MRP 依赖包外资源（字库、插件、存档目录），缺失时只打 `[fs] 打开失败`
  日志，多数仍能进主菜单。
- 网络 socket 全家已实现（见下节）；MD5/短信/电话本/相机/图层/图片解码
  仍为占位（返回失败不崩溃），需要时在 `api/impl.py` 补实现。
- 声音已完整实现三条通路，但 AMR/M4A/AAC 解码器不在范围内。
- 已实测注意：本机 `python` 命令是 3.13，依赖装在 3.12；`run.py` 会用
  当前解释器，若报缺依赖先 `pip install -r requirements.txt`。

## 网络模块与 RX 崩溃修复（2026-11-10）

按 mrpoid `network.c` + vmrp `dl_bridge.c` 补齐 `dsm_require_funcs` 的 11 个
网络底层函数（原来全是返回 `MR_FAILED` 的 stub）：

- `net.py`：10 槽 socket 状态机、TCP/UDP、阻塞/非阻塞 connect、
  `getSocketState`、DNS 缓存与超时、cmwap `10.0.0.172` 代理、
  可选 HTTP CONNECT 出站代理（`--net-proxy` / `PYMRP_NET_PROXY`）。
- 异步 `NETWORK_CB(result, userData)` 排队到主循环，用 `vm.call_arm()`
  手动切 r9 执行（不在 `emu_start()` 里重入）。
- 两张表同名函数参数不同：`dsm_require_funcs` 多一个 `userData`，
  已在 `dsmfuncs.py` 分开别名。

**RX 管理器崩溃**：复现出 `UC_ERR_READ_UNMAPPED @ PC=0x8EF1C`，
capstone 反汇编确认是 ext 内 `strnlen(NULL)`。根因链：浏览根目录 `./..`
→ 旧沙箱拒绝并回 NULL → ext 把 NULL 交给 `sprintf("%s")` → 读地址 0。
真机 0 地址可读，Unicorn 没映射才炸。修复三层：`vm.py` 映射 64KB 零页、
`fs.py` 把 `..` 钳制在 root 内、`impl.py` 完整实现 `mr_platEx(1204)`
（正确写回 `*output` / `*output_len`）；另加非法内存访问诊断钩子与
`--strict-null` 调试开关。90 步真实按键 + 945 次路径切换实测无崩溃。

自检 `tests/net_probe.py` 57 项全过（全部本机回环，不需联网）；原有 6 套
自检无回归。详见 [docs/13](docs/13-网络模块与内存健壮性.md)。

## 斯凯服务器复活：DNS 覆写 + WAP 代理（2026-11-10）

老板指出官方服务器全停了，让看 `open-skyengine/skyengine-flutter`。
把前端仓库 + Rust 子模块 `skyengine-v2` 全部拉下来逆向，结论是**三层**，
不是一台独立代理服务器：

| 层 | 实现位置（skyengine-v2） | 作用 |
|---|---|---|
| DNS 覆写 | `runtime.rs::default_dns_mappings()`、`arm/ext/network.rs::resolve_mapped_host()` | 3 个老斯凯域名 → `159.75.119.124`；前端由商店 `/config` 下发 hosts，经 `skyengine_api_set_dns_map` 注入 |
| 进程内 WAP 代理 | `wap_proxy.rs`（监听 127.0.0.1:0）、`mr/host/network.rs::route_mr_endpoint()` | 接管 `10.0.0.172`，解析绝对 URL / `Host` / `CONNECT`，按覆写表转发 |
| 远端复刻服务 | `159.75.119.124`（未开源） | 重新实现 `simpleDownload` 等斯凯 CGI（TLV 协议见 `test/e2e/simple-download-server.ts`） |

服务端实测（2026-11-10）：`mrp.jysafe.cn` → `159.75.119.124`，nginx/1.30.3，
80/6009 在线；`GET /` + `Host: spd.skymobiapp.com:6009` 被 DNSPod 未备案页 302，
但 **`POST /simpleDownload` 返回 200** —— 复刻 CGI 确实在跑。老域名当前
DNS 已变成 `38.48.128.189` / `135.181.255.27`，所以覆写是必需的。

**pymrp 已接通**：`net.py` 新增 `DEFAULT_DNS_MAP` / `parse_dns_map()` /
`parse_proxy_request()`、三条 `mr_connect` 路由规则、绝对 URL 改写、
CONNECT 隧道 + 自造 200 响应；CLI 新增 `--dns-map` / `--wap-proxy`。
与 Rust 引擎的差异：我们不开监听端口，用「假连接 + 首包改写」实现，
更轻但不支持同一 keep-alive 连接上中途换 Host 的重路由。

验证：`tests/legacy_net_probe.py` 离线 51 项、加 `--online` 55 项全过
（含真实 `POST /simpleDownload` 200）；全部 8 套自检无回归。
完整源码证据、协议字段、边界见
[docs/14](docs/14-斯凯服务器复活：DNS覆写与WAP代理.md)。

> 边界：`159.75.119.124` 是第三方服务、不是我们的资产，随时可能下线；
> 我们只做客户端接管，服务端 CGI 不在本项目范围。

## Git 仓库与知识库（2026-11-10）✅

- 源码已推送：**https://github.com/Yichou/pymrp.git**（main，362 文件 2.5 万行；
  ref//runtime//out 等版权物与大文件不入库，runtime 可用 fetch_runtime.py 重新获取）。
- `docs/` 知识库：SKYENGINE 手册 288 页全文整理（`docs/api/` 逐页保真 +
  `docs/api/topics/` 12 主题分册，零遗漏）+ 13 篇原理文档
  （00 体系总览 → 12 启动界面与游戏中心），入口 `docs/README.md`。
- **原创成果**：实测解出 MRP 包二进制格式（MRPG 头 / 条目表 / 独立 gzip 条目 /
  裸 RGB565 位图），并用「重打包 → 真实 mythroad 层加载渲染成功」闭环验证。
  工具 `mrp_emu/tools/mrp_pack.py` 支持 list/解包/替换重打包。
- 文档生成管线：`tools/extract_manual.py`（CHM→MD）与 `tools/build_docs.py`
  （主题聚合），手册更新后可一键重生成。
- 仓库 git 代理已固化 Clash 7890（local config），直接 git push 即可。

## RX 管理器界面错乱修复（2026-11-10）✅

老板反馈截图：RX 管理器里「RX管理器」标题栏重复出现 3 次、蓝色横条夹斜向噪点、
列表文字错位。已定位并修复，**不是字库/图层/资源缺失问题**。

**根因**：`dsm_require_funcs.drawBitmap` 与 `mr_table.mr_drawBitmap` 同名同签名，
但语义完全不同。前者是「把 DSM 离屏全屏缓冲的脏矩形同步到屏幕」，源行跨度是
**屏宽 240**、`x/y` 同时是源矩形起点；后者才是「贴一块紧凑 `w×h` 位图」。
之前 `api/dsmfuncs.py::ALIAS` 把两者指向同一实现，局部刷新 `(3,61,226,26)`
时按 `w=226` 跨度读，等于把屏顶标题栏贴到每个列表行 → 重复标题栏 + 斜纹。
整屏刷新 `(0,0,240,320)` 时 `w==屏宽` 两种语义恰好等价，所以静止首帧正常、
一滚动就花，非常有迷惑性。mrpoid 源码 `emulator.c:737/808` 与 `dsm.c:1436`
提供了 A 级证据；实测 `fb_addr=0x280000`、`dsm_buf=0x2A8180`，104 次调用中
88 次是局部矩形。

**改动**：

| 文件 | 内容 |
|---|---|
| `mrp_emu/gfx.py` | 新增 `Gfx.refresh_rect()`：按屏宽 stride 取源、只写脏矩形、裁剪/同址/退化处理 |
| `mrp_emu/api/impl.py` | 新增 `dsm_drawBitmap()`，与紧凑位图实现分离 |
| `mrp_emu/api/dsmfuncs.py` | `ALIAS["drawBitmap"]` 改绑 `dsm_drawBitmap` |
| `mrp_emu/tests/gfx_probe.py` | 新增 21 项：绑定检查、stride 语义、紧凑语义敏感性对照、真实 RX 逐次刷新逐像素比对 |
| `mrp_emu/tests/rx_gfx_trace.py` | 新增诊断工具：桥接调用明细、离屏缓冲导出、pyz 加载复测 |
| `docs/06`、`docs/08`、`docs/11`、`mrp_emu/README.md` | 知识库沉淀（源码、实测参数、陷阱条目） |
| `mrp_emu/mrp_emu.pyz` | 重打包 98.1 KB，修复已进入单文件版 |

**验证**：

- `gfx_probe.py` 21/21 通过：真实 RX 90 步按键期间 104 次 DSM 刷新，
  **fb 与离屏缓冲逐像素不一致 0 次**（局部 88 次）；
- 全套回归无退化：`selftest / key / touch / audio / launch / launcher /
  net / keymap / gfx / legacy_net` 全部 rc=0；
- 改动涉及 DSM 全局槽位，特意复测其它真实 MRP：`dsm_gm`（应用列表完整、
  图标/字库/选中高亮正常）、`box`、`tetris` 均正常渲染，无黑屏无花屏；
- 从 `mrp_emu.pyz` 加载代码（`PYMRP_FROM_PYZ=1`）复测 RX，同一帧界面完整；
- 三联对比图 `mrp_emu/out/rx_gfx_before_after.png`：老板截图 / 修复前复现 / 修复后。

**边界**：`mythroad/plugins/embrw.mrp`、`advbar.mrp` 等运行时插件仍缺失，
会打 `[fs] 打开失败` 日志（不影响本界面）；本次修复只针对刷屏语义，
不改动触控、字库、图层系统。
