from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.userinfo_manager import USER_INFO
from ..library.command_registry import registerCommand
from ..library.score_loader_sy import checkBindingAsync, binding_link

VALIDCOMMAND = ("/bindsy", "bindsy", "/授权水鱼", "授权水鱼", "/授水鱼", "授水鱼")

@registerCommand(
    name="bindsy",
    usage="/bindsy",
    description="授权水鱼账号。",
    aliases=("bindsy", "授水鱼"),
    category="账号与设置",
)
def isCommandText(text: str) -> bool:
    return text.lower() in VALIDCOMMAND

def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

bindsy = on_message(rule=to_me() & isValidCommand, priority=8)

@bindsy.handle()
async def _(event: Event):
    open_id = event.get_user_id()
    qq = USER_INFO.get(open_id).qqID
    if qq is None:
        await bindsy.finish("❌查询失败：请先使用 /bind 绑定 QQ 号。")
    if await checkBindingAsync(qq):
        await bindsy.finish("❌查询失败：此 QQ 号已完成水鱼授权，请勿重复授权。")
    try:
        link = await binding_link(qq)
    except Exception:
        await bindsy.finish("❌查询失败：暂时无法创建水鱼授权链接，请稍后重试。")
    await bindsy.finish(f"请点击以下链接完成水鱼账号授权：\n{link}\n链接有效期为 10 分钟。")
