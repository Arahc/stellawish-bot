from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.command_registry import registerChecker
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy

CANBE_PREFIX = ("/alias", "alias", "/查别名", "查别名", "/查别称", "查别称")
CANBE_SUFFIX = ("有什么别名", "有什么别称")

QUERY_POLICY = QueryPolicy(
    allow_song=True
)

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX) or lower_text.endswith(CANBE_SUFFIX)

async def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

alias = on_message(rule=to_me() & isValidCommand, priority=5)

@alias.handle()
async def _(event: Event):
    text = event.get_message().extract_plain_text().strip().lower()
    for prefix in CANBE_PREFIX:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    for suffix in CANBE_SUFFIX:
        if text.endswith(suffix):
            text = text[:-len(suffix)].strip()
            break
    query_engine = SONG_LIST.getQueryEngine()
    song = None
    if text:
        res = query_engine.query(text, QUERY_POLICY)
        if not res:
            await alias.finish(f"❌ 查询失败！未找到「{text}」对应的曲目。")
        if len(res) > 1:
            msg = "⚠️ 找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
            for e in res:
                msg += f"- {e.song.title}（可用 ID：{'，'.join(str(v) for v in e.song.getID().values())}）\n"
            await alias.finish(msg.strip())
        song = res[0].song
    else:
        await alias.finish("请提供歌曲名称或 ID。")

    alias_list = song.aliases
    if not alias_list:
        await alias.finish(f"✅ 查询成功！曲目「{song.title}」暂无别名。")
    else:
        await alias.finish(
            f"✅ 查询成功！曲目「{song.title}」的别名有：\n"+
            "\n".join([f"- {alias}" for alias in alias_list])
        )