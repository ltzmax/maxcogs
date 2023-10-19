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
from logging import LoggerAdapter
from typing import Any, Final

import discord
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import Config, commands
from redbot.core.utils.views import ConfirmView
from .embed import (
    redupdate,
    discordpyupdate,
    redupdateinfo,
    redupdateset_url,
    failedupdate,
)

log: RedTraceLogger = getLogger("red.maxcogs.redupdate")


class RedUpdate(commands.Cog):
    """Update [botname] to latest dev changes."""

    __author__: Final[str] = "MAX, kuro"
    __version__: Final[str] = "1.4.1"
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

        self.log: LoggerAdapter[RedTraceLogger] = LoggerAdapter(
            log, {"version": self.__version__}
        )

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.is_owner()
    @commands.group(aliases=["redset"], hidden=True)
    async def redupdateset(self, ctx: commands.Context):
        """Setting commands for redupdate cog."""

    @redupdateset.command(name="url")
    async def redupdateset_url(self, ctx: commands.Context, url: str):
        """Set the url for redupdate cog.

        Has to be vaild link such as `git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot` else it will not work.
        """
        await redupdateset_url(self, ctx, url)

    @redupdateset.command(name="reset")
    async def redupdateset_reset(self, ctx: commands.Context):
        """Reset the url for redupdate cog."""
        await self.config.redupdate_url.set(
            "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        )
        await ctx.send("Successfully reset the url.")

    @redupdateset.command(name="show", aliases=["showsettings", "settings", "view"])
    async def redupdateset_show(self, ctx: commands.Context):
        """Show the url for redupdate cog."""
        url = await self.config.redupdate_url()
        await ctx.send(f"The current url is `{url}`.")

    @commands.is_owner()
    @commands.command(aliases=["updatered"])
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdate(self, ctx: commands.Context):
        """Update [botname] to latest dev changes."""
        package = await self.config.redupdate_url()
        if not package:
            return await ctx.send("You need to set correct url for your fork first.")
        shell = self.bot.get_cog("Shell")
        try:
            await shell._shell_command(
                ctx,
                f"pip install -U --force-reinstall {package}",
                send_message_on_success=False,
            )
        except AttributeError:
            return await failedupdate(self, ctx)
        await redupdate(self, ctx)

    @commands.is_owner()
    @commands.command(aliases=["dpydevupdate"])
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def discordpyupdate(self, ctx: commands.Context):
        """Update discord.py to latest dev changes.

        Do note that this will update discord.py to latest dev changes and not to latest stable release. There may be breaking changes that will break your bot and are not yet on red.
        """
        package = "git+https://github.com/Rapptz/discord.py@master"
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Discord.py Update Information",
            description="This will update discord.py to latest dev changes and not to latest stable release. There may be breaking changes that will break your bot and are not yet on red.\n\nDo you want to continue?",
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
            except AttributeError:
                return await failedupdate(self, ctx)
            await discordpyupdate(self, ctx)
        else:
            embed = discord.Embed(
                title="Discord.py Update Cancelled",
                description="Cancelled updating {}.".format(self.bot.user.name),
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed, silent=True)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdateinfo(self, ctx: commands.Context):
        """Shows information about the cog."""
        await redupdateinfo(self, ctx)
