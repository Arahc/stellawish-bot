from __future__ import annotations

import asyncio
import os

import httpx

from .player import Player
from .score import ScoreList

API_SECRET = os.getenv("LXNS_API_SECRET")
PROBER_URL = "https://maimai.lxns.net/api/v0/maimai"
HTTP_TIMEOUT = httpx.Timeout(connect=2.5, read=7.0, write=7.0, pool=2.5)
HTTP_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)

_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        async with _client_lock:
            if _client is None or _client.is_closed:
                _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS)
    return _client


async def close() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def _failure(exc: Exception) -> str:
    return f"查询失败：落雪 API 暂不可用（{type(exc).__name__}）。"


async def b50Score(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    try:
        client = await _get_client()
        headers = {"Authorization": API_SECRET} if API_SECRET else {}
        response = await client.get(f"{PROBER_URL}/player/{user.lxID}/bests", headers=headers)
        response.raise_for_status()
        data = response.json()["data"]
        b35 = ScoreList.loadFromLX(data["standard"])
        b15 = ScoreList.loadFromLX(data["dx"])
        response = await client.get(f"{PROBER_URL}/player/{user.lxID}", headers=headers)
        response.raise_for_status()
        return True, "", Player(response.json()["data"]["name"]), b35, b15
    except (httpx.HTTPError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
        return False, _failure(exc), None, None, None


async def singleScore(user, pack_id: int) -> ScoreList:
    if pack_id < 10000:
        song_type = "standard"
    elif pack_id < 100000:
        song_type = "dx"
    else:
        song_type = "utage"
    client = await _get_client()
    headers = {"Authorization": API_SECRET} if API_SECRET else {}
    response = await client.get(
        f"{PROBER_URL}/player/{user.lxID}/bests",
        headers=headers,
        params={"song_id": pack_id % 10000, "song_type": song_type},
    )
    response.raise_for_status()
    return ScoreList.loadFromLX(response.json()["data"], pack_id=pack_id)
