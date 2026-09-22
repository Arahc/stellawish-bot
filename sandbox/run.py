"""Run full score workflows with checked-in API responses and no network."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from nonebot.adapters.qq import MessageSegment
from PIL import Image

from source.library import b50_drawer, score_loader_lx, score_loader_sy, songinfo_drawer
from source.library.b50_drawer import generateB50
from source.library.info_handler import QueryPolicy
from source.library.song import SongList
from source.library.song_manager import SONG_LIST
from source.library.songinfo_drawer import generateSongInfo
from source.library.userinfo import UserInfo
from source.plugins.MInfo import _render_result

from .sample_data import build_song_charts, load_samples, sample_response

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"


def seed_song_list(samples: dict) -> None:
    SONG_LIST.set(SongList(build_song_charts(samples)))


def _sample_cover(size: int = 400) -> Image.Image:
    image = Image.new("RGBA", (size, size), (210, 225, 245, 255))
    for x in range(size):
        image.putpixel((x, x), (80, 130, 210, 255))
        image.putpixel((size - x - 1, x), (80, 130, 210, 255))
    return image


async def _mock_cover(song_id: int, size: int = 100) -> Image.Image:
    return _sample_cover(size)


@dataclass
class SampleApi:
    samples: dict
    calls: list[str] = field(default_factory=list)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append(f"{request.method} {request.url.host}{path}")
        if request.url.host == "auth.diving-fish.com":
            if path.endswith("/oauth/token"):
                return httpx.Response(200, json={"access_token": "sandbox-access-token", "expires_in": 3600})
            if path.endswith("/oauth/device_authorization"):
                return httpx.Response(200, json={"verification_uri_complete": "https://sandbox.invalid/bind"})
            raise AssertionError(f"Unexpected sample auth request: {request.url}")
        if request.url.host == "www.diving-fish.com":
            if path.endswith("/query/player"):
                return httpx.Response(200, json=self.samples["sy_b50"])
            if path.endswith("/player/record"):
                return httpx.Response(200, json=sample_response(self.samples, "sy", "single"))
            raise AssertionError(f"Unexpected sample Diving-Fish request: {request.url}")
        if request.url.host == "maimai.lxns.net":
            if path.endswith("/bests"):
                song_type = request.url.params.get("song_type")
                if request.url.params.get("song_id") is not None:
                    return httpx.Response(200, json=sample_response(self.samples, "lx", "single", song_type))
                return httpx.Response(200, json=sample_response(self.samples, "lx", "b50"))
            if "/player/" in path:
                return httpx.Response(200, json={"data": {"name": self.samples["sy_b50"].get("nickname", "Sandbox User")}})
            raise AssertionError(f"Unexpected sample LXNS request: {request.url}")
        raise AssertionError(f"Unexpected sample host: {request.url}")


def _target(query: str):
    policy = QueryPolicy(allow_pack=True, allow_party=True, allow_chart=True)
    results = SONG_LIST.getQueryEngine().query(query.lower(), policy)
    if len(results) != 1:
        raise AssertionError(f"Expected one target for {query!r}, got {len(results)}")
    return results[0]


async def _prepare_clients(api: SampleApi) -> None:
    score_loader_sy._token_cache.clear()
    score_loader_sy._client = httpx.AsyncClient(transport=httpx.MockTransport(api))
    score_loader_lx._client = httpx.AsyncClient(transport=httpx.MockTransport(api))


async def run_checks() -> dict:
    samples = load_samples()
    seed_song_list(samples)
    api = SampleApi(samples)
    await _prepare_clients(api)

    original_b50_cover = b50_drawer.getSmallCover
    original_song_cover = songinfo_drawer.getCover
    b50_drawer.getSmallCover = _mock_cover
    songinfo_drawer.getCover = lambda song_id: _mock_cover(song_id, 400)
    try:
        sy_user = UserInfo("sandbox-sy", {"qqID": "10001", "syToken": "sample", "dataSource": "sy"})
        lx_user = UserInfo("sandbox-lx", {"lxID": "1000000001", "dataSource": "lx"})
        standard = _target("id 643")
        assert standard.pack.type == "SD"
        assert await score_loader_sy.checkBindingAsync(sy_user.qqID)
        assert await score_loader_sy.binding_link(sy_user.qqID) == "https://sandbox.invalid/bind"

        sy_single = await score_loader_sy.singleScore(sy_user, standard.pack.id)
        lx_single = await score_loader_lx.singleScore(lx_user, standard.pack.id)
        assert sy_single and lx_single and sy_single[0].song.id == 643 and lx_single[0].song.id == 643

        sy_ok, _, sy_player, sy_b35, sy_b15 = await score_loader_sy.b50Score(sy_user)
        lx_ok, _, lx_player, lx_b35, lx_b15 = await score_loader_lx.b50Score(lx_user)
        assert sy_ok and lx_ok and sy_player and lx_player
        assert len(sy_b35) == 35 and len(sy_b15) == 15
        assert len(lx_b35) == 35 and len(lx_b15) == 15

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        sy_b50_path = OUTPUT_DIR / "b50_sy.png"
        lx_b50_path = OUTPUT_DIR / "b50_lx.png"
        sy_b50_image = await generateB50(sy_player, sy_b35, sy_b15, sy_user)
        lx_b50_image = await generateB50(lx_player, lx_b35, lx_b15, lx_user)
        sy_b50_image.save(sy_b50_path)
        lx_b50_image.save(lx_b50_path)

        song_info_path = OUTPUT_DIR / "song_info_643.png"
        song_info_image = await generateSongInfo(standard.song, standard.pack)
        song_info_image.save(song_info_path)

        sy_markdown = _render_result(standard.song, standard.pack, sy_single)
        lx_markdown = _render_result(standard.song, standard.pack, lx_single)
        assert MessageSegment.markdown(sy_markdown).type == "markdown"
        assert "Excalibur" in sy_markdown and "100.8750%" in sy_markdown
        assert "100.8750%" in lx_markdown
        return {
            "status": "ok",
            "network": "mocked",
            "sample_files": ["sy_b50.json", "b50_lx.json", "single_643_sy.json", "single_643_lx.json"],
            "requests": api.calls,
            "records": {"sy_b35": len(sy_b35), "sy_b15": len(sy_b15), "lx_b35": len(lx_b35), "lx_b15": len(lx_b15)},
            "outputs": {
                "b50_sy": str(sy_b50_path.relative_to(ROOT.parent)),
                "b50_lx": str(lx_b50_path.relative_to(ROOT.parent)),
                "song_info": str(song_info_path.relative_to(ROOT.parent)),
            },
            "markdown": {"sy": sy_markdown, "lx": lx_markdown},
        }
    finally:
        b50_drawer.getSmallCover = original_b50_cover
        songinfo_drawer.getCover = original_song_cover
        await score_loader_sy.close()
        await score_loader_lx.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the verification result as JSON")
    args = parser.parse_args()
    result = asyncio.run(run_checks())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("sandbox checks: ok")
        print(f"generated: {', '.join(result['outputs'].values())}")
        print("sample-backed requests:")
        print("\n".join(f"  {call}" for call in result["requests"]))
