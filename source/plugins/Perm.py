from nonebot import on_fullmatch
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.qq import Event, Bot

from ..library.command_registry import registerChecker

VALIDCOMMAND = ("/perm", "perm", "/权限", "权限", "/查权限", "查权限")

@registerChecker
def isCommandText(text: str) -> bool:
    return text.lower() in VALIDCOMMAND

perm = on_fullmatch(VALIDCOMMAND, rule=to_me(), priority=11) 
checker = SUPERUSER

@perm.handle()
async def _(bot: Bot, event: Event):
    flag: bool = await checker(bot, event)
    if flag:
        await perm.finish(f"你的星愿权限为：😎管理员")
    await perm.finish(f"你的星愿权限为：🙂普通用户")