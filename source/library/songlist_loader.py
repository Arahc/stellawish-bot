import httpx
import json
from nonebot import logger
from datetime import datetime

from .static import LXNS_ALL_CHARTS_API_URL as CHARTS_API_URL
from .static import LXNS_ALL_ALIASES_API_URL as ALIASES_API_URL
from .static import SONG_INFO_PATH
from .songlist_manager import SONG_LIST
from .songlist import SongList

# ----------- File -----------

async def fetchChartsAPI():
    param = {"notes": "true"}
    async with httpx.AsyncClient() as client:
        response = await client.get(CHARTS_API_URL, params=param)
        response.raise_for_status()
        return response.status_code, response.json()

async def fetchAliasesAPI():
    async with httpx.AsyncClient() as client:
        response = await client.get(ALIASES_API_URL)
        response.raise_for_status()
        return response.status_code, response.json()

def loadSongInfo() -> dict:
    if not SONG_INFO_PATH.exists():
        return {}
    with open(SONG_INFO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def saveSongInfo(info: dict):
    with open(SONG_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)

def getSongInfo(songlist: SongList) -> dict:
    info = {"aliases": [], "dates": []}
    for sid, song in songlist.items():
        info["aliases"].append({"songID": sid, "aliases": song.aliases})
        if song.sdPack is not None:
            info["dates"].append({"packID": song.sdPack.id, "info_date": song.sdPack.info_dat_date, "pic_date": song.sdPack.info_pic_date})
        if song.dxPack is not None:
            info["dates"].append({"packID": song.dxPack.id, "info_date": song.dxPack.info_dat_date, "pic_date": song.dxPack.info_pic_date})
        for pack in song.utPack:
            info["dates"].append({"packID": pack.id, "info_date": pack.info_dat_date, "pic_date": pack.info_pic_date})
    return info

def initSongInfo(songlist: SongList, info: dict):
    # aliases
    aliases = info.get("aliases", [])
    for entry in aliases:
        sid = int(entry['songID']) % 10000
        if sid not in songlist:
            logger.warning(f"Alias entry with song_id {entry['songID']} does not match any song in the song list, skipping.")
            continue
        songlist[sid].aliases = entry.get("aliases", [])
    # info update time
    dates = info.get("dates", [])
    for entry in dates:
        pid = int(entry['packID'])
        sid = pid % 10000
        if sid not in songlist:
            logger.warning(f"Date entry with pack_id {entry['packID']} does not match any song in the song list, skipping.")
            continue
        if songlist[sid].sdPack and songlist[sid].sdPack.id == pid:
            songlist[sid].sdPack.info_dat_date = entry.get("info_date", "")
            songlist[sid].sdPack.info_pic_date = entry.get("pic_date", "")
        elif songlist[sid].dxPack and songlist[sid].dxPack.id == pid:
            songlist[sid].dxPack.info_dat_date = entry.get("info_date", "")
            songlist[sid].dxPack.info_pic_date = entry.get("pic_date", "")
        else:
            for pack in songlist[sid].utPack:
                if pack.id == pid:
                    pack.info_dat_date = entry.get("info_date", "")
                    pack.info_pic_date = entry.get("pic_date", "")
                    break

def UpdateAliases(songlist: SongList, aliases: list):
    for entry in aliases:
        sid = int(entry['song_id']) % 10000
        if sid not in songlist:
            logger.warning(f"Alias entry with song_id {entry['song_id']} does not match any song in the song list, skipping.")
            continue
        song = songlist[sid]
        if song.aliases:
            continue
            # skip if aliases already exist for this song, to avoid overwriting manually added or deleted aliases
        song.aliases = entry.get("aliases", [])
    saveSongInfo(getSongInfo(songlist))

# ----------- Maintenance -----------

def getToday() -> str:
    return datetime.now().strftime("%Y-%m-%d") # xxxx-xx-xx

def updatePicDate(packID: int) -> bool:
    songlist = SONG_LIST.getSongList()
    sid = packID % 10000
    date = getToday()
    if sid not in songlist:
        logger.warning(f"Pack ID {packID} does not match any song in the song list, skipping pic date update.")
        return False
    if songlist[sid].sdPack and songlist[sid].sdPack.id == packID:
        if songlist[sid].sdPack.info_pic_date == date:
            return False
        songlist[sid].sdPack.info_pic_date = date
    elif songlist[sid].dxPack and songlist[sid].dxPack.id == packID:
        if songlist[sid].dxPack.info_pic_date == date:
            return False
        songlist[sid].dxPack.info_pic_date = date
    else:
        for pack in songlist[sid].utPack:
            if pack.id == packID:
                if pack.info_pic_date == date:
                    return False
                pack.info_pic_date = date
                break
    SONG_LIST.set(songlist)
    saveSongInfo(getSongInfo(songlist))
    return True

def _updatePicDate(songlist: SongList, songID: int):
    date = getToday()
    if songlist[songID].sdPack:
        songlist[songID].sdPack.info_pic_date = date
    if songlist[songID].dxPack:
        songlist[songID].dxPack.info_pic_date = date
    for pack in songlist[songID].utPack:
        pack.info_pic_date = date
    SONG_LIST.set(songlist)
    saveSongInfo(getSongInfo(songlist))

def addAlias(sid: int, alias: str) -> bool:
    songlist = SONG_LIST.getSongList()
    if alias in songlist[sid].aliases:
        return False
    songlist[sid].aliases.append(alias)
    _updatePicDate(songlist, sid)
    SONG_LIST.set(songlist)
    saveSongInfo(getSongInfo(songlist))
    return True

def delAlias(sid: int, alias: str) -> bool:
    songlist = SONG_LIST.getSongList()
    if alias in songlist[sid].aliases:
        songlist[sid].aliases.remove(alias)
        _updatePicDate(songlist, sid)
        SONG_LIST.set(songlist)
        saveSongInfo(getSongInfo(songlist))
        return True
    return False

# ----------- Main -----------

async def main():
    status1, data1 = await fetchChartsAPI()
    if status1 != 200:
        raise RuntimeError(f"Charts API request failed, HTTP status {status1}")
    charts = data1["songs"]
    songlist = SongList(charts)
    logger.success(f"Successfully cached chart data, total {len(data1['songs'])} entries.")

    songinfo = loadSongInfo()
    initSongInfo(songlist, songinfo)

    status2, data2 = await fetchAliasesAPI()
    if data2 is not None:
        UpdateAliases(songlist, data2["aliases"])
        logger.success(f"Successfully cached alias data, total {len(data2['aliases'])} entries.")
    else:
        logger.warning(f"Aliases caching failed, HTTP status {status2}, skipping alias update.")

    for chart in charts:
        if "alias" not in chart:
            chart["alias"] = []
    
    SONG_LIST.set(songlist)
    logger.success("Song list updated successfully.")