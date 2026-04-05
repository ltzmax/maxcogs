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

import asyncio
import contextlib
import logging
from collections import defaultdict

import discord
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red

from .view import HelpView

log = logging.getLogger("red.maxcogs.slashhelpmenu")

_TITLE = "Available Slash Commands"
_DESCRIPTION = (
    "These are all the slash commands available on this bot.\n"
    "~~Strikethrough~~ indicates missing permissions.\n"
    "Note: not all permission requirements can be detected."
)
_BASE_CHAR_COUNT = len(_TITLE) + len(_DESCRIPTION)


class SlashHelpMenu(commands.Cog):
    """
    A simple help menu that shows all available slash commands grouped by their cog names.

    This is a slash command version of the default help command. It will not show context menu commands.
    """

    __version__ = "1.1.0"
    __author__ = "MAX"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/docs/SlashHelpMenu.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987638, force_registration=True)
        self.config.register_global(eph=False)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    def _new_embed(self, color: discord.Color) -> discord.Embed:
        return discord.Embed(
            title=_TITLE,
            color=color,
            description=_DESCRIPTION,
        )

    def _collect_commands(
        self,
        commands_list: list[app_commands.Command | app_commands.Group | app_commands.ContextMenu],
    ) -> defaultdict[str, list[tuple[str, app_commands.Command | app_commands.Group]]]:
        """
        Recursively walk the app command tree and bucket every non-context-menu
        command under its cog name.
        """
        cog_commands: defaultdict[
            str, list[tuple[str, app_commands.Command | app_commands.Group]]
        ] = defaultdict(list)

        def process(
            cmd: app_commands.Command | app_commands.Group | app_commands.ContextMenu,
            group_prefix: str = "",
            parent_cog_name: str | None = None,
        ) -> None:
            if cmd.name == "help" and not group_prefix:
                return
            if isinstance(cmd, app_commands.ContextMenu):
                return
            cog_name = parent_cog_name or "Uncategorized"
            if hasattr(cmd, "binding") and cmd.binding is not None:
                cog_name = getattr(
                    cmd.binding,
                    "qualified_name",
                    cmd.binding.__class__.__name__,
                )
            elif hasattr(cmd, "cog") and cmd.cog is not None:
                cog_name = getattr(
                    cmd.cog,
                    "qualified_name",
                    cmd.cog.__class__.__name__,
                )
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

    async def _can_use(
        self,
        interaction: discord.Interaction,
        cmd: app_commands.Command | app_commands.Group | app_commands.ContextMenu,
    ) -> bool:
        """
        Check whether the invoking user can use a command, combining Red's permission
        system with Discord's default_permissions.
        """
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return True
        if await self.bot.is_owner(interaction.user):
            return True
        if not await self.bot.allowed_by_whitelist_blacklist(who=interaction.user):
            return False
        cog: commands.Cog | None = None
        if hasattr(cmd, "binding") and cmd.binding is not None:
            cog = cmd.binding
        elif hasattr(cmd, "cog") and cmd.cog is not None:
            cog = cmd.cog

        if cog is not None and await self.bot.cog_disabled_in_guild(cog, interaction.guild):
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

    async def _build_mention(
        self,
        interaction: discord.Interaction,
        display_name: str,
        cmd: app_commands.Command | app_commands.Group,
    ) -> str:
        """
        Return a properly formatted mention string for a command.

        For subcommands (e.g. "tag list"), the parent command's ID is used so that
        the mention renders as </tag list:parent_id> rather than falling back to
        plain text.  The result is wrapped in strikethrough if the user lacks
        permission to run the command.
        """
        top_level_name = display_name.split()[0]
        mention = await self.bot.get_app_command_mention(top_level_name)

        if mention and " " in display_name:
            cmd_id = mention.split(":")[-1].rstrip(">")
            mention = f"</{display_name}:{cmd_id}>"
        elif not mention:
            mention = f"`/{display_name}`"

        if not await self._can_use(interaction, cmd):
            mention = f"~~{mention}~~"

        return mention

    @commands.group()
    @commands.is_owner()
    async def slashhelpset(self, ctx: commands.Context) -> None:
        """Settings for the slash help menu."""
        if ctx.invoked_subcommand is None:
            eph = await self.config.eph()
            embed = discord.Embed(
                title="SlashHelpMenu Settings",
                color=await ctx.embed_color(),
            )
            embed.add_field(name="Ephemeral messages", value=str(eph), inline=False)
            await ctx.send(embed=embed)

    @slashhelpset.command()
    async def toggle(self, ctx: commands.Context, toggle: bool) -> None:
        """Whether the help menu should be sent as an ephemeral message."""
        await self.config.eph.set(toggle)
        await ctx.send(f"Set ephemeral to {toggle}.")

    @app_commands.command(name="help", description="Shows all available slash commands.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        eph = await self.config.eph()
        await interaction.response.defer(ephemeral=eph)
        color = await self.bot.get_embed_color(interaction.channel)
        try:
            cog_commands = self._collect_commands(self.bot.tree.get_commands())

            if not cog_commands:
                await interaction.followup.send(
                    "No slash commands available to you.", ephemeral=True
                )
                return

            pages: list[discord.Embed] = []
            current_embed = self._new_embed(color)
            current_field_count = 0
            current_char_count = _BASE_CHAR_COUNT

            for cog_name, cmds in sorted(cog_commands.items()):
                sorted_cmds = sorted(cmds, key=lambda c: c[0])
                mentions: list[str] = list(
                    await asyncio.gather(
                        *[
                            self._build_mention(interaction, display_name, cmd)
                            for display_name, cmd in sorted_cmds
                        ]
                    )
                )

                joined = " ".join(mentions)
                field_parts: list[str] = []

                if len(joined) > 1024:
                    current_chunk: list[str] = []
                    for mention in mentions:
                        candidate = " ".join(current_chunk + [mention])
                        if len(candidate) > 1024:
                            field_parts.append(" ".join(current_chunk))
                            current_chunk = [mention]
                        else:
                            current_chunk.append(mention)
                    if current_chunk:
                        field_parts.append(" ".join(current_chunk))
                else:
                    field_parts.append(joined)

                for i, part in enumerate(field_parts, 1):
                    field_name = f"{cog_name} (Part {i})" if len(field_parts) > 1 else cog_name
                    field_char_count = len(part) + len(field_name) + 10
                    if (
                        current_field_count + 1 > 25
                        or current_char_count + field_char_count > 6000
                    ):
                        pages.append(current_embed)
                        current_embed = self._new_embed(color)
                        current_field_count = 0
                        current_char_count = _BASE_CHAR_COUNT

                    current_embed.add_field(name=field_name, value=part, inline=False)
                    current_field_count += 1
                    current_char_count += field_char_count

            if current_embed.fields:
                pages.append(current_embed)

            if not pages:
                await interaction.followup.send(
                    "No slash commands available to you.", ephemeral=True
                )
                return

            total_pages = len(pages)
            for i, page in enumerate(pages, 1):
                page.set_footer(text=f"Page {i} of {total_pages}")

            if total_pages == 1:
                await interaction.followup.send(embed=pages[0], ephemeral=eph)
                return

            view = HelpView(pages, interaction.user, interaction)
            await interaction.followup.send(embed=pages[0], view=view, ephemeral=eph)
        except Exception:
            log.exception("Unhandled error in /help command")
            with contextlib.suppress(discord.HTTPException):
                await interaction.followup.send(
                    "Something went wrong while generating the help menu.",
                    ephemeral=True,
                )
