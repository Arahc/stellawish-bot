import asyncio

from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.qq import Event, MessageSegment

from ..library import score_loader_lx, score_loader_sy
from ..library.command_registry import registerCommand
from ..library.info_handler import InfoTargetType, QueryPolicy
from ..library.song_manager import SONG_LIST
from ..library.static import DIFF_NAME_LIST
from ..library.userinfo_manager import USER_INFO


CANBE_PREFIX = ("/minfo", "minfo", "/单曲", "单曲")


@registerCommand(
    name="minfo",
    usage="/minfo <歌曲名称或 ID>",
    description="查询单曲成绩。",
    aliases=("minfo", "单曲"),
    category="成绩",
)
def isCommandText(text: str) -> bool:
    lower_text = text.lower().strip()
    return any(lower_text == prefix or lower_text.startswith(prefix + " ") for prefix in CANBE_PREFIX)


async def isValidCommand(event: Event) -> bool:
    return isCommandText(event.get_message().extract_plain_text())


minfo = on_message(rule=to_me() & isValidCommand, priority=4)

QUERY_POLICY = QueryPolicy(
    allow_pack=True,
    allow_party=True,
    allow_chart=True,
)


def _markdown_escape(value: object) -> str:
    text = str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _difficulty_name(diffid: int) -> str:
    if 0 <= diffid < len(DIFF_NAME_LIST):
        return DIFF_NAME_LIST[diffid]
    return f"难度 {diffid}"


def _format_score(score) -> str:
    chart = score.chart
    level = _markdown_escape(chart.diff)
    diff = _markdown_escape(_difficulty_name(chart.diffid))
    rank = _markdown_escape(chart.getRank(score.acc))
    fc = _markdown_escape(score.fc or "-")
    fs = _markdown_escape(score.fs or "-")
    date = _markdown_escape(score.date or "-")
    rating = score.getRating()
    return f"| {diff} | {level} | {score.acc:.4f}% | {rank} | {score.dxScore} | {fc} | {fs} | {rating} | {date} |"


def _render_result(song, pack, scores: list, selected_chart=None) -> str:
    if selected_chart is not None:
        scores = [score for score in scores if score.chart.diffid == selected_chart.diffid]
    scores = sorted(scores, key=lambda score: score.chart.diffid)
    title = _markdown_escape(song.title)
    pack_type = _markdown_escape(pack.type)
    lines = [
        f"## {title}",
        f"- 谱面：{pack_type}（ID `{pack.id}`）",
        f"- 版本：{_markdown_escape(pack.version)}",
        "",
        "| 难度 | 定数 | 达成率 | 评级 | DX | FC | FS | Rating | 日期 |",
        "| --- | ---: | ---: | --- | ---: | --- | --- | ---: | --- |",
    ]
    if scores:
        lines.extend(_format_score(score) for score in scores)
    else:
        lines.append("| - | - | 暂无成绩 | - | - | - | - | - | - |")
    return "\n".join(lines)


@minfo.handle()
async def _(event: Event):
    user = USER_INFO.get(event.get_user_id())
    if not user.canMInfo():
        await minfo.finish("查询失败：请先使用 /bind 绑定成绩数据源并完成授权。")

    text = event.get_message().extract_plain_text().strip()
    lower_text = text.lower()
    for prefix in CANBE_PREFIX:
        if lower_text == prefix:
            text = ""
            break
        if lower_text.startswith(prefix + " "):
            text = text[len(prefix):].strip()
            break
    if not text:
        await minfo.finish("请提供歌曲名称或 ID。")

    results = SONG_LIST.getQueryEngine().query(text.lower(), QUERY_POLICY)
    if not results:
        await minfo.finish(f"查询失败：未找到「{text}」对应的曲目。")
    if len(results) > 1:
        lines = ["找到多个符合条件的谱面，请使用更精确的名称或 ID："]
        for target in results:
            pack = target.pack
            suffix = f"，{_difficulty_name(target.chart.diffid)}" if target.chart else ""
            lines.append(f"- {target.song.title}（{pack.id}，{pack.type}{suffix}）")
        await minfo.finish("\n".join(lines))

    target = results[0]
    pack = target.pack
    loader = score_loader_sy if user.dataSource == "sy" else score_loader_lx
    try:
        scores = await asyncio.wait_for(loader.singleScore(user, pack.id), timeout=12)
    except asyncio.TimeoutError:
        await minfo.finish("查询超时：成绩服务响应过慢，请稍后重试。")
    except (score_loader_sy.NotBound, score_loader_sy.QueryLimitExceeded):
        await minfo.finish("查询失败：水鱼账号未完成授权或查询次数已达上限。")
    except Exception as e:
        await minfo.finish(f"查询失败：成绩服务暂时不可用（{type(e).__name__}: {str(e)}），请稍后重试。")

    markdown = _render_result(target.song, pack, scores, target.chart if target.type == InfoTargetType.CHART else None)
    await minfo.finish(MessageSegment.markdown(markdown))

