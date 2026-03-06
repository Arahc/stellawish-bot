from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, Message, MessageSegment

from ..library.command_registry import registerChecker
from ..library.utils import fetchChartCover
from ..library.static import VERSION_DICT, DIFF_NAME_LIST
from ..library.songlist_manager import SONG_LIST
from ..library.info_handler import QueryPolicy, InfoTarget, InfoTargetType

import re

CANBE_PREFIX = ("/info", "info", "/查歌", "查歌", "/查谱", "查谱")
CANBE_SUFFIX = ("是什么歌", "是什么谱", "的信息", "的曲目信息", "的谱面信息")

@registerChecker
def isCommandText(text: str) -> bool:
    lower_text = text.lower()
    return lower_text.startswith(CANBE_PREFIX) or lower_text.endswith(CANBE_SUFFIX)

async def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text().strip())

info = on_message(rule=to_me() & isValidCommand, priority=4)

QUERY_POLICY = QueryPolicy(
    allow_pack=True,
    allow_chart=True,
    allow_party=True,
)

def getPackInfo(info: InfoTarget) -> str:
    song = info.song
    pack = info.pack
    return (
        f"{song.title}（{pack.id}，{pack.type}）：\n"+
        f"🎵 曲师：{song.artist}\n"+
        f"🎼 bpm：{song.bpm}\n"+
        f"🕑 版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "") + "\n"+
        f"🗂️ 分类：{song.genre}\n"+
        (f"⬜ 白谱：定数 {pack.charts[4].diff}（by {pack.charts[4].charter}）\n" if len(pack.charts) > 4 else "")+
        f"🟪 紫谱：定数 {pack.charts[3].diff}（by {pack.charts[3].charter}）\n"+
        f"🟥 红谱：定数 {pack.charts[2].diff}（by {pack.charts[2].charter}）\n"+
        f"🟨 黄谱：定数 {pack.charts[1].diff}\n"+
        f"🟩 绿谱：定数 {pack.charts[0].diff}"
    )

KEEP_DECIMAL_ACC = 4
KEEP_DECIMAL_GR = 2

def getChartInfo(info: InfoTarget) -> str:
    song = info.song
    pack = info.pack
    chart = info.chart
    basescore = chart.tap + chart.hold*2 + chart.slide*3 + chart.touch + chart.breaks*5
    rewardscore = chart.breaks
    return (
        f"{song.title}（{pack.id}，{pack.type}）〈{DIFF_NAME_LIST[chart.diffid]}〉：\n"
        f"🎵 曲师：{song.artist}\n"+
        f"🎼 bpm：{song.bpm}\n"+
        f"🕑 版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "") + "\n"+
        f"🗂️ 分类：{song.genre}\n"+
        f"⭐ 难度：{chart.diff}" + (f"（by {chart.charter}）\n" if chart.charter != "-" else "\n")+
        f"TAP：{chart.tap} 个。" + (f"粉 -{round(20 / basescore, KEEP_DECIMAL_ACC)}%，绿 -{round(50 / basescore, KEEP_DECIMAL_ACC)}%，灰 -{round(100 / basescore, KEEP_DECIMAL_ACC)}%\n" if chart.tap != 0 else "\n")+
        f"HOLD：{chart.hold} 个。" + (f"粉 -{round(40 / basescore, KEEP_DECIMAL_ACC)}%，绿 -{round(100 / basescore, KEEP_DECIMAL_ACC)}%，灰 -{round(200 / basescore, KEEP_DECIMAL_ACC)}%\n" if chart.hold != 0 else "\n")+
        f"SLIDE：{chart.slide} 个。" + (f"粉 -{round(60 / basescore, KEEP_DECIMAL_ACC)}%，绿 -{round(150 / basescore, KEEP_DECIMAL_ACC)}%，灰 -{round(300 / basescore, KEEP_DECIMAL_ACC)}%\n" if chart.slide != 0 else "\n")+
        f"TOUCH：{chart.touch} 个。" + (f"粉 -{round(20 / basescore, KEEP_DECIMAL_ACC)}%，绿 -{round(50 / basescore, KEEP_DECIMAL_ACC)}%，灰 -{round(100 / basescore, KEEP_DECIMAL_ACC)}%\n" if chart.touch != 0 else "\n")+
        f"BREAK：{chart.breaks} 个。" + (f"50 落 -{round(0.25 / rewardscore, KEEP_DECIMAL_ACC)}%，500 粉 -{round(100 / basescore + 0.6 / rewardscore, KEEP_DECIMAL_ACC)}%，绿 -{round(300 / basescore + 0.7 / rewardscore, KEEP_DECIMAL_ACC)}%，灰 -{round(500 / basescore + 1 / rewardscore, KEEP_DECIMAL_ACC)}%\n" if chart.breaks != 0 else "\n")+
        f"👑鸟加 SSS+ 容错 {round(basescore / 40, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(100.5)}\n"+
        f"🕶️鸟 SSS 容错 {round(basescore / 20, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(100)}\n"+
        f"- SS+ 容错 {round(basescore / 40 * 3, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(99.5)}\n"+
        f"- SS 容错 {round(basescore / 10, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(99)}\n"+
        f"- S+ 容错 {round(basescore / 20 * 3, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(98)}\n"+
        f"🔓合格 S 容错 {round(basescore / 5, KEEP_DECIMAL_GR)} 粉，单曲 rating {chart.getRating(97)}"
    )

