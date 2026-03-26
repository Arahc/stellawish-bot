from .userinfo import UserInfo

class UserInfoManager:
    def __init__(self):
        self._userinfo: dict[str, UserInfo] = {}

    def set(self, user_info: UserInfo):
        self._userinfo[user_info.openID] = user_info

    def get(self, openID: str) -> UserInfo:
        if openID in self._userinfo:
            return self._userinfo[openID]
        res = UserInfo(openID, {})
        self._userinfo[openID] = res
        return res
    
    def exportJSON(self) -> dict[str, dict]:
        return {openID: info.exportJSON() for openID, info in self._userinfo.items()}

USER_INFO = UserInfoManager()
