from nonebot import get_driver

driver = get_driver()

from ..library.song_loader import main as UpdateChartsInfo
from ..library.userinfo_loader import main as LoadUserInfo

@driver.on_startup
async def StartUp():
    await UpdateChartsInfo()
    await LoadUserInfo()