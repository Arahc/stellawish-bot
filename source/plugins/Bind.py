from nonebot import on_startswith
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.userinfo_manager import USER_INFO
from ..library.userinfo_loader import setUserInfo
from ..library.command_registry import registerChecker

import re

CANBE_PREFIX = ("/bind", "bind", "/绑定", "绑定", "/绑", "绑")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX)

bind = on_startswith(CANBE_PREFIX, rule=to_me(), ignorecase=True, priority=8)

def isValidQQID(qqid: str) -> bool:
    return re.fullmatch(r"[1-9][0-9]{4,14}", qqid) is not None
def isValidDFToken(token: str) -> bool:
    return re.fullmatch(r"[a-zA-Z0-9]{20,}", token) is not None
def isValidLXID(lxid: str) -> bool:
    return re.fullmatch(r"[0-9]{10,}", lxid) is not None
def isValidSource(source: str) -> bool:
    return source in ("sy", "lx", "水鱼", "落雪")

ARG_MAP = {
    "qq": (isValidQQID, "qqID"),
    "sy": (isValidDFToken, "syToken"),
    "水鱼": (isValidDFToken, "syToken"),
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
        return False, "❌参数格式错误！请提供正确的参数，格式如：\n/bind qq <QQ号> sy <水鱼Token> lx <落雪ID> src <b50数据来源（sy或lx）>"
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
    "syToken": "水鱼 Token",
    "lxID": "落雪好友码",
    "dataSource": "b50 数据源"
}

def dumpInfo(info) -> str:
    lines = []
    for key, val in info.__dict__.items():
        if key == "openID":
            continue
        elif val is None:
            lines.append(f"❌{DUMP_MAP.get(key, key)}：未绑定")
        elif key == "syToken" or key == "lxID":
            lines.append(f"✅{DUMP_MAP.get(key, key)}：已绑定（不公开）")
        elif key == "dataSource":
            source_name = "水鱼" if val == "sy" else "落雪"
            lines.append(f"✅{DUMP_MAP.get(key, key)}：{source_name}")
        else:
            lines.append(f"✅{DUMP_MAP.get(key, key)}：{val}")
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
        text = "你的绑定信息如下：\n" + dumpInfo(info)
        await bind.finish(text)
    status, message = applyArgs(info, text)
    if not status:
        await bind.finish(message)
    setUserInfo(open_id, info)
    USER_INFO.set(info)
    message += dumpInfo(info)
    await bind.finish(message)