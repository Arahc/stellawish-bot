from nonebot.adapters.qq import MessageSegment
import os

def Q2B(s: str) -> str:
    res = ""
    for char in s:
        inside_code = ord(char)
        if inside_code == 12888:
            inside_code = 32
        elif 65281 <= inside_code <= 65374:
            inside_code -= 65248
        res += chr(inside_code)
    return res

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