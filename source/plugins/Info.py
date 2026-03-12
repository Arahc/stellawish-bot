from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Message, MessageSegment

from ..library.command_registry import registerChecker
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy
from ..library.songinfo_drawer import generateSongInfo
from ..library.upload_img import uploadImg, getURL

CANBE_PREFIX = ("/info", "info", "/查歌", "查歌")
CANBE_SUFFIX = ("是什么歌")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX) or lower_text.endswith(CANBE_SUFFIX)

async def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

info = on_message(rule=to_me() & isValidCommand, priority=4)

QUERY_POLICY = QueryPolicy(
    allow_pack=True,
    allow_party=True
)

@info.handle()
async def _(event: Event):
    text = event.get_message().extract_plain_text().strip().lower()
    for pre in CANBE_PREFIX:
        if text.startswith(pre):
            text = text[len(pre):].strip()
            break
    for suf in CANBE_SUFFIX:
        if text.endswith(suf):
            text = text[:-len(suf)].strip()
            break
    if text == "":
        await info.finish("请提供歌曲名称或 ID。")
    query_engine = SONG_LIST.getQueryEngine()
    res = query_engine.query(text, QUERY_POLICY)
    if not res:
        await info.finish(f"❌ 查询失败！未找到「{text}」对应的曲目。")
    if len(res) > 1:
        msg = "⚠️ 找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
        for e in res:
            msg += f"- {e.song.title}（{e.pack.id}，{e.pack.type}）\n"
        await info.finish(msg.strip())
    
    target = res[0] 
    song = target.song
    pack = target.pack
    if song.info_dat_date == song.info_pic_data:
        await info.send("⏳查询成功，正在发送图片……若长时间未回复，为 QQ 获取图片超时，请稍后再试。")
        url = getURL(f"generate/songinfo/{song.id}.png")
        await info.finish(MessageSegment.image(url))
    else:
        pic = generateSongInfo(song, pack)
        await info.send("⏳查询成功，正在发送图片……若长时间未回复，为 QQ 获取图片超时，请稍后再试。")
        url = uploadImg(pic, f"generate/songinfo/{song.id}.png", cache=False)
        song.info_pic_data = song.info_dat_date
        await info.finish(MessageSegment.image(url))