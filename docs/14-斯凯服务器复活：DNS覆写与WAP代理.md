# 14 斯凯服务器复活：DNS 覆写与 WAP 代理

> 调研对象：`open-skyengine/skyengine-flutter` + 子模块 `open-skyengine/skyengine-v2`
> （2026-09-26 前的 main 分支，MIT）。本机对照实现：pymrp `mrp_emu/net.py`。
> 置信度：源码 A 级、在线实测 A 级、服务端内部实现 D 级（未开源）。

## 0. 一句话结论

**它不是"搭了一台代理服务器"，而是三层组合**：

| 层 | 做什么 | 在哪 |
|---|---|---|
| ① DNS 覆写 | 把 MRP 里硬编码的老斯凯域名解析到自建复刻服务器 IP | 引擎 `runtime.rs` / `arm/ext/network.rs`；前端由商店 `/config` 下发 |
| ② 进程内 WAP 代理 | 接管已关停的移动 cmwap 网关 `10.0.0.172`，解析绝对 URL / Host / CONNECT 并按覆写表转发 | `wap_proxy.rs` + `mr/host/network.rs` |
| ③ 远端复刻服务 | 在 `159.75.119.124` 上重新实现斯凯的 CGI（`simpleDownload` 等） | **未开源**，属第三方在线服务 |

pymrp 现已实现 ① + ②，③ 直接复用对方在线的服务。

## 1. 为什么必须覆写 DNS

老域名今天还能解析，但已经不是斯凯的机器了（2026-11-10 实测）：

| 域名 | 当前 DNS | 说明 |
|---|---|---|
| `rop.skymobiapp.com` | `38.48.128.189` | 已易主/停放 |
| `spd.skymobiapp.com` | `38.48.128.189` | 同上，`simpleDownload` 的原主机 |
| `wap.skmeg.com` | `135.181.255.27` | 同上 |
| `mrp.jysafe.cn` | **`159.75.119.124`** | open-skyengine 自建，商店 API 与复刻 CGI 同机 |

所以「网络协议栈通了」不等于「连得上服务」：MRP 拿着老域名去 `mr_getHostByName`
会拿到一个错误的 IP。必须在**虚拟机内部**把 DNS 结果改掉，而不是改宿 hosts 文件。

## 2. Flutter 前端：映射表是服务端下发的

`lib/services/app_store_api.dart`：

- `APP_STORE_BASE_URL` 默认 `https://mrp.jysafe.cn/api/app/v1`（可用
  `--dart-define` 覆盖），请求带 `X-App-Key` + HMAC-SHA256 签名。
- `fetchConfig()` → `GET /config`，响应里含 `hosts: [{domain, ip}, ...]`
  （`AppStoreConfig` / `AppStoreHostMapping`）。

`lib/pages/home_page.dart::_dnsMapFromHosts()` 把列表拼成
`"domain->ip;domain2->ip2"` 字符串，经 `mrp_player_page.dart` →
`skyengine_engine.dart` 传给 C ABI：

```dart
// lib/skyengine/skyengine_bindings.dart
skyengine_api_set_dns_map(Pointer<Utf8>) -> Int32
```

也就是说**映射表是远程可配置的**，服务器换 IP 不用发版。
pymrp 目前用命令行 `--dns-map` + 内置默认表，没有接商店 `/config`（我们不需要签名凭据）。

## 3. Rust 引擎：三层关键源码

### 3.1 默认表与代理启动 —— `crates/skyengine-core/src/runtime.rs`

```rust
pub struct DnsMapping { source: String, address: Ipv4Addr, port: Option<u16> }

fn default_dns_mappings() -> Vec<DnsMapping> {
    ["rop.skymobiapp.com", "spd.skymobiapp.com", "wap.skmeg.com"]
        .into_iter()
        .map(|source| DnsMapping {
            source: source.into(),
            address: Ipv4Addr::new(159, 75, 119, 124),
            port: None,
        }).collect()
}
```

`Runtime::load_with_audio()` 里 `start_wap_proxy(&config.dns_mappings)`：
**只要映射表里出现 `10.0.0.172` 作为 source，就不启动内置代理**（让用户显式覆盖网关）。

### 3.2 进程内 WAP 代理 —— `crates/skyengine-core/src/wap_proxy.rs`

- `WAP_PROXY_ADDRESS = 10.0.0.172`，`TcpListener::bind(127.0.0.1, 0)` 随机端口，
  独立线程 accept，每连接一个线程；
