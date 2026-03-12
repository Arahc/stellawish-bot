from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Message, MessageSegment

import httpx

from ..library.user_info import getUserInfo, canFetchB50
from ..library.command_registry import registerChecker
from ..library.static import DIVEFISH_B50_API_URL as B50_API_URL
from ..library.b50_drawer import generateB50
from ..library.upload_img import uploadImg

VALID_COMMAND = ("/b50", "b50")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text in VALID_COMMAND

def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().lower().strip())

b50 = on_message(rule=to_me() & isValidCommand, priority=1)

@b50.handle()
async def _(event: Event):
    open_id = event.get_user_id()
    if not canFetchB50(open_id):
        await b50.finish("❌查询失败：你还没有绑定 QQ 号，请先使用 /bind <QQ 号> 进行绑定！")
    user_info = getUserInfo(open_id)
    qq_id = user_info.get('qqID')

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                B50_API_URL,
                json={
                    "qq": qq_id,
                    "b50": "1"
                },
                timeout=10
            )
        except Exception as e:
            await b50.finish(f"❌查询失败：请求水鱼 API 时发生错误：{e}")
    
    if resp.status_code == 400:
        await b50.finish(f"❌查询失败：你绑定的 QQ 号 {qq_id} 在水鱼中不存在，是否与水鱼账号关联的 QQ 号不符？")
    if resp.status_code == 403:
        await b50.finish(f"❌查询失败：访问被拒绝，你以 QQ 号 {qq_id} 关联的水鱼账号是否设置了隐私保护？")
    if resp.status_code != 200:
        await b50.finish(f"❌查询失败：水鱼 API 返回了错误的状态码 {resp.status_code}，请稍后再试。")

    data = resp.json()
    pic = generateB50(data)
    await b50.send("⏳查询成功，正在发送图片……若长时间未回复，为 QQ 获取图片超时，请稍后再试。")
    url = uploadImg(pic, f"generate/b50/{qq_id}.png", cache=False)
    await b50.finish(MessageSegment.image(url))
