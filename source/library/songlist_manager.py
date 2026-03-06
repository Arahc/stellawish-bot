import json

from .songlist import SongList
from .info_handler import QueryEngine
from .static import SONG_LIST_PATH as FILE_PATH

class SongListManager:
    def __init__(self):
        self._songlist: SongList | None = None
        self._queryengine: QueryEngine | None = None

    def set(self, song_list: SongList, *, save: bool = True):
        self._songlist = song_list
        self._queryengine = QueryEngine(song_list)
        if save:
            self.save_to_file()

    def getSongList(self) -> SongList:
        if self._songlist is None:
            raise RuntimeError("SONG_LIST not initialized")
        return self._songlist

    def getQueryEngine(self) -> QueryEngine:
        if self._queryengine is None:
            raise RuntimeError("QueryEngine not initialized")
        return self._queryengine

    def reload_from_dict(self, data: list[dict]):
        self._songlist = SongList(data)
        self._queryengine = QueryEngine(self._songlist)

    def reload_from_file(self):
        if not FILE_PATH.exists():
            raise FileNotFoundError(FILE_PATH)

        with FILE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self._songlist = SongList(data)
        self._queryengine = QueryEngine(self._songlist)

    def save_to_file(self):
        FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with FILE_PATH.open("w", encoding="utf-8") as f:
            json.dump(self._songlist.exportJSON(), f, ensure_ascii=False)

SONG_LIST = SongListManager()
