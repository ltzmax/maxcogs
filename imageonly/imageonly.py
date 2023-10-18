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
import re
from logging import LoggerAdapter
from typing import Any, Final

import discord
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.views import ConfirmView

log: RedTraceLogger = getLogger("red.maxcogs.imageonly")

URL_REGEX = re.compile(
    r"(http[s]?:\/\/[^\"\']*\.(?:png|jpg|jpeg|png|svg|webp|mov|webm))"
)


class ImageOnly(commands.Cog):
    """Only allow images in a channel."""

    __version__: Final[str] = "1.5.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/imageonly"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=78631113035100160)
        default_guild = {
            "channels": None,
            "enabled": False,
            "message_toggle": False,
            "message": "You can only send images in this channel.",
            "embed": False,
            "log_channel": None,
            "timeout": 10,
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

    async def log_channel_embed(self, guild: discord.Guild, message: discord.Message):
        """Send an embed to the log channel."""
        log_channel = await self.config.guild(guild).log_channel()
        if not log_channel:
            return
        log_channel = guild.get_channel(log_channel)
        if not log_channel:
            return
        if (
            not log_channel.permissions_for(guild.me).send_messages
            or not log_channel.permissions_for(guild.me).embed_links
        ):
            self.log.info(
                "I don't have permissions to send messages or embeds in the log channel. Disabling log channel."
            )
            await self.config.guild(guild).log_channel.set(None)
            return
        embed = discord.Embed(
            title="Message Deleted",
            description=f"{message.author.mention} sent a message that wasn't attachement!\n**Message**:\n{message.content}",
            color=await self.bot.get_embed_color(log_channel),
        )
        embed.set_author(
            name=f"{message.author} ({message.author.id})",
            icon_url=message.author.avatar.url,
        )
        embed.add_field(
            name="Channel:",
            value=f"{message.channel.mention} ({message.channel.id})",
            inline=False,
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Check if the message is an image."""
        if not message.guild:
            return
        if message.author.bot:
            return
        if not message.guild:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        channels = await self.config.guild(message.guild).channels()
        if channels is not None:
            if message.channel.id not in channels:
                return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        timeout = await self.config.guild(message.guild).timeout()

        if message.attachments or URL_REGEX.search(message.content):
            return
        if await self.config.guild(message.guild).message_toggle():
            if not message.channel.permissions_for(message.guild.me).send_messages:
                self.log.info(
                    "I don't have permissions to send messages in the channel. Disabling message."
                )
                await self.config.guild(message.guild).message_toggle.set(False)
            if await self.config.guild(message.guild).embed():
                if not message.channel.permissions_for(message.guild.me).embed_links:
                    self.log.info(
                        "I don't have permissions to send embeds in the channel. Disabling embeds."
                    )
                    await self.config.guild(message.guild).embed.set(False)
                embed = discord.Embed(
                    title="Only images allowed.",
                    description=await self.config.guild(message.guild).message(),
                    color=await self.bot.get_embed_color(message.channel),
                )
                await message.channel.send(
                    f"{message.author.mention}", embed=embed, delete_after=timeout
                )
            else:
                await message.channel.send(
                    f"{message.author.mention} {await self.config.guild(message.guild).message()}",
                    delete_after=timeout,
                )
        await message.delete()
        await self.log_channel_embed(message.guild, message)

    # Cause some people actually managed to post something without image / image link on edit.
    # So we have to check edits as well.
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Check if the message is an image."""
        if not before.guild:
            return
        if before.author.bot:
            return
        if not before.guild:
            return
        if not await self.config.guild(before.guild).enabled():
            return
        channels = await self.config.guild(before.guild).channels()
        if channels is not None:
            if before.channel.id not in channels:
                return
        if await self.bot.cog_disabled_in_guild(self, before.guild):
            return
        if await self.bot.is_automod_immune(before.author):
            return
        if before.attachments or URL_REGEX.search(before.content):
            return

        timeout = await self.config.guild(before.guild).timeout()

        if await self.config.guild(before.guild).message_toggle():
            if not before.channel.permissions_for(before.guild.me).send_messages:
                self.log.info(
                    "I don't have permissions to send messages in the channel. Disabling message."
                )
                await self.config.guild(before.guild).message_toggle.set(False)
            if await self.config.guild(before.guild).embed():
                if not before.channel.permissions_for(before.guild.me).embed_links:
                    self.log.info(
                        "I don't have permissions to send embeds in the channel. Disabling embeds."
                    )
                    await self.config.guild(before.guild).embed.set(False)
                embed = discord.Embed(
                    title="Only images allowed.",
                    description=await self.config.guild(before.guild).message(),
                    color=await self.bot.get_embed_color(before.channel),
                )
                await before.channel.send(
                    f"{before.author.mention}", embed=embed, delete_after=timeout
                )
            else:
                await before.channel.send(
                    f"{before.author.mention} {await self.config.guild(before.guild).message()}",
                    delete_after=timeout,
                )
        await before.delete()
        await self.log_channel_embed(before.guild, before)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def imageonly(self, ctx: commands.Context):
        """Image only settings."""

    @imageonly.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle image only on or off.

        It's disabled by default.
        """
        if await self.config.guild(ctx.guild).enabled():
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Image only disabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send(
                "Image only enabled.\nUse `{prefix}imageonly channel` to set the channel to allow only images.".format(
                    prefix=ctx.prefix
                )
            )

    @imageonly.command()
    async def channel(
        self,
        ctx: commands.Context,
        channels: commands.Greedy[discord.TextChannel] = None,
    ):
        """Set the channels to allow only images in."""
        if not channels:
            await self.config.guild(ctx.guild).channels.set(None)
            await ctx.send("Channels reset.")
        else:
            channels = [channel.id for channel in channels]
            await self.config.guild(ctx.guild).channels.set(channels)
            await ctx.send(
                "Channels set to {channels}.".format(
                    channels=humanize_list([f"<#{channel}>" for channel in channels])
                )
            )

    @imageonly.command()
    async def logchannel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
    ) -> None:
        """Set the channel to log deleted messages in."""
        if await self.config.guild(ctx.guild).log_channel():
            await self.config.guild(ctx.guild).log_channel.set(None)
            await ctx.send("Log channel reset.")
        else:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(
                "Log channel set to {channel}.".format(channel=channel.mention)
            )

    @imageonly.command()
    async def message(self, ctx: commands.Context, *, message: str = None):
        """Set the message to send when a user sends a non-image."""
        if message is None:
            await self.config.guild(ctx.guild).message.set(
                "You can only send images in this channel."
            )
            await ctx.send("Message reset.")
        else:
            if len(message) > 2000 or len(message) < 1:
                self.log.info("Message must be between 1 and 2000 characters.")
                return await ctx.send("Message must be between 1 and 2000 characters.")
            await self.config.guild(ctx.guild).message.set(message)
            await ctx.send("Message set.")

    @imageonly.command()
    async def msgtoggle(self, ctx: commands.Context):
        """Toggle the message on or off."""
        if await self.config.guild(ctx.guild).message_toggle():
            await self.config.guild(ctx.guild).message_toggle.set(False)
            await ctx.send("Message disabled.")
        else:
            await self.config.guild(ctx.guild).message_toggle.set(True)
            await ctx.send("Message enabled.")

    @imageonly.command()
    async def embed(self, ctx: commands.Context):
        """Toggle the message on or off."""
        if await self.config.guild(ctx.guild).embed():
            await self.config.guild(ctx.guild).embed.set(False)
            await ctx.send("Embed disabled.")
        else:
            await self.config.guild(ctx.guild).embed.set(True)
            await ctx.send("Embed enabled.")

    @imageonly.command()
    async def deleteafter(
        self, ctx: commands.Context, amount: commands.Range[int, 5, 120]
    ):
        """Set the delete after timeout.

        Default timeout is 10 seconds.
        Timeout must be between 5 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(amount)
        await ctx.send(f"Timeout set to {amount} seconds!")

    @imageonly.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """Show image only settings."""
        data = await self.config.guild(ctx.guild).all()
        enabled = data["enabled"]
        channels = data["channels"]
        if channels is not None:
            channels = humanize_list([f"<#{channel}>" for channel in channels])
        else:
            channels = "None"
        log_channel = data["log_channel"]
        if log_channel is not None:
            log_channel = "<#{log_channel}>".format(log_channel=log_channel)
        else:
            log_channel = "None"
        message = data["message"]
        msgtoggle = data["message_toggle"]
        embed = data["embed"]
        timeout = data["timeout"]
        embed = discord.Embed(
            title="Image only settings",
            description="""
            **Enabled:** {enabled}
            **Channel:** {channels}
            **Log channel:** {log_channel}
            **Embed:** {embed}
            **Timeout:** {timeout}
            **Message toggle:** {msgtoggle}
            **Message:** {message}
            """.format(
                enabled=enabled,
                channels=channels,
                log_channel=log_channel,
                embed=embed,
                timeout=timeout,
                msgtoggle=msgtoggle,
                message=message,
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @imageonly.command()
    @commands.bot_has_permissions(embed_links=True)
    async def reset(self, ctx: commands.Context):
        """Reset image only settings."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Are you sure?",
            description="This will reset all settings set for this cog.",
            color=await ctx.embed_color(),
        )
        embed.set_footer(text="This message will time out after 30 seconds.")
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            embed = discord.Embed(
                title="Settings reset.",
                description="All settings for this cog have been reset.",
                color=await ctx.embed_color(),
            )
            await self.config.guild(ctx.guild).clear()
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Cancelled.",
                description="Settings not reset.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @imageonly.command()
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
