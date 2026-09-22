from __future__ import annotations

import asyncio
import hashlib
import os
import time

import httpx

from .player import Player
from .score import ScoreList

CLIENT_ID = os.getenv("DF_CLIENT_ID")
CLIENT_SECRET = os.getenv("DF_CLIENT_SECRET")
AUTH_URL = "https://auth.diving-fish.com"
PROBER_URL = "https://www.diving-fish.com/api/maimaidxprober"
HTTP_TIMEOUT = httpx.Timeout(connect=2.5, read=7.0, write=7.0, pool=2.5)
HTTP_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)


class NotBound(Exception):
    """The QQ account has not been bound to Diving-Fish."""


class QueryLimitExceeded(Exception):
    """The upstream query limit has been exceeded."""


_token_cache: dict[str, tuple[str, float]] = {}
_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()
_token_lock = asyncio.Lock()


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        async with _client_lock:
            if _client is None or _client.is_closed:
                _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS)
    return _client


async def close() -> None:
    """Close the shared HTTP client during application shutdown."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def subject_ref(qq_id: str) -> str:
    return hashlib.sha256(f"{CLIENT_ID}:{qq_id}".encode()).hexdigest()


def mask_id(qq_id: str) -> str:
    return f"QQ {qq_id[:3]} *** {qq_id[-3:]}" if len(qq_id) >= 6 else "QQ " + "*" * len(qq_id)


async def binding_link(qq_id: str) -> str:
    client = await _get_client()
    response = await client.post(
        f"{AUTH_URL}/oauth/device_authorization",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "prober.records.read",
            "subject_ref": subject_ref(qq_id),
            "binding_label": mask_id(qq_id),
        },
    )
    response.raise_for_status()
    return response.json()["verification_uri_complete"]


async def _access_token(qq_id: str) -> str:
    token, expires_at = _token_cache.get(qq_id, (None, 0))
    if token and time.time() < expires_at - 30:
        return token
    async with _token_lock:
        token, expires_at = _token_cache.get(qq_id, (None, 0))
        if token and time.time() < expires_at - 30:
            return token
        client = await _get_client()
        response = await client.post(
            f"{AUTH_URL}/oauth/token",
            data={
                "grant_type": "urn:diving-fish:params:oauth:grant-type:on-behalf-of",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "subject": "ref:" + subject_ref(qq_id),
                "scope": "prober.records.read",
            },
        )
        if response.status_code == 400 and response.json().get("error") == "consent_required":
            raise NotBound()
        if response.status_code == 429:
            raise QueryLimitExceeded()
        response.raise_for_status()
        data = response.json()
        token = data["access_token"]
        _token_cache[qq_id] = (token, time.time() + float(data["expires_in"]))
        return token


def _failure(exc: Exception) -> str:
    if isinstance(exc, NotBound):
        return "查询失败：该 QQ 尚未绑定水鱼账号。"
    if isinstance(exc, QueryLimitExceeded):
        return "查询失败：水鱼 API 查询次数已达上限。"
    return f"查询失败：水鱼 API 暂不可用（{type(exc).__name__}）。"

async def checkBindingAsync(qq_id: str) -> bool:
    """Return whether Diving-Fish authorization is available for a QQ id."""
    if not qq_id:
        return False
    token, expires_at = _token_cache.get(qq_id, (None, 0))
    if token and time.time() < expires_at - 30:
        return True
    try:
        await _access_token(qq_id)
        return True
    except NotBound:
        return False
    except QueryLimitExceeded:
        return True
    except Exception:
        return False


def checkBinding(qq_id: str) -> bool:
    """Check only the in-memory cache from synchronous code.

    Network authorization checks must use :func:`checkBindingAsync`; calling
    ``asyncio.run`` from a NoneBot handler would conflict with its event loop.
    """
    token, expires_at = _token_cache.get(qq_id, (None, 0))
    return bool(token and time.time() < expires_at - 30)

async def b50Score(user) -> tuple[bool, str, Player | None, ScoreList | None, ScoreList | None]:
    try:
        client = await _get_client()
        response = await client.post(f"{PROBER_URL}/query/player", json={"qq": user.qqID, "b50": "1"})
        if response.status_code == 429:
            raise QueryLimitExceeded()
        response.raise_for_status()
        data = response.json()
        return True, "", Player(data["nickname"]), ScoreList.loadFromSY(data["charts"]["sd"]), ScoreList.loadFromSY(data["charts"]["dx"])
    except (httpx.HTTPError, asyncio.TimeoutError, ValueError, KeyError, TypeError, NotBound, QueryLimitExceeded) as exc:
        return False, _failure(exc), None, None, None


async def singleScore(user, pack_id: int) -> ScoreList:
    token = await _access_token(user.qqID)
    client = await _get_client()
    response = await client.post(
        f"{PROBER_URL}/player/record",
        headers={"Authorization": "Bearer " + token},
        json={"music_id": pack_id},
    )
    if response.status_code == 429:
        raise QueryLimitExceeded()
    if response.status_code == 401:
        _token_cache.pop(user.qqID, None)
    response.raise_for_status()
    payload = response.json()
    records = payload.get(str(pack_id)) if isinstance(payload, dict) else None
    if records is None and isinstance(payload, dict):
        records = payload.get(str(pack_id % 10000))
    data = payload.get("data") if isinstance(payload, dict) else None
    if records is None and isinstance(data, dict):
        # Diving-Fish has returned both {"data": {"<id>": [...]}}
        # and {"data": {"records": [...]}} over its API versions.
        records = data.get(str(pack_id))
        if records is None:
            records = data.get(str(pack_id % 10000))
        if records is None:
            records = data.get("records")
    if records is None and isinstance(data, list):
        records = data
    if records is None:
        raise ValueError(f"Diving-Fish response has no records for pack {pack_id}")
    return ScoreList.loadFromSY(records)
