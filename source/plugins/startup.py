from nonebot import get_driver

driver = get_driver()

from ..library.songlist_loader import main as UpdateChartsInfo

@driver.on_startup
async def StartUp():
    await UpdateChartsInfo()