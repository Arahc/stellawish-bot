import httpx
from pathlib import Path
from PIL import Image
import os

COVER_URL = "https://assets2.lxns.net/maimai/jacket/{id:04d}.png"
COVER_DIR =  Path(__file__).parent.parent / "data" / "pics" / "covers"
SMALL_DIR = Path(__file__).parent.parent / "data" / "pics" / "covers_small"

COVER_DIR.mkdir(parents=True, exist_ok=True)
SMALL_DIR.mkdir(parents=True, exist_ok=True)

async def getCover(song_id: int) -> Image.Image:
    file_path = COVER_DIR / f"{song_id % 10000:04d}.png"
    try:
        return Image.open(file_path).convert("RGBA")
    except (Image.UnidentifiedImageError, OSError):
        if file_path.exists():
            os.remove(file_path)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(COVER_URL.format(id=song_id % 10000))
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                else:
                    raise ValueError(f"No cover for song id {song_id} found.")
            except Exception:
                raise ValueError(f"No cover for song id {song_id} found.")
        return Image.open(file_path).convert("RGBA")

async def getSmallCover(song_id: int, size: int = 100) -> Image.Image:
    file_path = SMALL_DIR / f"{song_id % 10000:04d}.png"
    if not file_path.exists():
        img = await getCover(song_id)
        img = img.resize((size, size), Image.LANCZOS)
        img.save(file_path)
        return img
    return Image.open(file_path).convert("RGBA")