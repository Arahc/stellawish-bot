class UserInfo:
    openID: str
    qqID: str | None
    syToken: str | None
    lxID: str | None
    dataSource: str = "sy"  # "sy" or "lx", "sy" default

    iconID: str = "0"
    plateID: str = "0"

    def __init__(self, openID: str, data: dict):
        self.openID = openID
        self.qqID = data.get('qqID')
        self.syToken = data.get('syToken')
        self.lxID =  data.get('lxID')
        self.dataSource = data.get('dataSource', "sy")
        self.iconID = str(data.get('iconID') or "0")
        self.plateID = str(data.get('plateID') or "0")
    
    def bindSource(
        self,
        qqID: str | None = None,
        syToken: str | None = None,
        lxID: str | None = None,
        dataSource: str | None = None
    ):
        if qqID is not None:
            self.qqID = qqID
        if syToken is not None:
            self.syToken = syToken
        if lxID is not None:
            self.lxID = lxID
        if dataSource is not None:
            self.dataSource = dataSource

    def setPersonal(self, iconID: str | None = None, plateID: str | None = None):
        if iconID is not None:
            self.iconID = iconID
        if plateID is not None:
            self.plateID = plateID
    
    def exportJSON(self) -> dict:
        return {
            "qqID": self.qqID,
            "syToken": self.syToken,
            "lxID": self.lxID,
            "dataSource": self.dataSource,
            "iconID": self.iconID,
            "plateID": self.plateID
        }

    def canB50(self) -> bool:
        if self.dataSource == "sy":
            return self.qqID is not None
        elif self.dataSource == "lx":
            return self.lxID is not None
        return False
