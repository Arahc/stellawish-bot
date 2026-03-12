from typing import Optional
import httpx
from nonebot import logger
from datetime import datetime

from .static import DIVEFISH_ALL_CHARTS_API_URL as CHARTS_API_URL
from .static import SONG_LIST_ETAG_PATH as ETAG_PATH
from .static import LXNS_ALL_ALIASES_API_URL as ALIASES_API_URL
from .songlist_manager import SONG_LIST
from .songlist import SongList

# ----------- File -----------

async def fetchChartsAPI(etag: Optional[str] = None):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag

    async with httpx.AsyncClient() as client:
        response = await client.get(CHARTS_API_URL, headers=headers)
        new_etag = response.headers.get("ETag")

        if response.status_code == 304:
            return 304, None, new_etag

        response.raise_for_status()
        return response.status_code, response.json(), new_etag

def loadETAG() -> Optional[str]:
    if ETAG_PATH.exists():
        return ETAG_PATH.read_text(encoding="utf-8").strip()
    return None

def saveETAG(etag: str):
    ETAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ETAG_PATH.write_text(etag, encoding="utf-8")

async def fetchAliasesAPI():
    async with httpx.AsyncClient() as client:
        response = await client.get(ALIASES_API_URL)
        response.raise_for_status()
        return response.status_code, response.json()

def UpdateAliases(charts: list[dict], aliases: list[dict]):
    if not charts or not aliases:
        return
    for chart in charts:
        chart["alias"] = []
        for entry in aliases:
            sx_id = int(entry.get("song_id"))
            if not sx_id:
                continue
            if sx_id > 100000:
                continue
            if int(chart["id"]) % 10000 == sx_id:
                chart["alias"].extend(entry.get("aliases", []))
                break

# ----------- Maintenance -----------

def getToday() -> str:
    return datetime.now().strftime("%Y-%m-%d") # xxxx-xx-xx

def addAlias(sid: int, alias: str) -> bool:
    songlist = SONG_LIST.getSongList()
    if alias in songlist[sid].aliases:
        return False
    songlist[sid].aliases.append(alias)
    songlist[sid].info_dat_date = getToday()
    SONG_LIST.set(songlist)
    return True

def delAlias(sid: int, alias: str) -> bool:
    songlist = SONG_LIST.getSongList()
    if alias in songlist[sid].aliases:
        songlist[sid].aliases.remove(alias)
        songlist[sid].info_dat_date = getToday()
        SONG_LIST.set(songlist)
        return True
    return False

def mergeCharts(old: list[dict], new: list[dict]):
    old_dict = {entry["id"]: entry for entry in old}
    print(old_dict)
    old_ids = list(old_dict.keys())
    for entry in new:
        song_id = int(entry["id"])
        entry["info_dat_date"] = getToday()
        if song_id in old_ids:
            entry["alias"] = old_dict[song_id].get("alias", [])
            logger.info(f"Merged alias for song ID {song_id}: {entry['alias']}")
        else:
            logger.info(f"No old entry for song ID {song_id}, skipping alias merge.")

# ----------- Main -----------

TO_CHINA_VERSION_NAME = {
    "maimai でらっくす": "舞萌 DX",
    "maimai でらっくす PLUS": "舞萌 DX",
    "maimai でらっくす Splash": "舞萌 DX 2021",
    "maimai でらっくす Splash PLUS": "舞萌 DX 2021",
    "maimai でらっくす UNiVERSE": "舞萌 DX 2022",
    "maimai でらっくす UNiVERSE PLUS": "舞萌 DX 2022",
    "maimai でらっくす FESTiVAL": "舞萌 DX 2023",
    "maimai でらっくす FESTiVAL PLUS": "舞萌 DX 2023",
    "maimai でらっくす BUDDiES": "舞萌 DX 2024",
    "maimai でらっくす BUDDiES PLUS": "舞萌 DX 2024",
    "maimai でらっくす PRiSM": "舞萌 DX 2025",
    "maimai でらっくす PRiSM PLUS": "舞萌 DX 2026",
}

async def main(load_alias: bool = True):
    saved_etag = loadETAG()
    status_1, charts, new_etag = await fetchChartsAPI(saved_etag)
    if status_1 == 304:
        logger.success("Success to load cached music data.")
        SONG_LIST.reload_from_file()
        charts = SONG_LIST.getSongList().exportJSON()
    elif status_1 == 200 and charts is not None:
        if new_etag:
            saveETAG(new_etag)
        logger.success(f"Successfully cached new data, total {len(charts)} entries.")
        try:
            SONG_LIST.reload_from_file()
            old_songlist = SONG_LIST.getSongList().exportJSON()
            mergeCharts(old_songlist, charts)
        except Exception as e:
            logger.info(f"Old songlist load failed, skip merging.")
    else:
        logger.error(f"Charts caching failed, HTTP status {status_1}")

    for chart in charts:
        if not chart["basic_info"]["from"].startswith("maimai"):
            chart["basic_info"]["from"] = "maimai " + chart["basic_info"]["from"]
        if chart["basic_info"]["from"] in TO_CHINA_VERSION_NAME:
            chart["basic_info"]["from"] = TO_CHINA_VERSION_NAME[chart["basic_info"]["from"]]
        if chart["basic_info"]["from"].startswith("maimai 舞萌 DX"):
            chart["basic_info"]["from"] = chart["basic_info"]["from"][7:]

    for chart in charts:
        if chart["type"] == "DX":
            continue
        for c in chart["charts"]:
            if len(c["notes"]) == 4:
                c["notes"] = c["notes"][:3] + [0] + c["notes"][3:]

    if load_alias:
        status_2, aliases = await fetchAliasesAPI()
        UpdateAliases(charts, aliases["aliases"])
        if aliases is not None:
            logger.success(f"Successfully cached alias data, total {len(aliases['aliases'])} entries.")
        else:
            logger.error(f"Aliases caching failed, HTTP status {status_2}")
    else:
        logger.info("Skipped loading alias from lxns.net")

    for chart in charts:
        if "alias" not in chart:
            chart["alias"] = []
    
    SONG_LIST.set(SongList(charts))
    SONG_LIST.save_to_file()