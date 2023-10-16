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
from logging import LoggerAdapter
from typing import Any, Dict, Final, Optional, Pattern, Union

import discord
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

SPOILER_REGEX: Pattern[str] = re.compile(r"(?s)\|\|(.+?)\|\|")

log: RedTraceLogger = getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.5.2"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/nospoiler/README.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "log_channel": None,
            "spoiler_warn": False,
            "spoiler_warn_message": "Usage of spoiler is not allowed in this server.",
            "spoiler_warn_message_embed": False,
            "timeout": 10,
        }
        self.config.register_guild(**default_guild)

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
            self.log.info(
                f"Spoiler filter is now disabled because I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            await self.config.guild(guild).log_channel.set(None)
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
                self.log.info(
                    f"Spoiler filter is now disabled because I don't have manage_messages permission."
                )
                await self.config.guild(message.guild).enabled.set(False)
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
            return

        timeout = await self.config.guild(message.guild).timeout()

        if SPOILER_REGEX.search(message.content):
            if await self.config.guild(message.guild).spoiler_warn():
                if await self.config.guild(message.guild).spoiler_warn_message_embed():
                    if not message.channel.permissions_for(
                        message.guild.me
                    ).embed_links:
                        self.log.info(
                            f"Spoiler warning message embed is now disabled because I don't have embed_links permission in {message.channel.mention}."
                        )
                        await self.config.guild(message.guild).spoiler_warn.set(False)
                        return
                    embed = discord.Embed(
                        title="Warning",
                        description=await self.config.guild(
                            message.guild
                        ).spoiler_warn_message(),
                        color=await self.bot.get_embed_color(message.channel),
                    )
                    await message.channel.send(
                        f"{message.author.mention}", embed=embed, delete_after=timeout
                    )
                else:
                    await message.channel.send(
                        f"{message.author.mention} {await self.config.guild(message.guild).spoiler_warn_message()}",
                        delete_after=timeout,
                    )
            await self.log_channel_embed(message.guild, message)
            await message.delete()
            return
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    if await self.config.guild(message.guild).spoiler_warn():
                        if await self.config.guild(
                            message.guild
                        ).spoiler_warn_message_embed():
                            if not message.channel.permissions_for(
                                message.guild.me
                            ).embed_links:
                                self.log.info(
                                    f"Spoiler warning message embed is now disabled because I don't have embed_links permission in {message.channel.mention}."
                                )
                                await self.config.guild(message.guild).spoiler_warn.set(
                                    False
                                )
                                return
                            embed = discord.Embed(
                                title="Warning",
                                description=await self.config.guild(
                                    message.guild
                                ).spoiler_warn_message(),
                                color=await self.bot.get_embed_color(message.channel),
                            )
                            await message.channel.send(
                                f"{message.author.mention}",
                                embed=embed,
                                delete_after=timeout,
                            )
                        else:
                            await message.channel.send(
                                f"{message.author.mention} {await self.config.guild(message.guild).spoiler_warn_message()}",
                                delete_after=timeout,
                            )
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
                self.log.info(
                    f"Spoiler filter is now disabled because I don't have manage_messages permission."
                )
                await self.config.guild(guild).enabled.set(False)
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

        timeout = await self.config.guild(guild).timeout()

        if SPOILER_REGEX.search(message.content):
            if await self.config.guild(guild).spoiler_warn():
                if await self.config.guild(guild).spoiler_warn_message_embed():
                    if not channel.permissions_for(guild.me).embed_links:
                        self.log.info(
                            f"Spoiler warning message embed is now disabled because I don't have embed_links permission in {channel.mention}."
                        )
                        await self.config.guild(guild).spoiler_warn.set(False)
                        return
                    embed = discord.Embed(
                        title="Warning",
                        description=await self.config.guild(
                            guild
                        ).spoiler_warn_message(),
                        color=await self.bot.get_embed_color(channel),
                    )
                    await channel.send(
                        f"{message.author.mention}", embed=embed, delete_after=timeout
                    )
                else:
                    await channel.send(
                        f"{message.author.mention} {await self.config.guild(guild).spoiler_warn_message()}",
                        delete_after=timeout,
                    )
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
            self.log.info(
                "I cannot toggle the spoiler filter because I don't have manage_messages permission."
            )
            return await ctx.send(
                "I don't have manage_messages permission to let you toggle the spoiler filter."
            )
        if await self.config.guild(ctx.guild).enabled():
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Spoiler filter is now disabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("Spoiler filter is now enabled.")

    @nospoiler.command()
    async def deleteafter(
        self, ctx: commands.Context, amount: commands.Range[int, 5, 120]
    ):
        """Set the delete after timeout.

        Default timeout is 10 seconds.
        Timeout must be between 5 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(amount)
        await ctx.send(f"Timeout set to {amount} seconds!")

    @nospoiler.command()
    async def logchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ) -> None:
        """Set the channel where the bot will log the deleted spoiler messages.

        If the channel is not set, the bot will not log the deleted spoiler messages.
        """
        if not ctx.bot_permissions.send_messages or not ctx.bot_permissions.embed_links:
            log.info(
                f"I cannot set the log channel because I don't have send_messages or embed_links permission in {ctx.channel.mention}."
            )
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

    @nospoiler.command()
    async def warn(self, ctx: commands.Context) -> None:
        """Toggle warning message when a user tries to use spoiler."""
        spoiler_warn = await self.config.guild(ctx.guild).spoiler_warn()
        if spoiler_warn:
            await self.config.guild(ctx.guild).spoiler_warn.set(False)
            await ctx.send("Spoiler warning message is now disabled.")
        else:
            await self.config.guild(ctx.guild).spoiler_warn.set(True)
            await ctx.send("Spoiler warning message is now enabled.")

    @nospoiler.command()
    async def warnmessage(self, ctx: commands.Context, *, message: str) -> None:
        """Set the spoiler warning message."""
        if len(message) > 1024 or len(message) < 1:
            return await ctx.send("Message must be between 1 and 1024 characters.")
        await self.config.guild(ctx.guild).spoiler_warn_message.set(message)
        await ctx.send("Spoiler warning message has been set.")

    @nospoiler.command(aliases=["resetwarnmsg", "resetwarn"])
    async def resetwarnmessage(self, ctx: commands.Context) -> None:
        """Reset the spoiler warning message to default."""
        await self.config.guild(ctx.guild).spoiler_warn_message.set(
            "Usage of spoiler is not allowed in this server."
        )
        await ctx.send("Spoiler warning message has been reset.")

    @nospoiler.command()
    async def embed(self, ctx: commands.Context) -> None:
        """Toggle the spoiler warning message embed."""
        if not ctx.bot_permissions.embed_links:
            self.log.info(
                f"I cannot toggle the spoiler warning message embed because I don't have embed_links permission in {ctx.channel.mention}."
            )
            return await ctx.send(
                "I don't have embed_links permission to let you toggle the spoiler warning message embed."
            )
        spoiler_warn_message_embed = await self.config.guild(
            ctx.guild
        ).spoiler_warn_message_embed()
        if spoiler_warn_message_embed:
            await self.config.guild(ctx.guild).spoiler_warn_message_embed.set(False)
            await ctx.send("Spoiler warning message embed is now disabled.")
        else:
            await self.config.guild(ctx.guild).spoiler_warn_message_embed.set(True)
            await ctx.send("Spoiler warning message embed is now enabled.")

    @nospoiler.command(aliases=["view", "views"])
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context) -> None:
        """Show the settings."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        log_channel = config["log_channel"]
        if log_channel is None:
            log_channel = "Not set"
        else:
            log_channel = ctx.guild.get_channel(log_channel).mention

        spoiler_warn = config["spoiler_warn"]
        spoiler_warn_message = config["spoiler_warn_message"]
        spoiler_warn_message_embed = config["spoiler_warn_message_embed"]
        timeout = config["timeout"]
        embed = discord.Embed(
            title="Spoiler Filter Settings",
            description=f"Spoiler filter is currently **{'enabled' if enabled else 'disabled'}**\nLog Channel: {log_channel}.",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="Warning Message:",
            value=f"{'Enabled' if spoiler_warn else 'Disabled'}",
            inline=False,
        )
        embed.add_field(
            name="Warning Message Embed:",
            value=f"{'Enabled' if spoiler_warn_message_embed else 'Disabled'}",
            inline=False,
        )
        embed.add_field(name="Timeout:", value=f"{timeout} seconds", inline=False)
        embed.add_field(
            name="Warning Message Content:",
            value=box(spoiler_warn_message, lang="yaml"),
            inline=False,
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
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)
