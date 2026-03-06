from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Bot, Message, MessageSegment
from nonebot_plugin_waiter import waiter
from nonebot_plugin_session import EventSession, SessionIdType

import random

from ..library.game_manager import GameManager
from ..library.command_registry import registerChecker, isAnyCommand
from ..library.utils import fetchChartCover
from ..library.static import VERSION_DICT, VERSION_LIST
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy

VALIDCOMMAND = ("/chartel", "chartel", "/猜歌", "猜歌", "/舞萌猜歌", "舞萌猜歌")
@registerChecker
def isCommandText(text: str) -> bool:
    return text.lower() in VALIDCOMMAND

def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

chartel = on_message(rule=to_me() & isValidCommand, priority=10)

QUERY_POLICY = QueryPolicy(
    allow_pack=True
)

class Game:
    status: dict[str, any] = {}
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.target = None, None
        self.guess_count = 0
        self.finished = False

    def start(self):
        self.target = self._pickChart()
        self.guess_count = 0
        self.finished = False
        Game.status[self.session_id] = self

    def isFinished(self) -> bool:
        return self.finished

    async def endGame(self, reason: str) -> Message:
        self.finished = True
        GameManager.endGame(self.session_id)
        header = ""
        if reason == "cancel":
            header = "❌取消游戏，"
        elif reason == "timeout":
            header = "⌛游戏超时，"
        elif reason == "success":
            header = "🎉恭喜猜对，"
        header += f"共猜测 {self.guess_count} 次，答案是：\n"
        song = self.target[0]
        pack = self.target[1]
        return Message([
            MessageSegment.text(
                header+ 
                f"{song.title}（id {pack.id}，{pack.type}）\n"
                f"🎼 bpm：{song.bpm}\n"
                f"🟪 紫谱难度：{pack.charts[3].diff}\n"
                f"🟥 红谱难度：{pack.charts[2].diff}\n"
                f"🕑 谱面版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "")
            ),
            await fetchChartCover(song.id)
        ])

    async def handle(self, text: str) -> Message:
        query_engine = SONG_LIST.getQueryEngine()
        res = query_engine.query(text, QUERY_POLICY)
        if not res:
            return Message(f"未找到「{text}」对应的曲目！")
        if len(res) > 1:
            msg = "找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
            for e in res:
                msg += f"- {e.song.title}（{e.pack.id}，{e.pack.type}）\n"
            return Message(msg.strip())
        song = res[0].song
        pack = res[0].pack
        ans_song = self.target[0]
        ans_pack = self.target[1]

        self.guess_count += 1
        if pack.id == ans_pack.id:
            return await self.endGame("success")

        bpm_hint = self._valueCMP(song.bpm, ans_song.bpm)
        master_hint = self._valueCMP(pack.charts[3].diff, ans_pack.charts[3].diff)
        expert_hint = self._valueCMP(pack.charts[2].diff, ans_pack.charts[2].diff)
        version_hint = self._versionCMP(pack.version, ans_pack.version)
        return Message(
            f"{song.title}（id {pack.id}，{pack.type}）\n"
            f"🎼 bpm：{song.bpm}（{bpm_hint}）\n"
            f"🟪 紫谱难度：{pack.charts[3].diff}（{master_hint}）\n"
            f"🟥 红谱难度：{pack.charts[2].diff}（{expert_hint}）\n"
            f"🕑 谱面版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "") + f"（{version_hint}）"
        )

    def _pickChart(self) -> dict:
        songlist = list(SONG_LIST.getSongList().values())
        song = random.choice(songlist)
        rand_pool = []
        while song.sdChart is None and song.dxChart is None:
            song = random.choice(songlist)
        if song.sdChart:
            rand_pool.append(song.sdChart)
        if song.dxChart:
            rand_pool.append(song.dxChart)
        pack = random.choice(rand_pool)
        return song, pack

    def _valueCMP(self, guess, target):
        if guess < target:
            return "低了"
        if guess > target:
            return "高了"
        return "对了"

    def _versionCMP(self, guess: str, target: str) -> str:
        if guess == target:
            return "对了"
        if guess in VERSION_LIST and target in VERSION_LIST:
            guess_index = VERSION_LIST.index(guess)
            target_index = VERSION_LIST.index(target)
            if guess_index < target_index:
                return "早了"
            else:
                return "晚了"
        raise ValueError("版本比较时出现未知版本名称")

@chartel.handle()
async def _(bot: Bot, event: Event, session: EventSession):
    session_id = session.get_id(SessionIdType.GROUP)

    if GameManager.hasGame(session_id):
        active = GameManager.getGame(session_id)
        await chartel.finish(
            f"❌ 当前已有{active.game_type}游戏正在进行，无法开始新的游戏！"
        )

    gm = Game(event.get_user_id(), session_id)
    gm.start()
    GameManager.startGame(session_id, "猜歌", gm)
    await chartel.send(
        "这是一个舞萌猜歌小游戏！\n"
        "你可以输入歌名或 ID（如 id11761）来猜歌，我会告诉你：\n"
        "- 你猜的歌的 bpm 高了还是低了；\n"
        "- 你猜的歌的紫谱难度高了还是低了；\n"
        "- 你猜的歌的红谱难度高了还是低了；\n"
        "- 你猜的歌的版本早了还是晚了；\n"
        "猜出答案就算获胜！\n"
        "输入「不玩了」可以立刻结束游戏。"
    )

    @waiter(waits=["message"], block=False, rule=to_me(), keep_session=False)
    async def listen(_event: Event, _session: EventSession):
        if _session.get_id(SessionIdType.GROUP) != session_id:
            return None, _event
        text = _event.get_message().extract_plain_text().strip()
        if text.startswith("不玩了"):
            return await gm.endGame("cancel"), _event
        if isAnyCommand(text) or text == "":
            return False, _event
        return await gm.handle(text), _event

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