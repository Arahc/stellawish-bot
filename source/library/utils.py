from nonebot.adapters.qq import MessageSegment
import os

def isFontBomb(text: str) -> bool:
    for c in text:
        code = ord(c)
        if (
            0x0000 <= code <= 0x007F or      # ASCII
            0x3000 <= code <= 0x303F or      # CJK punctuation
            0x3040 <= code <= 0x309F or      # Hiragana
            0x30A0 <= code <= 0x30FF or      # Katakana
            0x31F0 <= code <= 0x31FF or      # Katakana phonetic ext
            0x3400 <= code <= 0x4DBF or      # CJK Extension A
            0x4E00 <= code <= 0x9FFF or      # CJK Unified Ideographs
            0xF900 <= code <= 0xFAFF or      # CJK compatibility ideographs
            0xFF00 <= code <= 0xFFEF or      # Fullwidth forms
            0x20000 <= code <= 0x2EBEF       # CJK Extension B–F
        ):
            continue
        return True
    return False

import httpx
async def fetchChartCover(id: int | str, noexcept: bool = False) -> MessageSegment:
    coverid = int(id) % 10000
    host = os.getenv("DOMAIN_BASE")
    url = f"{host}/covers/{coverid:04d}.png"
    if noexcept:
        return MessageSegment.image(url)
    else:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.head(url, timeout=5)
            except:
                return MessageSegment.text("\n⚠️获取封面失败（网络异常）")
            if resp.status_code == 200:
                return MessageSegment.image(url)
            elif resp.status_code == 403:
                return MessageSegment.text("\n⚠️获取封面失败（请求被拒绝，请联系开发者！）")
            else:
                return MessageSegment.text("\n⚠️获取封面失败（封面不存在，请联系开发者！）")