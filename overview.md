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

---

## 曲奇启动器：从崩溃到正常主界面（2026-11-10）

老板贴的「冒泡6.0（线条模拟器提取（曲奇启动）.mrp」日志以
`PC=0x87A24 / @0x15858(2B) / UC_ERR_READ_UNMAPPED` 结束。
**四个问题叠加**，前三个属于模拟器、第四个属于运行环境：

| # | 根因 | 修复 |
|---|---|---|
| 1 | 低地址只映射 `0x0–0x10000`，透明位图 blit 读到野指针 `0x15858` 就终止整个 VM | `vm.py` 低地址映射扩到 `CODE_ADDRESS`（真机 ROM/RAM 语义） |
| 2 | `cstr()` 遇「半个汉字截断的 GBK」整串退化成 latin-1，`冒泡`→`Ã°ÅÝ` | `memory.py` 改 GBK 宽容解码 + 去替换符 |
| 3 | ext 路径缓冲约 32 字节，长中文名必被截断 → 包内 `res_lang0.rc` 报 `code=2002`、深蓝空屏 | `catalog.safe_run_name()` 自动用包头 8.3 短名 `cookie.mrp` 启动，中文名只用于显示 |
| 4 | `mythroad/app240320/` 运行时资源包缺失（斯凯服务器停运） | 非致命，主界面正常；已列清单于 `docs/15 §七` |

反汇编铁证：`0x87A24: ldrh sl,[lr]` + `cmp/strhne/blt` 是逐像素透明 blit 循环；
崩溃时 `r9=0x2A5B74` 正常，排除 r9 切换老坑。只补 `0x10000–0x20000`
会把崩溃从第 0 帧推迟到第 5 帧，必须补满 `0x80000`。

**顺带修正**：`c2u` 槽位按官方 `mr/mr_gb2312.c` 签名重写（返回新分配的
UCS-2 / UTF-16BE 宽串、写 `*size`、可被 `mr_free` 释放）；旧实现把 UTF-8
写进 `err` 指针。曲奇实测未调用该槽位，属潜伏错误。

**改动文件**：`mrp_emu/vm.py`、`memory.py`、`api/impl.py`、`catalog.py`、
`cli.py`；新增 `tests/cookie_probe.py`、`docs/15-曲奇启动器崩溃复盘.md`；
`docs/08 §3.6/§4.5`、`docs/11`、`mrp_emu/README.md` 同步沉淀。

**验证**：`cookie_probe` **35/35**（含真实曲奇 300 帧零异常、帧缓冲
72690/76800 非零、乱码 0 条、`res_lang0` 2002 归零）；全套 **11 个探针 rc=0**；
`mrp_emu.pyz` 重打包 **100.1 KB**，从单文件版跑同样正常。
对比图 `mrp_emu/out/cookie_before_after.png`：左深蓝空屏 → 右完整
冒泡 6.0 九宫格（在线音乐 / 游戏中心 / 下载管理）。

## 导航键区域扁平化改版（2026-11-10）✅

按老板给的参考截图重做机壳导航区。逐像素采样原图（401×190）拿到配色与
比例，再据此重排几何：

| | 优化前 | 优化后 |
|---|---|---|
| 机身 | 300×660 | **300×690**（导航区 122px → 147px） |
| 圆盘 | r=38 金属环 + 空心 OK 圈 | **r=62 扁平圆盘 + 实心 OK 圆（hole=23）** |
| 四角按键 | 72×24 扁条 | **58×59 大圆角方块** |
| 配色 | 强渐变 + 黑描边 | `#292C33` 底 / `#383C45` 软键 / `#46B45D` 拨号 / `#C84335` 挂断，纯色弱渐变 |
| 箭头 | 6px 钝三角 | 实心等腰三角，距圆心 0.725r |

三个关键比值与参考图对齐：圆盘直径/按键高 2.102（参考 2.105）、
OK/圆盘 0.371（参考 0.375）、圆盘/机身宽 0.413（参考 0.399）。圆盘
x 88–212 与左右按键列各留 8px，不重叠；数字键盘整体下移到 y=542。

**改动文件**：`ui/skin.py`（`build_default()` v2 + `load_skin()` 补齐旧 JSON
调色键）、`ui/phone.py`（`_draw_nav` 重写、`_draw_key` 扁平化、新增 `_arrow`）、
`runtime/skin.json` 重建、`tests/selftest.py` 去掉硬编码坐标改从皮肤推导；
新增 `tests/skin_probe.py`（48 项）、`docs/16-皮肤系统与导航区扁平化.md`，
并同步 `docs/11`、`docs/12`、`docs/README.md`、`mrp_emu/README.md`。

**验证**：`skin_probe` **48/48**（几何比例、逐像素配色采样、命中、按下态、
旧皮肤 JSON 兼容）；全套 **12 个探针 rc=0**；`mrp_emu.pyz` 重打包
**101.1 KB**，从单文件版跑 `dsm_gm.mrp` 应用列表正常且新机壳生效。
对比图 `mrp_emu/out/skin_nav_compare.png`（参考 / 前 / 后三联）与
`out/skin_full_compare.png`（整机前后）。

