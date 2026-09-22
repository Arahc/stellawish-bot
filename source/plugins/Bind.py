from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.userinfo_manager import USER_INFO
from ..library.userinfo_loader import bindScoreSource
from ..library.command_registry import registerCommand
from ..library.score_loader_sy import checkBindingAsync

import re

CANBE_PREFIX = ("/bind", "bind", "/绑定", "绑定", "/绑", "绑")

@registerCommand(
    name="bind",
    usage="/bind qq <QQ号> lx <落雪ID> src <sy|lx>",
    description="绑定成绩数据源；参数可以按需组合。",
    aliases=("bind", "绑定"),
    category="账号与设置",
)
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return any(lower_text == prefix or lower_text.startswith(prefix + " ") for prefix in CANBE_PREFIX)

def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

bind = on_message(rule=to_me() & isValidCommand, priority=8)

def isValidQQID(qqid: str) -> bool:
    return re.fullmatch(r"[1-9][0-9]{4,14}", qqid) is not None
def isValidLXID(lxid: str) -> bool:
    return re.fullmatch(r"[0-9]{10,}", lxid) is not None
def isValidSource(source: str) -> bool:
    return source in ("sy", "lx", "水鱼", "落雪")

ARG_MAP = {
    "qq": (isValidQQID, "qqID"),
    "lx": (isValidLXID, "lxID"),
    "落雪": (isValidLXID, "lxID"),
    "source": (isValidSource, "dataSource"),
    "src": (isValidSource, "dataSource"),
    "源": (isValidSource, "dataSource"),
    "数据源": (isValidSource, "dataSource")
}

def applyArgs(info, text: str) -> tuple[bool, str]:
    tokens = text.split()
    if len(tokens) % 2 != 0:
        return False, "❌参数格式错误！请提供正确的参数，格式如：\n/bind qq <QQ号> lx <落雪ID> src <b50数据来源（sy或lx）>"
    for i in range(0, len(tokens), 2):
        key = tokens[i].lower()
        val = tokens[i + 1]
        if key not in ARG_MAP:
            return False, f"❌未知参数：{key}"
        validator, field = ARG_MAP[key]
        if not validator(val):
            return False, f"❌参数 {key} 格式错误！"

        if field == "dataSource": # special check
            val = "sy" if val in ("sy", "水鱼") else "lx"

        setattr(info, field, val)
    return True, "✅绑定成功！当前绑定信息状态如下：\n"

DUMP_MAP = {
    "qqID": "QQ 号",
    "lxID": "落雪好友码",
    "dataSource": "数据源"
}

async def dumpInfo(info) -> str:
    lines = []
    for key, val in info.__dict__.items():
        if key == "openID":
            continue
        if DUMP_MAP.get(key) is None:
            continue
        if val is None:
            lines.append(f"❌{DUMP_MAP.get(key, key)}：未绑定")
        elif key == "lxID":
            lines.append(f"✅{DUMP_MAP.get(key, key)}：已绑定（不公开）")
        elif key == "dataSource":
            source_name = "水鱼" if val == "sy" else "落雪"
            lines.append(f"✅{DUMP_MAP.get(key, key)}：{source_name}")
        else:
            lines.append(f"✅{DUMP_MAP.get(key, key)}：{val}")
    if info.dataSource == "sy" and info.qqID is not None and not await checkBindingAsync(info.qqID):
        lines.append("⚠️水鱼账号未完成授权：请使用 /bindsy 进行绑定")
    return "\n".join(lines)

@bind.handle()
async def _(event: Event):
    text = event.get_message().extract_plain_text().strip()
    lower_text = text.lower()
    for pre in CANBE_PREFIX:
        if lower_text.startswith(pre):
            text = text[len(pre):].strip()
            break
    open_id = event.get_user_id()
    info = USER_INFO.get(open_id)
    if not text:
        text = "你的绑定信息如下：\n" + await dumpInfo(info)
        await bind.finish(text)
    status, message = applyArgs(info, text)
    if not status:
        await bind.finish(message)
    bindScoreSource(open_id, info)
    message += await dumpInfo(info)
    await bind.finish(message)
