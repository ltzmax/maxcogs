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

import discord
from red_commons.logging import getLogger
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red

from .formatters import _BASE_CHAR_COUNT, build_mention, can_use, collect_commands, new_embed
from .view import HelpView


log = getLogger("red.maxcogs.slashhelpmenu")


class SlashHelpMenu(commands.Cog):
    """
    A simple help menu that shows all available slash commands grouped by their cog names.

    This is a slash command version of the default help command. It will not show context menu commands.
    """

    __version__ = "1.2.0"
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

    def _collect_commands(self, commands_list: list) -> dict:
        return collect_commands(commands_list)

    async def _can_use(self, interaction: discord.Interaction, cmd) -> bool:
        return await can_use(self.bot, interaction, cmd)

    async def _build_mention(
        self, interaction: discord.Interaction, display_name: str, cmd
    ) -> str:
        return await build_mention(self.bot, interaction, display_name, cmd)

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
            current_embed = new_embed(color)
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
                        candidate = " ".join([*current_chunk, mention])
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
                        current_embed = new_embed(color)
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
