from nonebot import get_driver

driver = get_driver()

from ..library.song_loader import main as UpdateChartsInfo
from ..library.userinfo_loader import main as LoadUserInfo
from ..library.cover_manager import close_client

@driver.on_startup
async def StartUp():
    await UpdateChartsInfo()
    await LoadUserInfo()


@driver.on_shutdown
async def Shutdown():
    await close_client()
