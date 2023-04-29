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
    __version__ = "0.1.5"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/nospoiler/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild = {
            "enabled": False,
            "ignored_channels": [],
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx):
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """handle spoiler messages"""
        if message.guild is None:
            return

        data = await self.config.guild(message.guild).all()
        enabled = data["enabled"]
        if not enabled:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        for channel in data["ignored_channels"]:
            if message.channel.id == channel:
                return
        if not message.guild.me.guild_permissions.manage_messages:
            log.info("I don't have permission to manage_messages to remove spoiler.")
            return
        if message.author.bot:
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
        if await self.config.guild(guild).ignored_channels():
            return
        if not guild.me.guild_permissions.manage_messages:
            return
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            # due to some discord issues this can happen causing the message is too old to fetch.
            log.error("There was an error fetching the message.")
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
        """Toggle the spoiler filter on or off.

        Spoiler filter is disabled by default.
        """
        guild = ctx.guild
        if not ctx.bot_permissions.manage_messages:
            msg = (
                f"{self.bot.user.name} does not have permission to `manage_messages` to remove spoiler.\n"
                "It need this permission before you can enable the spoiler filter. "
                f"Else {self.bot.user.name} will not be able to remove any spoiler messages."
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
        """Add or remove ignore a channel from the spoiler filter.

        If a channel is ignored, spoiler messages will not be deleted.
        Note: you cannot ignore a voice chat channel.
        """
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        if not enabled:
            msg = (
                "Spoiler filter is disabled.\n"
                f"Enable it with `{ctx.clean_prefix}nospoiler toggle` "
                "before you can ignore a channel."
            )
            return await ctx.send(msg, ephemeral=True)
        ignored_channels = config["ignored_channels"]
        if channel.id in ignored_channels:
            ignored_channels.remove(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channel.mention} is no longer ignored.")
        else:
            ignored_channels.append(channel.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channel.mention} is now ignored.")

    @nospoiler.command(aliases=["clear"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(2, 120, commands.BucketType.guild)
    async def reset(self, ctx):
        """Reset all settings back to default.

        This will disable the spoiler filter and remove all ignored channels.
        """
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        ignored_channels = config["ignored_channels"]
        # if all settings are already default, return.
        # this is to prevent clearing the config if no settings are set.
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
                title="Spoiler filter settings have been reset.",
                colour=discord.Colour.green(),
            )
            await view.message.edit(embed=embed)
        else:
            embed = discord.Embed(
                title="Alright. I will not reset.",
                colour=discord.Colour.red(),
            )
            await view.message.edit(embed=embed)

    @nospoiler.command(
        aliases=["view", "views", "setting", "showsettings", "showsetting"]
    )
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
        # handle if there are too many ignored channels to show
        # due to embed field limits
        if len(ignored_channels) > 1024:
            ignored_channels = "Too many to show."
        embed = discord.Embed(
            title="Spoiler Filter Settings",
            description="These are the current settings for the spoiler filter.",
        )
        embed.add_field(
            name="Enabled",
            value=enabled,
            inline=False,
        )
        embed.add_field(
            name="Ignored Channels",
            value=ignored_channels,
            inline=False,
        )
        await ctx.send(embed=embed)

    @nospoiler.command(with_app_command=False)
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