def getPartyInfo(info: InfoTarget) -> str:
    song = info.song
    pack = info.pack
    if pack.charts[0].type == "normal":
        chart = pack.charts[0]
        return (
            f"{song.title}（{pack.id}，{pack._type}）〈🪩宴会厅〉：\n"
            f"🎵 曲师：{song.artist}\n"+
            f"🎼 bpm：{song.bpm}\n"+
            f"🕑 版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "") + "\n"+
            f"🗂️ 分类：{song.genre}\n"+
            f"⭐ 难度：{chart.diff}\n"+
            f"TAP：{chart.tap} 个。\n"+
            f"HOLD：{chart.hold} 个。\n"+
            f"SLIDE：{chart.slide} 个。\n"+
            f"TOUCH：{chart.touch} 个。\n"+
            f"BREAK：{chart.breaks} 个。"
        )
    else:
        chart1 = pack.charts[0]  # 1P chart
        chart2 = pack.charts[1]  # 2P chart
        return (
            f"{song.title}（{pack.id}，{pack._type}）〈🪩宴会厅〉：\n"
            f"🎵 曲师：{song.artist}\n"+
            f"🎼 bpm：{song.bpm}\n"+
            f"🕑 版本：{pack.version}" + (f"〔{VERSION_DICT[pack.version]}〕" if VERSION_DICT[pack.version] else "") + "\n"+
            f"🗂️ 分类：{song.genre}\n"+
            f"⭐ 难度：{chart1.diff}\n"+
            f"TAP：1P {chart1.tap} 个，2P {chart2.tap} 个。\n"+
            f"HOLD：1P {chart1.hold} 个，2P {chart2.hold} 个。\n"+
            f"SLIDE：1P {chart1.slide} 个，2P {chart2.slide} 个。\n"+
            f"TOUCH：1P {chart1.touch} 个，2P {chart2.touch} 个。\n"+
            f"BREAK：1P {chart1.breaks} 个，2P {chart2.breaks} 个。"
        )

@info.handle()
async def _(event: Event):
    text = event.get_message().extract_plain_text().strip().lower()
    for pre in CANBE_PREFIX:
        if text.startswith(pre):
            text = text[len(pre):].strip()
            break
    for suf in CANBE_SUFFIX:
        if text.endswith(suf):
            text = text[:-len(suf)].strip()
            break
    if text == "":
        await info.finish("请提供歌曲名称或 ID。")
    query_engine = SONG_LIST.getQueryEngine()
    res = query_engine.query(text, QUERY_POLICY)
    if not res:
        await info.finish(f"❌ 查询失败！未找到「{text}」对应的曲目。")
    if len(res) > 1:
        msg = "⚠️ 找到多个符合条件的曲目，请使用更精确的名称或 ID：\n"
        for e in res:
            msg += f"- {e.song.title}（{e.pack.id}，{e.pack.type}）\n"
        await info.finish(msg.strip())
    
    target = res[0]
    if target.type == InfoTargetType.PACK:
        if target.pack.type in ["SD", "DX"]:
            msg = getPackInfo(target)
        else:
            msg = getPartyInfo(target)
    else:
        msg = getChartInfo(target)

    await info.finish(
        message=Message([
            MessageSegment.text(msg),
            await fetchChartCover(target.song.id)
        ])
    )