- `parse_request()` 三种请求：
  - `CONNECT host:port` → 回 `HTTP/1.1 200 Connection Established` 后双向 `relay()`；
  - 绝对 URL `GET http://host/path` → 改写成 `GET /path`，剥掉 `Proxy-Connection`，
    缺 `Host` 时补上；
  - 相对路径 + `Host` 头 → 原样转发；
- `connect_target()`：命中 `dns_mappings`（按域名或按 IP）就连映射地址，
  否则走系统 DNS、只取 IPv4；失败回 502，坏请求回 400；
- 请求头最大 64KB，上游连接超时 3s。

### 3.3 socket 路由三条规则 —— `mr/host/network.rs::route_mr_endpoint`

`mr_connect(s, ip, port)` 传进来的 `ip` 是**主机序 u32**（`a<<24|b<<16|c<<8|d`）：

1. 若某映射的 `source` 本身就是这个 IP 字符串 → 连 `mapping.address:port`；
2. 若 `ip == 10.0.0.172` 且内置代理在跑 → 连 `127.0.0.1:随机端口`（WAP 代理）；
3. 若某映射 `address == ip` 且带 `port` → 只改端口；
4. 否则原样连。

`arm/ext/network.rs` 里 `resolve_mapped_host()` 覆写 `mr_getHostByName`，
`route_mapped_endpoint()` 对 ARM ext 层 socket 做同样的三条路由；首次 `send`
会先缓冲请求头（`pending_http_request`），检查 `Host` / `CONNECT` 后决定是否重连。
`mr/host/network.rs::test_com1(100, name)` 说明 MR/Lua 层的 DNS 查询也走映射表。

### 3.4 CLI 契约 —— `apps/skyengine/src/main.rs`

```
--dns-map 'HOST->IPv4[:PORT];...'
```

源去尾点、转小写；目标可以是纯 IPv4 或 `IPv4:PORT`；重复源报错；
传了 `--dns-map` 就**替换**默认表（不是追加）。README 明确写：
「显式映射 `10.0.0.172` 则会覆盖进程内代理」。

### 3.5 服务端协议长什么样 —— `test/e2e/simple-download-server.ts`

这是他们为测试写的 **simpleDownload 协议复刻**，能看出老 CGI 的形状：

- HTTP `POST /simpleDownload`，`Host: spd.skymobiapp.com:6009`；
- body 是 TLV：`uint32 tag | uint32 len | value`；
- 请求关键字段 `0x2775` = productId、`0x29ce` = appId；
- 响应 TLV：`0x64`=200、`0x65`=productId、`0x2c4`=插件长度、
  `0x2c5`=MD5、`0x2d1`=插件二进制，`Content-Type: application/x-tar`；
- `simpleDownloadDnsMap()` 把 `10.0.0.172` 和 `spd.skymobiapp.com`
  都指到本机测试端口。

`test/e2e/gjxwsmn/temp.test.ts` 的真实断言：
`my_connect(fd, '159.75.119.124', 6009)` 后发出
`POST /simpleDownload HTTP/1.1\r\nHost: spd.skymobiapp.com:6009`。

## 4. 服务端真的还活着（2026-11-10 实测）

| 探测 | 结果 |
|---|---|
| `mrp.jysafe.cn` DNS | `159.75.119.124` |
| `http://159.75.119.124/` 与 `:6009/` | 200 `nginx/1.30.3` |
| 直连 TCP `159.75.119.124:6009` | 可连 |
| `GET /` + `Host: spd.skymobiapp.com:6009` | **302** → `dnspod.qcloud.com/static/webblock.html?d=spd.skymobi...`（未备案拦截页） |
| `GET /` + `Host: wap.skmeg.com` / `mrp.jysafe.cn` / 纯 IP | 200 HTML |
| `POST /simpleDownload` + `Host: spd.skymobiapp.com:6009`、`Content-Length: 0` | **200** ← 复刻 CGI 确实在跑 |

最后一条很关键：**GET 被 DNSPod 拦、POST /simpleDownload 放行**，说明服务器是按
Host + 方法 + 路径做白名单的，不是一台普通 nginx。在线探针只发空 body，
不构造 TLV，不会真的触发插件下载。

组织 `open-skyengine` 只有 4 个公开仓库：`skyengine-flutter`、`skyengine-v2`、
`skyengine-tools`、`official-wiki`。**服务端代码没有开源**，我们只能当黑盒用。

## 5. pymrp 的对照实现

新增/改动文件：`mrp_emu/net.py`、`app.py`、`cli.py`、
`tests/legacy_net_probe.py`。