---

## 启动性能：17.1s → 0.85s，以及四角按键压矮

老板反馈「从 pygame 欢迎日志到界面要 20 秒」。逐段计时定位到**两次 8 秒**：

| 阶段 | 优化前 | 优化后 |
|---|---:|---:|
| `pygame.init()`（连带 `SDL_INIT_AUDIO`，WASAPI 枚举） | 8096 ms | 0（不再调用） |
| `AudioEngine` 同步 `mixer.init()` | 8039 ms | 0（无声卡直接跳过） |
| `display.init()+font.init()` | — | **0.3 ms** |
| 端到端 headless / 窗口 `--frames 3` | 17.12 s | **0.85 s / 0.96 s** |
| 首帧上屏（`PYMRP_TIMING`） | — | **240.6 ms** |

关键前提：这台 Windows 机器没有音频输出端点（`waveOutGetNumDevs()==0`）。
试过把 `mixer.init()` 丢后台线程，结果 WASAPI 的 C 调用不释放 GIL，主循环
90 帧被拖到 9.5 秒 —— 否掉。最终方案是**根本不碰 SDL 音频**：
`cli.py::init_pygame_minimal()` 只初始化 display + font；
`audio/mixer.py::_device_probe()` 用 winmm 快速判定无设备就静音降级
（行为与原来「8 秒后失败」一致，只是瞬间完成）。

新增 `PYMRP_TIMING=1` 五段打点、`--audio-driver fast|...`（DirectSound 兜底）、
`--frames N` 窗口模式自动退出。知识库新增
`docs/17-启动性能：SDL初始化与音频设备探测.md`。

**顺带修掉的测试陷阱**：`gfx_probe` / `net_probe` 的 RX 90 步按键偶发崩溃，
用 HEAD 原版代码对照复跑同样失败 → 与本次改动无关。根因是 RX 运行时自建的
`brw/`、`cookie/` 等缓存目录让下一次目录枚举漂移。新增
`tests/rx_env.py` 构造固定隔离快照（只复制 `cfunction.ext` + `mythroad/*.mrp`），
两个探针改用它，稳定全绿且刷新采样更充分（211 次 / 局部 194 次）。

**四角按键**：按老板第二版参考图把 `58×59` 压到 **`58×50`**，上下两排中心
不变、间隙 11px → 20px，圆盘更突出。`runtime/skin.json` 已重建，
`skin_probe` 同步断言（50 项）。

**验证**：全套 **13 个探针 rc=0**（gfx/net 各重复跑 2 次稳定）；
`mrp_emu.pyz` 重打包 **102.5 KB**，从单文件版跑 `--demo --frames 4` 首帧
707ms、`dsm_gm.mrp` 正常。对比图 `out/startup_perf_compare.png`、
`out/skin_keyheight_compare.png`。

**边界**：`waveOutGetNumDevs()>0` 但 WASAPI 仍打不开的环境（远程桌面虚拟声卡）
用 `--audio-driver fast`；非 Windows 不做探测，保持 SDL 默认行为。

---

## 高分屏缩放 + 退出收尾 + 崩溃隔离

老板一次提了三个问题，逐个拆掉：

### ① 缩放发糊（两个独立的放大叠在一起）

| 来源 | 修法 |
|---|---|
| Windows 系统 DPI 拉伸（进程不感知 DPI） | `cli.py::enable_dpi_awareness()` → `PER_MONITOR_AWARE_V2`（实测生效） |
| 我们自己 `smoothscale` 拉伸 300×690 成品图 | 机壳改**整数倍矢量重绘**：`skin.py::scaled_skin()` + `PhoneUI(scale=k)` |

非整数倍缩放无解（像素被打散到半个物理像素），所以 `--scale` 只认整数倍，
`cli` 不再对整帧拉伸，事件坐标直接用物理像素。对比图 `out/zoom_compare.png`：
左=整图拉伸（文字发虚）、右=矢量重绘（笔画锐利）；整机 2x 截图 600×1380。

### ② mr_exit() 之后音乐不停、句柄不关

**根因一句话：`vm.exited` 只被设置，从来没有被消费。** 于是退出后背景音乐继续
放、socket 挂着、文件句柄占着（**句柄号会被下次会话复用**）、界面回不去。

新增统一收尾：`App.shutdown_session()` → 停声音（`AudioEngine.stop_all()`：
音效/PCM 流/流媒体/背景音乐）→ 关 socket（`NetEngine.close_network()`）→
关句柄（`VirtualFs.close_all()`）→ `back_to_home()` 退回系统界面。
cli 主循环每帧检查 `vm.exited` 并触发。

端到端日志：`[vm] 应用调用 mr_exit()` → `[teardown] 已关闭 1 个文件句柄、
10 个 socket` → `[teardown] 应用退出（mr_exit）`。

