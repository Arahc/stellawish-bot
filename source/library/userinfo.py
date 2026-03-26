class UserInfo:
    openID: str
    qqID: str | None
    syToken: str | None
    lxID: str | None
    b50Source: str = "sy"  # "sy" or "lx", "sy" default

    def __init__(self, openID: str, data: dict):
        self.openID = openID
        self.qqID = data.get('qqID')
        self.syToken = data.get('syToken')
        self.lxID =  data.get('lxID')
        self.b50Source = data.get('b50Source', "sy")
    
    def set(
        self,
        qqID: str | None = None,
        syToken: str | None = None,
        lxID: str | None = None,
        b50Source: str | None = None
    ):
        if qqID is not None:
            self.qqID = qqID
        if syToken is not None:
            self.syToken = syToken
        if lxID is not None:
            self.lxID = lxID
        if b50Source is not None:
            self.b50Source = b50Source
    
    def exportJSON(self) -> dict:
        return {
            "qqID": self.qqID,
            "syToken": self.syToken,
            "lxID": self.lxID,
            "b50Source": self.b50Source
        }

    def canB50(self) -> bool:
        if self.b50Source == "sy":
            return self.qqID is not None
        elif self.b50Source == "lx":
            return self.lxID is not None
        return False