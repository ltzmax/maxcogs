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
from typing import Optional, Any
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box

HYPERLINK_REGEX = re.compile("^\[.*\]\(https?://.*\)$")

log = logging.getLogger("red.maxcogs.hyperlink")

# This is just to avoid people trying to post hyperlinks in channels with scam or other malicious content,
# This helps prevent that, but it's not foolproof and should not be relied on as a primary method of protection.
# you should still have a good moderation team and a good moderation bot to help prevent these things from happening in the first place,
# but this is just a simple cog to help prevent some of the more common scams and malicious links from being posted in big servers with a lot of people.
# Scam links has become a common issue in big servers and some small servers, They've started to use URL shortners and hyperlinking text to make it look less suspicious.


class Hyperlink(commands.Cog):
    """Delete messages with hyperlinks in them"""

    __author__ = "ltzmax"
    __version__ = "0.0.1"
    __docs__ = "https://maxcogs.gitbook.io/maxcogs/cogs/hyperlink"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "delete_hyperlinks": False,
            "log_channel": None,
            "timeout": 10,
            "delete_message": "Your message was deleted because it contained a hyperlink.",
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def log_hyperlink(self, guild: discord.Guild, message: discord.Message):
        log_channel = await self.config.guild(guild).log_channel()
        if log_channel is None:
            return
        channel = guild.get_channel(log_channel)
        if channel is None:
            return
        if (
            not channel.permissions_for(guild.me).send_messages
            or not channel.permissions_for(guild.me).embed_links
        ):
            log.error(
                f"Unable to send messages in {channel.mention} in {guild.name} ({guild.id}) due to missing permissions."
            )
            return
        embed = discord.Embed(
            title="Hyperlink Deleted",
            description=f"Message sent by {message.author.mention} was deleted because it contained a hyperlink.\n{box(message.content, lang='yaml')}",
            color=discord.Color.red(),
        )
        embed.add_field(name="Channel:", value=message.channel.mention)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not await self.config.guild(message.guild).delete_hyperlinks():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if HYPERLINK_REGEX.search(message.content):
            if await self.config.guild(message.guild).log_channel():
                await self.log_hyperlink(message.guild, message)
            if await self.config.guild(message.guild).delete_message():
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    log.error(
                        f"Unable to send message in {message.channel.mention} in {message.guild.name} ({message.guild.id}) due to missing permissions."
                    )
                    return
                await message.channel.send(
                    f"{message.author.mention}, {await self.config.guild(message.guild).delete_message()}",
                    delete_after=await self.config.guild(message.guild).timeout(),
                )
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                log.error(
                    f"Unable to delete message in {message.channel.mention} in {message.guild.name} ({message.guild.id}) due to missing permissions."
                )
                return
            await message.delete()

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if not await self.config.guild(after.guild).delete_hyperlinks():
            return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return
        if after.author.bot:
            return
        if await self.bot.is_automod_immune(after.author):
            return
        if HYPERLINK_REGEX.search(after.content):
            if await self.config.guild(after.guild).log_channel():
                await self.log_hyperlink(after.guild, after)
            if await self.config.guild(after.guild).delete_message():
                if not after.channel.permissions_for(after.guild.me).send_messages:
                    log.info(
                        f"Unable to send message in {after.channel.mention} in {after.guild.name} ({after.guild.id}) due to missing permissions."
                    )
                    return
                await after.channel.send(
                    f"{after.author.mention}, {await self.config.guild(after.guild).delete_message()}",
                    delete_after=await self.config.guild(after.guild).timeout(),
                )
            if not after.channel.permissions_for(after.guild.me).manage_messages:
                log.info(
                    f"Unable to delete message in {after.channel.mention} in {after.guild.name} ({after.guild.id}) due to missing permissions."
                )
                return
            await after.delete()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def hyperlink(self, ctx):
        """Manage hyperlink settings"""

    @hyperlink.command()
    async def toggle(self, ctx: commands.Context, *, toggle: bool):
        """Toggle deleting hyperlinks"""
        await self.config.guild(ctx.guild).delete_hyperlinks.set(toggle)
        await ctx.send(
            f"Hyperlink deletion is now {'enabled' if toggle else 'disabled'}."
        )

    @hyperlink.command()
    async def logchannel(
        self, ctx: commands.Context, *, channel: Optional[discord.TextChannel]
    ):
        """Set the channel to log hyperlinks"""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel.set(None)
            return await ctx.send("Hyperlink logging channel cleared.")
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Hyperlink logging channel set to {channel.mention}.")

    @hyperlink.command()
    async def message(self, ctx: commands.Context, *, message: str):
        """Set the message to send when a hyperlink is deleted"""
        if len(message) < 2 or len(message) > 2000:
            return await ctx.send("Message must be between 2 and 2000 characters.")
        await self.config.guild(ctx.guild).delete_message.set(message)
        await ctx.send("Hyperlink delete message set to:\n" + message)

    @hyperlink.command()
    async def timeout(
        self, ctx: commands.Context, *, timeout: commands.Range[int, 10, 120]
    ):
        """Set the timeout for the message to be deleted"""
        await self.config.guild(ctx.guild).timeout.set(timeout)
        await ctx.send(f"Hyperlink delete timeout set to {timeout} seconds.")

    @hyperlink.command()
    async def settings(self, ctx: commands.Context):
        """Show the current settings for hyperlinks"""
        settings = await self.config.guild(ctx.guild).all()
        settings["log_channel"] = (
            ctx.guild.get_channel(settings["log_channel"]) or "Not set"
        )
        await ctx.send(
            f"## Hyperlink settings:\n"
            f"> **Toggle**: {settings['delete_hyperlinks']}\n"
            f"> **Log Channel**: {settings['log_channel']}\n"
            f"> **Timeout**: {settings['timeout']} seconds\n"
            f"> **Delete Message**: {settings['delete_message']}"
        )

    @commands.bot_has_permissions(embed_links=True)
    @hyperlink.command()
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
