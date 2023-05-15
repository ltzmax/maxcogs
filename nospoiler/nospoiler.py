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

from redbot.core.utils.chat_formatting import box
from redbot.core import Config, commands, app_commands

SPOILER_REGEX = re.compile(r"(?s)\|\|(.+?)\|\|")

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__ = "MAX"
    __version__ = "0.2.23"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/nospoiler/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild = {
            "enabled": False,
            "message_toggle": False,
            "message": [],
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
        if not await self.config.guild(message.guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if not message.guild.me.guild_permissions.manage_messages:
            return
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if SPOILER_REGEX.search(message.content):
            if await self.config.guild(message.guild).message_toggle():
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    await self.config.guild(message.guild).message_toggle.set(False)
                    log.info(
                        "Missing permissions to send messages so i disabled it for you."
                    )
                await message.channel.send(
                    f"{message.author.mention} {await self.config.guild(message.guild).message()}",
                    delete_after=10,
                )
                await message.delete()
            else:
                await message.delete()
                return
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    if await self.config.guild(message.guild).message_toggle():
                        if not message.channel.permissions_for(
                            message.guild.me
                        ).send_messages:
                            await self.config.guild(message.guild).message_toggle.set(
                                False
                            )
                            log.info(
                                "Missing permissions to send messages so i disabled it for you."
                            )
                        await message.channel.send(
                            f"{message.author.mention} {await self.config.guild(message.guild).message()}",
                            delete_after=10,
                        )
                        await message.delete()
                    else:
                        await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """handle edits"""
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        if not await self.config.guild(guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if not guild.me.guild_permissions.manage_messages:
            return
        if await self.bot.is_automod_immune(guild.me):
            return
        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
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

    @nospoiler.command(aliases=["togglemsg"])
    async def togglemessage(self, ctx):
        """Enable or disable the message to send when a user sends a spoiler message.

        If the message is disabled, the bot will delete the spoiler message without sending a message.
        """
        guild = ctx.guild
        message_toggle = await self.config.guild(guild).message_toggle()
        if message_toggle:
            await self.config.guild(guild).message_toggle.set(False)
            await ctx.send("Message is now disabled.")
        else:
            await self.config.guild(guild).message_toggle.set(True)
            await ctx.send("Message is now enabled.")

    @nospoiler.command(aliases=["msg"])
    @app_commands.describe(
        message="Set the message to send when a user sends a spoiler message."
    )
    async def message(self, ctx, *, message: str = None):
        """Set the message to send when a user sends a spoiler message.

        If no message is provided, the default message will be sent.
        If you want to disable the message, use `[p]nospoiler set togglemessage`.
        """
        if message is not None and len(message) > 1024:
            return await ctx.send("Message cannot be longer than 1024 characters.")
        if message is None:
            await self.config.guild(ctx.guild).message.set(
                "You cannot send spoiler in this server."
            )
            await ctx.send("The message has been reset to default.")
        else:
            await self.config.guild(ctx.guild).message.set(message)
            await ctx.send("The message has been set.")

    @nospoiler.command(aliases=["view", "views"])
    async def settings(self, ctx):
        """Show the settings."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        message = config["message"]
        togglemessage = config["message_toggle"]
        if message is None:
            message = "Default Message"
        else:
            message = f"{message}"
        if togglemessage:
            message_toggle = "Enabled"
        else:
            message_toggle = "Disabled"

        await ctx.send(
            f"`{'Enabled':<16}`: {enabled}\n`{'Toggle message':<16}`: {message_toggle}\n`{'Message':<16}`: {message}"
        )

    @nospoiler.command(with_app_command=False)
    async def version(self, ctx: commands.Context):
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        await ctx.send(
            box(f"{'Author':<10}: {author}\n{'Version':<10}: {version}", lang="yaml")
        )
