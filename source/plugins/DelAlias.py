from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Bot
from nonebot.permission import SUPERUSER

from ..library.command_registry import registerChecker
from ..library.load_charts import delAlias
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy

CANBE_PREFIX = ("/delalias", "delalias", "/删别名", "删别名", "/删别称", "删别称")

@registerChecker
def isCommandText(text: str) -> bool:
    return text.lower().startswith(CANBE_PREFIX)

async def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

delalias = on_message(rule=to_me() & isValidCommand, priority=7)
permission_checker = SUPERUSER

QUERY_POLICY = QueryPolicy(
    allow_song=True
)

@delalias.handle()
async def _(bot: Bot, event: Event):
    perm = await permission_checker(bot, event)
    if not perm:
        await delalias.finish("🚫 删除失败！你没有权限使用此命令。")

    text = event.get_message().extract_plain_text().strip().lower()
    for prefix in CANBE_PREFIX:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    query_engine = SONG_LIST.getQueryEngine()
    splits_by_space = text.split()
    res = []
    for i in range(1, len(splits_by_space)):
        left_part = " ".join(splits_by_space[:i]).strip()
        right_part = " ".join(splits_by_space[i:]).strip()
        if not left_part or not right_part:
            continue
        target = query_engine.query(left_part, QUERY_POLICY)
        if target:
            for t in target:
                if right_part in t.song.aliases:
                    res.append((t, right_part))
    if not res:
        await delalias.finish(f"❌ 删除失败！未检索到任何有关曲目。")
    if len(res) > 1:
        msg = "⚠️ 找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
        for e, _ in res:
            msg += f"- {e.song.title}（可用 ID：{'，'.join(str(v) for v in e.song.getID().values())}）\n"
        await delalias.finish(msg.strip())
    
    song = res[0][0].song
    alias = res[0][1]

    if delAlias(song.id, alias):
        await delalias.finish(f"✅ 删除成功！已将别名「{alias}」从曲目「{song.title}」中移除。")
    await delalias.finish(f"❌ 删除失败！曲目「{song.title}」没有此别名。")