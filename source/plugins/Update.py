from nonebot import on_startswith
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Bot

from maimai_py import MaimaiClient, PlayerIdentifier, ArcadeProvider

from ..library.command_registry import registerChecker
from ..library.user_info import getUserInfo

CANBE_PREFIX = ("/update", "update", "/舞萌更新", "舞萌更新", "/传水鱼", "传水鱼")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX)

update = on_startswith(CANBE_PREFIX, rule=to_me(), ignorecase=True, priority=4)

@update.handle()
async def _(bot: Bot, event: Event):
    await update.finish("❌鉴于舞萌服务器安全性更新，此功能暂不可用 :(")

    text = event.get_message().extract_plain_text().strip()
    lower_text = text.lower()
    for pre in CANBE_PREFIX:
        if lower_text.startswith(pre):
            text = text[len(pre):].strip()
            break
    open_id = event.get_user_id()
    user_info = getUserInfo(open_id)
    if not user_info:
        await update.finish("❌你还没有绑定任何信息，请先绑定水鱼 Token！")
    if not user_info.get('token'):
        await update.finish("❌你还没有绑定水鱼 Token，请先绑定水鱼 Token！")
    if not text:
        await update.finish("❌请提供舞萌公众号二维码代码！格式：/update <code>")
    maimai = MaimaiClient()
    token = user_info['token']
    code = text
    account = await maimai.qrcode(code)
    scores = await maimai.scores(account, provider=ArcadeProvider())
    try:
        await maimai.updates(PlayerIdentifier(credentials=token), scores.scores, provider=divingfish)
    except Exception as e:
        await update.finish(f"❌上传失败！错误信息：{e}")
    await update.finish("✅上传成功！水鱼数据已更新。")
