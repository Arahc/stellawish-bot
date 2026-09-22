"""Load the checked-in score responses and derive minimal chart metadata.

The score APIs return records, while the bot's score model also needs chart
objects from the song list.  The sample responses do not contain note counts,
so this module derives only the metadata required to resolve the records and
uses deterministic placeholder notes for offline rendering.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent


def load_json(name: str):
    with (ROOT / name).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_samples() -> dict:
    return {
        "sy_b50": load_json("sy_b50.json"),
        "lx_b50": load_json("b50_lx.json"),
        "sy_single": load_json("single_643_sy.json"),
        "lx_single": load_json("single_643_lx.json"),
    }


def _base_id(record: dict, source: str) -> int:
    raw_id = record.get("song_id") if source == "sy" else record.get("id")
    return int(raw_id) % 10000


def _pack_type(record: dict) -> str:
    value = str(record.get("type", "")).lower()
    if value in {"sd", "standard"}:
        return "SD"
    if value in {"dx"}:
        return "DX"
    if value in {"ut", "utage"}:
        return "UT"
    raise ValueError(f"Unsupported sample chart type: {record.get('type')!r}")


def _level_value(record: dict) -> str:
    if record.get("ds") is not None:
        return str(record["ds"])
    level = str(record.get("level", "0"))
    match = re.match(r"\d+(?:\.\d+)?", level)
    return match.group(0) if match else "0"


def _chart(record: dict, chart_type: str) -> dict:
    result = {
        "version": 25000,
        "type": "standard" if chart_type == "SD" else "dx" if chart_type == "DX" else "utage",
        "level": str(record.get("level", "0")),
        "level_value": _level_value(record),
        "note_designer": "sandbox sample",
        # Response samples do not include note counts. These stable notes are
        # only for rendering; score values themselves come from the samples.
        "notes": {"tap": 100, "hold": 20, "slide": 30, "touch": 10, "break": 5},
    }
    if chart_type == "UT":
        result.update({"kanji": "宴会场", "is_buddy": False})
    return result


def _records(samples: dict) -> list[tuple[dict, str]]:
    pairs: list[tuple[dict, str]] = []
    sy_b50 = samples["sy_b50"]["charts"]
    pairs.extend((record, "sy") for record in sy_b50["sd"] + sy_b50["dx"])
    pairs.extend((record, "lx") for record in samples["lx_b50"]["standard"] + samples["lx_b50"]["dx"])
    pairs.extend((record, "sy") for record in samples["sy_single"]["643"])
    pairs.extend((record, "lx") for record in samples["lx_single"])
    return pairs


def build_song_charts(samples: dict) -> list[dict]:
    """Build SongList-compatible chart metadata from all sample records."""
    songs: dict[int, dict] = {}
    packs: dict[tuple[int, str], dict[int, dict]] = defaultdict(dict)
    for record, source in _records(samples):
        sid = _base_id(record, source)
        chart_type = _pack_type(record)
        song = songs.setdefault(
            sid,
            {
                "id": str(sid),
                "title": record.get("title") or record.get("song_name") or f"Sample {sid}",
                "artist": "sandbox sample",
                "bpm": 120,
                "genre": "maimai",
                "difficulties": {"standard": [], "dx": [], "utage": []},
            },
        )
        index = int(record.get("level_index", 0))
        packs[(sid, chart_type)][index] = _chart(record, chart_type)
        if chart_type == "UT":
            song["id"] = str(int(record.get("song_id", record.get("id"))))

    for (sid, chart_type), charts in packs.items():
        max_index = max(charts)
        fallback = charts[max_index]
        complete = [charts.get(index, fallback) for index in range(max_index + 1)]
        key = {"SD": "standard", "DX": "dx", "UT": "utage"}[chart_type]
        songs[sid]["difficulties"][key] = complete
    return list(songs.values())


def sample_response(samples: dict, provider: str, endpoint: str, song_type: str | None = None):
    """Return the JSON payload shape expected by the corresponding loader."""
    if provider == "sy":
        if endpoint == "b50":
            return samples["sy_b50"]
        return {"data": {"records": samples["sy_single"]["643"]}}
    if endpoint == "b50":
        return {"data": samples["lx_b50"]}
    if song_type == "utage":
        records = [record for record in samples["lx_single"] if record.get("type") == "utage"]
    else:
        records = samples["lx_single"]
    return {"data": records}

