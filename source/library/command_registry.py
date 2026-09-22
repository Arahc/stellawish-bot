from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class CommandInfo:
    name: str
    usage: str
    description: str
    aliases: tuple[str, ...] = ()
    category: str = "其他"
    permission: str | None = None


CHECKERS: list[Callable[[str], bool]] = []
COMMANDS: list[CommandInfo] = []
CATEGORY_ORDER = ("查询", "成绩", "账号与设置", "游戏", "管理", "其他")

def registerChecker(func):
    CHECKERS.append(func)
    return func


def registerCommand(
    *,
    name: str,
    usage: str,
    description: str,
    aliases: Iterable[str] = (),
    category: str = "其他",
    permission: str | None = None,
):
    """Register command matching logic and its help metadata together."""
    def decorator(checker: Callable[[str], bool]):
        CHECKERS.append(checker)
        COMMANDS.append(CommandInfo(
            name=name,
            usage=usage,
            description=description,
            aliases=tuple(aliases),
            category=category,
            permission=permission,
        ))
        return checker
    return decorator


def getCommands() -> tuple[CommandInfo, ...]:
    return tuple(COMMANDS)


def registerCommandInfo(
    command: CommandInfo,
    checker: Callable[[str], bool] | None = None,
) -> None:
    """Register help metadata for commands owned by external plugins."""
    COMMANDS.append(command)
    if checker is not None:
        CHECKERS.append(checker)


def renderHelp() -> str:
    lines = [
        "# 星愿 Bot 帮助",
        "",
        "使用下面的指令格式与 Bot 交互。尖括号表示必填参数，方括号表示可选参数。",
        "",
    ]
    categories: dict[str, list[CommandInfo]] = {}
    for command in COMMANDS:
        categories.setdefault(command.category, []).append(command)

    ordered_categories = [category for category in CATEGORY_ORDER if category in categories]
    ordered_categories.extend(category for category in categories if category not in CATEGORY_ORDER)
    for category in ordered_categories:
        commands = sorted(categories[category], key=lambda command: command.name)
        lines.append(f"## {category}")
        lines.append("")
        for command in commands:
            lines.append(f"### `{command.usage}`")
            lines.append(command.description)
            if command.permission:
                lines.append(f"权限：`{command.permission}`")
            if command.aliases:
                lines.append(f"别名：{'、'.join(f'`{alias}`' for alias in command.aliases)}")
            lines.append("")
    return "\n".join(lines).rstrip()

def isAnyCommand(text: str) -> bool:
    return any(checker(text) for checker in CHECKERS)
