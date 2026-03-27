from .static import RATING_LIST, VERSION_DICT, GENRE_DICT

class Chart:
    def __init__(self, chart:dict, diffid: int, notes: dict):
        self.tap = notes['tap']
        self.hold = notes['hold']
        self.slide = notes['slide']
        self.touch = notes['touch']
        self.breaks = notes['break']
        self.diff = (chart['level'] if int(chart['level_value']) == 0 else float(chart['level_value']))
        self.diffid = diffid
        self.charter = chart['note_designer']

    def getTotalNotes(self) -> int:
        return self.tap + self.hold + self.slide + self.touch + self.breaks
    def getMaxDXscore(self) -> int:
        return self.getTotalNotes() * 3
    def getScoreInfo(self) -> tuple[int, int]:
        return (
            self.tap + self.hold*2 + self.slide*3 + self.touch + self.breaks*5,
            self.breaks
        )
    def getRank(self, acc: float) -> str:
        for i in range(len(RATING_LIST)):
            if acc >= RATING_LIST[i][0]:
                return RATING_LIST[i][1]
        return "D"
    def getRating(self, acc: float) -> int:
        if self.diffid > 4:
            return 0
        for i in range(len(RATING_LIST)):
            if acc >= RATING_LIST[i][0]:
                return int(RATING_LIST[i][2] * self.diff * acc)
        return 0

def _getVersion(verID: int) -> str:
    mxID = 10000
    res = "maimai"
    for name, item in VERSION_DICT.items():
        id = item[0]
        if verID >= id and id > mxID:
            mxID = id
            res = name
    return res

class ChartPack:
    def __init__(self, pack: list, id: int):
        self.id = id
        diff0 = pack[0]
        self.version = _getVersion(diff0['version'])
        self.info_dat_date = "1111-11-11"
        self.info_pic_date = "0000-00-00"
        if self.id >= 100000:
            self.tag = diff0['kanji']
            self.type = "UT"
            if diff0['is_buddy']:
                self.charts = [
                    Chart(pack[0], 6, pack[0]['notes']['left']),
                    Chart(pack[0], 7, pack[0]['notes']['right'])
                ]
            else:
                self.charts = [Chart(pack[0], 5, pack[0]['notes'])]
        else:
            self.tag = ""
            self.type = ("SD" if diff0['type'] == "standard" else "DX")
            self.charts = [Chart(pack[i], i, pack[i]['notes']) for i in range(len(pack))]

def _toSDid(id: int) -> int:
    return id % 10000

def _toDXid(id: int) -> int:
    return id % 10000 + 10000

class Song:
    def __init__(self, song:dict):
        self.id = int(song['id']) % 10000
        self.title = song['title']
        if int(song['id']) >= 100000:
            self.title = song['title'][3:]
        self.artist = song['artist']
        self.bpm = int(song['bpm'])
        self.genre = GENRE_DICT.get(song['genre'], song['genre'])
        self.map = song.get("map", "无")
        self.aliases = []
        self.sdPack = None
        self.dxPack = None
        self.utPack = []
        if song['difficulties']['standard']:
            self.sdPack = ChartPack(song['difficulties']['standard'], _toSDid(self.id))
        if song['difficulties']['dx']:
            self.dxPack = ChartPack(song['difficulties']['dx'], _toDXid(self.id))
        if int(song['id']) >= 100000:
            self.utPack.append(ChartPack(song['difficulties']['utage'], int(song['id'])))
        self.mergeChart(song)

    def mergeChart(self, song:dict):
        if int(song['id']) >= 100000:
            self.utPack.append(ChartPack(song['difficulties']['utage'], int(song['id'])))
        else:
            if song['difficulties']['standard']:
                self.sdPack = ChartPack(song['difficulties']['standard'], _toSDid(self.id))
            if song['difficulties']['dx']:
                self.dxPack = ChartPack(song['difficulties']['dx'], _toDXid(self.id))

    def getCharts(self) -> list[ChartPack]:
        res = []
        if self.sdPack:
            res.append(self.sdPack)
        if self.dxPack:
            res.append(self.dxPack)
        for party in self.utPack:
            res.append(party)
        return res

    def getID(self) -> dict[str, int]:
        res = {}
        if self.sdPack:
            res['SD'] = self.sdPack.id
        if self.dxPack:
            res['DX'] = self.dxPack.id
        for party in self.utPack:
            res[party.tag] = party.id
        return res
            
class SongList(dict[int, Song]):
    def __init__(self, charts: list[dict]):
        super().__init__()
        for song in charts:
            song_id = int(song['id']) % 10000
            if song_id not in self:
                self[song_id] = Song(song)
            else:
                self[song_id].mergeChart(song)

    def findByTitle(self, text: str) -> list[Song]:
        res = []
        text = text.strip().lower()
        for song in self.values():
            if text in song.title or text in song.alias:
                res.append(song)
        return res

    def findByID(self, id: int) -> tuple[Song | None, ChartPack | None]:
        sid = id % 10000
        if sid in self:
            song = self[sid]
            if song.sdPack is not None and song.sdPack.id == id:
                return song, song.sdPack
            if song.dxPack is not None and song.dxPack.id == id:
                return song, song.dxPack
            for party in song.utPack:
                if party.id == id:
                    return song, party
        return None, None