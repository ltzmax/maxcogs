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

from typing import Any, Final, Optional, Literal

import discord
import logging
from redbot.core import commands, Config
from redbot.core.utils.views import ConfirmView
from redbot.core.utils.chat_formatting import box
from .view import Buttons

log = logging.getLogger("red.maxcogs.redupdate")


async def redupdate(self, ctx: commands.Context):
    embed = discord.Embed(
        description="Successfully updated {}.".format(self.bot.user.name),
        color=await ctx.embed_color(),
    )
    embed.set_footer(text="Restart required to apply changes!")
    view = Buttons(ctx)
    view.message = await ctx.send(embed=embed, view=view)


async def failedupdate(self, ctx: commands.Context):
    msg = (
        "You need to have Shell from JackCogs loaded and installed to use this command."
    )
    embed = discord.Embed(
        title="Error in redupdate",
        description=msg,
        color=await ctx.embed_color(),
    )
    view = discord.ui.View()
    style = discord.ButtonStyle.gray
    jack = discord.ui.Button(
        style=style,
        label="JackCogs repo",
        url="https://github.com/jack1142/JackCogs",
    )
    view.add_item(item=jack)
    return await ctx.send(embed=embed, view=view)


class RedUpdate(commands.Cog):
    """Update [botname] to latest dev/stable changes."""

    __author__: Final[str] = "MAX, kuro"
    __version__: Final[str] = "1.4.4"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/redupdate"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=0x1A108201, force_registration=True
        )
        default_global = {
            "redupdate_url": "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        }
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.is_owner()
    @commands.group(aliases=["redset"])
    async def redupdateset(self, ctx: commands.Context):
        """Setting commands for redupdate cog."""

    @redupdateset.command(name="url")
    async def redupdateset_url(self, ctx: commands.Context, url: str):
        """Set your custom fork url of red.

        Has to be vaild link such as `git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot` else it will not work.
        """
        # Cause i'm super lazy and don't want to make a regex for this.
        # usually forks that are private uses `git+ssh://git@` instead of `https://`.
        if not url.startswith("git+ssh://git@github.com") and not url.startswith(
            "git+https://github.com"
        ):
            return await ctx.send("This is not a valid url for your fork.")
        if not url.endswith("#egg=Red-DiscordBot"):
            return await ctx.send("This is not a valid url for your fork.")
        data = await self.config.redupdate_url()
        if data == url:
            return await ctx.send("This url is already set.")
        await self.config.redupdate_url.set(url)
        await ctx.tick()

    @redupdateset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def redupdateset_settings(self, ctx: commands.Context):
        """Show the url for redupdate cog."""
        url = await self.config.redupdate_url()
        embed = discord.Embed(
            title="Redupdate Settings",
            description="Current url for redupdate cog is `{}`.".format(url),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @redupdateset.command(name="version")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdateset_version(self, ctx: commands.Context):
        """Shows information about the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)

    @commands.is_owner()
    @commands.command(aliases=["devupdate", "updatered"], usage="[version]")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdate(
        self,
        ctx: commands.Context,
        version: Optional[Literal["dev", "stable"]] = "stable",
    ):
        """
        update [botname] to latest changes.

        it will update to latest stable changes by default unless you specify `dev` as version.

        Arguments:
        - `[version]`: `dev` or `stable`
        """
        package = (
            "Red-DiscordBot"
            if version == "stable"
            else await self.config.redupdate_url()
        )
        view = ConfirmView(ctx.author, disable_buttons=True)
        if version == "dev":
            embed = discord.Embed(
                title="Red Update Information",
                description="This will update {} to latest dev changes.".format(
                    self.bot.user.name
                ),
                color=await ctx.embed_color(),
            )
            embed.add_field(
                name="⚠️Warning⚠️",
                value="This will update to latest dev changes and may include breaking changes that can break cogs that does not support latest changes. Are you sure you want to continue?",
                inline=False,
            )
            embed.add_field(
                name="Note:",
                value="You should be using ``{prefix}updatered`` without specifying version to update to latest stable changes.".format(
                    prefix=ctx.clean_prefix,
                    inline=False,
                ),
            )
            embed.set_footer(
                text="Be sure you want to update to latest dev changes before continuing!"
            )
            view.message = await ctx.send(embed=embed, view=view)
            await view.wait()
            if view.result:
                shell = self.bot.get_cog("Shell")
                try:
                    await shell._shell_command(
                        ctx,
                        f"pip install -U --force-reinstall {package}",
                        send_message_on_success=False,
                    )
                except AttributeError as e:
                    return await failedupdate(self, ctx)
                    log.error(e)
                await redupdate(self, ctx)
            else:
                embed = discord.Embed(
                    title="Red Update Cancelled",
                    description="Cancelled updating {}.".format(self.bot.user.name),
                    color=await ctx.embed_color(),
                )
                await ctx.send(embed=embed, silent=True)
        if version == "stable":
            shell = self.bot.get_cog("Shell")
            try:
                await shell._shell_command(
                    ctx,
                    f"pip install -U --force-reinstall {package}",
                    send_message_on_success=False,
                )
            except AttributeError as e:
                return await failedupdate(self, ctx)
                log.error(e)
            await redupdate(self, ctx)

    @commands.is_owner()
    @commands.command(aliases=["dpydevupdate"], hidden=True)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def discordpyupdate(self, ctx: commands.Context):
        """Update discord.py to latest dev changes.

        Do note that this will update discord.py to latest dev changes and not to latest stable release. There may be breaking changes that will break your bot and are not yet on red.
        """
        package = "git+https://github.com/Rapptz/discord.py@master"
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Discord.py Update Information",
            description="This will update discord.py to latest dev changes and not to latest stable release. There may be breaking changes that will break your bot and are not yet on red and may fail to start your bot.\n\nDo you want to continue?",
            color=await ctx.embed_color(),
        )
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            shell = self.bot.get_cog("Shell")
            try:
                await shell._shell_command(
                    ctx,
                    f"pip install -U --force-reinstall {package}",
                    send_message_on_success=False,
                )
            except AttributeError as e:
                return await failedupdate(self, ctx)
                log.error(e)
            await redupdate(self, ctx)
        else:
            embed = discord.Embed(
                title="Discord.py Update Cancelled",
                description="Cancelled updating {}.".format(self.bot.user.name),
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed, silent=True)
