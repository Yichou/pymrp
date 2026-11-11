"""MRP 模拟器常量。

内存布局与事件码全部对齐 vmrp(C) 的实现，数值不可随意改动：
    header/vmrp.h  ->  START_ADDRESS / STACK / MEMORY_MANAGER
    mythroad/dsm.h ->  DSM_INIT 等事件码、VMRP_VER
"""

# ---------------------------------------------------------------- 内存布局
# 与 vmrp 完全一致，改了 cfunction.ext 里的绝对地址假设就会崩。
CODE_ADDRESS = 0x80000                          # 代码段起点
CODE_SIZE = 1024 * 1024 * 1                     # 1MB
STACK_ADDRESS = CODE_ADDRESS + CODE_SIZE        # 0x180000
STACK_SIZE = 1024 * 1024 * 1                    # 1MB
MEMORY_MANAGER_ADDRESS = STACK_ADDRESS + STACK_SIZE   # 0x280000
MEMORY_MANAGER_SIZE = 1024 * 1024 * 6                  # 6MB
START_ADDRESS = CODE_ADDRESS
END_ADDRESS = MEMORY_MANAGER_ADDRESS + MEMORY_MANAGER_SIZE
TOTAL_MEMORY = END_ADDRESS - START_ADDRESS

# ---------------------------------------------------------------- 屏幕
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 320
SCREEN_BPP = 16          # RGB565

# ---------------------------------------------------------------- DSM 事件码
# mythroad/include/dsm.h
DSM_INIT = -100
MR_START_DSM = -99
MR_PAUSEAPP = -98
MR_RESUMEAPP = -97
MR_TIMER = -96
MR_EVENT = -95

VMRP_VER = 20210701

# dsm_flag
FLAG_USE_UTF8_FS = 1 << 0
FLAG_USE_UTF8_EDIT = 1 << 1

# ---------------------------------------------------------------- 返回值
MR_SUCCESS = 0
MR_FAILED = -1
MR_IGNORE = 1
MR_WAITING = 2
MR_NO_EXIST = -2

# ---------------------------------------------------------------- 文件
MR_FILE_RDONLY = 0x01
MR_FILE_WRONLY = 0x02
MR_FILE_RDWR = 0x04
MR_FILE_CREATE = 0x08

MR_SEEK_SET = 0
MR_SEEK_CUR = 1
MR_SEEK_END = 2

MR_IS_FILE = 1
MR_IS_DIR = 2
MR_IS_INVALID = 8

# ---------------------------------------------------------------- 输入事件
# 传给 ARM 侧 mr_event 的 code
# 严格对齐 mythroad/include/mrporting.h 的 enum（MR_KEY_PRESS 从 0 开始）
MR_KEY_PRESS = 0
MR_KEY_RELEASE = 1
MR_MOUSE_DOWN = 2
MR_MOUSE_UP = 3
MR_MENU_SELECT = 4
MR_MENU_RETURN = 5
MR_DIALOG_EVENT = 6
MR_SMS_INDICATION = 7
MR_EVENT_EXIT = 8
MR_SMS_RESULT = 9
MR_LOCALUI_EVENT = 10
MR_OSD_EVENT = 11
MR_MOUSE_MOVE = 12
MR_ERROR_EVENT = 13

