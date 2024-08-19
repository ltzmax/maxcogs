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
import logging
from typing import Any, Dict, Final, List, Literal, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView
from .view import ChannelView

log = logging.getLogger("red.maxcogs.autopublisher")


class AutoPublisher(commands.Cog):
    """Automatically push news channel messages."""

    __version__: Final[str] = "2.2.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/AutoPublisher.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=15786223, force_registration=True)
        default_guild: Dict[str, Union[bool, List[int]]] = {
            "toggle": False,
            "ignored_channels": [],
        }
        default_global = {
            "published_count": 0,
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def increment_published_count(self):
        data = await self.config.all()
        total_count = data.get("published_count", 0)
        total_count += 1
        await self.config.published_count.set(total_count)

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message) -> None:
        """Automatically publish messages in news channels."""
        if message.guild is None:
            return

        isAutoPublisherEnabled = await self.config.guild(message.guild).toggle()
        ignoredChannels = await self.config.guild(message.guild).ignored_channels()
        isCogDisabled = await self.bot.cog_disabled_in_guild(self, message.guild)
        hasPermissions = (
            message.guild.me.guild_permissions.manage_messages
            and message.guild.me.guild_permissions.view_channel
        )
        isNewsFeatureEnabled = "NEWS" in message.guild.features
        isTextChannel = isinstance(message.channel, discord.TextChannel)
        isNewsChannel = isTextChannel and message.channel.is_news()

        if (
            not isAutoPublisherEnabled
            or message.channel.id in ignoredChannels
            or isCogDisabled
            or not hasPermissions
        ):
            return
        if not isNewsFeatureEnabled:
            if isAutoPublisherEnabled:
                await self.config.guild(message.guild).toggle.set(False)
                log.warning(
                    f"AutoPublisher has been disabled in {message.guild} due to News Channel feature not being enabled."
                )
            return
        if not isNewsChannel and isTextChannel:
            return
        if isTextChannel and isNewsChannel:
            try:
                await asyncio.sleep(0.5)
                await asyncio.wait_for(message.publish(), timeout=60)
                await self.increment_published_count()
            except (
                discord.HTTPException,
                discord.Forbidden,
                asyncio.TimeoutError,
            ) as e:
                log.error(e)

    @commands.guild_only()
    @commands.group(aliases=["aph", "autopub"])
    @commands.admin_or_permissions(manage_guild=True)
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher setting."""

    @commands.is_owner()
    @autopublisher.command()
    async def stats(self, ctx: commands.Context):
        """
        Show the number of published messages.

        NOTE: The count will never reset unless you manually reset it or and delete the data from the files. (not recommended)
        """
        data = await self.config.all()
        total_count = data.get("published_count", 0)
        msg = (
            "Total Published Messages:\n"
            f"{box(humanize_number(total_count), lang='yaml')}"
        )
        await ctx.send(msg)

    @autopublisher.command()
    @commands.bot_has_permissions(manage_messages=True, view_channel=True)
    async def toggle(self, ctx: commands.Context):
        """Toggle AutoPublisher enable or disable.

        - It's disabled by default.
            - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.

        **Note:**
        - This cog requires News Channel. If you don't have it, you can't use this cog.
            - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)
        """
        if "NEWS" not in ctx.guild.features:
            view = discord.ui.View()
            style = discord.ButtonStyle.gray
            discordinfo = discord.ui.Button(
                style=style,
                label="Learn more here",
                url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                emoji="<:icons_info:880113401207095346>",
            )
            view.add_item(item=discordinfo)
            return await ctx.send(
                f"Your server doesn't have News Channel feature. Please enable it first.",
                view=view,
            )
        await self.config.guild(ctx.guild).toggle.set(
            not await self.config.guild(ctx.guild).toggle()
        )
        toggle = await self.config.guild(ctx.guild).toggle()
        await ctx.send(f"AutoPublisher has been {'enabled' if toggle else 'disabled'}.")

    @autopublisher.command()
    async def ignorechannel(self, ctx: commands.Context):
        """Ignore a news channel to prevent AutoPublisher from publishing messages in it.

        Please note select menu's can't view more than 25 channels.

        - This command will show a select menu to choose one or more news channel(s) to ignore.

        **Note:**
        - Use `Confirm` button to confirm the selected channel(s) to ignore.
        - Use `Remove` button to remove the selected channel(s) from the ignored list.
        - You can confrim or remove multiple channels at once. (must go by one by one)
        """
        if not "NEWS" in ctx.guild.features:
            view = discord.ui.View()
            style = discord.ButtonStyle.gray
            discordinfo = discord.ui.Button(
                style=style,
                label="Learn more here",
                url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                emoji="<:icons_info:880113401207095346>",
            )
            view.add_item(item=discordinfo)
            return await ctx.send(
                f"Your server doesn't have News Channel feature. Please enable it first.",
                view=view,
            )

        # Check if there are any news channels
        news_channels = [channel for channel in ctx.guild.text_channels if channel.is_news()]
        if not news_channels:
            return await ctx.send("There are no news channels available to ignore.")

        view = ChannelView(ctx, self.bot, self.config, ctx.guild.id)
        message = await ctx.send("Select a news channel to ignore:", view=view)
        view.message = message  # Set the message reference in the view

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
        msg = (
            f"AutoPublisher is currently {'enabled' if toggle else 'disabled'}.\n"
            f"Ignored channels: {humanize_list(ignored_channels) if ignored_channels else 'None'}"
        )
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=msg,
            color=await ctx.embed_color(),
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
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)

    @autopublisher.command()
    async def reset(self, ctx: commands.Context) -> None:
        """Reset AutoPublisher setting."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset AutoPublisher setting?", view=view
        )
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            await ctx.send("AutoPublisher setting has been reset.")
        else:
            await ctx.send("AutoPublisher setting reset has been cancelled.")

    @commands.is_owner()
    @autopublisher.command(hidden=True)  # To prevent accidental usage.
    @commands.bot_has_permissions(embed_links=True)
    async def resetcount(self, ctx: commands.Context) -> None:
        """Reset the published messages count."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Reset Published Messages Count",
            description="Are you sure you want to reset the published messages count?",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="⚠️WARNING⚠️",
            value="This action will reset the published messages count to `0` and cannot be undone unless you have a backup of the data.",
            inline=False,
        )
        embed.set_footer(text="Be careful with this action.")
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self.config.published_count.set(0)
            await ctx.send("Published messages count has been reset.")
        else:
            await ctx.send("Published messages count reset has been cancelled.")
