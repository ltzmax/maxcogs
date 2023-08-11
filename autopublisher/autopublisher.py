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
from typing import Any, Dict, Final, List, Literal, Union

import discord
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list

log: RedTraceLogger = getLogger("red.maxcogs.autopublisher")

DISCORD_INFO: Final[
    str
] = "<https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server>"


class AutoPublisher(commands.Cog):
    """Automatically push news channel messages."""

    __version__: Final[str] = "0.1.11"
    __author__: Final[str] = "MAX"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/autopublisher/README.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=15786223, force_registration=True
        )
        default_guild: Dict[str, Union[bool, List[int]]] = {
            "toggle": False,
            "ignored_channels": [],
        }
        self.config.register_guild(**default_guild)

        self.log: LoggerAdapter[RedTraceLogger] = LoggerAdapter(
            log, {"version": self.__version__}
        )

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
        if message.channel.id in (
            await self.config.guild(message.guild).ignored_channels()
        ):
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if (
            not message.guild.me.guild_permissions.manage_messages
            or not message.guild.me.guild_permissions.view_channel
        ):
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                self.log.info(
                    "AutoPublisher has been disabled due to missing permissions in {guild}.".format(
                        guild=message.guild.name
                    )
                )
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
                    ),
                )

    @commands.group(aliases=["aph", "autopub"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher setting."""

    @autopublisher.command()
    @commands.bot_has_permissions(
        embed_links=True, manage_messages=True, view_channel=True
    )
    async def toggle(self, ctx: commands.Context, toggle: bool) -> None:
        """Toggle AutoPublisher enable or disable.

        - It's disabled by default.
            - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.

        **Note:**
        - This cog requires News Channel. If you don't have it, you can't use this cog.
            - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)
        """
        if "NEWS" not in ctx.guild.features:
            embed = discord.Embed(
                title="News Channel is not enabled.",
                description=f"Please enable News Channel feature in your server. [Learn more]({DISCORD_INFO})",
                color=await ctx.embed_color(),
            )
            return await ctx.send(embed=embed)
        if (
            not ctx.guild.me.guild_permissions.manage_messages
            or not ctx.guild.me.guild_permissions.view_channel
        ):
            embed = discord.Embed(
                title="Missing permissions.",
                description=f"I need `manage_messages` and `view_channel` permissions to be able to publish messages. Please ensure that I have those permissions.",
                color=await ctx.embed_color(),
            )
            return await ctx.send(embed=embed)
        await self.config.guild(ctx.guild).toggle.set(toggle)
        if toggle:
            embed = discord.Embed(
                title="AutoPublisher is now enabled.",
                description=f"AutoPublisher will now publish messages from news channels.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="AutoPublisher is now disabled.",
                description=f"AutoPublisher will no longer publish messages from news channels.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(
        aliases=["ignorechannels"], usage="<add_or_remove> <channels>"
    )
    async def ignore(
        self,
        ctx: commands.Context,
        add_or_remove: Literal["add", "remove"],
        channels: commands.Greedy[discord.TextChannel] = None,
    ) -> None:
        """Add or remove channels for your guild.

        `<add_or_remove>` should be either `add` to add channels or `remove` to remove channels.

        **Example:**
        - `[p]autopublisher ignore add #news`
        - `[p]autopublisher ignore remove #news`

        **Note:**
        - You can add or remove multiple channels at once.
        - You can also use channel ID instead of mentioning the channel.
        """
        if channels is None:
            await ctx.send("`Channels` is a required argument.")
            return

        async with self.config.guild(ctx.guild).ignored_channels() as c:
            for channel in channels:
                if add_or_remove.lower() == "add":
                    if not channel.id in c:
                        c.append(channel.id)

                elif add_or_remove.lower() == "remove":
                    if channel.id in c:
                        c.remove(channel.id)

        ids = len(list(channels))
        embed = discord.Embed(
            title="Success!",
            description=f"{'added' if add_or_remove.lower() == 'add' else 'removed'} {ids} {'channel' if ids == 1 else 'channels'}.",
            color=0xE91E63,
        )
        embed.add_field(
            name=f"{'channel:' if ids == 1 else 'channels:'}",
            value=humanize_list([channel.mention for channel in channels]),
        )  # This needs menus to be able to show all channels if there are more than 25 channels.
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(aliases=["view"])
    async def settings(self, ctx: commands.Context) -> None:
        """Show AutoPublisher setting."""
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channels = data["ignored_channels"]
        ignored_channels: List[str] = []
        for channel in channels:
            channel = ctx.guild.get_channel(channel)
            ignored_channels.append(channel.mention)
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=f"AutoPublisher is currently **{'enabled' if toggle else 'disabled'}**.",
            color=0xE91E63,
        )
        if ignored_channels:
            embed.add_field(
                name="Blacklisted Channels:",
                value=humanize_list(ignored_channels),
            )  # This needs menus to be able to show all channels if there are more than 25 channels.
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