# ---------------------------------------------------------------- 键值
# mythroad 的 mr_key 枚举顺序（mrporting.h）。
# 注意顺序：数字 -> * -> # -> 方向 -> POWER(挂机) -> 软键 -> SEND -> SELECT。
# 早期版本这里把 SELECT 写成 16、END 写成 20，把「确定」当成「挂机」发出去，
# 导致启动器菜单不响应，已修正。
KEY_0 = 0
KEY_1 = 1
KEY_2 = 2
KEY_3 = 3
KEY_4 = 4
KEY_5 = 5
KEY_6 = 6
KEY_7 = 7
KEY_8 = 8
KEY_9 = 9
KEY_STAR = 10
KEY_POUND = 11
KEY_UP = 12
KEY_DOWN = 13
KEY_LEFT = 14
KEY_RIGHT = 15
KEY_POWER = 16          # 挂机键（老代码里误称为 END）
KEY_SOFTLEFT = 17
KEY_SOFTRIGHT = 18
KEY_SEND = 19
KEY_SELECT = 20         # 确定/选择
KEY_VOLUME_UP = 21
KEY_VOLUME_DOWN = 22
KEY_CLEAR = 23
KEY_A = 24
KEY_B = 25
KEY_CAPTURE = 26
KEY_NONE = 27
KEY_NUM = 12

# 兼容别名：皮肤/键盘里叫 END 的，实际就是挂机键
KEY_END = KEY_POWER

KEY_NAME_TO_CODE = {
    "0": KEY_0, "1": KEY_1, "2": KEY_2, "3": KEY_3, "4": KEY_4,
    "5": KEY_5, "6": KEY_6, "7": KEY_7, "8": KEY_8, "9": KEY_9,
    "*": KEY_STAR, "#": KEY_POUND,
    "UP": KEY_UP, "DOWN": KEY_DOWN, "LEFT": KEY_LEFT, "RIGHT": KEY_RIGHT,
    "SELECT": KEY_SELECT, "OK": KEY_SELECT,
    "SOFT_L": KEY_SOFTLEFT, "SOFT_R": KEY_SOFTRIGHT,
    "SEND": KEY_SEND, "END": KEY_END, "POWER": KEY_POWER,
    "CLEAR": KEY_CLEAR,
    "VOL_UP": KEY_VOLUME_UP, "VOL_DOWN": KEY_VOLUME_DOWN,
    "A": KEY_A, "B": KEY_B,
}

# ---------------------------------------------------------------- 声音
# mrporting.h: typedef enum { MR_SOUND_MIDI, MR_SOUND_WAV, MR_SOUND_MP3,
#                            MR_SOUND_PCM, MR_SOUND_M4A, MR_SOUND_AMR,
#                            MR_SOUND_AMR_WB } MR_SOUND_TYPE;
MR_SOUND_MIDI = 0
MR_SOUND_WAV = 1
MR_SOUND_MP3 = 2
MR_SOUND_PCM = 3          # 8K 16bit PCM，分段流式喂入
MR_SOUND_M4A = 4
MR_SOUND_AMR = 5
MR_SOUND_AMR_WB = 6

SOUND_TYPE_NAMES = {
    MR_SOUND_MIDI: "MIDI",
    MR_SOUND_WAV: "WAV",
    MR_SOUND_MP3: "MP3",
    MR_SOUND_PCM: "PCM",
    MR_SOUND_M4A: "M4A",
    MR_SOUND_AMR: "AMR",
    MR_SOUND_AMR_WB: "AMR-WB",
}

# ---------------------------------------------------------------- 流媒体
# mr_platEx(201x..216x) 的多媒体播放器。x = T_MEDIA_TYPE：
#   typedef enum { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR,
#                  MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC,
#                  MEDIA_UNKNOW } T_MEDIA_TYPE;
# 所以 2014 = 初始化 AMR 设备，2042 = 播放 WAVE，2093 = 查 MP3 状态。
MEDIA_MIDI = 1
MEDIA_WAVE = 2
MEDIA_MP3 = 3
MEDIA_AMR = 4
MEDIA_PCM = 5
MEDIA_M4A = 6
MEDIA_AAC = 7
MEDIA_LYRIC = 8
MEDIA_UNKNOW = 9

MEDIA_TYPE_NAMES = {
    MEDIA_MIDI: "MIDI", MEDIA_WAVE: "WAVE", MEDIA_MP3: "MP3",
    MEDIA_AMR: "AMR", MEDIA_PCM: "PCM", MEDIA_M4A: "M4A",
    MEDIA_AAC: "AAC", MEDIA_LYRIC: "LYRIC", MEDIA_UNKNOW: "未知",
}

