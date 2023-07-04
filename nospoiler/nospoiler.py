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
import re
from typing import Union, Final, Pattern, Dict, Optional, Any

import discord
from redbot.core.bot import Red
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from red_commons.logging import RedTraceLogger, getLogger

SPOILER_REGEX: Pattern[str] = re.compile(r"(?s)\|\|(.+?)\|\|")

log: RedTraceLogger = getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.5.2"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/nospoiler/README.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "log_channel": None,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def log_channel_embed(
        self,
        guild: discord.Guild,
        message: discord.Message,
        attachment: Union[discord.Attachment, None] = None,
    ) -> None:
        """Send embed to log channel."""
        log_channel = await self.config.guild(guild).log_channel()
        log_channel = guild.get_channel(log_channel)
        if log_channel is None:
            return
        if (
            not log_channel.permissions_for(guild.me).send_messages
            or not log_channel.permissions_for(guild.me).embed_links
        ):
            await self.config.guild(guild).log_channel.set(None)
            log.info(
                f"Spoiler filter is now disabled because I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            return
        if message.content:
            embed = discord.Embed(
                title="Spoiler Message Deleted",
                description=f"**Author:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}\n**Message:** {box(message.content)}",
                color=await self.bot.get_embed_color(log_channel),
            )
        else:
            embed = discord.Embed(
                title="Spoiler Message Deleted",
                description=f"**Author:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}",
                color=await self.bot.get_embed_color(log_channel),
            )
        if attachment is not None:
            embed.add_field(name="Attachment:", value=attachment.url)
            view = discord.ui.View()
            style = discord.ButtonStyle.gray
            attachment = discord.ui.Button(
                style=style, label="Attachment URL", url=attachment.url
            )
            view.add_item(item=attachment)
            await log_channel.send(embed=embed, view=view)
        else:
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """handle spoiler messages"""
        if message.guild is None:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if not message.guild.me.guild_permissions.manage_messages:
            if await self.config.guild(message.guild).enabled():
                await self.config.guild(message.guild).enabled.set(False)
                log.info(
                    f"Spoiler filter is now disabled because I don't have manage_messages permission."
                )
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if SPOILER_REGEX.search(message.content):
            await self.log_channel_embed(message.guild, message)
            await message.delete()
            return
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    await self.log_channel_embed(message.guild, message, attachment)
                    await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        """handle edits"""
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        if not await self.config.guild(guild).enabled():
            return
        if not guild.me.guild_permissions.manage_messages:
            if await self.config.guild(guild).enabled():
                await self.config.guild(guild).enabled.set(False)
                log.info(
                    f"Spoiler filter is now disabled because I don't have manage_messages permission."
                )
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if message.author.bot:
            return
        if SPOILER_REGEX.search(message.content):
            await self.log_channel_embed(guild, message)
            await message.delete()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx: commands.Context) -> None:
        """Manage the spoiler filter settings."""

    @nospoiler.command()
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle the spoiler filter on or off.

        Spoiler filter is disabled by default.
        """
        if not ctx.bot_permissions.manage_messages:
            msg = (
                f"{self.bot.user.name} does not have permission to `manage_messages` to remove spoiler.\n"
                "It need this permission before you can enable the spoiler filter. "
                f"Else {self.bot.user.name} will not be able to remove any spoiler messages."
            )
            await ctx.send(msg, ephemeral=True)
            return
        enabled = await self.config.guild(ctx.guild).enabled()
        if enabled:
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Spoiler filter is now disabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("Spoiler filter is now enabled.")

    @nospoiler.command()
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Set the channel where the bot will log the deleted spoiler messages.

        If the channel is not set, the bot will not log the deleted spoiler messages.
        """
        if not ctx.bot_permissions.send_messages or not ctx.bot_permissions.embed_links:
            msg = (
                f"{self.bot.user.name} does not have permission to `send_messages` or `embed_links` to send log messages.\n"
                "It need this permission before you can set the log channel. "
                f"Else {self.bot.user.name} will not be able to send any log messages."
            )
            await ctx.send(msg)
            return
        if channel is None:
            await self.config.guild(ctx.guild).log_channel.set(None)
            await ctx.send("Log channel has been reset.")
        else:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel has been set to {channel.mention}.")

    @nospoiler.command(aliases=["view", "views"])
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context) -> None:
        """Show the settings."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        log_channel = config["log_channel"]
        embed = discord.Embed(
            title="Spoiler Filter Settings",
            description=f"Spoiler filter is currently **{'enabled' if enabled else 'disabled'}**\nLog Channel: {log_channel}.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @nospoiler.command()
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
