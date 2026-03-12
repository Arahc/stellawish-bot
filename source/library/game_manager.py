from typing import Dict

class ActiveGame:
    def __init__(self, game_type: str, game_obj: object):
        self.game_type = game_type
        self.game_obj = game_obj

class GameManager:
    active_games: Dict[str, ActiveGame] = {}

    @classmethod
    def hasGame(cls, session_id: str) -> bool:
        return session_id in cls.active_games

    @classmethod
    def getGame(cls, session_id: str) -> ActiveGame | None:
        return cls.active_games.get(session_id)

    @classmethod
    def startGame(cls, session_id: str, game_type: str, game_obj: object):
        cls.active_games[session_id] = ActiveGame(game_type, game_obj)

    @classmethod
    def endGame(cls, session_id: str):
        cls.active_games.pop(session_id, None)