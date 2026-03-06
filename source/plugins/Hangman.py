from nonebot import on_startswith
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Bot
from nonebot_plugin_waiter import waiter
from nonebot_plugin_session import EventSession, SessionIdType

import random
import re

from ..library.game_manager import GameManager
from ..library.command_registry import registerChecker, isAnyCommand
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy
from ..library.utils import Q2B

DEFAULT_SONG_NUM = 8

CANBE_PREFIX = ("/hangman", "hangman", "/开字母", "开字母", "/舞萌开字母", "舞萌开字母")
@registerChecker
def isCommandText(text: str) -> bool:
    return text.lower().startswith(CANBE_PREFIX)

hangman = on_startswith(CANBE_PREFIX, priority=9, ignorecase=True)

QUERY_POLICY = QueryPolicy(
    allow_song=True,
)

class Game:
    status: dict[str, any] = {}
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.n = DEFAULT_SONG_NUM
        self.target = []
        self.current = []
        self.guesses = []
        self.success_count = []
        self.finished = False

    def start(self, n: int = DEFAULT_SONG_NUM):
        self.target = self._pickChart(n)
        self.n = n
        for i in range(n):
            hovered_title = ""
            for ch in self.target[i]:
                hovered_title += '?' if ch != ' ' else ' '
            self.current.append(hovered_title)
        self.guesses = []
        self.success_count = [-1] * n
        self.finished = False
        Game.status[self.session_id] = self

    def isFinished(self) -> bool:
        return self.finished

    async def endGame(self, reason: str) -> str:
        self.finished = True
        GameManager.endGame(self.session_id)
        res = ""
        if reason == "cancel":
            res = "❌取消游戏\n"
        elif reason == "timeout":
            res = "⌛游戏超时\n"
        elif reason == "end":
            res = "⭕游戏结束\n"
        for i in range(self.n):
            if self.success_count[i] == -1:
                res += "❌ " + self.target[i] + "\n"
            else:
                res += "✅ " + self.current[i] + f"（开 {self.success_count[i]} 个字母时猜出）\n"
        res += f"已开字符：{', '.join(self.guesses)}"
        return res

    async def handleLetter(self, letter: str) -> str:
        letter = Q2B(letter).lower().strip()
        if not letter:
            return "❌ 请输入要开的字符！"
        if len(letter) > 1:
            return "❌ 每次只能开一个字符！"
        if letter == '?':
            return "❌ 不能开问号！"
        if letter in self.guesses:
            return f"❌「{letter}」已经开过了！"
        self.guesses.append(letter)
        for i in range(self.n):
            if self.success_count[i] != -1:
                continue
            match = Q2B(self.target[i]).lower()
            self.current[i] = ''.join(
                self.target[i][j] if match[j] == letter else self.current[i][j]
                for j in range(len(self.target[i]))
            )
        
        if all(tar == cur for tar, cur in zip(self.target, self.current)):
            return await self.endGame("end")

        return "\n" + self._generateCurrentStatus(show_number=False)

    async def handleSong(self, text: str) -> str:
        query_engine = SONG_LIST.getQueryEngine()
        res = query_engine.query(text, QUERY_POLICY)
        if not res:
            return f"未找到「{text}」对应的曲目！"
        if len(res) > 1:
            msg = "找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
            for e in res:
                msg += f"- {e.song.title}（可用 ID：{'，'.join(str(v) for v in e.song.getID().values())}）\n"
            return msg.strip()
        song = res[0].song

        guessed_index = -1
        for i in range(self.n):
            if self.success_count[i] == -1 and self.target[i] == song.title:
                guessed_index = i
                break
        if guessed_index == -1:
            return f"❌ 曲目「{song.title}」不在剩余的答案中！"
        self.current[guessed_index] = song.title
        self.success_count[guessed_index] = len(self.guesses)

        if all(tar == cur for tar, cur in zip(self.target, self.current)):
            return await self.endGame("end")

        return (
            f"✅ 恭喜猜对！当前状态：\n"+
            self._generateCurrentStatus(show_number=False)
        )

    def _isValidTitle(self, title: str) -> bool:
        title = Q2B(title)
        if '?' in title:
            return False
        for ch in title:
            if re.match(r'[A-Za-z0-9]', ch):
                return True
        return False

    def _pickChart(self, N: int) -> list[str]:
        res = []
        songs = SONG_LIST.getSongList().values()
        all_valid_titles = [
            s.title
            for s in songs if (s.sdChart or s.dxChart) and self._isValidTitle(s.title)
        ]
        used_titles = set()
        for _ in range(N):
            tit = random.choice(all_valid_titles)
            while tit.lower() in used_titles:
                tit = random.choice(all_valid_titles)
            res.append(tit)
            used_titles.add(tit.lower())
        return res

    def _generateCurrentStatus(self, show_number: bool = False) -> str:
        res = ""
        for i in range(self.n):
            if self.success_count[i] == -1:
                if self.current[i] == self.target[i]:
                    res += "❌ " + self.current[i] + "\n"
                else:
                    res += "🤔 " + self.current[i] + "\n"
            else:
                res += "✅ " + self.current[i]
                if show_number:
                    res += f"（开 {self.success_count[i]} 个字母时猜出）\n"
                else:
                    res += "\n"
        res += f"已开字符：{', '.join(self.guesses)}"
        return res

@hangman.handle()
async def _(bot: Bot, event: Event, session: EventSession):
    session_id = session.get_id(SessionIdType.GROUP)

    if GameManager.hasGame(session_id):
        active = GameManager.getGame(session_id)
        await hangman.finish(
            f"当前已有{active.game_type}游戏正在进行，无法开始新的游戏！"
        )
    
    text = event.get_message().extract_plain_text()
    for pre in CANBE_PREFIX:
        if text.lower().startswith(pre.lower()):
            text = text[len(pre):].strip()
            break
    
    song_number = DEFAULT_SONG_NUM
    if text.isdigit():
        song_number = int(text)
        if song_number <= 0 or song_number > 30:
            await hangman.finish("开字母的歌曲数量应在 1 到 30 之间！")

    gm = Game(event.get_user_id(), session_id)
    gm.start(song_number)
    GameManager.startGame(session_id, "开字母", gm)
    await hangman.send(
        "这是一个舞萌开字母小游戏！\n"
        "你可以输入「开」+ 字符 来开一个字符；或输入歌名或 ID（如 id11761）来直接猜歌。\n"
        "你的目标是在不把歌名所有字符开出来的情况下把它猜出来！\n"
        "输入「不玩了」可以立刻结束游戏。"
    )
    await hangman.send("\n" + gm._generateCurrentStatus(show_number=False))

    @waiter(waits=["message"], block=False, rule=to_me(), keep_session=False)
    async def listen(_event: Event, _session: EventSession):
        if _session.get_id(SessionIdType.GROUP) != session_id:
            return None, _event
        text = _event.get_message().extract_plain_text().strip()
        if text.startswith("不玩了"):
            return await gm.endGame("cancel"), _event
        if isAnyCommand(text) or text == "":
            return False, _event
        if text.startswith("开"):
            return await gm.handleLetter(text[1:].strip().lower()), _event
        return await gm.handleSong(text.strip()), _event

    async for resp in listen(timeout=1200):
        if resp is None:
            resp = await gm.endGame("timeout")
        res = resp[0]
        eve = resp[1]
        if res is False:
            continue
        await bot.send(
            event=eve,
            message=res,
            reply_message=False
        )
        if gm.isFinished():
            break