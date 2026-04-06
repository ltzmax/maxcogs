"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from collections import defaultdict

import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red


_TITLE = "Available Slash Commands"
_DESCRIPTION = (
    "These are all the slash commands available on this bot.\n"
    "~~Strikethrough~~ indicates missing permissions.\n"
    "Note: not all permission requirements can be detected."
)
_BASE_CHAR_COUNT = len(_TITLE) + len(_DESCRIPTION)


def new_embed(color: discord.Color) -> discord.Embed:
    """Return a fresh help embed with the standard title and description."""
    return discord.Embed(
        title=_TITLE,
        color=color,
        description=_DESCRIPTION,
    )


def collect_commands(
    commands_list: list,
) -> defaultdict:
    """
    Recursively walk the app command tree and bucket every non-context-menu
    command under its cog name.
    """
    cog_commands: defaultdict = defaultdict(list)

    def process(cmd, group_prefix="", parent_cog_name=None):
        if cmd.name == "help" and not group_prefix:
            return
        if isinstance(cmd, app_commands.ContextMenu):
            return

        cog_name = parent_cog_name or "Uncategorized"
        if hasattr(cmd, "binding") and cmd.binding is not None:
            cog_name = getattr(cmd.binding, "qualified_name", cmd.binding.__class__.__name__)
        elif hasattr(cmd, "cog") and cmd.cog is not None:
            cog_name = getattr(cmd.cog, "qualified_name", cmd.cog.__class__.__name__)
        elif hasattr(cmd, "module") and cmd.module:
            cog_name = cmd.module.split(".")[-1].replace("cog", "").title()

        display_name = f"{group_prefix} {cmd.name}".strip() if group_prefix else cmd.name

        if isinstance(cmd, app_commands.Group):
            if cmd.description and not cmd.commands:
                cog_commands[cog_name].append((display_name, cmd))
            for subcmd in cmd.commands:
                process(subcmd, group_prefix=display_name, parent_cog_name=cog_name)
        else:
            cog_commands[cog_name].append((display_name, cmd))

    for cmd in commands_list:
        process(cmd)

    return cog_commands


async def can_use(
    bot: Red,
    interaction: discord.Interaction,
    cmd,
) -> bool:
    """
    Check whether the invoking user can use a command, combining Red's permission
    system with Discord's default_permissions.
    """
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return True
    if await bot.is_owner(interaction.user):
        return True
    if not await bot.allowed_by_whitelist_blacklist(who=interaction.user):
        return False

    cog: commands.Cog | None = None
    if hasattr(cmd, "binding") and cmd.binding is not None:
        cog = cmd.binding
    elif hasattr(cmd, "cog") and cmd.cog is not None:
        cog = cmd.cog

    if cog is not None and await bot.cog_disabled_in_guild(cog, interaction.guild):
        return False

    default_perms: discord.Permissions | None = None
    current = cmd
    while current is not None:
        default_perms = getattr(current, "default_permissions", None)
        if default_perms is not None:
            break
        current = getattr(current, "parent", None)

    if default_perms is None:
        return True
    if not interaction.guild.me.guild_permissions.is_superset(default_perms):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    return interaction.user.guild_permissions.is_superset(default_perms)


async def build_mention(
    bot: Red,
    interaction: discord.Interaction,
    display_name: str,
    cmd,
) -> str:
    """
    Return a properly formatted mention string for a command.

    For subcommands (e.g. "tag list"), the parent command's ID is used so that
    the mention renders as </tag list:parent_id> rather than falling back to
    plain text. The result is wrapped in strikethrough if the user lacks
    permission to run the command.
    """
    top_level_name = display_name.split()[0]
    mention = await bot.get_app_command_mention(top_level_name)

    if mention and " " in display_name:
        cmd_id = mention.split(":")[-1].rstrip(">")
        mention = f"</{display_name}:{cmd_id}>"
    elif not mention:
        mention = f"`/{display_name}`"

    if not await can_use(bot, interaction, cmd):
        mention = f"~~{mention}~~"

    return mention
