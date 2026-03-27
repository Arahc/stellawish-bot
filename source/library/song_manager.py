from .song import SongList
from .info_handler import QueryEngine

class SongListManager:
    def __init__(self):
        self._songlist: SongList | None = None
        self._queryengine: QueryEngine | None = None

    def set(self, song_list: SongList):
        self._songlist = song_list
        self._queryengine = QueryEngine(song_list)

    def getSongList(self) -> SongList:
        if self._songlist is None:
            raise RuntimeError("SONG_LIST not initialized")
        return self._songlist

    def getQueryEngine(self) -> QueryEngine:
        if self._queryengine is None:
            raise RuntimeError("QueryEngine not initialized")
        return self._queryengine

SONG_LIST = SongListManager()
