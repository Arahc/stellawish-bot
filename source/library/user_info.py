import json

from .static import DIVEFISH_BIND_PATH as INFO_PATH

# ----------- Info -----------

def saveInfo(data: dict):
    INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INFO_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True)

def loadInfo() -> dict:
    if INFO_PATH.exists():
        with INFO_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    return {}

def canFetchB50(open_id: str) -> bool:
    info = loadInfo()
    if open_id in info and 'qqID' in info[open_id]:
        return True
    return False

# ----------- Maintenance -----------

def addInfo(open_id: str, qq_id: str | None, token: str | None):
    info=loadInfo()
    if open_id not in info:
        info[open_id] = {}
    if qq_id:
        info[open_id]['qqID'] = qq_id
    if token:
        info[open_id]['token'] = token
    saveInfo(info)

def getUserInfo(open_id: str) -> dict | None:
    info = loadInfo()
    if open_id in info:
        return info[open_id]
    return None
