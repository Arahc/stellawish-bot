import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter
import os
from dotenv import load_dotenv

load_dotenv()

right_path = __file__.rstrip(os.path.basename(__file__))
os.chdir(right_path)

nonebot.init(session_expire_timeout=3600)

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)

nonebot.load_builtin_plugins('echo')

nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()