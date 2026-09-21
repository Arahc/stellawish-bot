"""Cover loading with bounded network access and a local fallback."""

import asyncio
import os
import time
from pathlib import Path

import httpx
from PIL import Image

from .static import COVER_DIR, SMALL_DIR, PIC_DIR

COVER_URL = "https://assets2.lxns.net/maimai/jacket/{}.png"

FALLBACK_PATH = PIC_DIR / "covers" / "0.png"

COVER_DIR.mkdir(parents=True, exist_ok=True)
SMALL_DIR.mkdir(parents=True, exist_ok=True)

_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()
_download_slots = asyncio.Semaphore(8)
_song_locks: dict[int, asyncio.Lock] = {}
_remote_disabled_until = 0.0


def _load_image(path: Path) -> Image.Image:
    # Copy the decoded image so the file descriptor is closed immediately.
    with Image.open(path) as image:
        return image.convert("RGBA").copy()


def _fallback(size: int | None = None) -> Image.Image:
    try:
        image = _load_image(FALLBACK_PATH)
    except (OSError, Image.UnidentifiedImageError):
        image = Image.new("RGBA", (400, 400), (225, 225, 225, 255))
    target_size = size or 400
    if image.size != (target_size, target_size):
        image = image.resize((target_size, target_size), Image.LANCZOS)
    return image


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        async with _client_lock:
            if _client is None or _client.is_closed:
                timeout = httpx.Timeout(connect=2.5, read=4.0, write=4.0, pool=2.5)
                limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
                _client = httpx.AsyncClient(
                    timeout=timeout,
                    limits=limits,
                    follow_redirects=True,
                    headers={"User-Agent": "StellawishBot/1.0"},
                )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def _download_cover(song_id: int, file_path: Path) -> bool:
    global _remote_disabled_until
    if time.monotonic() < _remote_disabled_until:
        return False
    try:
        client = await _get_client()
        async with _download_slots:
            # Requests may have waited behind another failed batch. Re-check
            # the circuit here so queued covers do not start new requests.
            if time.monotonic() < _remote_disabled_until:
                return False
            response = await client.get(COVER_URL.format(song_id % 10000))
        if response.status_code in (403, 429):
            # Avoid sending dozens of requests after an anti-bot response.
            _remote_disabled_until = time.monotonic() + 60
            return False
        if response.status_code >= 500:
            _remote_disabled_until = time.monotonic() + 15
            return False
        if response.status_code != 200 or not response.content:
            return False
        # os.replace makes a partially downloaded image impossible to observe.
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        await asyncio.to_thread(temp_path.write_bytes, response.content)
        await asyncio.to_thread(os.replace, temp_path, file_path)
        return True
    except (httpx.HTTPError, OSError):
        _remote_disabled_until = time.monotonic() + 15
        return False


async def getCover(song_id: int) -> Image.Image:
    normalized_id = song_id % 10000
    file_path = COVER_DIR / f"{normalized_id}.png"
    try:
        return await asyncio.to_thread(_load_image, file_path)
    except (Image.UnidentifiedImageError, OSError):
        # Concurrent requests for the same missing cover share one download.
        lock = _song_locks.setdefault(normalized_id, asyncio.Lock())
        async with lock:
            try:
                return await asyncio.to_thread(_load_image, file_path)
            except (Image.UnidentifiedImageError, OSError):
                try:
                    await asyncio.to_thread(file_path.unlink, missing_ok=True)
                except OSError:
                    pass
                if not await _download_cover(normalized_id, file_path):
                    return await asyncio.to_thread(_fallback)
                try:
                    return await asyncio.to_thread(_load_image, file_path)
                except (Image.UnidentifiedImageError, OSError):
                    try:
                        await asyncio.to_thread(file_path.unlink, missing_ok=True)
                    except OSError:
                        pass
                    return await asyncio.to_thread(_fallback)


async def getSmallCover(song_id: int, size: int = 100) -> Image.Image:
    normalized_id = song_id % 10000
    file_path = SMALL_DIR / f"{normalized_id}.png"
    try:
        image = await asyncio.to_thread(_load_image, file_path)
        if image.size != (size, size):
            image = image.resize((size, size), Image.LANCZOS)
        return image
    except (Image.UnidentifiedImageError, OSError):
        image = await getCover(normalized_id)
        if image.size != (size, size):
            image = image.resize((size, size), Image.LANCZOS)
        # Do not persist a fallback image as a real cover.  Otherwise a
        # temporary outage would permanently poison the small-cover cache.
        source_path = COVER_DIR / f"{normalized_id}.png"
        if source_path.exists():
            try:
                await asyncio.to_thread(image.save, file_path, "PNG")
            except OSError:
                pass
        return image
