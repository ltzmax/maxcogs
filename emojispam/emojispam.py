import discord
import re
import logging
from typing import Any, Final, Literal
from redbot.core.utils.chat_formatting import box
from redbot.core import commands, Config

log = logging.getLogger("red.maxcogs.emojispam")

EMOJI_REGEX = re.compile("<a?:(\w+):(\d+)>")

class EmojiSpam(commands.Cog):
    """Similar emojispam filter to dyno but without ban, kick and mute."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.1.0"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/emojispam/README.md"


    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "enabled": False,
            "emoji_limit": 5,
            "emoji_limit_msg": "You are sending too many emojis!",
            "emoji_limit_msg_enabled": False,
            "ignored_channels": [],
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
        message: discord.Message
    ):
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
            await self.config.guild(guild).log_channel.set(None)
            log.info(
                "I don't have permissions to send messages or embeds in the log channel. Disabling log channel."
            )
            return
        embed = discord.Embed(
            title="Emoji Spam Filter detected",
            description=f"{message.author.mention} sent too many emojis in {message.channel.mention}!\n**Message**:\n {message.content}",
            color=await self.bot.get_embed_color(log_channel),
        )
        embed.set_footer(text=f"User ID: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.channel.id in await self.config.guild(message.guild).ignored_channels():
            return
        if not await self.config.guild(message.guild).enabled():
            return 
        if EMOJI_REGEX.search(message.content):
            emojis = EMOJI_REGEX.findall(message.content)
            if len(emojis) > await self.config.guild(message.guild).emoji_limit():
                if await self.bot.is_automod_immune(message.author):
                    return
                if await self.config.guild(message.guild).emoji_limit_msg_enabled():
                    if not message.channel.permissions_for(message.guild.me).send_messages:
                        await self.config.guild(message.guild).emoji_limit_msg_enabled.set(False)
                        log.info(
                            f"I don't have permissions to send messages in {message.channel.mention}. Disabling message."
                        )
                    await message.channel.send(
                        f"{message.author.mention} {await self.config.guild(message.guild).emoji_limit_msg()}", delete_after=10
                    )
                await self.log_channel_embed(message.guild, message)
                await message.delete()

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return
        if not after.guild:
            return
        if after.channel.id in await self.config.guild(after.guild).ignored_channels():
            return
        if not await self.config.guild(after.guild).enabled():
            return
        if len(after.content) < await self.config.guild(after.guild).emoji_limit():
            return
        if EMOJI_REGEX.search(after.content):
            emojis = EMOJI_REGEX.findall(after.content)
            if len(emojis) > await self.config.guild(after.guild).emoji_limit():
                if await self.bot.is_automod_immune(after.author):
                    return
                if await self.config.guild(after.guild).emoji_limit_msg_enabled():
                    if not after.channel.permissions_for(after.guild.me).send_messages:
                        await self.config.guild(after.guild).emoji_limit_msg_enabled.set(False)
                        log.info(
                            f"I don't have permissions to send messages in {after.channel.mention}. Disabling message."
                        )
                    await after.channel.send(
                        f"{after.author.mention} {await self.config.guild(after.guild).emoji_limit_msg()}", delete_after=10
                    )
                await self.log_channel_embed(after.guild, after)
                await after.delete()
    
    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def emojispam(self, ctx: commands.Context):
        """Manage the emoji spam filter."""

    @emojispam.command()
    async def toggle(self, ctx: commands.Context, enabled: bool = None):
        """Toggle the emoji spam filter.
        
        If no enabled state is provided, the current state will be toggled.
        """
        if enabled is None:
            enabled = not await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(enabled)
        if enabled:
            await ctx.send("Emoji spam filter enabled!")
        else:
            await ctx.send("Emoji spam filter disabled!")

    @emojispam.command()
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the log channel.
        
        If no channel is provided, the log channel will be disabled.
        """
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
        if limit < 1:
            return await ctx.send("Limit must be greater than 1!")
        if limit > 100:
            return await ctx.send("Limit must be less than 100!")
        await self.config.guild(ctx.guild).emoji_limit.set(limit)
        await ctx.send(f"Emoji limit set to {limit}!")

    @emojispam.command()
    async def msg(self, ctx: commands.Context, *, msg: str):
        """Set the message to send when a user goes over the emoji limit.
        
        Default message is:
        `You are sending too many emojis!`.
        """
        if len(msg) > 1092 or len(msg) < 1:
            return await ctx.send("Message must be between 1 and 1092 characters!")
        await self.config.guild(ctx.guild).emoji_limit_msg.set(msg)
        await ctx.send("Message set!")

    @emojispam.command()
    async def resetmsg(self, ctx: commands.Context):
        """Reset the message to the default message."""
        await self.config.guild(ctx.guild).emoji_limit_msg.set("You are sending too many emojis!")
        await ctx.send("Message reset back to default!")

    @emojispam.command(usage="<enable|disable>")
    async def msgtoggle(self, ctx: commands.Context, add_or_remove: Literal["enable", "disable"]):
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
            async with self.config.guild(ctx.guild).ignored_channels() as ignored_channels:
                ignored_channels.append(channel.id)
            await ctx.send(f"{channel.mention} is now ignored!")

    @emojispam.command()
    async def unignore(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unignore a channel."""
        if not channel:
            channel = ctx.channel
        if channel.id not in await self.config.guild(ctx.guild).ignored_channels():
            await ctx.send("Channel isn't ignored!")
        else:
            async with self.config.guild(ctx.guild).ignored_channels() as ignored_channels:
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
        embed = discord.Embed(
            title="Emoji Spam Filter Settings",
            description=box(
                f"{'Enabled':15}: {enabled}\n{'Emoji Limit':<15}: {emoji_limit}\n{'Message':<15}: {emoji_limit_msg}\n{'Message Enabled':<14}: {emoji_limit_msg_enabled}",
                lang="yaml",
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
        await ctx.send(embed=embed)
