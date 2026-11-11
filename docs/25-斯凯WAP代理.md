# 斯凯 WAP 代理（proxy.51mrp.com）

> 现象：浏览器插件链（`brwcore.ext`）发出的请求在日志里长这样：
>
> ```
> [arm] [INFO]mr_open(mythroad/ipaddr2.ini,1) fd is: 0
> [arm] [INFO]mr_send 0 POST /page2 HTTP/1.1
> Host: proxy.51mrp.com
> User-Agent: Nokia6681/2.0
> Accept: */*
> Content-Type: application/octet-stream
> Connection: Keep-Alive
> Content-Length: 154
> ```

---

## 一、协议全貌

来源：`runtime/mythroad/plugins/brwcore.mrp` 的 `brwcore.ext`（148KB）
与 `wbrwcore.mrp` 的 `wbrwcore.ext`。这两个是浏览器内核，**唯一**同时
引用 `/page2`、`proxy.51mrp.com`、`ipaddr2.ini` 的包。

### 1.1 字符串表还原

| 字符串 | 作用 |
|---|---|
| `ipaddr2.ini` | 代理地址缓存文件（真机上由运营商下发） |
| `proxy.51mrp.com` | 默认代理域名（读不到 ini 时的回退） |
| `%s:%s` | 解析 ini 里的 `<host>:<port>` |
| `%d.%d.%d.%d` | 把 DNS 解析结果格式化成 IP |
| `%s:%d` | 拼接请求行的 `Host:` |
| `POST` | 请求方法 |
| `Host:` `User-Agent:` `Accept:` `Content-Type:` `Connection:` `Content-Length:` | 请求头模板 |
| `Nokia6681/2.0` | 斯凯浏览器内核的固定 UA |
| `application/octet-stream` | 请求体类型（二进制协议） |
| `Keep-Alive` | 连接复用 |
| `/page2` | 主内容端点 |
| `/image` `/mrp` | 图片 / MRP 资源端点 |
| `/res` `/sta` `/other` | 其它资源与状态端点 |

### 1.2 代理地址的解析顺序

```
1) mr_open("mythroad/ipaddr2.ini")     -> 读 <host>:<port>
   失败（fd=0）-> 回退
2) DNS 解析 proxy.51mrp.com            -> %d.%d.%d.%d
3) connect -> POST /page2  Host: proxy.51mrp.com
```

老板日志里 `mr_open(mythroad/ipaddr2.ini,1) fd is: 0` 说明**第 1 步失败**，
走的是第 2 步回退路径。

### 1.3 请求体是二进制协议

正文里带一串参数（`brwcore.ext` 的字符串表）：

```
%s%s&nwid=%u&hsman=%s&hstype=%s&prtver=%u&vmver=%u
&scrsize=%u&ramsize=%u&imsi=%s&imei=%s&smscntr=%s
&lac=0&cellId=0&mcc=0&mnc=0
```

即：设备标识 + 机型 + 屏幕分辨率 + 内存大小 + IMSI/IMEI + 短信计数。
这正是 `docs/22` 里修的 `mr_getUserInfo` 字段布局要提供的东西 ——
填不对，服务端会拒绝。

---

## 二、宿主侧需要做什么

### 2.1 DNS 映射

`proxy.51mrp.com` / `proxy2.51mrp.com` 必须解析到复刻服务端。
skyengine-v2 的**每个**插件 e2e 都显式传了：

```
dnsMap: "...;proxy.51mrp.com->159.75.119.124;proxy2.51mrp.com->159.75.119.124"
```

我们的 `DEFAULT_DNS_MAP` 此前只有 3 条（`rop` / `spd` / `wap.skmeg.com`），
恰好漏掉这两条 —— 见 `docs/24` 的断点 1。

### 2.2 内置 WAP 代理

`parse_proxy_request()` 已经支持 `POST /path` + `Host:` 形式
（mode=`host`），按 Host 头定位目标并原样转发，与 skyengine-v2
`wap_proxy.rs::parse_request` 的 `Forward` 分支一致。

实测链路：

```
[1] ipaddr2.ini 内容 = b'proxy.51mrp.com:80\n'
[2] sscanf('%s:%s') -> host='proxy.51mrp.com' port='80'
[3] DNS 解析 proxy.51mrp.com -> 159.75.119.124
[net] WAP host proxy.51mrp.com:80 -> 159.75.119.124:80
[4] send -> 326
[5] recv 225 字节, body = 'retcode=0\n'
```

复刻服务端确实实现了 `/page2`，返回 `retcode=0`。

### 2.3 生成 ipaddr2.ini

新增 `mrp_emu/proxyenv.py`：生成 `mythroad/ipaddr2.ini`，
内容 `proxy.51mrp.com:80`。这样 `brwcore.ext` 第 1 步就能拿到地址，
不必依赖"读不到再回退"。

已在 `cli.py` 的全局启动流程里接入（与系统字库准备并列）：

```python
from .proxyenv import prepare_proxy_environment
prepare_proxy_environment(workdir, log=log)
```

写**域名**而不是 IP：域名解析交给 DNS 映射表，换服务端时不用改文件。

---

## 三、端点清单

`brwcore.ext` 用到的六个端点：

| 端点 | 用途 |
|---|---|
| `/page2` | 主内容（POST，正文是上面那串设备统计参数） |
| `/image` | 图片 |
| `/mrp` | MRP 资源 |
| `/res` | 其它资源 |
| `/sta` | 状态查询 |
| `/other` | 其它 |

---

## 四、改动清单

| 文件 | 改动 |
|---|---|
| `mrp_emu/proxyenv.py` | **新增** —— 斯凯代理环境准备器（`ipaddr2.ini` 生成 + 端点/UA 常量） |
| `mrp_emu/cli.py` | 全局启动流程接入 `prepare_proxy_environment()` |
| `mrp_emu/net.py` | `DEFAULT_DNS_MAP` 补 `proxy.51mrp.com` / `proxy2.51mrp.com`（见 docs/24） |
| `tests/proxy_probe.py` | **新增** 26 项代理专项探针 |

---

## 五、验证

- `proxy_probe` 26 项全通过
- 全套 **22 个探针 rc=0、0 失败**
- 6 个真实应用运行无异常
- pyz 已重打包（143.5 KB）

---

## 六、已知边界

1. **`ipaddr2.ini` 与 `skyurl.cfg` 都是真机上下发的文件**，本地没有原件。
   我们只按逆向出的格式生成 `ipaddr2.ini`；`skyurl.cfg` 的格式还没逆出
   （`brwcore.ext` 里只有文件名，没有内容模板），暂时不管 —— 读不到时
   它自己会走回退。

2. **请求体的设备统计参数依赖 `mr_getUserInfo`**。`docs/22` 已经把字段
   布局修正（IMEI+0 / IMSI+16 / manufactory+32 / type+40 / ver+48），
   但真机上这些值是真实设备信息，我们填的是伪值。服务端如果校验
   设备指纹，可能仍然拒绝 —— 这需要实测确认。

3. **完整的浏览器插件往返仍未本地复现**：`brwcore` 是 ext 内部用
   `mr_c_load` 加载的纯 ext 包，宿主不直接参与加载；触发它需要
   游戏内广告条 → 浏览器的完整交互路径。
