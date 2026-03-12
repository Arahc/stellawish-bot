from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto
import re

from .songlist import Song, ChartPack, Chart, SongList
from .static import INFO_QUERY_PACK_KEY, INFO_QUERY_DIFF_KEY

@dataclass
class QueryPolicy:
    allow_song: bool = False
    allow_pack: bool = False
    allow_party: bool = False
    allow_chart: bool = False

@dataclass
class QueryIntent:
    title: Optional[str] = None
    type: Optional[str] = None # "SD", "DX", "宴"
    diff: Optional[int] = None # 绿 0, 黄 1, 红 2, 紫 3, 白 4
    id: Optional[int] = None

class QueryIntentParser:
    @classmethod
    def parse(cls, text: str) -> list[QueryIntent]:
        text = text.strip().lower()
        res = [] # candidates of QueryIntent
        id_pattern = re.fullmatch(r"id\s*(\d+)", text, re.IGNORECASE)
        if id_pattern:
            res.append(QueryIntent(id=int(id_pattern.group(1))))
        else:
            res.append(QueryIntent(title=text))
        for pre, diff in INFO_QUERY_DIFF_KEY.items():
            if text.startswith(pre):
                rest = text[len(pre):].strip()
                id_pattern = re.fullmatch(r"id\s*(\d+)", rest, re.IGNORECASE)
                if id_pattern:
                    res.append(QueryIntent(id=int(id_pattern.group(1)), diff=diff))
                else:
                    res.append(QueryIntent(title=rest, diff=diff))
                for pre2, pack in INFO_QUERY_PACK_KEY.items():
                    if rest.startswith(pre2):
                        rest2 = rest[len(pre2):].strip()
                        id_pattern = re.fullmatch(r"id\s*(\d+)", rest2, re.IGNORECASE)
                        if id_pattern:
                            res.append(QueryIntent(id=int(id_pattern.group(1)), type=pack, diff=diff))
                        else:
                            res.append(QueryIntent(title=rest2, type=pack, diff=diff))
        for pre, pack in INFO_QUERY_PACK_KEY.items():
            if text.startswith(pre):
                rest = text[len(pre):].strip()
                id_pattern = re.fullmatch(r"id\s*(\d+)", rest, re.IGNORECASE)
                if id_pattern:
                    res.append(QueryIntent(id=int(id_pattern.group(1)), type=pack))
                else:
                    res.append(QueryIntent(title=rest, type=pack))
                for pre2, diff in INFO_QUERY_DIFF_KEY.items():
                    if rest.startswith(pre2):
                        rest2 = rest[len(pre2):].strip()
                        id_pattern = re.fullmatch(r"id\s*(\d+)", rest2, re.IGNORECASE)
                        if id_pattern:
                            res.append(QueryIntent(id=int(id_pattern.group(1)), type=pack, diff=diff))
                        else:
                            res.append(QueryIntent(title=rest2, type=pack, diff=diff))
        return res

class InfoTargetType(Enum):
    SONG = auto()
    PACK = auto()
    CHART = auto()

@dataclass
class InfoTarget:
    type: InfoTargetType
    song: Song
    pack: ChartPack | None = None
    chart: Chart | None = None

class QueryEngine:
    def __init__(self, songlist: SongList):
        self.songlist = songlist
        self.song_entries: list[InfoTarget] = []
        self.pack_entries: list[InfoTarget] = []
        self.chart_entries: list[InfoTarget] = []
        self._build()
    
    def _build(self):
        for song in self.songlist.values():
            self.song_entries.append(
                InfoTarget(type=InfoTargetType.SONG, song=song)
            )
            for pack in song.getCharts():
                self.pack_entries.append(
                    InfoTarget(type=InfoTargetType.PACK, song=song, pack=pack)
                )
                for chart in pack.charts:
                    self.chart_entries.append(
                        InfoTarget(type=InfoTargetType.CHART, song=song, pack=pack, chart=chart)
                    )
    
    def _matchTitle(self, indent: QueryIntent, song: Song) -> bool:
        if not indent.title:
            return True
        t = indent.title
        return (
            t == song.title.lower() or
            any(t == alias.lower() for alias in song.aliases)
        )

    def _matchPack(self, indent: QueryIntent, pack: ChartPack) -> bool:
        if not indent.type:
            return True
        return pack.type == indent.type
    
    def _matchDiff(self, indent: QueryIntent, chart: Chart) -> bool:
        if not indent.diff:
            return True
        if chart.diffid > 4:
            return indent.diff == 4
        return chart.diffid == indent.diff

    def _query(self, intent: QueryIntent) -> list[InfoTarget]:
        is_song = False
        if intent.diff:
            pool = self.chart_entries
        elif intent.type:
            pool = self.pack_entries
        else:
            pool = self.song_entries
            is_song = True
        res = []
        for entry in pool:
            if not self._matchTitle(intent, entry.song):
                continue
            if entry.type and not self._matchPack(intent, entry.pack):
                continue
            if entry.chart and not self._matchDiff(intent, entry.chart):
                continue
            res.append(entry)
            if is_song:
                if entry.song.sdChart:
                    res.append(InfoTarget(
                        type=InfoTargetType.PACK,
                        song=entry.song,
                        pack=entry.song.sdChart
                    ))
                if entry.song.dxChart:
                    res.append(InfoTarget(
                        type=InfoTargetType.PACK,
                        song=entry.song,
                        pack=entry.song.dxChart
                    ))
                if entry.song.partyChart:
                    for p in entry.song.partyChart:
                        res.append(InfoTarget(
                            type=InfoTargetType.PACK,
                            song=entry.song,
                            pack=p
                        ))
        return res

    def _queryByID(self, intent: QueryIntent) -> list[InfoTarget]:
        sid = intent.id % 10000
        song = self.songlist.get(sid, None)
        if not song:
            return []
        pack = song.chartID.get(intent.id, None)
        if not pack:
            return []
        if intent.type:
            if intent.type != pack.type:
                return []
        if intent.diff:
            if intent.diff < len(pack.charts):
                return [InfoTarget(
                    type=InfoTargetType.CHART,
                    song=song,
                    pack=pack,
                    chart=pack.charts[intent.diff]
                )]
            return []
        return [
            InfoTarget(
                type=InfoTargetType.PACK,
                song=song,
                pack=pack
            ),
            InfoTarget(
                type=InfoTargetType.SONG,
                song=song
            )
        ]

    def _applyPolicy(self, entries: list[InfoTarget], policy: QueryPolicy) -> list[InfoTarget]:
        res = []
        for e in entries:
            if e.type == InfoTargetType.SONG and not policy.allow_song:
                continue
            if e.type == InfoTargetType.PACK and not policy.allow_pack:
                continue
            if e.type == InfoTargetType.CHART and not policy.allow_chart:
                continue
            if e.pack.type == "宴" and not policy.allow_party:
                continue
            res.append(e)
        return res

    def query(self, text: str, policy: QueryPolicy) -> list[InfoTarget]:
        res = []
        seen = set()
        intents = QueryIntentParser.parse(text)
        for intent in intents:
            if intent.id is not None:
                entries = self._queryByID(intent)
            else:
                entries = self._query(intent)
            entries = self._applyPolicy(entries, policy)
            for e in entries:
                key = (
                    e.type,
                    e.song.id,
                    e.pack.id if e.pack else None,
                    e.chart.diff if e.chart else None
                )
                if key not in seen:
                    seen.add(key)
                    res.append(e)
        return res