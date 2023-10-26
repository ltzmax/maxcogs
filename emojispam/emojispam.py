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
from typing import Any, Final, Literal

import discord
import regex
from redbot.core.bot import Red
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

log: RedTraceLogger = getLogger("red.maxcogs.emojispam")

EMOJI_REGEX = regex.compile(r"(?<emoji>[\p{Emoji_Presentation}]|<a?:\w+:(\d+)>|<:)")


def count_emojis(message):
    """Counts the total number of emojis in a message."""
    emoji_count = 0
    for emoji in EMOJI_REGEX.findall(message.content):
        emoji_count += 1
    return emoji_count


class EmojiSpam(commands.Cog):
    """Similar emojispam filter to dyno but without ban, kick and mute."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.5.7"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/emojispam"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled": False,
            "emoji_limit": 5,
            "emoji_limit_msg": "Please don't spam emojis. You are sending too many.",
            "emoji_limit_msg_enabled": False,
            "ignored_channels": [],
            "log_channel": None,
            "use_embed": False,
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
            title="EmojiSpam Deleted",
            description=f"{message.author.mention} sent too many emojis!\n**Message**:\n{message.content}",
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
        if message.author.bot:
            return
        if not message.guild:
            return
        if (
            message.channel.id
            in await self.config.guild(message.guild).ignored_channels()
        ):
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if not message.guild.me.guild_permissions.manage_messages:
            if await self.config.guild(message.guild).enabled:
                await self.config.guild(message.guild).enabled.set(False)
                self.log.info(
                    f"I don't have the ``manage_messages`` permission to let you enable emojispam filter in {message.guild.name}. Disabling filter."
                )
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        timeout = await self.config.guild(message.guild).timeout()

        emoji_count = count_emojis(message)

        if emoji_count > await self.config.guild(message.guild).emoji_limit():
            if await self.bot.is_automod_immune(message.author):
                return
            if await self.config.guild(message.guild).emoji_limit_msg_enabled():
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    self.log.info(
                        f"I don't have permissions to send messages in {message.channel.mention}. Disabling message."
                    )
                    await self.config.guild(message.guild).emoji_limit_msg_enabled.set(
                        False
                    )
                if await self.config.guild(message.guild).use_embed():
                    if not message.channel.permissions_for(
                        message.guild.me
                    ).embed_links:
                        self.log.info(
                            f"I don't have permissions to send embeds in {message.channel.mention}. Disabling embeds."
                        )
                        await self.config.guild(message.guild).use_embed.set(False)
                    embed = discord.Embed(
                        title="Warning",
                        description=await self.config.guild(
                            message.guild
                        ).emoji_limit_msg(),
                        color=await self.bot.get_embed_color(message.channel),
                    )
                    await message.channel.send(
                        f"{message.author.mention}", embed=embed, delete_after=timeout
                    )
                else:
                    await message.channel.send(
                        f"{message.author.mention} {await self.config.guild(message.guild).emoji_limit_msg()}",
                        delete_after=timeout,
                    )
            await self.log_channel_embed(message.guild, message)
            await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        if not await self.config.guild(guild).enabled():
            return
        if not guild.me.guild_permissions.manage_messages:
            if await self.config.guild(guild).enabled:
                self.log.info(
                    f"I don't have the ``manage_messages`` permission to let you enable emojispam filter in {guild.name}. Disabling filter."
                )
                await self.config.guild(guild).enabled.set(False)
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if payload.channel_id in await self.config.guild(guild).ignored_channels():
            return
        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return
        if not channel.permissions_for(guild.me).read_message_history:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        if message.author.bot:
            return

        timeout = await self.config.guild(guild).timeout()

        emoji_count = count_emojis(message)

        if emoji_count > await self.config.guild(guild).emoji_limit():
            if await self.bot.is_automod_immune(message.author):
                return
            if await self.config.guild(guild).emoji_limit_msg_enabled():
                if not channel.permissions_for(guild.me).send_messages:
                    self.log.info(
                        f"I don't have permissions to send messages in {channel.mention}. Disabling message."
                    )
                    await self.config.guild(guild).emoji_limit_msg_enabled.set(False)
                if await self.config.guild(guild).use_embed():
                    if not channel.permissions_for(guild.me).embed_links:
                        await self.config.guild(guild).use_embed.set(False)
                        self.log.info(
                            f"I don't have permissions to send embeds in {channel.mention}. Disabling embeds."
                        )
                    embed = discord.Embed(
                        title="Warning",
                        description=await self.config.guild(guild).emoji_limit_msg(),
                        color=await self.bot.get_embed_color(channel),
                    )
                    await channel.send(
                        f"{message.author.mention}", embed=embed, delete_after=timeout
                    )
                else:
                    await channel.send(
                        f"{message.author.mention} {await self.config.guild(guild).emoji_limit_msg()}",
                        delete_after=timeout,
                    )
            await self.log_channel_embed(guild, message)
            await message.delete()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def emojispam(self, ctx: commands.Context):
        """Manage the emoji spam filter."""

    @emojispam.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle the emoji spam filter.

        If no enabled state is provided, the current state will be toggled.
        """
        if not ctx.bot_permissions.manage_messages:
            self.log.info(
                f"I don't have the ``manage_messages`` permission to let you enable emojispam filter in {ctx.guild.name}. Disabling filter."
            )
            return await ctx.send(
                "I don't have the ``manage_messages`` permission to let you enable emojispam filter in this server."
            )
        await self.config.guild(ctx.guild).enabled.set(
            not await self.config.guild(ctx.guild).enabled()
        )
        await ctx.send(
            f"Emoji spam filter is now {'enabled' if await self.config.guild(ctx.guild).enabled() else 'disabled'}!"
        )

    @emojispam.command()
    async def embed(self, ctx: commands.Context, toggle: bool = None):
        """Toggle the use of embeds for the message.

        If no enabled state is provided, the current state will be toggled.
        """
        if not ctx.bot_permissions.embed_links:
            self.log.info(
                f"I don't have the ``embed_links`` permission to let you enable embeds for the message in {ctx.guild.name}. Disabling embeds."
            )
            return await ctx.send(
                "I don't have the ``embed_links`` permission to let you enable embeds for the message in this server."
            )
        await self.config.guild(ctx.guild).use_embed.set(toggle)
        if toggle:
            await ctx.send("Embeds enabled!")
        else:
            await ctx.send("Embeds disabled!")

    @emojispam.command()
    async def logchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the log channel.

        If no channel is provided, the log channel will be disabled.
        """
        if (
            channel
            and not channel.permissions_for(ctx.me).send_messages
            or not channel.permissions_for(ctx.me).embed_links
        ):
            self.log.info(
                f"I don't have the ``send_messages`` or ``embed_links`` permission to let you set the log channel in {ctx.guild.name}. Disabling log channel."
            )
            return await ctx.send(
                "I don't have the ``send_messages`` or ``embed_links`` permission to let you set the log channel there."
            )
        if not channel:
            await self.config.guild(ctx.guild).log_channel.set(None)
            await ctx.send("Log channel disabled!")
        else:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel set to {channel.mention}!")

    @emojispam.command()
    async def limit(self, ctx: commands.Context, limit: int):
        """Set the emoji limit.

        Default limit is 5.
        Limit must be between 1 and 100.

        If limit is set to 4, a user can send 4 emojis, but not 5.
        """
        if limit < 1 or limit > 100:
            return await ctx.send("Limit must be between 1 and 100!")
            self.log.info(f"Limit must be between 1 and 100 in {ctx.guild.name}.")
        await self.config.guild(ctx.guild).emoji_limit.set(limit)
        await ctx.send(f"Emoji limit set to {limit}!")

    @emojispam.command(aliases=["timeout"])
    async def deleteafter(
        self, ctx: commands.Context, amount: commands.Range[int, 5, 120]
    ):
        """Set the delete after timeout.

        Default timeout is 10 seconds.
        Timeout must be between 5 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(amount)
        await ctx.send(f"Timeout set to {amount} seconds!")

    @emojispam.command()
    async def msg(self, ctx: commands.Context, *, msg: str):
        """Set the message to send when a user goes over the emoji limit.

        Default message is:
        `Please don't spam emojis. You are sending too many.`.
        """
        if len(msg) > 1092 or len(msg) < 1:
            self.log.info(
                f"Message must be between 1 and 1092 characters in {ctx.guild.name}."
            )
            return await ctx.send("Message must be between 1 and 1092 characters!")
        await self.config.guild(ctx.guild).emoji_limit_msg.set(msg)
        await ctx.send("Message set!")

    @emojispam.command()
    async def resetmsg(self, ctx: commands.Context):
        """Reset the message to the default message."""
        await self.config.guild(ctx.guild).emoji_limit_msg.set(
            "Please don't spam emojis. You are sending too many."
        )
        await ctx.send("Message reset back to default!")

    @emojispam.command(usage="<enable|disable>")
    async def msgtoggle(
        self, ctx: commands.Context, add_or_remove: Literal["enable", "disable"]
    ):
        """Enable or disable the message.

        If the message is disabled, no message will be sent when a user goes over the emoji limit.

        Default state is disabled.

        **Valid options:**
        - enable
        - disable

        **Example:**
        - `[p]emojispam msgtoggle enable`
          - This will enable the message and send it when a user goes over the emoji limit.
        - `[p]emojispam msgtoggle disable`
          - This will disable the message and will not send it when a user goes over the emoji limit.
        """
        if add_or_remove == "enable":
            await self.config.guild(ctx.guild).emoji_limit_msg_enabled.set(True)
            await ctx.send("Message enabled!")
        elif add_or_remove == "disable":
            await self.config.guild(ctx.guild).emoji_limit_msg_enabled.set(False)
            await ctx.send("Message disabled!")
        else:
            await ctx.send("Invalid option!")

    @emojispam.command()
    async def ignore(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Ignore a channel.

        When a channel is ignored, the emoji spam filter will not be applied to that channel.
        """
        if not channel:
            channel = ctx.channel
        if channel.id in await self.config.guild(ctx.guild).ignored_channels():
            await ctx.send("Channel already ignored!")
        else:
            async with self.config.guild(
                ctx.guild
            ).ignored_channels() as ignored_channels:
                ignored_channels.append(channel.id)
            await ctx.send(f"{channel.mention} is now ignored!")

    @emojispam.command()
    async def unignore(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Unignore a channel."""
        if not channel:
            channel = ctx.channel
        if channel.id not in await self.config.guild(ctx.guild).ignored_channels():
            await ctx.send("Channel isn't ignored!")
        else:
            async with self.config.guild(
                ctx.guild
            ).ignored_channels() as ignored_channels:
                ignored_channels.remove(channel.id)
            await ctx.send(f"{channel.mention} is no longer ignored!")

    @emojispam.command()
    async def listignored(self, ctx: commands.Context):
        """List ignored channels."""
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()
        if not ignored_channels:
            await ctx.send("No channels are ignored!")
        else:
            await ctx.send(
                f"Currently ignored channels: {', '.join([ctx.guild.get_channel(c).mention for c in ignored_channels])}"
            )

    @emojispam.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """Show the current settings."""
        all = await self.config.guild(ctx.guild).all()
        enabled = all["enabled"]
        emoji_limit = all["emoji_limit"]
        emoji_limit_msg = all["emoji_limit_msg"]
        emoji_limit_msg_enabled = all["emoji_limit_msg_enabled"]
        embed = all["use_embed"]
        timeout = all["timeout"]
        log_channel = all["log_channel"]
        if log_channel:
            log_channel = f"<#{log_channel}>"
        else:
            log_channel = "None"
        ignored_channels = all["ignored_channels"]
        if not ignored_channels:
            ignored_channels = "None"
        else:
            ignored_channels = ", ".join(
                [
                    ctx.guild.get_channel(c).mention
                    for c in await self.config.guild(ctx.guild).ignored_channels()
                ]
            )

        embed = discord.Embed(
            title="Emoji Spam Filter Settings",
            description="""
            **Enabled:** {enabled}
            **Emoji Limit:** {emoji_limit}
            **Message Enabled:** {emoji_limit_msg_enabled}
            **Embed:** {embed}
            **Timeout:** {timeout}
            **Log Channel:** {log_channel}
            **Ignored Channels:** {ignored_channels}
            **Message:** {emoji_limit_msg}
            """.format(
                enabled=enabled,
                emoji_limit=emoji_limit,
                emoji_limit_msg_enabled=emoji_limit_msg_enabled,
                embed=embed,
                timeout=timeout,
                log_channel=log_channel,
                ignored_channels=ignored_channels,
                emoji_limit_msg=emoji_limit_msg,
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @emojispam.command()
    @commands.bot_has_permissions(embed_links=True)
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

    @emojispam.command()
    @commands.bot_has_permissions(embed_links=True)
    async def reset(self, ctx: commands.Context):
        """Reset all settings back to default."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Are you sure you want to do this?",
            description="This will reset all settings for this cog and cannot be undone. You will have to redo everything.",
            color=await ctx.embed_color(),
        )
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            embed = discord.Embed(
                title="Settings Reset",
                description="All settings for this cog have been reset.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Settings Reset Cancelled",
                description="Cancelled resetting settings for this cog.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
