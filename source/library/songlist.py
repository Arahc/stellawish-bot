from .static import RATING_LIST

class Chart:
    tap: int = 0
    hold: int = 0
    slide: int = 0
    touch: int = 0
    breaks: int = 0
    diff: float = 0.0 # difficulty is usually one decimal number
    diffid: int = 0 # difficulty id: 0 green, 1 yellow, 2 red, 3 purple, 4 white
    charter: str = "-" # "-" means unknown

    def __init__(self, chart:dict, diff: float, diffid: int):
        self.tap = chart['notes'][0]
        self.hold = chart['notes'][1]
        self.slide = chart['notes'][2]
        self.touch = chart['notes'][3]
        self.breaks = chart['notes'][4]
        self.diff = diff
        self.diffid = diffid
        self.charter = chart['charter']
    
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
        for i in range(len(RATING_LIST)):
            if acc >= RATING_LIST[i][0]:
                return int(RATING_LIST[i][2] * self.diff * acc)
        return 0

class PartyChart:
    tap: int = 0
    hold: int = 0
    slide: int = 0
    touch: int = 0
    breaks: int = 0
    diff: str = "0?" # difficulty is usually "xxx?"
    diffid: int = 0
    type: str = "normal" # type is "normal" (normal party chart) or "1P" or "2P" (two players needed chart)
    charter: str = "-"

    def __init__(self, chart:dict, diff: str, type: str):
        self.tap = chart['notes'][0]
        self.hold = chart['notes'][1]
        self.slide = chart['notes'][2]
        self.touch = chart['notes'][3]
        self.breaks = chart['notes'][4]
        self.diff = diff
        self.type = type
        if type == "normal":
            self.diffid = 5
        elif type == "1P":
            self.diffid = 6
        else:
            self.diffid = 7
    
    def exportJSON(self) -> tuple[dict, str]:
        return {
            "notes": [self.tap, self.hold, self.slide, self.touch, self.breaks],
        }, self.diff

    def getRank(self, acc: float) -> str:
        if self.type == "normal":
            for i in range(len(RATING_LIST)):
                if acc >= RATING_LIST[i][0]:
                    return RATING_LIST[i][1]
        else:
            for i in range(len(RATING_LIST)):
                if acc >= RATING_LIST[i][0]*2:
                    return RATING_LIST[i][1]
        return "D"

class ChartPack:
    id: int = 0
    version: str = ""
    type: str = "SD"
    # charts: list[Chart] = []

    def __init__(self, music:dict):
        self.id = int(music['id'])
        self.version = music['basic_info']['from']
        self.type = music['type']
        self.charts = [Chart(music['charts'][i], float(music['ds'][i]), i) for i in range(len(music['charts']))]

    def exportJSON(self) -> tuple[list[dict], list[float], int, str]:
        charts = []
        ds = []
        for chart in self.charts:
            chart_entry, diff = chart.exportJSON()
            charts.append(chart_entry)
            ds.append(diff)
        return charts, ds, self.id, self.version

class PartyChartPack:
    id: int = 0
    version: str = ""
    type: str = "宴"
    _type: str = "SD"
    tag: str = "[宴]"
    # charts: list[PartyChart] = []

    def __init__(self, music:dict):
        self.id = int(music['id'])
        self.version = music['basic_info']['from']
        self.charts = []
        self._type = music['type']
        self.tag = music['title'][:3]
        if len(music['charts']) == 1:
            self.charts = [PartyChart(music['charts'][0], music['level'][0], "normal")]
        else:
            self.charts = [
                PartyChart(music['charts'][0], music['level'][0], "1P"),
                PartyChart(music['charts'][1], music['level'][1], "2P")
            ]
    
    def exportJSON(self) -> tuple[list[dict], list[str], int, str, str, str]:
        charts = []
        level = []
        for chart in self.charts:
            chart_entry, diff = chart.exportJSON()
            charts.append(chart_entry)
            level.append(diff)
        return charts, level, self.id, self.version, self._type, self.tag

class Song:
    id: int = 0
    title: str = ""
    artist: str = ""
    bpm: int = 0
    genre: str = ""
    # aliases: list[str] = []
    sdChart: ChartPack | None = None
    dxChart: ChartPack | None = None
    # partyChart: list[PartyChartPack] = []

    def __init__(self, music:dict):
        self.id = int(music['id']) % 10000
        self.title = music['title']
        self.artist = music['basic_info']['artist']
        self.bpm = int(music['basic_info']['bpm'])
        self.genre = music['basic_info']['genre']
        self.aliases = music['alias']
        self.partyChart = []
        self.chartID = {}
        self.mergeChart(music)
    
    def mergeChart(self, music:dict):
        if int(music['id']) >= 100000:
            pack = PartyChartPack(music)
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
            charts, ds, id, version = self.sdChart.exportJSON()
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
                "charts": charts
            })
        if self.dxChart:
            charts, ds, id, version = self.dxChart.exportJSON()
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
                "charts": charts
            })
        if self.partyChart:
            for party in self.partyChart:
                charts, level, id, version, type, tag = party.exportJSON()
                res.append({
                    "id": id,
                    "type": type,
                    "title": (tag+self.title if tag not in self.title else self.title),
                    "basic_info": {
                        "artist": self.artist,
                        "bpm": self.bpm,
                        "genre": self.genre,
                        "from": version
                    },
                    "alias": self.aliases,
                    "level": level,
                    "type": type,
                    "charts": charts
                })
        return res

    def getCharts(self) -> list[ChartPack | PartyChartPack]:
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

    def findByID(self, id: int) -> tuple[Song | None, ChartPack | PartyChartPack | None]:
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