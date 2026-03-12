from .static import RATING_LIST

class Chart:
    tap: int = 0
    hold: int = 0
    slide: int = 0
    touch: int = 0
    breaks: int = 0
    diff: float | str = 0.0 # difficulty is usually one decimal number or "xxx?"
    diffid: int = 0 # difficulty id: 0 绿, 1 黄, 2 红, 3 紫, 4 白, 5 普通宴, 6 双人宴 1P, 7 双人宴 2P
    charter: str = "-" # "-" means unknown

    def __init__(self, chart:dict, diff: float | str, diffid: int):
        self.tap = chart['notes'][0]
        self.hold = chart['notes'][1]
        self.slide = chart['notes'][2]
        self.touch = chart['notes'][3]
        self.breaks = chart['notes'][4]
        self.diff = diff
        self.diffid = diffid
        self.charter = chart.get('charter', '-')
    
    def exportJSON(self) -> tuple[dict, float]:
        return {
            "notes": [self.tap, self.hold, self.slide, self.touch, self.breaks],
            "charter": self.charter
        }, self.diff

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

class ChartPack:
    id: int = 0
    version: str = ""
    type: str = "SD"
    tag: str = ""
    # charts: list[Chart] = []

    def __init__(self, music:dict):
        self.id = int(music['id'])
        self.version = music['basic_info']['from']
        if self.id >= 100000:
            self.tag = music['title'][:3]
            self.type = "宴"
            self.charts = [Chart(music['charts'][i], music['level'][i], i + 5) for i in range(len(music['charts']))]
        else:
            self.type = music['type']
            self.charts = [Chart(music['charts'][i], float(music['ds'][i]), i) for i in range(len(music['charts']))]

    def exportJSON(self) -> tuple[list[dict], list[float | str], int, str, str]:
        charts = []
        diffs = []
        for chart in self.charts:
            chart_entry, diff = chart.exportJSON()
            charts.append(chart_entry)
            diffs.append(diff)
        return charts, diffs, self.id, self.version, self.tag

class Song:
    id: int = 0
    title: str = ""
    artist: str = ""
    bpm: int = 0
    genre: str = ""
    # aliases: list[str] = []
    sdChart: ChartPack | None = None
    dxChart: ChartPack | None = None
    # partyChart: list[ChartPack] = []

    info_dat_date: str = "1111-11-11" # last time this song's info updated
    info_pic_data: str = "0000-00-00" # which date the latest picture info of this song was based on. Use the two fields to determine whether the song's picture info needs to be updated

    def __init__(self, music:dict):
        self.id = int(music['id']) % 10000
        self.title = music['title']
        if music['id'] >= 100000:
            self.title = music['title'][3:]
        self.artist = music['basic_info']['artist']
        self.bpm = int(music['basic_info']['bpm'])
        self.genre = music['basic_info']['genre']
        self.aliases = music['alias']
        self.partyChart = []
        self.chartID = {}
        self.mergeChart(music)
        self.info_dat_date = music.get('info_dat_date', "1111-11-11")
        self.info_pic_data = music.get('info_pic_data', "0000-00-00")

    def mergeChart(self, music:dict):
        if int(music['id']) >= 100000:
            pack = ChartPack(music)
            self.chartID[pack.id] = pack
            self.partyChart.append(pack)
        elif music['type'] == "SD":
            pack = ChartPack(music)
            self.chartID[pack.id] = pack
            self.sdChart = pack
        elif music['type'] == "DX":
            pack = ChartPack(music)
            self.chartID[pack.id] = pack
            self.dxChart = pack
    
    def exportJSON(self) -> list[dict]:
        res = []
        if self.sdChart:
            charts, ds, id, version, tag = self.sdChart.exportJSON()
            res.append({
                "id": id,
                "type": "SD",
                "title": self.title,
                "basic_info": {
                    "artist": self.artist,
                    "bpm": self.bpm,
                    "genre": self.genre,
                    "from": version
                },
                "alias": self.aliases,
                "ds": ds,
                "charts": charts,
                "info_dat_date": self.info_dat_date,
                "info_pic_data": self.info_pic_data
            })
        if self.dxChart:
            charts, ds, id, version, tag = self.dxChart.exportJSON()
            res.append({
                "id": id,
                "type": "DX",
                "title": self.title,
                "basic_info": {
                    "artist": self.artist,
                    "bpm": self.bpm,
                    "genre": self.genre,
                    "from": version
                },
                "alias": self.aliases,
                "ds": ds,
                "charts": charts,
                "info_dat_date": self.info_dat_date,
                "info_pic_data": self.info_pic_data
            })
        if self.partyChart:
            for party in self.partyChart:
                charts, level, id, version, tag = party.exportJSON()
                res.append({
                    "id": id,
                    "type": "宴",
                    "title": (tag+self.title if tag not in self.title else self.title),
                    "basic_info": {
                        "artist": self.artist,
                        "bpm": self.bpm,
                        "genre": self.genre,
                        "from": version
                    },
                    "alias": self.aliases,
                    "level": level,
                    "charts": charts,
                    "info_dat_date": self.info_dat_date,
                    "info_pic_data": self.info_pic_data
                })
        return res

    def getCharts(self) -> list[ChartPack]:
        res = []
        if self.sdChart:
            res.append(self.sdChart)
        if self.dxChart:
            res.append(self.dxChart)
        for party in self.partyChart:
            res.append(party)
        return res

    def getID(self) -> dict[str, int]:
        res = {}
        if self.sdChart:
            res['SD'] = self.sdChart.id
        if self.dxChart:
            res['DX'] = self.dxChart.id
        for party in self.partyChart:
            res[party.tag] = party.id
        return res
            
class SongList(dict[int, Song]):
    def __init__(self, charts: list[dict]):
        super().__init__()
        for music in charts:
            song_id = int(music['id']) % 10000
            if song_id not in self:
                self[song_id] = Song(music)
            else:
                self[song_id].mergeChart(music)

    def exportJSON(self) -> list[dict]:
        res = []
        for song in self.values():
            res.extend(song.exportJSON())
        return res

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
            if song.sdChart is not None and song.sdChart.id == id:
                return song, song.sdChart
            if song.dxChart is not None and song.dxChart.id == id:
                return song, song.dxChart
            for party in song.partyChart:
                if party.id == id:
                    return song, party
        return None, None