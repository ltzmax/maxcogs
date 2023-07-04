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
from logging import LoggerAdapter
from typing import Dict, Final, Any

import discord
from redbot.core.bot import Red
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from red_commons.logging import RedTraceLogger, getLogger

log: RedTraceLogger = getLogger("red.maxcogs.autopublisher")

DISCORD_INFO: Final[str] = "<https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server>"


class AutoPublisher(commands.Cog):
    """Automatically push news channel messages."""
    
    __version__: Final[str] = "0.1.10"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/autopublisher/README.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=15786223, force_registration=True
        )
        default_guild: Dict[str, bool] = {
            "toggle": False,
        }
        self.config.register_guild(**default_guild)
        
        self.log: LoggerAdapter[RedTraceLogger] = LoggerAdapter(log, {"version": self.__version__})

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message) -> None:
        """Publish message to news channel."""
        if message.guild is None:
            return
        if not await self.config.guild(message.guild).toggle():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if (
            not message.guild.me.guild_permissions.manage_messages
            or not message.guild.me.guild_permissions.view_channel
        ):
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                self.log.info("AutoPublisher has been disabled due to missing permissions in {guild}.".format(guild=message.guild.name))
            return
        if "NEWS" not in message.guild.features:
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                self.log.info(
                    "AutoPublisher has been disabled due to missing News Channel feature in {guild}.".format(
                        guild=message.guild.name
                    )
                )
            return
        if not message.channel.is_news():
            return
        if message.channel.is_news():
            try:
                await asyncio.wait_for(message.publish(), timeout=60)
            except (
                discord.HTTPException,
                discord.Forbidden,
                asyncio.TimeoutError,
            ) as e:
                self.log.error(
                    "Failed to publish message in {channel} due to {error}".format(
                        channel=message.channel.mention, error=e
                    )
                )

    @commands.group(aliases=["aph", "autopub"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher setting."""

    @autopublisher.command()
    async def toggle(self, ctx: commands.Context, toggle: bool) -> None:
        """Toggle AutoPublisher enable or disable.

        - It's disabled by default.
            - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.

        **Note:**
        - This cog requires News Channel. If you don't have it, you can't use this cog.
            - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)
        """
        if "NEWS" not in ctx.guild.features:
            await ctx.send(
                "This server doesn't have News Channel feature to use this cog.\nLearn more here on how to enable:\n{DISCORD_INFO}".format(
                    DISCORD_INFO=DISCORD_INFO
                ),
                ephemeral=True,
            )
            return
        if (
            not ctx.guild.me.guild_permissions.manage_messages
            or not ctx.guild.me.guild_permissions.view_channel
        ):
            await ctx.send(
                "I don't have `manage_messages` or `view_channel` permission to use this cog.",
                ephemeral=True,
            )
            return
        await self.config.guild(ctx.guild).toggle.set(toggle)
        if toggle:
            await ctx.send("AutoPublisher is now enabled.")
        else:
            await ctx.send("AutoPublisher is now disabled.")

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(aliases=["view"])
    async def settings(self, ctx: commands.Context) -> None:
        """Show AutoPublisher setting."""
        config = await self.config.guild(ctx.guild).toggle()
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=f"AutoPublisher is currently **{'enabled' if config else 'disabled'}**.",
            color=0xE91E63,
        )
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command()
    async def version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
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
        await ctx.send(embed=embed)
