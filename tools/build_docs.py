"""把 handbook 页按主题聚合成分册清单。

输入: build/manual_index.json  (tools/extract_manual.py 产出)
输出: docs/api/topics/<n>-<slug>.md   按主题连续阅读的接口清单
      docs/api/topics/README.md       分册索引
      build/coverage.json             分类覆盖率（未归类页面清单）
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "docs" / "api" / "topics"

# (文号, 分册 slug, 中文标题, 一句定位, [页 slug...])
CATS: list[tuple[str, str, str, str, list[str]]] = [
    ("01", "porting", "移植总纲与模型",
     "三层结构、抽象接口 vs 扩展接口、版本号规则、接口跟踪表",
     ["SKYENGINE-简介", "抽象移植接口", "外部移植接口", "平台版本号规则", "接口跟踪表",
      "code-定义", "扩展接口-mr_platmr_platEx", "mr_plat", "mr_platEx"]),

    ("02", "core", "核心运行时：内存与进程",
     "内存申请释放、第二内存、内部 cache、扩展内存",
     ["mr_mem_get", "mr_mem_free", "mr_printf", "mr_platEx-1001", "mr_platEx-1002",
      "mr_platEx-1012", "mr_platEx-1013", "mr_platEx-1014", "mr_platEx-1015"]),

    ("03", "fs", "文件系统与存储",
     "打开/读写/定位/目录枚举、文件查找、盘符空间、文件浏览器",
     ["mr_open", "mr_close", "mr_read", "mr_write", "mr_seek", "mr_getLen",
      "mr_remove", "mr_rename", "mr_mkDir", "mr_rmDir", "mr_ferrno",
      "mr_findStart", "mr_findGetNext", "mr_findStop", "mr_save_mrp",
      "mr_plat-1231", "mr_plat-1218", "mr_platEx-1204", "mr_platEx-1220",
      "mr_platEx-1305", "mr_platEx-1306", "mr_platEx-1401", "mr_platEx-1402",
      "mr_platEx-1403", "mr_platEx-1404", "mr_platEx-1405", "mr_platEx-1406",
      "mr_platEx-11", "mr_platEx-12", "mr_platEx-1221", "mr_plat-1105"]),

    ("04", "gfx", "图形、位图与图层",
     "画位图、屏幕信息、字库、窗口、图层系统、PNG/GIF 解码、旋转与刷屏",
     ["mr_drawBitmap", "mr_getScreenInfo", "mr_getCharBitmap",
      "mr_winCreate", "mr_winRelease",
      "mr_plat-101", "mr_plat-104", "mr_plat-105", "mr_plat-1020",
      "mr_plat-1310", "mr_plat-1312", "mr_plat-1314", "mr_plat-1317",
      "mr_plat-1318", "mr_plat-1319", "mr_plat-1320", "mr_plat-1321",
      "mr_plat-1322", "mr_plat-1325", "mr_plat-1326", "mr_plat-3012",
      "mr_platEx-1201", "mr_platEx-1207", "mr_platEx-1308", "mr_platEx-1309",
      "mr_platEx-1311", "mr_platEx-1313", "mr_platEx-1315", "mr_platEx-1316",
      "mr_platEx-3001", "mr_platEx-3002", "mr_platEx-3003", "mr_platEx-3004",
      "mr_platEx-3005", "mr_platEx-3007", "mr_platEx-3008", "mr_platEx-3009",
      "mr_platEx-3010", "mr_platEx-3011", "mr_platEx-3013", "mr_platEx-3014",
      "mr_platEx-3015"]),

    ("05", "audio", "声音与流媒体",
     "mr_playSound 一次性播放、mr_platEx 201x~225x 有状态播放器、PCM 环形缓冲、音量与铃声",
     ["mr_playSound", "mr_stopSound", "mr_plat-102", "mr_plat-103",
      "mr_plat-1302", "mr_plat-1213", "mr_platEx-1208",
      "mr_platEx-201x", "mr_platEx-202x", "mr_platEx-203x", "mr_platEx-204x",
      "mr_platEx-205x", "mr_platEx-206x", "mr_platEx-207x", "mr_platEx-208x",
      "mr_platEx-209x", "mr_platEx-210x", "mr_platEx-211x", "mr_platEx-212x",
      "mr_platEx-213x", "mr_platEx-215x", "mr_platEx-216x",
      "mr_platEx-220x", "mr_platEx-221x", "mr_platEx-222x", "mr_platEx-223x",
      "mr_platEx-224x", "mr_platEx-225x", "mr_plat-7"]),

    ("06", "camera", "相机、录音与拍照",
     "camera 生命周期与变焦、预览取帧、拍照、录音与 PCM 取音",
     ["mr_plat-2500", "mr_plat-2502", "mr_plat-2503", "mr_plat-2504",
      "mr_plat-2506", "mr_plat-2507", "mr_plat-2508",
      "mr_plat-2701", "mr_plat-2702", "mr_plat-2703",
      "mr_platEx-2501", "mr_platEx-2505", "mr_platEx-2509",
      "mr_platEx-2700", "mr_platEx-2704"]),

    ("07", "net", "网络与连接",
     "socket 全套、DNS、WAP、APN、WIFI、连接状态与联网时长",
     ["mr_socket", "mr_connect", "mr_closeSocket", "mr_send", "mr_recv",
      "mr_sendto", "mr_recvfrom", "mr_initNetwork", "mr_closeNetwork",
      "mr_getHostByName", "mr_getNetworkID", "mr_connectWAP",
      "mr_plat-1001", "mr_plat-1002", "mr_plat-1107", "mr_plat-1110",
      "mr_plat-1111", "mr_plat-1327", "mr_plat-1328",
      "mr_platEx-1003", "mr_platEx-1108", "mr_platEx-1109", "mr_platEx-6004"]),

    ("08", "system", "系统、时间与设备状态",
     "时间日期、系统信息、SIM 与信号、背光与主题、震动与传感器、语言与时区、闹钟天气",
     ["mr_getTime", "mr_getDatetime", "mr_sleep", "mr_info", "mr_getUserInfo",
      "mr_newSIMInd", "mr_startShake",
      "mr_plat-1", "mr_plat-2", "mr_plat-3", "mr_plat-1004", "mr_plat-1006",
      "mr_plat-1011", "mr_plat-1016", "mr_plat-1018", "mr_plat-1113",
      "mr_plat-1114", "mr_plat-1115", "mr_plat-1205", "mr_plat-1206",
      "mr_plat-1211", "mr_plat-1214", "mr_plat-1215", "mr_plat-1216",
      "mr_plat-1217", "mr_plat-4001", "mr_plat-4002", "mr_plat-4003",
      "mr_plat-4004", "mr_plat-4005", "mr_plat-4006",
      "mr_platEx-0x90001", "mr_platEx-0x90002", "mr_platEx-1005",
      "mr_platEx-1017", "mr_platEx-1112", "mr_platEx-1116", "mr_platEx-1117",
      "mr_platEx-1222", "mr_platEx-1223", "mr_platEx-1224", "mr_platEx-1225",
      "mr_platEx-1226", "mr_platEx-1307", "mr_platEx-5001", "mr_platEx-5002",
      "mr_platEx-5011", "mr_platEx-5013", "mr_platEx-5014", "mr_platEx-5015",
      "mr_platEx-5016", "mr_platEx-5017", "mr_platEx-5018", "mr_platEx-5019",
      "mr_platEx-1009"]),

    ("09", "ui", "UI 控件：菜单、编辑框、文本框、对话框",
     "平台原生控件族、弹出列表、软键文本、桌面气泡框",
     ["mr_menuCreate", "mr_menuSetItem", "mr_menuShow", "mr_menuRefresh",
      "mr_menuRelease", "mr_editCreate", "mr_editGetText", "mr_editRelease",
      "mr_textCreate", "mr_textRefresh", "mr_textRelease",
      "mr_dialogCreate", "mr_dialogRefresh", "mr_dialogRelease",
      "mr_plat-1333",
      "mr_platEx-1", "mr_platEx-2", "mr_platEx-3", "mr_platEx-4",
      "mr_platEx-5", "mr_platEx-5101", "mr_platEx-6000", "mr_platEx-6001",
      "mr_platEx-6002", "mr_platEx-6003"]),

    ("10", "event", "事件、定时器与生命周期",
     "mr_event 事件模型、定时器族、前后台切换、子应用加载（start_dsm）",
     ["mr_event", "mr_timer", "mr_timerStart", "mr_timerStop",
      "mr_pauseApp", "mr_resumeApp", "mr_exit", "mr_stop", "mr_registerAPP",
      "mr_start_dsm", "mr_start_dsm_ex", "mr_start_dsmB", "mr_start_dsmC",
      "mr_plat-1003", "mr_plat-1391",
      "mr_platEx-1004", "mr_platEx-1323", "mr_platEx-6005"]),

    ("11", "operator", "短信、电话本与运营商",
     "短信收发与信箱、彩信、电话本（本地与非本地 UI）、本机号码",
     ["mr_sendSms", "mr_smsIndiaction", "数据账号接口", "电话本接口",
      "mr_call", "mr_plat-1100", "mr_plat-1101", "mr_plat-1106",
      "mr_plat-4017", "mr_plat-4022", "mr_plat-4031",
      "mr_platEx-1008", "mr_platEx-1102", "mr_platEx-1103", "mr_platEx-1104",
      "mr_platEx-1203", "mr_platEx-4011", "mr_platEx-4012",
      "mr_platEx-4016", "mr_platEx-4021", "mr_platEx-4032",
      "mr_platEx-4033", "mr_platEx-4041", "mr_platEx-4042", "mr_platEx-4043"]),

    ("12", "misc", "平台杂项与历史遗留",
     "NES 模拟器、平台 QQ、手柄、动感芯片、以及无归档的零散 code",
     ["mr_plat-4", "mr_plat-5", "mr_plat-6", "mr_plat-8",
      "mr_platEx-1006", "mr_platEx-1332", "mr_platEx-1210"]),
]


def brief(p: dict) -> str:
    out = [f"#### `{p['title'].split(' - ')[0]}`" +
           (f" — {p['title'].split(' - ', 1)[1]}" if " - " in p["title"] else ""), ""]
    if p["proto"]:
        out.append(f"```c\n{p['proto']}\n```")
    if p["desc"]:
        out.append("**说明** " + p["desc"].split("\n")[0])
    if p["params"]:
        ps = "; ".join(" ".join(r) for r in p["params"])
        out.append(f"**参数** {ps}")
    if p["ret"]:
        out.append("**返回** " + " / ".join(
            ln for ln in p["ret"].split("\n") if ln.strip())[:300])
    if p["remarks"]:
        r = " ".join(ln for ln in p["remarks"].split("\n") if ln.strip())
        out.append("**备注** " + (r[:400] + ("…" if len(r) > 400 else "")))
    out.append(f"[全文]({p['slug']}.md)")
    out.append("")
    return "\n".join(out)


def main() -> int:
    pages = json.loads((BUILD / "manual_index.json").read_text(encoding="utf-8"))
    by_slug = {p["slug"]: p for p in pages}
    OUT.mkdir(parents=True, exist_ok=True)

    used: set[str] = set()
    index = ["# 分册索引", "", "按主题聚合的手册接口清单。逐页原件在 `docs/api/`，",
             "本目录是同一批内容的主题重排，便于连续阅读与移植时对照。", "",
             "| 分册 | 主题 | 接口数 |", "|---|---|---|"]

    for num, cslug, title, lead, slugs in CATS:
        found = [by_slug[s] for s in slugs if s in by_slug]
        missing = [s for s in slugs if s not in by_slug]
        used.update(p["slug"] for p in found)
        body = [f"# {num} · {title}", "", f"> {lead}", "",
                f"本册收录 {len(found)} 个接口。内容由手册正文自动抽取，未作改写。", ""]
        for p in found:
            body.append(brief(p))
        if missing:
            body += ["## 手册中不存在的页", "", "、".join(f"`{m}`" for m in missing), ""]
        fname = f"{num}-{cslug}.md"
        (OUT / fname).write_text("\n".join(body), encoding="utf-8")
        index.append(f"| [{num} {title}]({fname}) | {lead} | {len(found)} |")

    orphan = [p for p in pages if p["slug"] not in used]
    if orphan:
        body = ["# 13 · 未归类", "", f"以下 {len(orphan)} 页未进入任何分册，保留以免遗漏。", ""]
        body += [brief(p) for p in orphan]
        (OUT / "13-orphan.md").write_text("\n".join(body), encoding="utf-8")
        index.append(f"| [13 未归类](13-orphan.md) | 待人工判读 | {len(orphan)} |")

    (OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    (BUILD / "coverage.json").write_text(json.dumps(
        {"total": len(pages), "classified": len(used),
         "orphan": [p["slug"] for p in orphan]}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"total={len(pages)} classified={len(used)} orphan={len(orphan)}")
    if orphan:
        print("未归类:", [p["slug"] for p in orphan])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
