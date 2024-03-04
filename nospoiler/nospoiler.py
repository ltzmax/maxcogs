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
import logging
from typing import Any, Dict, Final, Optional, Pattern, Union

import discord
import TagScriptEngine as tse
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from ._tagscript import (
    TAGSCRIPT_LIMIT,
    TagCharacterLimitReached,
    TagscriptConverter,
    process_tagscript,
    warn_message,
)

SPOILER_REGEX: Pattern[str] = re.compile(r"(?s)\|\|(.+?)\|\|")

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.5.6"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/nospoiler"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "log_channel": None,
            "spoiler_warn": False,
            "spoiler_warn_message": warn_message,
            "timeout": 10,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def validate_tagscript(self, tagscript: str) -> bool:
        length = len(tagscript)
        if length > TAGSCRIPT_LIMIT:
            raise TagCharacterLimitReached(TAGSCRIPT_LIMIT, length)
        return True

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
            log.info(
                f"I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            return
        color = await self.bot.get_embed_color(log_channel)
        embed = discord.Embed(
            title="Deleted Spoiler Message",
            color=color,
            description=f"**Message:**\n{box(message.content, lang='yaml') if len(message.content) < 2024 else 'Message too long to display.'}",
        )
        embed.add_field(name="Member:", value=message.author.mention)
        embed.add_field(name="Channel:", value=message.channel.mention)
        if attachment:
            embed.add_field(name="Attachment:", value=attachment.url, inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """handle spoiler messages"""
        if message.guild is None:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if not message.guild.me.guild_permissions.manage_messages:
            log.info(
                f"NoSpoiler is missing permission to manage_messages to do anything in {message.guild.name} ({message.guild.id})"
            )
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
            return

        if SPOILER_REGEX.search(message.content):
            if await self.config.guild(message.guild).spoiler_warn():
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    log.info(
                        f"i do not have permission to send_messages in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
                    )
                    return
                warnmessage = await self.config.guild(
                    message.guild
                ).spoiler_warn_message()
                delete_after = await self.config.guild(message.guild).timeout()
                color = await self.bot.get_embed_color(message.channel)
                kwargs = process_tagscript(
                    warnmessage,
                    {
                        "server": tse.GuildAdapter(message.guild),
                        "member": tse.MemberAdapter(message.author),
                        "author": tse.MemberAdapter(message.author),
                        "color": tse.StringAdapter(str(color)),
                    },
                )
                kwargs["allowed_mentions"] = discord.AllowedMentions(
                    everyone=False, roles=False
                )
                kwargs["delete_after"] = delete_after
                await message.channel.send(**kwargs)
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                log.info(
                    f"i do not have permission to manage_messages in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
                )
                return
            if await self.config.guild(message.guild).log_channel():
                await self.log_channel_embed(message.guild, message)
            await message.delete()
            return
        if attachments := message.attachments:
            for attachment in attachments:
                if attachment.is_spoiler():
                    if await self.config.guild(message.guild).spoiler_warn():
                        if not message.channel.permissions_for(
                            message.guild.me
                        ).send_messages:
                            log.info(
                                f"i do not have permission to send_messages in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
                            )
                            return
                        warnmessage = await self.config.guild(
                            message.guild
                        ).spoiler_warn_message()
                        delete_after = await self.config.guild(message.guild).timeout()
                        color = await self.bot.get_embed_color(message.channel)
                        kwargs = process_tagscript(
                            warnmessage,
                            {
                                "server": tse.GuildAdapter(message.guild),
                                "member": tse.MemberAdapter(message.author),
                                "author": tse.MemberAdapter(message.author),
                                "color": tse.StringAdapter(str(color)),
                            },
                        )
                        kwargs["allowed_mentions"] = discord.AllowedMentions(
                            everyone=False, roles=False
                        )
                        kwargs["delete_after"] = delete_after
                        await message.channel.send(**kwargs)
                    if not message.channel.permissions_for(
                        message.guild.me
                    ).manage_messages:
                        log.info(
                            f"i do not have permission to manage_messages in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
                        )
                        return
                    if await self.config.guild(message.guild).log_channel():
                        await self.log_channel_embed(message.guild, message, attachment)
                    await message.delete()

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if not await self.config.guild(after.guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return
        if after.author.bot:
            return
        if await self.bot.is_automod_immune(after.author):
            return
        if SPOILER_REGEX.search(after.content):
            if await self.config.guild(after.guild).spoiler_warn():
                if not after.channel.permissions_for(after.guild.me).send_messages:
                    log.info(
                        f"Unable to send message in {after.channel.mention} in {after.guild.name} ({after.guild.id}) due to missing permissions."
                    )
                    return
                warnmessage = await self.config.guild(
                    after.guild
                ).spoiler_warn_message()
                delete_after = await self.config.guild(after.guild).timeout()
                color = await self.bot.get_embed_color(after.channel)
                kwargs = process_tagscript(
                    warnmessage,
                    {
                        "server": tse.GuildAdapter(after.guild),
                        "member": tse.MemberAdapter(after.author),
                        "author": tse.MemberAdapter(after.author),
                        "color": tse.StringAdapter(str(color)),
                    },
                )
                kwargs["allowed_mentions"] = discord.AllowedMentions(
                    everyone=False, roles=False
                )
                kwargs["delete_after"] = delete_after
                await after.channel.send(**kwargs)
            if not after.channel.permissions_for(after.guild.me).manage_messages:
                log.info(
                    f"Unable to delete message in {after.channel.mention} in {after.guild.name} ({after.guild.id}) due to missing permissions."
                )
                return
            if await self.config.guild(after.guild).log_channel():
                await self.log_channel_embed(after.guild, after)
            await after.delete()

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
            return await ctx.send(
                "I don't have manage_messages permission to let you toggle the spoiler filter."
            )
        await self.config.guild(ctx.guild).enabled.set(
            not await self.config.guild(ctx.guild).enabled()
        )
        await ctx.send(
            f"Nospoiler is now {'enabled' if await self.config.guild(ctx.guild).enabled() else 'disabled'}."
        )

    @nospoiler.command()
    async def timeout(
        self, ctx: commands.Context, amount: commands.Range[int, 10, 120]
    ):
        """Set the delete after timeout.

        Default timeout is 10 seconds.
        Timeout must be between 10 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(amount)
        await ctx.send(f"Timeout has been set to {amount} seconds.")

    @nospoiler.command()
    async def logchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ) -> None:
        """Set the channel where the bot will log the deleted spoiler messages.

        If the channel is not set, the bot will not log the deleted spoiler messages.
        """
        if channel:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel has been set to {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).log_channel.clear()
            await ctx.send("Log channel has been reset.")

    @nospoiler.command()
    async def togglewarnmsg(self, ctx: commands.Context, toggle: bool = None) -> None:
        """Toggle the spoiler warning message on or off."""
        await self.config.guild(ctx.guild).spoiler_warn.set(toggle)
        await ctx.send(
            f"Spoiler warning message is now {'enabled' if toggle else 'disabled'}."
        )

    @nospoiler.command()
    async def message(
        self, ctx: commands.Context, *, message: Optional[TagscriptConverter]
    ) -> None:
        """
        Set the spoiler warning message.

        (Supports Tagscript)

        **Blocks:**
        - [Assugnment Block](https://phen-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#assignment-block)
        - [If Block](https://phen-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#if-block)
        - [Embed Block](https://phen-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#embed-block)
        - [Command Block](https://phen-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#command-block)

        **Variable:**
        - `{server}`: [Your guild/server.](https://phen-cogs.readthedocs.io/en/latest/tags/default_variables.html#server-block)
        - `{member}`: [Author of the message.](https://phen-cogs.readthedocs.io/en/latest/tags/default_variables.html#author-block)
        - `{color}`: [botname]'s default color.

        **Example:**
        ```
        {embed(title):No spoiler allowed.}
        {embed(description):{member(mention)} Usage of spoiler is not allowed in this server.}
        {embed(color):{color}}
        ```
        **Without embed:**
        ```
        {member(mention)} Usage of spoiler is not allowed in this server.
        ```
        """
        if message:
            await self.config.guild(ctx.guild).spoiler_warn_message.set(message)
            await ctx.send("Spoiler warning message has been set.")
        else:
            await self.config.guild(ctx.guild).spoiler_warn_message.clear()
            await ctx.send("Spoiler warning message has been reset.")

    @nospoiler.command(aliases=["view", "views"])
    async def settings(self, ctx: commands.Context) -> None:
        """Show the settings."""
        all = await self.config.guild(ctx.guild).all()
        enabled = all["enabled"]
        if enabled:
            enabled = "Enabled"
        else:
            enabled = "Disabled"
        log_channel = all["log_channel"]
        if log_channel:
            log_channel = ctx.guild.get_channel(log_channel).mention
        else:
            log_channel = "Not set"
        spoiler_warn = all["spoiler_warn"]
        if spoiler_warn:
            spoiler_warn = "Enabled"
        else:
            spoiler_warn = "Disabled"
        timeout = all["timeout"]
        spoiler_warn_message = all["spoiler_warn_message"]
        await ctx.send(
            "## Nospoiler Settings\n"
            f"> **Toggle**: {enabled}\n"
            f"> **Log Channel**: {log_channel}\n"
            f"> **Spoiler Warning**: {spoiler_warn}\n"
            f"> **Timeout**: {timeout} seconds\n"
            f"> **Spoiler Warning Message**:\n{box(f'{spoiler_warn_message}', lang='yaml')}"
        )

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
