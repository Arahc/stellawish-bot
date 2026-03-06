from pathlib import Path
from PIL import ImageFont

class FontManager:
    FONT_DIR = Path(__file__).parent.parent / "data" / "fonts"
    _fonts: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    @classmethod
    def get(cls, name: str, size: int) -> ImageFont.FreeTypeFont:
        key = (name, size)
        if key not in cls._fonts:
            font_path = cls.FONT_DIR / name
            cls._fonts[key] = ImageFont.truetype(str(font_path), size)
        return cls._fonts[key]
