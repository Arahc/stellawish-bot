from PIL import Image, ImageFilter, ImageDraw

def truncate(text: str, max_width: int, font) -> str:
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text

    for i in range(len(text), 0, -1):
        t = text[:i] + "…"
        if draw.textbbox((0, 0), t, font=font)[2] <= max_width:
            return t
    return text

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