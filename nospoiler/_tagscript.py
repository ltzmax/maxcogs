from importlib import reload
from typing import Any, Dict, Final, List, final

import TagScriptEngine as tse
from redbot.core.bot import Red
from redbot.core import commands
from redbot.core.errors import CogLoadError
from redbot.core.utils.chat_formatting import humanize_number

warn_message: Final[
    str
] = "{member(mention)} Usage of spoiler is not allowed in this server."

TAGSCRIPT_LIMIT: Final[int] = 10_000


blocks: List[tse.Block] = [
    tse.LooseVariableGetterBlock(),
    tse.AssignmentBlock(),
    tse.CommandBlock(),
    tse.EmbedBlock(),
    tse.IfBlock(),
]

tagscript_engine: tse.Interpreter = tse.Interpreter(blocks)


def process_tagscript(
    content: str, seed_variables: Dict[str, tse.Adapter] = {}
) -> Dict[str, Any]:
    output: tse.Response = tagscript_engine.process(content, seed_variables)
    kwargs: Dict[str, Any] = {}
    if output.body:
        kwargs["content"] = output.body[:2000]
    if embed := output.actions.get("embed"):
        kwargs["embed"] = embed
    return kwargs


class TagError(Exception):
    """
    Base exception class.
    """


@final
class TagCharacterLimitReached(TagError):
    """Raised when the TagScript character limit is reached."""

    def __init__(self, limit: int, length: int):
        super().__init__(
            f"TagScript cannot be longer than {humanize_number(limit)} (**{humanize_number(length)}**)."
        )


@final
class TagscriptConverter(commands.Converter[str]):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        try:
            await ctx.cog.validate_tagscript(argument)
        except TagError as e:
            raise commands.BadArgument(str(e))
        return argument


async def validate_tagscriptengine(
    bot: Red, tse_version: str, *, reloaded: bool = False
):
    try:
        import TagScriptEngine as tse
    except ImportError as exc:
        raise CogLoadError(
            "The NoSpoiler cog failed to install TagScriptEngine. Reinstall the cog and restart your "
            "bot. If it continues to fail to load contact the cog author."
        ) from exc

    commands = [
        "`pip(3) uninstall -y TagScriptEngine`",
        "`pip(3) uninstall -y TagScript`",
        f"`pip(3) install AdvancedTagScriptEngine=={tse_version}`",
    ]
    commands = "\n".join(commands)

    message = (
        "The NoSpoiler cog attempted to install AdvancedTagScriptEngine, but the version installed "
        "is outdated. Shut down your bot, then in shell in your venv, run the following "
        f"commands:\n{commands}\nAfter running these commands, restart your bot and reload "
        "Tags. If it continues to fail to load, contact the cog author."
    )

    if not hasattr(tse, "VersionInfo"):
        if not reloaded:
            reload(tse)
            await validate_tagscriptengine(bot, tse_version, reloaded=True)
            return

        await bot.send_to_owners(message)
        raise CogLoadError(message)

    if tse.version_info < tse.VersionInfo.from_str(tse_version):
        await bot.send_to_owners(message)
        raise CogLoadError(message)