| 能力 | skyengine-v2 | pymrp |
|---|---|---|
| 默认覆写 3 个老域名 → 159.75.119.124 | `runtime.rs` | `DEFAULT_DNS_MAP` |
| `HOST->IP[:PORT];...` 解析 | `main.rs::parse_dns_mappings` | `parse_dns_map()` |
| `mr_getHostByName` 覆写 | `resolve_mapped_host()` | `get_host_by_name()` 先查表 |
| `mr_connect` 三条路由 | `route_mr_endpoint()` | `connect()` 规则 1/2/3 |
| cmwap `10.0.0.172` 网关代理 | 独立监听 127.0.0.1:随机端口 + 线程 | **假连接 + 首包改写**（不监听端口） |
| 绝对 URL 改 origin-form / 剥 Proxy-Connection / 补 Host | `parse_request()` | `parse_proxy_request()` |
| CONNECT 隧道 + 自造 200 | `serve_client()` | `pending_recv` + `tunnel` |
| 显式 `10.0.0.172->IP:PORT` 覆盖代理 | ✅ | ✅ |
| `--wap-proxy off` | （靠显式映射） | ✅ 显式开关 |
| 商店 `/config` 远程下发 hosts | ✅ | ❌（不需要签名凭据，用命令行） |
| 每请求换 Host 的 keep-alive 重路由 | ✅（检查每个请求头） | ❌ 只解析首个请求 |
| 服务端 CGI | ❌ 未开源 | ❌ 不在本项目范围 |

**实现要点**：pymrp 不额外开监听端口，而是在 `connect(10.0.0.172)` 时把槽位标成
`is_proxy` 并返回"假成功"；第一次 `send()` 用 `parse_proxy_request()` 解析出真实
authority → `resolve_target()` 应用覆写表 → `_dial()` 真连 → 改写后的首包用
`_send_all()` 发出，但返回给 MRP 的仍是**原始请求长度**（MRP 用返回值判断是否发完）。
CONNECT 的 200 响应塞进 `SocketSlot.pending_recv`，`recv()` 优先消费。

## 6. 使用

```bash
cd mrp_emu
python run.py                                   # 默认已接管 3 个老域名 + 内置 WAP 代理
python run.py --dns-map ""                      # 清空覆写，完全按系统 DNS
python run.py --dns-map "spd.skymobiapp.com->127.0.0.1:8088"   # 指到自己的复刻服务
python run.py --dns-map "10.0.0.172->159.75.119.124:13230"     # 网关直连，绕开内置代理
python run.py --wap-proxy off                   # 不接管 10.0.0.172
python run.py --net-proxy http://127.0.0.1:7890 # MRP 的 TCP 出站走 Clash（可选）

python tests/legacy_net_probe.py                # 51 项，纯回环、不需联网
python tests/legacy_net_probe.py --online       # 55 项，含 159.75.119.124:6009 只读探针
```

`PYMRP_NET_PROXY=http://127.0.0.1:7890` 环境变量可让在线探针走 CONNECT 代理。

## 7. 边界与风险（如实说）

1. **159.75.119.124 是第三方服务**，不是我们的资产，随时可能下线/改策略；
   内置默认 IP 是照抄 skyengine-v2 的做法，出问题用 `--dns-map` 覆盖即可。
2. 我们只做了**客户端接管**。要让某个具体游戏的注册/计费/插件下载真正跑通，
   还得服务端实现它那套 CGI；客户端代理只是把流量送到正确的地方。
3. `GET` 返回 DNSPod 302 是服务端的 Host 白名单行为，**不是模拟器 bug**；
   真实 MRP 用的是 `POST /simpleDownload`。
4. 同一条 keep-alive 连接上中途换 Host 的场景，pymrp 只按首个请求路由，
   Rust 引擎会逐请求检查。绝大多数 2008 年的 MRP 一连接一请求，影响很小。
5. CONNECT 隧道是纯字节透传，不做 TLS 终止；老 MRP 基本是明文 HTTP。
6. 在线探针只发 `Content-Length: 0` 的空 POST，不构造 TLV，不触发真实下载。

## 8. 资料溯源

- <https://github.com/open-skyengine/skyengine-flutter> （Dart 前端，MIT）
- <https://github.com/open-skyengine/skyengine-v2> （Rust 引擎子模块，MIT）
- 本地参考副本（不进 git）：`ref/skyengine-flutter/`、`ref/skyengine-v2/`
- 相关文档：[13 网络模块与内存健壮性](13-网络模块与内存健壮性.md)、
  [11 pymrp 实现对照](11-pymrp实现对照.md)