### ③ 三国志 `PC=0x2FF282` 野指针崩溃

本地 900 帧按键稳定复现（老板日志 `0xCE875143` / 本地 `0xCE87512B`，同一段
代码）。定位结论：**应用侧缺陷** —— 反汇编显示 PC 落进 switch 编译出的跳转表
（数据），即间接跳转目标算错；`mr_platEx(1204)` 与 mrpoid 官方语义一致、
可排除；造 5 个假缺失文件后野指针值一模一样，**不是"读到空数据"**。

模拟器侧做**崩溃隔离**：以前只有 `timer` 有 try，按键路径全裸调 ——
`key_event` 一崩进程直接死。现在所有 VM 调用（`key_event`/`touch_event`/`timer`）
统一走 `guarded`：记录原因 → 收尾 → 退回系统界面，进程退出码仍是 0。

**改动文件**：`cli.py`（DPI 感知、整数倍缩放、`guarded`、exited 消费）、
`ui/skin.py`（`scaled_skin`）、`ui/phone.py`（矢量重绘）、`app.py`
（`shutdown_session`）、`fs.py`（`close_all`）、`audio/mixer.py`（`stop_all`）、
`audio/media.py`（`release_all`）。

**验证**：新增 `tests/exit_probe.py` 23 项、`tests/crash_probe.py` 15 项；
全套 **15 个探针 rc=0**；`mrp_emu.pyz` 重打包 **105.6 KB**，从单文件版跑
`--scale 2` 得到 600×1380 窗口、DPI 感知 `per-monitor-v2`、首帧 970ms。
知识库新增 `docs/18-高分屏缩放与退出收尾.md`，同步 `08/11/16/17`、README。

---

## sprintf 与槽位表：老板问「你是不是没实现 sprintf」

老板在 RX 管理器列表里圈出一个字符 **f**（红箭头），问是不是 sprintf 没实现。
查下来结论分成两半：**那个 f 不是 bug，但 sprintf 确实有真问题。**

### 那个 f：像素级取证

把截图高亮行右侧逐像素打成字符画，是一个**完整的小写 f**（9 行高，顶部弯钩 +
中间横杠 + 竖笔 + 尾钩），不是乱码残留；同列的普通行是文件名的末尾 "p"。
→ 它是**列表右侧固定列的元素**，普通行画成深色在浅底上看不见，选中行反白才显眼。
→ 30 秒判定实验：选中另一个文件，若标记跟着文件名变 = 应用画了两遍；
若始终是 "f" = 文件类型列（f=file），属正常设计。

### sprintf：残缺 + 返回值错

| 项 | 之前 | 现在 |
|---|---|---|
| 格式覆盖 | 不支持 `%f`；`%ld` 的 `l` 被当转换符吃掉只剩 32 位；宽度/精度/对齐基本没做 | 重写为「解析/取参/渲染」三段：全转换符 + 长度修饰符 + 标志 + 宽度精度 + `*` |
| `mr_sprintf` | **没有** | 已实现（与 sprintf 同语义），等槽位确认即可挂表 |
| **返回值** | Python **字符数** ❌ | **字节数**（C 标准）——中文文件名会让应用定位下一列时错位 |

配套：`bridge.py::ArmCall` 新增 `qarg/farg`（AAPCS：64 位/浮点变参走栈、8 字节对齐）。

### 顺手挖出的槽位表真相

官方 mrpoid `_mr_c_function_table[]` 的 0x048 是 `mr_sprintf`，我们那格是 `atoi`
—— **从 0x048 起整表错位一格，112 项不一致**。但：

- 前 17 项（0x000–0x040）**完全一致**；
- 我们的顺序是**从 `cfunction.ext` 反推**的（0x054/0x058 是 ext 里真实的空洞，
  官方那里是 rand/NULL）—— 不是抄错，是**不同版本的布局**；
- 实测 4 个真实 MRP 跑下来，mr_table 只被调 4 次，**0x048 之后从未被调用**
  （应用走 DSM 层 51 槽；C 库由 ext 自己的 `_mr_c_function_new` 注册接管）。

**没有盲目改表**（146 槽顺序改错风险远大于收益），改用 `tests/table_probe.py`
把差异清单固化，等 ext 侧硬证据。

**改动文件**：`api/impl.py`（`_fmt` 重写、`sprintf` 字节数、`mr_sprintf`）、
`bridge.py`（`qarg/farg`）、`api/mrtable.py`（槽位注释）。

**验证**：新增 `tests/fmt_probe.py` 44 项、`tests/table_probe.py` 11 项；
全套 **17 个探针 rc=0**；`mrp_emu.pyz` 重打包 **107.9 KB**，从单文件版跑曲奇
300 帧零异常。知识库新增 `docs/19-sprintf与槽位表排查.md`。

**遗留**：RX 本地进不去列表（启动卡在「下载字库」对话框，源站斯凯已停运），
所以本地没法逐像素复现老板画面；那需要从真机导出 skyfont 相关缓存。
