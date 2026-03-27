from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

import httpx

from ..library.userinfo_manager import USER_INFO
from ..library.command_registry import registerChecker
from ..library.static import DIVEFISH_B50_API_URL as B50_API_URL
from ..library.static import LXNS_API_SECRET as LXNS_KEY
from ..library.b50_drawer import generateB50
from ..library.upload_img import uploadImg
from ..library.score import ScoreList
from ..library.player import Player
from ..library.utils import LXNS_B50_API, LXNS_PROFILE_API, shorterID

VALID_COMMAND = ("/b50", "b50")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text in VALID_COMMAND

def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().lower().strip())

b50 = on_message(rule=to_me() & isValidCommand, priority=1)

API_TIME_OUT = 15

def fectchB50_SY(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    qqID = user.qqID
    with httpx.Client() as client:
        try:
            resp = client.post(
                B50_API_URL,
                json={
                    "qq": qqID,
                    "b50": "1"
                },
                timeout=API_TIME_OUT
            )
        except Exception as e:
            return False, f"❌查询失败：请求水鱼 API 时发生错误：{e}", None, None, None
        if resp.status_code == 400:
            return False, f"❌查询失败：你绑定的 QQ 号 {qqID} 在水鱼中不存在，是否与水鱼账号关联的 QQ 号不符？", None, None, None
        if resp.status_code == 403:
            return False, f"❌查询失败：访问被拒绝，你以 QQ 号 {qqID} 关联的水鱼账号是否设置了隐私保护？", None, None, None
        if resp.status_code != 200:
            return False, f"❌查询失败：水鱼 API 返回了错误的状态码 {resp.status_code}，请联系 bot 管理员。", None, None, None
        data = resp.json()
        return (
            True,
            "",
            Player(data['nickname']),
            ScoreList.loadFromSY(data['charts']['sd']),
            ScoreList.loadFromSY(data['charts']['dx'])
        )

def fectchB50_LX(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    with httpx.Client() as client:
        try:
            resp = client.get(
                LXNS_B50_API(user.lxID),
                headers={"Authorization": LXNS_KEY},
                timeout=API_TIME_OUT
            )
        except Exception as e:
            return False, f"❌查询失败：请求落雪 API 时发生错误：{e}", None, None, None
        data = resp.json()['data']
        b35 = ScoreList.loadFromLX(data['standard'])
        b15 = ScoreList.loadFromLX(data['dx'])
    with httpx.Client() as client:
        try:
            resp = client.get(
                LXNS_PROFILE_API(user.lxID),
                headers={"Authorization": LXNS_KEY},
                timeout=API_TIME_OUT
            )
        except Exception as e:
            return False, f"❌查询失败：请求落雪 API 时发生错误：{e}", None, None, None
        data = resp.json()['data']
        player = Player(data['name'])
    return (True, "", player, b35, b15)

@b50.handle()
async def _(event: Event):
    open_id = event.get_user_id()
    user = USER_INFO.get(open_id)
    if not user.canB50():
        print(f"用户 {open_id} 无法使用 b50 功能，用户信息：{user.exportJSON()}")
        await b50.finish("❌查询失败：你还没有绑定水鱼/落雪，请先使用 /bind 指令进行绑定！")
    if user.dataSource == "sy":
        flag, message, player, b35, b15 = fectchB50_SY(user)
    else:
        flag, message, player, b35, b15 = fectchB50_LX(user)

    if not flag:
        await b50.finish(message)
    pic = generateB50(player, b35, b15)
    await b50.send("⏳查询成功，正在发送图片……若长时间未回复，为 QQ 获取图片超时，请稍后再试。")
    url = uploadImg(pic, f"generate/b50/{shorterID(open_id)}.png", cache=False)
    await b50.finish(MessageSegment.image(url))
