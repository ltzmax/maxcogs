import discord
import re
import logging

from redbot.core import Config, commands, app_commands

SPOILER_REGEX = re.compile(r"\|\|(.+?)\|\|")

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__ = "MAX"
    __version__ = "0.1.0"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/nospoiler/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild = {"enabled": False, "ignored_channels": []}
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx):
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        """handle spoiler messages"""
        member = message.author
        guild = message.guild
        config = await self.config.guild(guild).all()
        if not config["enabled"]:
            return
        if not guild.me.guild_permissions.manage_messages:
            log.info("I don't have permission to manage_messages to remove spoiler.")
            return
        if message.channel.id in config["ignored_channels"]:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if member.bot:
            return
        if await self.bot.is_automod_immune(member):
            return
        if SPOILER_REGEX.search(message.content):
            await message.delete()
            return
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """handle edits"""
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        if not await self.config.guild(guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if not guild.me.guild_permissions.manage_messages:
            log.info("I don't have permission to manage_messages to remove spoiler.")
            return
        channel = guild.get_channel(payload.channel_id)
        if channel.id in await self.config.guild(guild).ignored_channels():
            return
        message = await channel.fetch_message(payload.message_id)
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(payload.cached_message.author):
            return
        if SPOILER_REGEX.search(message.content):
            await message.delete()

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx):
        """Manage the spoiler filter settings."""

    @nospoiler.command()
    async def toggle(self, ctx):
        """Toggle spoiler filter on or off."""
        guild = ctx.guild
        if guild.me.guild_permissions.manage_messages is False:
            return await ctx.send(
                "I don't have permission to `manage_messages` to toggle spoiler filter.\ni need this permission to be able to remove spoiler messages.",
                ephemeral=True,
            )
        if await self.config.guild(ctx.guild).enabled():
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Spoiler filter disabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("Spoiler filter enabled.")

    @nospoiler.command()
    @app_commands.describe(channel="The channel to ignore or remove from ignore list.")
    async def ignorechannel(self, ctx, channel: discord.TextChannel):
        """Add or remove ignore a channel from the spoiler filter."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        if not enabled:
            return await ctx.send(
                "Spoiler filter is disabled. Enable it with `[p]nospoiler toggle`.",
                ephemeral=True,
            )
        ignored_channels = config["ignored_channels"]
        if channel.id in ignored_channels:
            await self.config.guild(ctx.guild).ignored_channels.set(
                [c for c in ignored_channels if c != channel.id]
            )
            await ctx.send(f"Removed <#{channel.id}> from ignore list.")
        else:
            await self.config.guild(ctx.guild).ignored_channels.set(
                ignored_channels + [channel.id]
            )
            await ctx.send(f"Ignoring <#{channel.id}>.")

    # todo: add confirmation.
    @nospoiler.command(aliases=["reset"])
    async def clear(self, ctx):
        """Reset all settings back to default."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Settings reset to default.")

    @nospoiler.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx):
        """Show the settings."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        ignored_channels = config["ignored_channels"]
        if ignored_channels:
            ignored_channels = ", ".join(
                f"<#{channel}>" for channel in ignored_channels
            )
        else:
            ignored_channels = "None"
        embed = discord.Embed(
            title="Spoiler Filter Settings",
            description=f"Enabled: {enabled}\nIgnored Channels: {ignored_channels}",
        )
        await ctx.send(embed=embed)
