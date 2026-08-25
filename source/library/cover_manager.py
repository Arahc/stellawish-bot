import httpx
from pathlib import Path
from PIL import Image
import os


# Diving Fish 封面源
# 网络请求使用 5 位数字，例如：
# 1832 -> 01832.png
COVER_URL = "https://www.diving-fish.com/covers/{id:05d}.png"

# 本地仍然保持原来的目录和 4 位文件名
COVER_DIR = Path(__file__).parent.parent / "data" / "pics" / "covers"
SMALL_DIR = Path(__file__).parent.parent / "data" / "pics" / "covers_small"


COVER_DIR.mkdir(parents=True, exist_ok=True)
SMALL_DIR.mkdir(parents=True, exist_ok=True)


def get_cover_source_id(song_id: int) -> int:
    song_id = int(song_id)

    if 10001 <= song_id <= 11000:
        song_id -= 10000

    return song_id


async def getCover(song_id: int) -> Image.Image:
    local_id = song_id % 10000
    file_path = COVER_DIR / f"{local_id:04d}.png"

    tmp_path = file_path.with_suffix(".png.tmp")

    try:
        with Image.open(file_path) as img:
            img.verify()

        return Image.open(file_path).convert("RGBA")

    except (Image.UnidentifiedImageError, OSError):
        file_path.unlink(missing_ok=True)

    source_id = get_cover_source_id(song_id)
    url = COVER_URL.format(id=source_id)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20.0,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/png,image/*,*/*;q=0.8",
        },
    ) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                raise ValueError(
                    f"Cover server returned {content_type!r} "
                    f"instead of an image"
                )
            if not resp.content.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError(
                    "Cover server returned invalid PNG data"
                )
            with open(tmp_path, "wb") as f:
                f.write(resp.content)
            with Image.open(tmp_path) as img:
                img.verify()
            os.replace(tmp_path, file_path)

        except Exception as e:
            tmp_path.unlink(missing_ok=True)

            raise ValueError(
                f"Failed to download cover for song id "
                f"{song_id} (source id {source_id}): {e}"
            ) from e
    return Image.open(file_path).convert("RGBA")


async def getSmallCover(song_id: int, size: int = 100) -> Image.Image:
    file_path = SMALL_DIR / f"{song_id % 10000:04d}.png"
    try:
        with Image.open(file_path) as img:
            img.verify()
        return Image.open(file_path).convert("RGBA")
    except (Image.UnidentifiedImageError, OSError):
        file_path.unlink(missing_ok=True)
    img = await getCover(song_id)
    img = img.resize((size, size), Image.LANCZOS)
    img.save(file_path)
    return img