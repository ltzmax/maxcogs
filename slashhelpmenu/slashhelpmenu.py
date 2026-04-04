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

import contextlib
from collections import defaultdict

import discord
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red

from .view import HelpView


class SlashHelpMenu(commands.Cog):
    """
    A simple help menu that shows all available slash commands grouped by their cog names.

    This is a slash command version of the default help command. It will not show context menu commands.
    """

    __version__ = "1.0.0"
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

    async def _can_use(
        self,
        interaction: discord.Interaction,
        cmd: app_commands.Command | app_commands.Group,
    ) -> bool:
        """
        Check if the user and the bot can use a command based on default_permissions.

        (In some cases this may not be 100% accurate, but it's the best we can do without actually trying to invoke the command.)
        """
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return True
        default_perms = None
        current = cmd
        while current is not None:
            default_perms = getattr(current, "default_permissions", None)
            if default_perms is not None:
                break
            current = getattr(current, "parent", None)
        if default_perms is None:
            return True
        bot_me = interaction.guild.me
        if not bot_me.guild_permissions.is_superset(default_perms):
            return False
        if interaction.user.guild_permissions.administrator or await self.bot.is_owner(
            interaction.user
        ):
            return True
        return interaction.user.guild_permissions.is_superset(default_perms)

    @commands.group()
    @commands.is_owner()
    async def slashhelpset(self, ctx: commands.Context):
        """Settings for the slash help menu."""

    @slashhelpset.command()
    async def toggle(self, ctx: commands.Context, toggle: bool):
        """Whether the help menu should be sent as an ephemeral message."""
        await self.config.eph.set(toggle)
        await ctx.send(f"Set ephemeral to {toggle}.")

    @app_commands.command(name="help", description="Shows all available slash commands.")
    @app_commands.default_permissions(embed_links=True)
    async def help_command(self, interaction: discord.Interaction):
        try:
            commands_list = self.bot.tree.get_commands()
            cog_commands = defaultdict(list)

            # This is a recursive function that processes all commands and groups
            # and puts them into a dictionary with the cog name as the key.
            def process_command(cmd, group_prefix="", parent_cog_name=None):
                if cmd.name == "help" and not group_prefix:
                    return

                # Skip context menus for now.
                # they're pretty limited so idk if its worth the effort to include them in the help menu.
                # but in future i'll imporve this to include them in a separate section or something.
                if isinstance(cmd, app_commands.ContextMenu):
                    return

                cog_name = parent_cog_name or "Uncategorized"
                if hasattr(cmd, "binding") and cmd.binding:
                    cog_name = cmd.binding.__class__.__name__.replace("Cog", "").title()
                elif hasattr(cmd, "cog") and cmd.cog:
                    cog_name = cmd.cog.__class__.__name__.replace("Cog", "").title()
                elif hasattr(cmd, "module") and cmd.module:
                    cog_name = cmd.module.split(".")[-1].replace("cog", "").title()
                display_name = f"{group_prefix} {cmd.name}".strip() if group_prefix else cmd.name

                if isinstance(cmd, app_commands.Group):
                    if hasattr(cmd, "description") and cmd.description and not cmd.commands:
                        cog_commands[cog_name].append((display_name, cmd))
                    for subcmd in cmd.commands:
                        process_command(
                            subcmd, group_prefix=display_name, parent_cog_name=cog_name
                        )
                else:
                    cog_commands[cog_name].append((display_name, cmd))

            for cmd in commands_list:
                process_command(cmd)

            if not cog_commands:
                return await interaction.response.send_message(
                    "No slash commands available to you.", ephemeral=True
                )

            pages = []
            current_embed = discord.Embed(
                title="Available Slash Commands",
                color=discord.Color.blurple(),
                description="These are all the slash commands available on this bot.\n~~Strikethrough~~ indicates missing permissions.\nNote: not all permission requirements can be detected.",
            )
            current_field_count = 0
            current_char_count = 0

            for cog_name, cmds in sorted(cog_commands.items()):
                cmds = sorted(cmds, key=lambda c: c[0])
                field_parts = []

                mentions = []
                for display_name, cmd in cmds:
                    slash_mention = await self.bot.get_app_command_mention(display_name)
                    if slash_mention is None:
                        slash_mention = f"`/{display_name}`"
                    if not await self._can_use(interaction, cmd):
                        slash_mention = f"~~{slash_mention}~~"
                    mentions.append(slash_mention)

                current_part = " ".join(mentions) if mentions else "None"
                if len(current_part) > 1024:
                    current_field_part = []
                    for mention in mentions:
                        _line = " ".join(current_field_part + [mention])
                        if len(_line) > 1024:
                            field_parts.append(" ".join(current_field_part))
                            current_field_part = [mention]
                        else:
                            current_field_part.append(mention)
                    if current_field_part:
                        field_parts.append(" ".join(current_field_part))
                else:
                    field_parts.append(current_part)

                for i, part in enumerate(field_parts, 1):
                    field_name = f"{cog_name} (Part {i})" if len(field_parts) > 1 else cog_name
                    field_char_count = len(part)

                    if (
                        current_field_count + 1 > 25
                        or current_char_count + field_char_count + len(field_name) + 10 > 3000
                    ):
                        pages.append(current_embed)
                        current_embed = discord.Embed(
                            title="Available Slash Commands",
                            color=discord.Color.blurple(),
                            description="These are all the slash commands available on this bot.\n~~Strikethrough~~ indicates missing permissions. Note: not all permission requirements can be detected.",
                        )
                        current_field_count = 0
                        current_char_count = 0

                    current_embed.add_field(name=field_name, value=part, inline=False)
                    current_field_count += 1
                    current_char_count += field_char_count + len(field_name) + 10

            if current_embed.fields:
                pages.append(current_embed)

            if not pages:
                return await interaction.response.send_message(
                    "No slash commands available to you.", ephemeral=True
                )

            total_pages = len(pages)
            for i, page in enumerate(pages, 1):
                page.set_footer(text=f"Page {i} of {total_pages}")

            eph = await self.config.eph()
            if len(pages) == 1:
                return await interaction.response.send_message(embed=pages[0], ephemeral=eph)

            view = HelpView(pages, interaction.user)
            await interaction.response.send_message(embed=pages[0], view=view, ephemeral=eph)
            view.message = await interaction.original_response()
        except Exception:
            with contextlib.suppress(discord.HTTPException):
                await interaction.response.send_message(
                    "Something went wrong while generating the help menu.", ephemeral=True
                )
