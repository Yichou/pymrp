# PymRP — Python 实现的 MRP 模拟器 + SkyEngine 知识库

> 抢救性项目：MRP 是 2004–2011 年中国功能机（MTK/展讯/ADI 平台）上的应用生态，
> 编译器与官方基础设施已经消失。本仓库用 Python 复刻其模拟器（vmrp 路线），
> 并把散落的官方手册整理成可传承的知识库。

## 这是什么

```
mrp_emu/   Python 版 MRP 模拟器
           Unicorn 执行 ARM + pygame 绘制 MTK 直板机界面
           能运行真实 .mrp 应用（含官方启动器与游戏）

docs/      SkyEngine / Mythroad / MRP 知识库
           288 页官方 CHM 手册全文整理 + 12 篇原理文档 + 实测包格式规范

tools/     文档生成脚本（CHM → Markdown 管线）
```

## 快速开始

```bash
pip install -r mrp_emu/requirements.txt   # unicorn pygame numpy

cd mrp_emu
python tools/fetch_runtime.py             # 获取运行时（cfunction.ext + 字库 + 游戏，需联网）
python run.py                             # MTK 真机桌面 → 游戏中心 → 点列表直接玩
python run.py --boot gamecenter            # 直接进游戏中心
python run.py runtime/mythroad/box.mrp     # 跳过桌面，单跑一个 MRP
```

> 首次进入游戏中心会在**后台**拉取在线索引（vmrp.github.io 的 664 个 MRP，
> 含标题/开发商/描述），落盘成 `runtime/cache/online_index.json`；之后直接读缓存，
> 7 天才刷新一次。点在线条目会按需下载单个包到 `runtime/mythroad/`，下完自动启动。
> 本地列表扫描运行环境下所有 `.mrp`，只读每个文件的前 240 字节取元数据。
> 详见 [docs/12 启动界面与游戏中心](docs/12-启动界面与游戏中心.md)。

> MRP 应用自己的网络也已打通（TCP/UDP、DNS、cmwap 代理、异步回调）。
> 系统开了 Clash 想让 MRP 走它：`python run.py --net-proxy http://127.0.0.1:7890`。
> 完整接口契约与 RX 管理器崩溃复盘见
> [docs/13 网络模块与内存健壮性](docs/13-网络模块与内存健壮性.md)。

## 文档入口

**从 [docs/README.md](docs/README.md) 开始**。三分钟看懂这套系统 →
[docs/00-这套系统是什么.md](docs/00-这套系统是什么.md)。

- 想自己实现模拟器：[docs/02 运行原理](docs/02-运行原理-虚拟机怎么跑MRP.md) +
  [docs/07 实现路线图](docs/07-实现路线图.md) +
  [docs/08 陷阱清单](docs/08-陷阱清单.md)
- 想拆包/改资源：[docs/03 MRP 包格式规范](docs/03-MRP包格式规范.md)（实测，含解析器）
- 查接口：[docs/04 接口地图](docs/04-接口地图.md) → `docs/api/topics/` 分册

## 测试

```bash
cd mrp_emu
python tests/selftest.py       # ARM 执行 + 桥接链路
python tests/audio_probe.py    # 声音 70 项断言
python tests/key_probe.py      # 按键/触摸
python tests/launcher_probe.py # 启动界面 / 游戏中心 / 点击直达启动（35 项）
python tests/net_probe.py      # 网络 57 项（TCP/UDP/DNS/cmwap/回调）+ RX 崩溃回归
```

## 资料声明

原手册与 `cfunction.ext` 版权属 SKY-MOBI（斯凯网络）。本仓库对其的整理与引用
属于技术资料保存与研究目的。详见 [docs/10-资料溯源与考古.md](docs/10-资料溯源与考古.md)。
