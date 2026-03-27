import json
from nonebot import logger

from .userinfo import UserInfo
from .userinfo_manager import USER_INFO
from .static import USER_INFO_PATH as INFO_PATH

# ----------- File -----------

def loadUserInfo() -> dict:
    if not INFO_PATH.exists():
        return {}
    with open(INFO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def saveUserInfo(info: dict):
    with open(INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)

# ----------- Maintenance -----------

def setUserInfo(openID: str, data: dict | UserInfo):
    if isinstance(data, UserInfo):
        user_info = data
    else:
        user_info = USER_INFO.get(openID)
        user_info.set(
            qqID=data.get('qqID'),
            syToken=data.get('syToken'),
            lxID=data.get('lxID'),
            dataSource=data.get('dataSource')
        )
    USER_INFO.set(user_info)
    saveUserInfo(USER_INFO.exportJSON())

async def main():
    data = loadUserInfo()
    for openID, info in data.items():
        user_info = UserInfo(openID, info)
        USER_INFO.set(user_info)
    logger.success(f"Successfully loaded user info for {len(data)} users.")