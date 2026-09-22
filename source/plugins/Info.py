import asyncio

from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

from ..library.command_registry import registerCommand
from ..library.song_manager import SONG_LIST
from ..library.info_handler import QueryPolicy
from ..library.songinfo_drawer import generateSongInfo
from ..library.upload_img import uploadImgAsync, getURL
from ..library.song_loader import updatePicDate, getToday

CANBE_PREFIX = ("/info", "info", "/查歌", "查歌")
CANBE_SUFFIX = ("是什么歌",)

@registerCommand(
    name="info",
    usage="/info <歌曲名称或 ID>",
    description="查询歌曲、谱面和歌曲信息图。",
    aliases=("info", "查歌", "<歌曲>是什么歌"),
    category="查询",
)
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
        await info.finish(f"❌查询失败！未找到「{text}」对应的曲目。")
    if len(res) > 1:
        msg = "⚠️找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
        for e in res:
            msg += f"- {e.song.title}（{e.pack.id}，{e.pack.type}）\n"
        await info.finish(msg.strip())
    
    target = res[0] 
    song = target.song
    pack = target.pack
    await info.send(f"⏳查询成功，正在生成图片……若长时间未回复，为图片上传超时，请稍后再试。")
    try:
        # Mark the cover date only after a new image has been uploaded.  A
        # failed render must not make later requests use a missing URL.
        if pack.info_pic_date != getToday():
            image = await asyncio.wait_for(generateSongInfo(song, pack), timeout=15)
            url = await uploadImgAsync(image, f"generate/songinfo/{pack.id}.png", timeout=15)
            updatePicDate(pack.id)
        else:
            url = getURL(f"generate/songinfo/{pack.id}.png")
    except asyncio.TimeoutError:
        await info.finish("图片生成或上传超时，请稍后重试。")
    except Exception:
        await info.finish("图片生成或上传失败，请稍后重试。")
    await info.finish(MessageSegment.image(url))