# mr_platEx 主族编号（高位）
PLATEX_MEDIA_INIT = 201
PLATEX_MEDIA_LOAD_FILE = 202
PLATEX_MEDIA_LOAD_BUF = 203
PLATEX_MEDIA_PLAY = 204
PLATEX_MEDIA_PAUSE = 205
PLATEX_MEDIA_RESUME = 206
PLATEX_MEDIA_STOP = 207
PLATEX_MEDIA_CLOSE = 208
PLATEX_MEDIA_STATE = 209
PLATEX_MEDIA_SEEK_TIME = 210
PLATEX_MEDIA_SEEK_OFFSET = 211
PLATEX_MEDIA_TOTAL_TIME = 212
PLATEX_MEDIA_CUR_TIME = 213
PLATEX_MEDIA_CUR_TIME2 = 215
PLATEX_MEDIA_RELEASE = 216
PLATEX_MEDIA_BG_LOAD = 222
PLATEX_MEDIA_BG_PLAY = 223
PLATEX_MEDIA_BG_STOP = 224
PLATEX_MEDIA_BG_FREE = 225

# PLAY_STATE：209x 的返回值是 MR_PLAT_VALUE_BASE + 状态值
MR_MEDIA_IDLE = 1001
MR_MEDIA_INITED = 1002
MR_MEDIA_LOADED = 1003
MR_MEDIA_PLAYING = 1004
MR_MEDIA_PAUSED = 1005
MR_MEDIA_SUSPENDED = 1006
MR_MEDIA_SUSPENDING = 1007

MEDIA_STATE_NAMES = {
    MR_MEDIA_IDLE: "IDLE", MR_MEDIA_INITED: "INITED",
    MR_MEDIA_LOADED: "LOADED", MR_MEDIA_PLAYING: "PLAYING",
    MR_MEDIA_PAUSED: "PAUSED", MR_MEDIA_SUSPENDED: "SUSPENDED",
    MR_MEDIA_SUSPENDING: "SUSPENDING",
}

# mr_platEx / mr_plat 的成功返回码（mrporting.h: MR_IGNORE 1 表示"不关心/不支持"）
MR_IGNORE = 1
MR_PLAT_VALUE_BASE = 1000

# ---------------------------------------------------------------- 平台号
# 冒充一台 MTK 平台的 QVGA 屏幕功能机
MR_PLAT_VALUE = 0x1000        # 平台类型
MR_PLAT_CH_DBC = 1            # 中文字符集
MR_PLAT_SMS_UTF8 = 0

# 伪机型参数，MRP 通过 mr_getUserInfo / mr_plat 读到
DEVICE_MODEL = "MTK-QVGA"
DEVICE_VENDOR = "MTK"
IMEI = "860000000000000"
# IMSI：46000 = 中国移动，末 10 位是用户号
IMSI = "460000123456789"

# mr_userinfo 结构里各字段的偏移（mrporting.h / dl_mrporting.h）
#   uint8 IMEI[16]        +0
#   uint8 IMSI[16]        +16
#   char  manufactory[8]  +32
#   char  type[8]         +40
#   uint32 ver            +48
#   uint8 spare[12]       +52
USERINFO_IMEI_OFF = 0
USERINFO_IMSI_OFF = 16
USERINFO_MANUFACTORY_OFF = 32
USERINFO_TYPE_OFF = 40
USERINFO_VER_OFF = 48
USERINFO_SIZE = 64

# mr_getUserInfo 各字段的填充值
MANUFACTORY = "MTK"            # 厂商名（<=7 字符）
MODEL_TYPE = "MTK-QVGA"        # 机型（<=7 字符）
SW_VERSION = 0x00010000        # 软件版本（u32）
