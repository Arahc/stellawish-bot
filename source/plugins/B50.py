import asyncio

import httpx
from nonebot import get_driver, on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

from ..library.userinfo_manager import USER_INFO
from ..library.command_registry import registerChecker
from ..library.static import DIVEFISH_B50_API_URL as B50_API_URL
from ..library.static import LXNS_API_SECRET as LXNS_KEY
from ..library.b50_drawer import generateB50
from ..library.upload_img import uploadImgAsync
from ..library.score import ScoreList
from ..library.player import Player
from ..library.utils import LXNS_B50_API, LXNS_PROFILE_API, shorterID

VALID_COMMAND = ("/b50", "b50")


@registerChecker
def isCommandText(text: str) -> bool:
    return text.lower() in VALID_COMMAND


def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().lower().strip())


b50 = on_message(rule=to_me() & isValidCommand, priority=1)

API_TIME_OUT = 10
HTTP_TIMEOUT = httpx.Timeout(connect=2.5, read=7.0, write=7.0, pool=2.5)
HTTP_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_api_client: httpx.AsyncClient | None = None
_api_client_lock = asyncio.Lock()


async def _get_api_client() -> httpx.AsyncClient:
    global _api_client
    if _api_client is None or _api_client.is_closed:
        async with _api_client_lock:
            if _api_client is None or _api_client.is_closed:
                _api_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS)
    return _api_client


@get_driver().on_shutdown
async def _close_api_client() -> None:
    global _api_client
    if _api_client is not None and not _api_client.is_closed:
        await _api_client.aclose()
    _api_client = None


def _request_error(source: str, exc: Exception) -> str:
    return f"Query failed: {source} is unavailable ({type(exc).__name__}). Please try again later."


async def fetchB50_SY(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    try:
        client = await _get_api_client()
        resp = await client.post(B50_API_URL, json={"qq": user.qqID, "b50": "1"})
        if resp.status_code == 400:
            return False, "❌查询失败：绑定的 QQ 账号在水鱼中不存在。", None, None, None
        if resp.status_code == 403:
            return False, "❌查询失败：服务拒绝访问，请检查账号隐私设置。", None, None, None
        if resp.status_code != 200:
            return False, f"❌查询失败：服务返回 HTTP {resp.status_code}。", None, None, None
        data = resp.json()
        return (
            True,
            "",
            Player(data["nickname"]),
            ScoreList.loadFromSY(data["charts"]["sd"]),
            ScoreList.loadFromSY(data["charts"]["dx"]),
        )
    except (httpx.HTTPError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
        return False, _request_error("水鱼 API", exc), None, None, None


async def fetchB50_LX(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    try:
        client = await _get_api_client()
        headers = {"Authorization": LXNS_KEY}
        resp = await client.get(LXNS_B50_API(user.lxID), headers=headers)
        if resp.status_code != 200:
            return False, f"❌查询失败：落雪 API 返回 HTTP {resp.status_code}。", None, None, None
        data = resp.json()["data"]
        b35 = ScoreList.loadFromLX(data["standard"])
        b15 = ScoreList.loadFromLX(data["dx"])

        resp = await client.get(LXNS_PROFILE_API(user.lxID), headers=headers)
        if resp.status_code != 200:
            return False, f"❌查询失败：落雪用户信息返回 HTTP {resp.status_code}。", None, None, None
        player = Player(resp.json()["data"]["name"])
        return True, "", player, b35, b15
    except (httpx.HTTPError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
        return False, _request_error("落雪 API", exc), None, None, None


@b50.handle()
async def _(event: Event):
    open_id = event.get_user_id()
    user = USER_INFO.get(open_id)
    if not user.canB50():
        await b50.finish("❌查询失败：请先使用 /bind 绑定水鱼或落雪账号。")

    # Send progress before any remote request or image rendering starts.
    await b50.send("⏳查询已开始，正在获取成绩并生成图片，请稍候……")
    try:
        fetch = fetchB50_SY(user) if user.dataSource == "sy" else fetchB50_LX(user)
        flag, message, player, b35, b15 = await asyncio.wait_for(fetch, timeout=API_TIME_OUT + 2)
    except asyncio.TimeoutError:
        await b50.finish("❌查询超时：数据服务响应过慢，请稍后重试。")
    if not flag:
        await b50.finish(message)

    try:
        pic = await asyncio.wait_for(generateB50(player, b35, b15, user), timeout=20)
        url = await uploadImgAsync(pic, f"generate/b50/{shorterID(open_id)}.png", timeout=15)
    except asyncio.TimeoutError:
        await b50.finish("❌图片生成或上传超时，请稍后重试。")
    except Exception:
        await b50.finish("❌图片生成或上传失败，请稍后重试。")
    await b50.finish(MessageSegment.image(url))
