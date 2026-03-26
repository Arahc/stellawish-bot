from pathlib import Path
import os

def rgb(r: int, g: int, b: int) -> tuple[int, int, int]:
    return (r, g, b)

DIVEFISH_API_BASE_URL = "https://www.diving-fish.com/api/maimaidxprober"

DIVEFISH_B50_API_URL = DIVEFISH_API_BASE_URL + "/query/player"

LXNS_API_BASE_URL = "https://maimai.lxns.net/api/v0/maimai"
LXNS_ALL_CHARTS_API_URL = LXNS_API_BASE_URL + "/song/list"
LXNS_ALL_ALIASES_API_URL = LXNS_API_BASE_URL + "/alias/list"

BOT_PIC_DOMAIN = os.getenv("DOMAIN_BASE")

DATA_PATH = Path(__file__).parent.parent / "data"
SONG_INFO_PATH = DATA_PATH / "song_info.json"
USER_INFO_PATH = DATA_PATH / "user_info.json"

VERSION_DICT = {
    "maimai": (10000, "真"),
    "maimai PLUS": (11000, "真"),
    "GreeN": (12000, "超"),
    "GreeN PLUS": (13000, "檄"),
    "ORANGE": (14000, "橙"),
    "ORANGE PLUS": (15000, "晓"),
    "PiNK": (16000, "桃"),
    "PiNK PLUS": (17000, "樱"),
    "MURASAKi": (18000, "紫"),
    "MURASAKi PLUS": (18500, "堇"),
    "MiLK": (19000, "白"),
    "MiLK PLUS": (19500, "雪"),
    "FiNALE": (19900, "辉"),
    "舞萌DX": (20000, "熊华"),
    "舞萌DX 2021": (21000, "爽煌"),
    "舞萌DX 2022": (22000, "宙星"),
    "舞萌DX 2023": (23000, "祭祝"),
    "舞萌DX 2024": (24000, "双宴"),
    "舞萌DX 2025": (25000, "镜"),
    "舞萌DX 2026": (26000, "彩")
}

GENRE_DICT = {
    "POPSアニメ": "流行&动漫",
    "niconicoボーカロイド": "niconico&VOCALOID™",
    "東方Project": "东方Project",
    "ゲームバラエティ": "其他游戏",
    "maimai": "舞萌",
    "オンゲキCHUNITHM": "音击/中二节奏",
    "宴会場": "宴会场"
}

RATING_LIST = [
    (100.5, "SSS+", 0.224),
    (100.4999, "SSS", 0.222),
    (100, "SSS", 0.216),
    (99.9999, "SS+", 0.214),
    (99.5, "SS+", 0.211),
    (99, "SS", 0.208),
    (98.9999, "S+", 0.206),
    (98, "S+", 0.203),
    (97, "S", 0.2),
    (96.9999, "AAA", 0.176),
    (94, "AAA", 0.168),
    (90, "AA", 0.152),
    (80, "A", 0.136),
    (79.9999, "BBB", 0.128),
    (75, "BBB", 0.12),
    (70, "BB", 0.112),
    (60, "B", 0.096),
    (50, "C", 0.08),
    (40, "D", 0.064),
    (30, "D", 0.048),
    (20, "D", 0.032),
    (10, "D", 0.016),
    (0, "D", 0),
]

INFO_QUERY_PACK_KEY = {
    "sd": "SD",
    "Sd": "SD",
    "sD": "SD",
    "SD": "SD",
    "标": "SD",
    "dx": "DX",
    "Dx": "DX",
    "dX": "DX",
    "DX": "DX",
    "宴": "UT"
}
INFO_QUERY_DIFF_KEY = {
    "绿": 0,
    "黄": 1,
    "红": 2,
    "紫": 3,
    "白": 4
}

DIFF_NAME_LIST = ["Basic", "Advanced", "Expert", "Master", "Re:Master", "宴会场", "宴会场（1P）", "宴会场（2P）"]

STAR_DXRATE_LIST = [84.99, 89.99, 92.99, 94.99, 96.99, 98.99, 99.99, 100.00]

DIFF_COL_LIST = [
    [ rgb(105, 202, 73)  , rgb(112, 194, 119) , rgb(134, 210, 101) ], # Basic
    [ rgb(237, 182, 44)  , rgb(234, 194, 62)  , rgb(238, 200, 119) ], # Advanced
    [ rgb(233, 150, 157) , rgb(223, 159, 159) , rgb(236, 167, 167) ], # Expert
    [ rgb(157, 98, 203)  , rgb(182, 112, 194) , rgb(198, 151, 206) ], # Master
    [ rgb(243, 229, 245) , rgb(245, 216, 238) , rgb(251, 237, 247) ], # Re:Master
    [ rgb(219, 148, 219) , rgb(230, 157, 230) , rgb(218, 157, 230) ], # 宴会场
    [ rgb(219, 148, 219) , rgb(230, 157, 230) , rgb(218, 157, 230) ], # 宴会场 1P
    [ rgb(219, 148, 219) , rgb(230, 157, 230) , rgb(218, 157, 230) ]  # 宴会场 2P
]
DIFF_FONT_COL_LIST = [
    rgb(238, 245, 248), # Basic
    rgb(238, 245, 248), # Advanced
    rgb(238, 245, 248), # Expert
    rgb(238, 245, 248), # Master
    rgb(195, 70, 231),  # Re:Master
    rgb(238, 245, 248), # 宴会场
    rgb(238, 245, 248), # 宴会场 1P
    rgb(238, 245, 248)  # 宴会场 2P
]
PIC_FOOTER_COL = rgb(31, 30, 51)