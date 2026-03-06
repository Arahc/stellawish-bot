from pathlib import Path
import os

DIVEFISH_API_BASE_URL = "https://www.diving-fish.com/api/maimaidxprober"

DIVEFISH_ALL_CHARTS_API_URL = DIVEFISH_API_BASE_URL + "/music_data"
DIVEFISH_B50_API_URL = DIVEFISH_API_BASE_URL + "/query/player"


LXNS_ALL_ALIASES_API_URL = "https://maimai.lxns.net/api/v0/maimai/alias/list"

BOT_PIC_DOMAIN = os.getenv("DOMAIN_BASE")

DATA_PATH = Path(__file__).parent.parent / "data"

SONG_LIST_PATH = DATA_PATH / "all_charts.json"
SONG_LIST_ETAG_PATH = DATA_PATH / "all_charts.etag"
DIVEFISH_BIND_PATH = DATA_PATH / "divefish_bind.json"

VERSION_DICT = {
    "maimai": "真",
    "maimai PLUS": "真",
    "maimai GreeN": "超",
    "maimai GreeN PLUS": "檄",
    "maimai ORANGE": "橙",
    "maimai ORANGE PLUS": "晓",
    "maimai PiNK": "桃",
    "maimai PiNK PLUS": "樱",
    "maimai MURASAKi": "紫",
    "maimai MURASAKi PLUS": "堇",
    "maimai MiLK": "白",
    "maimai MiLK PLUS": "雪",
    "maimai FiNALE": "辉",
    "舞萌 DX": "熊华",
    "舞萌 DX 2021": "爽煌",
    "舞萌 DX 2022": "宙星",
    "舞萌 DX 2023": "祭祝",
    "舞萌 DX 2024": "双宴",
    "舞萌 DX 2025": "镜"
}
VERSION_LIST = list(VERSION_DICT.keys())

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
    "标": "SD",
    "dx": "DX",
    "宴": "宴"
}
INFO_QUERY_DIFF_KEY = {
    "绿": 0,
    "黄": 1,
    "红": 2,
    "紫": 3,
    "白": 4
}
DIFF_NAME_LIST = ["🟩Basic", "🟨Advanced", "🟥Expert", "🟪Master", "⬜Re:Master"]