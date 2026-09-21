from nonebot import on_startswith
from nonebot.rule import to_me
from nonebot.adapters.qq import Event

from ..library.userinfo_manager import USER_INFO
from ..library.userinfo_loader import bindScoreSource
from ..library.command_registry import registerChecker
from ..library.static import ICON_DIR, PLATE_DIR

CANBE_PREFIX = ("/profile", "/prof", "profile", "prof", "设置", "/设置", "设", "/设")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX)

prof = on_startswith(CANBE_PREFIX, rule=to_me(), ignorecase=True, priority=8)

AVAILABLE_AVATAR_IDS = {path.stem for path in ICON_DIR.glob("*.png")}
AVAILABLE_PLATE_IDS = {path.stem for path in PLATE_DIR.glob("*.png")}


def isValidAvatarID(iconid: str) -> bool:
    return iconid in AVAILABLE_AVATAR_IDS

def isValidPlateID(plateid: str) -> bool:
    return plateid in AVAILABLE_PLATE_IDS

ARG_MAP = {
    "tx": (isValidAvatarID, "iconID"),
    "ic": (isValidAvatarID, "iconID"),
    "icon": (isValidAvatarID, "iconID"),
    "头像": (isValidAvatarID, "iconID"),
    "xm": (isValidPlateID, "plateID"),
    "xmk": (isValidPlateID, "plateID"),
    "pl": (isValidPlateID, "plateID"),
    "plate": (isValidPlateID, "plateID"),
    "姓名框": (isValidPlateID, "plateID"),
}

def applyArgs(info, text: str) -> tuple[bool, str]:
    tokens = text.split()
    if len(tokens) % 2 != 0:
        return False, "❌参数格式错误！请提供正确的参数，格式如：\n/prof tx <头像ID> xmk <姓名框ID>\n可以通过 https://bot-docs.otmdb.cn/maimai/icons.html 和 https://bot-docs.otmdb.cn/maimai/plates.html 查询可用的头像和姓名框。"
    updates = {}
    for i in range(0, len(tokens), 2):
        key = tokens[i].lower()
        val = tokens[i + 1]
        if key not in ARG_MAP:
            return False, f"❌未知参数：{key}"
        validator, field = ARG_MAP[key]
        if not validator(val):
            return False, f"❌参数 {key} 错误：不存在的头像或姓名框 ID！\n可以通过 https://bot-docs.otmdb.cn/maimai/icons.html 和 https://bot-docs.otmdb.cn/maimai/plates.html 查询可用的头像和姓名框。"
        updates[field] = val
    info.setPersonal(**updates)
    return True, "✅设置成功！当前个人信息如下：\n"

DUMP_MAP = {
    "iconID": "头像 ID",
    "plateID": "姓名框 ID"
}

def dumpInfo(info) -> str:
    lines = []
    for key, val in info.__dict__.items():
        if key == "openID":
            continue
        if DUMP_MAP.get(key) is None:
            continue
        if val is None:
            lines.append(f"⚠️{DUMP_MAP.get(key, key)}：未设置")
        else:
            lines.append(f"✅{DUMP_MAP.get(key, key)}：{val}")
    return "\n".join(lines)

@prof.handle()
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
        text = "你的个人信息如下：\n" + dumpInfo(info) + "\n可以通过 https://bot-docs.otmdb.cn/maimai/icons.html 和 https://bot-docs.otmdb.cn/maimai/plates.html 查询可用的头像和姓名框。"
        await prof.finish(text)
    status, message = applyArgs(info, text)
    if not status:
        await prof.finish(message)
    bindScoreSource(open_id, info)
    message += dumpInfo(info) + "\n可以通过 https://bot-docs.otmdb.cn/maimai/icons.html 和 https://bot-docs.otmdb.cn/maimai/plates.html 查询可用的头像和姓名框。"
    await prof.finish(message)
