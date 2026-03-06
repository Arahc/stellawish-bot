from nonebot import on_startswith
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.user_info import addInfo, getUserInfo
from ..library.command_registry import registerChecker

CANBE_PREFIX = ("/bind", "bind", "/绑定水鱼", "绑定水鱼", "/绑水鱼", "绑水鱼")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX)

bind = on_startswith(CANBE_PREFIX, rule=to_me(), ignorecase=True, priority=8)

def isValidQQID(qqid: str) -> bool:
    return qqid.isdigit() and 10000 <= int(qqid) <= 999999999999
def isValidToekn(token: str) -> bool:
    return len(token) >= 20

@bind.handle()
async def _(event: Event):
    text = event.get_message().extract_plain_text().strip()
    lower_text = text.lower()
    for pre in CANBE_PREFIX:
        if lower_text.startswith(pre):
            text = text[len(pre):].strip()
            break
    open_id = event.get_user_id()
    user_info = getUserInfo(open_id)
    if not text:
        if not user_info:
            await bind.finish("❌你还没有绑定任何信息，请提供 QQ 号和水鱼 Token 进行绑定！")
        if not user_info.get('qqID'):
            await bind.finish("❌你还没有绑定 QQ 号，请提供 QQ 号进行绑定！")
        if not user_info.get('token'):
            await bind.finish("❌你还没有绑定水鱼 Token，请提供水鱼 Token 进行绑定！")
        await bind.finish(
            "你的信息绑定情况如下：\n"+
            f"✅QQ 号：{user_info['qqID']}\n"+
            f"✅水鱼 Token（不公开）\n"+
            "如需修改，只需重新发送绑定命令即可。"
        )
    splits_by_space = text.split()
    if len(splits_by_space) == 2:
        qq_id = splits_by_space[0]
        token = splits_by_space[1]
        if not isValidQQID(qq_id):
            await bind.finish("❌绑定失败！请提供合法的 QQ 号。")
    elif len(splits_by_space) == 1:
        text = splits_by_space[0]
        if isValidQQID(text):
            qq_id = text
            token = None
        elif len(text) >= 10:
            qq_id = None
            token = text
        else:
            await bind.finish("❌绑定失败！请提供合法的 QQ 号或水鱼 Token。")
    else:
        await bind.finish("❌绑定失败！请提供正确的 QQ 号和水鱼 Token，格式如：\n/bind <QQ号> <token>")
    addInfo(open_id, qq_id, token)
    user_info = getUserInfo(open_id)
    await bind.finish(
        "绑定成功！你的信息绑定情况如下：\n"+
        (f"✅QQ 号：{user_info['qqID']}\n" if user_info.get('qqID') else "❌QQ 号\n")+
        (f"✅水鱼 Token（不公开）\n" if user_info.get('token') else "❌水鱼 Token\n")+
        f"若您发送了 Token，建议撤回绑定消息，以免 Token 泄露。"
    )