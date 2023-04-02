import discord
import re
import logging
from typing import Union

from redbot.core import Config, commands, app_commands
from .views import ResetSpoilerFilterConfirm

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
        channel = message.channel
        guild = message.guild
        if not guild:
            return
        if message.author.bot:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if not channel.permissions_for(guild.me).manage_messages:
            log.info(
                f"I dont have permission to manage messages in {message.guild.name} in channel {message.channel.name}."
            )
            return
        if await self.config.guild(message.guild).ignored_channels():
            return
        if await self.bot.is_automod_immune(message.author):
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
        if not channel.permissions_for(guild).manage_messages:
            log.info(
                f"I dont have permission to manage messages in {message.guild.name} in channel {message.channel.name}."
            )
            return
        if await self.config.guild(guild).ignored_channels():
            return
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)
        if not message:
            return
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
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
        """Toggle the spoiler filter on or off."""
        guild = ctx.guild
        if not ctx.bot_permissions.manage_messages:
            msg = (
                "I don't have permission to manage_messages to remove spoiler.\n"
                "I need this permission before i can enable the spoiler filter."
            )
            return await ctx.send(msg, ephemeral=True)
        enabled = await self.config.guild(guild).enabled()
        if enabled:
            await self.config.guild(guild).enabled.set(False)
            await ctx.send("Spoiler filter is now disabled.")
        else:
            await self.config.guild(guild).enabled.set(True)
            await ctx.send("Spoiler filter is now enabled.")

    @nospoiler.command()
    @app_commands.describe(channel="The channel to ignore or remove from ignore list.")
    async def ignorechannel(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.Thread, discord.ForumChannel],
    ):
        """Add or remove ignore a channel from the spoiler filter."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        if not enabled:
            return await ctx.send(
                f"Spoiler filter is disabled. Enable it with `{ctx.clean_prefix}nospoiler toggle` before you can ignore a channel.",
                ephemeral=True,
            )
        ignored_channels = config["ignored_channels"]
        if channel.id in ignored_channels:
            ignored_channels.remove(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channel.mention} is no longer ignored.")
        else:
            ignored_channels.append(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channel.mention} is now ignored.")

    @nospoiler.command(aliases=["reset"])
    @commands.bot_has_permissions(embed_links=True)
    async def clear(self, ctx):
        """Reset all settings back to default."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        ignored_channels = config["ignored_channels"]
        if not enabled and not ignored_channels:
            embed = discord.Embed(
                title="There are no settings to reset.",
                colour=discord.Colour.red(),
            )
            return await ctx.send(embed=embed, ephemeral=True)
        embed = discord.Embed(
            title="Are you sure you want to reset?",
            description="This will reset all settings back to default.",
            colour=discord.Colour.red(),
        )
        view = ResetSpoilerFilterConfirm(ctx)
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.value is True:
            await self.config.guild(ctx.guild).clear()
            embed = discord.Embed(
                title="Settings reset.",
                colour=discord.Colour.green(),
            )
            await view.message.edit(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title="Reset cancelled.",
                colour=discord.Colour.red(),
            )
            await view.message.edit(embed=embed, view=None)

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

    @nospoiler.command()
    async def version(self, ctx: commands.Context):
        """Shows the version of the cog."""
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Cog Version:",
                description=f"Author: {self.__author__}\nVersion: {self.__version__}",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(
                f"Cog Version: {self.__version__}\nAuthor: {self.__author__}"
            )
