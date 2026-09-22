import asyncio

from nonebot import get_driver, on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

from ..library import score_loader_lx, score_loader_sy
from ..library.b50_drawer import generateB50
from ..library.command_registry import registerCommand
from ..library.upload_img import uploadImgAsync
from ..library.userinfo_manager import USER_INFO
from ..library.utils import shorterID

VALID_COMMAND = ("/b50", "b50")


@registerCommand(
    name="b50",
    usage="/b50",
    description="查询并生成 Best 50 成绩图。",
    aliases=("b50",),
    category="成绩",
)
def isCommandText(text: str) -> bool:
    return text.lower() in VALID_COMMAND


def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().lower().strip())


b50 = on_message(rule=to_me() & isValidCommand, priority=1)


@get_driver().on_shutdown
async def _close_score_loaders() -> None:
    await score_loader_sy.close()
    await score_loader_lx.close()


@b50.handle()
async def _(event: Event):
    open_id = event.get_user_id()
    user = USER_INFO.get(open_id)
    if not user.canB50():
        await b50.finish("查询失败：请先使用 /bind 绑定水鱼或落雪账号。")

    await b50.send("查询已开始，正在获取成绩并生成图片，请稍候……")
    loader = score_loader_sy if user.dataSource == "sy" else score_loader_lx
    try:
        flag, message, player, b35, b15 = await asyncio.wait_for(loader.b50Score(user), timeout=12)
    except asyncio.TimeoutError:
        await b50.finish("查询超时：数据服务响应过慢，请稍后重试。")
    if not flag:
        await b50.finish(message)

    try:
        pic = await asyncio.wait_for(generateB50(player, b35, b15, user), timeout=20)
        url = await uploadImgAsync(pic, f"generate/b50/{shorterID(open_id)}.png", timeout=15)
    except asyncio.TimeoutError:
        await b50.finish("图片生成或上传超时，请稍后重试。")
    except Exception:
        await b50.finish("图片生成或上传失败，请稍后重试。")
    await b50.finish(MessageSegment.image(url))
