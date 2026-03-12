from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont

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

class GridManager:
    def __init__(self, width: int, height: int, element_w: list[int], element_h: list[int]):
        self.gridW = element_w
        self.gridH = element_h
        self.rows = len(element_h)
        self.cols = len(element_w)
        if sum(self.gridH) + (self.rows - 1) > height:
            raise ValueError(f"Not enough height for the given number of rows: {sum(self.gridH) + (self.rows - 1)} > {height}")
        if sum(self.gridW) + (self.cols - 1) > width:
            raise ValueError(f"Not enough width for the given number of columns: {sum(self.gridW) + (self.cols - 1)} > {width}")
        self.gapH = (width - sum(self.gridW) - (self.cols - 1)) // (self.cols - 1) if self.cols > 1 else 0
        self.gapV = (height - sum(self.gridH) - (self.rows - 1)) // (self.rows - 1) if self.rows > 1 else 0

    def places(self, n: int) -> list[tuple[int, int]]:
        pos = []
        if n > self.rows * self.cols:
            raise ValueError(f"Number of elements exceeds grid capacity: {n} > {self.rows * self.cols}")
        y = 0
        for r in range(self.rows):
            x = 0
            for c in range(self.cols):
                pos.append((x, y))
                if len(pos) == n:
                    return pos
                x += self.gridW[c] + self.gapH
            y += self.gridH[r] + self.gapV
        return pos

def truncate(text: str, max_width: int, font) -> str:
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text

    for i in range(len(text), 0, -1):
        t = text[:i] + "…"
        if draw.textbbox((0, 0), t, font=font)[2] <= max_width:
            return t
    return text

def wrap(text: str, max_width: int, font) -> list[str]:
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines

def filter(img: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    if img.mode != "RGBA":
        raise ValueError("Image must be RGBA")
    colored = Image.new("RGBA", img.size, color)
    blended = Image.blend(img, colored, alpha=color[3] / 255)
    res = img.copy()
    res.paste(blended, (0, 0), mask=img.getchannel('A'))
    return res

def shadowed(img: Image.Image, offset: tuple[int, int], blur: int, scale: float = 1.0, color: tuple[int, int, int, int] = (0, 0, 0, 128)) -> Image.Image:
    if img.mode != "RGBA":
        raise ValueError("Image must be RGBA")

    scaled = img.copy()
    scaled = scaled.resize((int(img.width * scale), int(img.height * scale)), resample=Image.LANCZOS)

    alpha = scaled.getchannel('A')
    shad = Image.new("RGBA", scaled.size, color)
    shad.putalpha(alpha)
    shad = shad.filter(ImageFilter.GaussianBlur(blur))

    dx, dy = offset
    disx, disy = img.size[0] * abs(scale - 1) / 2, img.size[1] * abs(scale - 1) / 2
    dx += -int(disx) if scale > 1 else int(disx)
    dy += -int(disy) if scale > 1 else int(disy)

    res = Image.new("RGBA", (int(img.width * scale) + abs(dx) + blur * 2, int(img.height * scale) + abs(dy) + blur * 2))
    res.alpha_composite(shad, (blur + max(0, dx), blur + max(0, dy)))
    res.alpha_composite(img, (blur + max(0, -dx), blur + max(0, -dy)))
    return res