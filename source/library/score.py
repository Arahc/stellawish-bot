from .song import Chart, ChartPack, Song
from .song_manager import SONG_LIST
from .static import STAR_DXRATE_LIST
from .score_ra_calcer import RatingCalcer, defaultRaCalcer

class Score:
    def __init__(self, song: Song, pack: ChartPack, chart: Chart,
                 acc: float, dx_score: int | None, 
                 fc: str, fs: str, date: str | None):
        self.song = song
        self.chart = chart
        self.pack = pack
        self.acc = round(acc, 4) # round to 4 decimal places for consistent display
        self.dxScore = dx_score
        self.fc = fc
        self.fs = fs
        self.date = date if date is not None else "-"
        # date is in format "YYYY-MM-DD" or "-" if not available

    @classmethod
    def loadFromSY(cls, data: dict):
        songlist = SONG_LIST.getSongList()
        pid = int(data['song_id'])

        song, pack= songlist.findByID(pid)
        chart = pack.charts[int(data['level_index'])]
        acc = float(data['achievements'])
        dxScore = int(data['dxScore'])
        fc = data['fc'] # in SY, fc and fs are empty string if not achieved
        fs = data['fs']
        date = '-' # SY does not provide date information\
        return cls(song, pack, chart, acc, dxScore, fc, fs, date)

    @classmethod
    def loadFromLX(cls, data: dict):
        songlist = SONG_LIST.getSongList()
        sid = int(data['id'])

        song = songlist[sid]
        if data['type'] == 'standard':
            pack = song.sdPack
        else:
            pack = song.dxPack
        chart = pack.charts[int(data['level_index'])]
        acc = float(data['achievements'])
        dxScore = int(data['dx_score'])
        fc = data['fc'] or "" # in LX, fc and fs are null if not achieved
        fs = data['fs'] or ""
        date = data['play_time'][:10] if data.get('play_time') else '-' # in format "YYYY-MM-DD" or "-" if not available. The provided string is "YYYY-MM-DDTHH:MM:SSZ" such as "2026-02-07T12:18:11Z"
        return cls(song, pack, chart, acc, dxScore, fc, fs, date)

    def getStar(self) -> int:
        mxDXScore = self.chart.getMaxDXscore()
        rate = int(self.dxScore / mxDXScore * 10000) / 100
        res = 0
        for i in range(len(STAR_DXRATE_LIST)):
            if rate > STAR_DXRATE_LIST[i]:
                res = i + 1
        if res > 7:
            res = 7
        return res

    def getRating(self, calcer: RatingCalcer | None = None) -> int | float:
        if calcer is None:
            calcer = defaultRaCalcer()
        return calcer(self)


class ScoreList(list[Score]):
    def __init__(self, scores: list[Score], source: str, raCalcer: RatingCalcer | None = None):
        super().__init__(scores or [])
        self.source = source
        if raCalcer is None:
            raCalcer = defaultRaCalcer()
        self.raCalcer = raCalcer

    @classmethod
    def loadFromSY(cls, data: list[dict], raCalcer: RatingCalcer | None = None):
        scores = [Score.loadFromSY(item) for item in data]
        return cls(scores, "sy", raCalcer)

    @classmethod
    def loadFromLX(cls, data: list[dict], raCalcer: RatingCalcer | None = None):
        scores = [Score.loadFromLX(item) for item in data]
        return cls(scores, "lx", raCalcer)

    @property
    def ra(self) -> int | float:
        return sum(score.getRating(self.raCalcer) for score in self)

    def sortByRa(self):
        self.sort(key=lambda x: x.getRating(self.raCalcer), reverse=True) # from ra highest to lowest
    def sortByAcc(self):
        self.sort(key=lambda x: x.acc, reverse=True) # from acc highest to lowest
    def sortByDate(self):
        self.sort(key=lambda x: x.date, reverse=True) # from date newest to oldest