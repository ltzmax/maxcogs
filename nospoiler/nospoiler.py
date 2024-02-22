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
import logging
import re

from typing import Optional, List, Any
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import humanize_list, box

NOSPOILER_REGEX = re.compile(r"(?s)\|\|(.+?)\|\|")

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """Delete messages with spoilers in them."""

    __author__ = "MAX"
    __version__ = "2.0.0"
    __docs__ = "https://maxcogs.gitbook.io/maxcogs/cogs/nospoiler"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "toggle": False,
            "log_channel": None,
            "warnmsg": False,
            "use_embed": False,
            "timeout": 10,
            "default_message": "This message was deleted because it contained a spoiler.",
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
        attachments: List[discord.Attachment] = None,
    ) -> None:
        log_channel = guild.get_channel(await self.config.guild(guild).log_channel())
        if log_channel is None:
            return

        if (
            not log_channel.permissions_for(guild.me).embed_links
            or not log_channel.permissions_for(guild.me).send_messages
        ):
            log.info("No permissions to send messages or embeds in log channel.")
            return

        embed = discord.Embed(
            title="Message Deleted",
            description=f"Message sent by {message.author.mention} in {message.channel.mention} was deleted.\n{box(message.content, lang='yaml') if message.content else ''}",
            color=discord.Color.red(),
        )
        attachments = (
            message.attachments
        )  # Get the list of attachments from the message
        if attachments:
            for i, attachment in enumerate(attachments):
                embed.add_field(
                    name=f"Attachment {i+1}:", value=attachment.url, inline=False
                )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if not await self.config.guild(message.guild).toggle():
            return
        if not message.channel.permissions_for(message.guild.me).manage_messages:
            log.info(
                "No permissions to manage messages in {message.guild.name} ({channel.name})."
            )
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if NOSPOILER_REGEX.search(message.content):
            if await self.config.guild(message.guild).warnmsg():
                if await self.config.guild(message.guild).use_embed():
                    if not message.channel.permissions_for(message.author).embed_links:
                        log.info(
                            "No permissions to embed links in {message.guild.name} ({channel.name})."
                        )
                        return
                    embed = discord.Embed(
                        title="Spoiler Detected",
                        description=f"{message.author.mention}, {await self.config.guild(message.guild).default_message()}",
                        color=discord.Color.red(),
                    )
                    await message.channel.send(
                        embed=embed,
                        delete_after=await self.config.guild(message.guild).timeout(),
                    )
                else:
                    if not message.channel.permissions_for(
                        message.author
                    ).send_messages:
                        log.info(
                            "No permissions to send messages in {message.guild.name} ({channel.name})."
                        )
                        return
                    await message.channel.send(
                        f"{message.author.mention}, {await self.config.guild(message.guild).default_message()}",
                        delete_after=await self.config.guild(message.guild).timeout(),
                    )
            await message.delete()
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    if await self.config.guild(message.guild).warnmsg():
                        if await self.config.guild(message.guild).use_embed():
                            if not message.channel.permissions_for(
                                message.author
                            ).embed_links:
                                log.info(
                                    "No permissions to embed links in {message.guild.name} ({channel.name})."
                                )
                                return
                            embed = discord.Embed(
                                title="Spoiler Detected",
                                description=f"{message.author.mention}, {await self.config.guild(message.guild).default_message()}",
                                color=discord.Color.red(),
                            )
                            await message.channel.send(
                                embed=embed,
                                delete_after=await self.config.guild(
                                    message.guild
                                ).timeout(),
                            )
                        else:
                            await message.channel.send(
                                f"{message.author.mention}, {await self.config.guild(message.guild).default_message()}",
                                delete_after=await self.config.guild(
                                    message.guild
                                ).timeout(),
                            )
                    if await self.config.guild(message.guild).log_channel():
                        await self.log_channel_embed(message.guild, message, attachment)
                    await message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        if not await self.config.guild(guild).toggle():
            return
        if not guild.me.guild_permissions.manage_messages:
            log.info("No permissions to manage messages in {guild.name}.")
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if await self.bot.is_automod_immune(
            guild.get_member(payload.data["author"]["id"])
        ):
            return
        message = await guild.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )
        if NOSPOILER_REGEX.search(message.content):
            if not message.channel.permissions_for(message.author).manage_messages:
                log.info(
                    "No permissions to manage messages in {guild.name} ({channel.name})."
                )
                return
            await message.delete()
            if await self.config.guild(guild).warnmsg():
                if await self.config.guild(guild).use_embed():
                    if not message.channel.permissions_for(message.author).embed_links:
                        log.info(
                            "No permissions to embed links in {guild.name} ({channel.name})."
                        )
                        return
                    embed = discord.Embed(
                        title="Spoiler Detected",
                        description=f"{message.author.mention}, {await self.config.guild(guild).default_message()}",
                        color=discord.Color.red(),
                    )
                    await message.channel.send(
                        embed=embed,
                        delete_after=await self.config.guild(guild).timeout(),
                    )
                else:
                    await message.channel.send(
                        f"{message.author.mention}, {await self.config.guild(guild).default_message()}",
                        delete_after=await self.config.guild(guild).timeout(),
                    )
            if await self.config.guild(guild).log_channel():
                await self.log_channel_embed(guild, message)
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    if await self.config.guild(guild).warnmsg():
                        if await self.config.guild(guild).use_embed():
                            if not message.channel.permissions_for(
                                message.author
                            ).embed_links:
                                log.info(
                                    "No permissions to embed links in {guild.name} ({channel.name})."
                                )
                                return
                            embed = discord.Embed(
                                title="Spoiler Detected",
                                description=f"{message.author.mention}, {await self.config.guild(guild).default_message()}",
                                color=discord.Color.red(),
                            )
                            await message.channel.send(
                                embed=embed,
                                delete_after=await self.config.guild(guild).timeout(),
                            )
                        else:
                            await message.channel.send(
                                f"{message.author.mention}, {await self.config.guild(guild).default_message()}",
                                delete_after=await self.config.guild(guild).timeout(),
                            )
                    if await self.config.guild(guild).log_channel():
                        await self.log_channel_embed(guild, message, attachment)
                    await message.delete()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def nospoiler(self, ctx):
        """Manage NoSpoiler settings."""

    @nospoiler.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle NoSpoiler."""
        if not ctx.bot_permissions.manage_messages:
            return await ctx.send("I don't have permissions to manage messages.")
        toggle = await self.config.guild(ctx.guild).toggle()
        await self.config.guild(ctx.guild).toggle.set(not toggle)
        await ctx.send(f"NoSpoiler is now {'enabled' if not toggle else 'disabled'}.")

    @nospoiler.command()
    async def logchannel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ):
        """Set the log channel for NoSpoiler."""
        await self.config.guild(ctx.guild).log_channel.set(
            channel.id if channel else None
        )
        await ctx.send(
            f"Log channel set to {channel.mention if channel else 'Disabled'}."
        )

    @nospoiler.command()
    async def warnmsg(self, ctx: commands.Context):
        """Toggle the warning message."""
        warnmsg = await self.config.guild(ctx.guild).warnmsg()
        await self.config.guild(ctx.guild).warnmsg.set(not warnmsg)
        await ctx.send(
            f"Warning message is now {'enabled' if not warnmsg else 'disabled'}."
        )

    @nospoiler.command()
    async def useembed(self, ctx: commands.Context):
        """Toggle the use of embeds."""
        if not ctx.bot_permissions.embed_links:
            return await ctx.send("I don't have permissions to embed links.")
        use_embed = await self.config.guild(ctx.guild).use_embed()
        await self.config.guild(ctx.guild).use_embed.set(not use_embed)
        await ctx.send(
            f"Use of embeds is now {'enabled' if not use_embed else 'disabled'}."
        )

    @nospoiler.command()
    async def message(self, ctx: commands.Context, *, message: str):
        """Set the default message for NoSpoiler."""
        if len(message) < 2 or len(message) > 2000:
            return await ctx.send("The message must be between 2 and 2000 characters.")
        await self.config.guild(ctx.guild).default_message.set(message)
        await ctx.send(f"Default message set to {message}.")

    @nospoiler.command()
    async def timeout(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ):
        """Set the timeout for the warning message."""
        await self.config.guild(ctx.guild).timeout.set(seconds)
        await ctx.send(f"Timeout set to {seconds} seconds.")

    @nospoiler.command()
    async def settings(self, ctx: commands.Context):
        """Show the current settings for NoSpoiler."""
        all = await self.config.guild(ctx.guild).all()
        toggle = "Enabled" if all["toggle"] else "Disabled"
        log_channel = (
            ctx.guild.get_channel(all["log_channel"]).mention
            if all["log_channel"]
            else "Disabled"
        )
        warnmsg = "Enabled" if all["warnmsg"] else "Disabled"
        use_embed = "Enabled" if all["use_embed"] else "Disabled"
        timeout = all["timeout"]
        default_message = all["default_message"]
        embed = discord.Embed(
            title="NoSpoiler Settings",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Toggle:", value=toggle, inline=False)
        embed.add_field(name="Log Channel:", value=log_channel, inline=False)
        embed.add_field(name="Warning Message:", value=warnmsg, inline=False)
        embed.add_field(name="Use Embed:", value=use_embed, inline=False)
        embed.add_field(name="Timeout:", value=f"{timeout} seconds", inline=False)
        embed.add_field(name="Default Message:", value=default_message, inline=False)
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @nospoiler.command(with_app_command=False)
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
