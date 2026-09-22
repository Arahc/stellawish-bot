from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

from ..library.command_registry import registerCommand, renderHelp

VALID_COMMAND = ("/help", "help", "/帮助", "帮助")

@registerCommand(
    name="help",
    usage="/help",
    description="查看 Bot 的全部指令、使用格式和功能。",
    aliases=("help", "帮助"),
    category="其他",
)
def isCommandText(text: str) -> bool:
    return text.lower() in VALID_COMMAND


# ==== nonebot 自带插件，无需介绍 ====

# registerCommandInfo(CommandInfo(
#     name="echo",
#     usage="/echo [文本]",
#     description="重复发送输入的文本。",
#     category="其他",
# ), checker=_isEchoCommand)

# registerCommandInfo(CommandInfo(
#     name="status",
#     usage="/status",
#     description="查询机器人服务器状态；也可以通过戳一戳机器人触发。",
#     aliases=("status", "状态"),
#     category="其他",
#     permission="管理员",
# ), checker=_isStatusCommand)


def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())


help_command = on_message(rule=to_me() & isValidCommand, priority=1)


@help_command.handle()
async def _(event: Event):
    await help_command.finish(MessageSegment.markdown(renderHelp()))
