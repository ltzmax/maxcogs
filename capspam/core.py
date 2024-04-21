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

import io
import logging
import re
from typing import Dict, Literal, Optional, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list

CAP_DETECTOR = re.compile(r"[A-Z]", re.MULTILINE)
URL_DETECTOR = re.compile(
    r"(?:http[s]?://)?(?:[a-zA-Z]|[0-9]|[$@.&+]|[\-]|[\*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)
WARN_MESSAGE_DELETE_COOLDOWN = 10

log = logging.getLogger("red.maxcogs.capspam")


# Respect link detection with discord.gg links as well.
def get_non_discord_urls(text):
    urls = URL_DETECTOR.findall(text)
    return [url for url in urls if "discord.gg" not in url]


class CapSpam(commands.Cog):
    """Prevent users from sending messages with too many caps."""

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=22222222222)
        self._enabled_guilds_ids = []
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "warn_message": "Your message contain too many caps!",
            "limit": 3,
            "modlog_channel": None,
            "warn_msg_toggle": False,
            "ignored_channels": [],
            "timeout": WARN_MESSAGE_DELETE_COOLDOWN,
            "allowed_mentions": True,
            "ignore_links": True,
        }
        self.config.register_guild(**default_guild)

    __version__ = "1.2.0"
    __author__ = "MAX, Predeactor"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/docs/CapSpam.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(
        self, *, requester: str, user_id: int
    ) -> Dict[str, str]:
        """Nothing to delete"""
        return {}

    async def modlog(self, guild: discord.Guild, message: str):
        modlog_channel = await self.config.guild(guild).modlog_channel()
        if not modlog_channel:
            return
        channel = guild.get_channel(modlog_channel)
        if not channel:
            return
        if (
            not channel.permissions_for(guild.me).send_messages
            or not channel.permissions_for(guild.me).embed_links
        ):
            log.warning(
                "I don't have permission to send messages or embed links in {channel}.".format(
                    channel=channel
                )
            )
            return

        embed = discord.Embed(
            title="CapSpam Detected",
            description="Message too long" if len(message) > 4000 else message,
            color=await self.bot.get_embed_color(channel),
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if not await self.config.guild(message.guild).enabled():
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        ignored_channels = await self.config.guild(message.guild).ignored_channels()
        if message.channel.id in ignored_channels:
            return

        # Ignore messages with links or attachments
        if await self.config.guild(message.guild).ignore_links():
            if (
                URL_DETECTOR.search(message.content)
                or message.attachments
                or get_non_discord_urls(message.content)
            ):
                return

        # Check for caps
        caps = CAP_DETECTOR.findall(message.content)
        if len(caps) >= await self.config.guild(message.guild).limit():
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                log.warning("I don't have permissions to manage_messages.")
                return
            await message.delete()
            if await self.config.guild(message.guild).warn_msg_toggle():
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    log.warning(
                        "I don't have permission to send messages in {channel}.".format(
                            channel=message.channel
                        )
                    )
                    return
                await message.channel.send(
                    f"{message.author.mention}, {await self.config.guild(message.guild).warn_message()}",
                    delete_after=WARN_MESSAGE_DELETE_COOLDOWN,
                    allowed_mentions=discord.AllowedMentions(
                        users=await self.config.guild(message.guild).allowed_mentions()
                    ),
                )
            await self.modlog(
                message.guild,
                f"Member: {message.author.mention} ({message.author.id})\nMessage:\n{box(message.content, lang='yaml')}",
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if not before.guild:
            return
        if not await self.config.guild(before.guild).enabled():
            return

        ignored_channels = await self.config.guild(before.guild).ignored_channels()
        if before.channel.id in ignored_channels:
            return

        if await self.bot.cog_disabled_in_guild(self, before.guild):
            return
        if await self.bot.is_automod_immune(before.author):
            return

        # Ignore messages with links or attachments
        if await self.config.guild(before.guild).ignore_links():
            if (
                URL_DETECTOR.search(after.content)
                or after.attachments
                or get_non_discord_urls(after.content)
            ):
                return

        # Check for caps
        caps = CAP_DETECTOR.findall(after.content)
        if len(caps) >= await self.config.guild(before.guild).limit():
            if not after.channel.permissions_for(after.guild.me).manage_messages:
                log.warning("I don't have permissions to manage_messages.")
                return
            await after.delete()
            if await self.config.guild(before.guild).warn_msg_toggle():
                if not after.channel.permissions_for(after.guild.me).send_messages:
                    log.warning(
                        "I don't have permission to send messages in {channel}.".format(
                            channel=after.channel
                        )
                    )
                    return
                await after.channel.send(
                    f"{after.author.mention}, {await self.config.guild(before.guild).warn_message()}",
                    delete_after=WARN_MESSAGE_DELETE_COOLDOWN,
                    allowed_mentions=discord.AllowedMentions(
                        users=await self.config.guild(before.guild).allowed_mentions()
                    ),
                )
            await self.modlog(
                before.guild,
                f"Member: {before.author.mention} ({before.author.id})\nMessage:\n{box(after.content, lang='yaml')}",
            )

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def capspam(self, ctx: commands.GuildContext):
        """Manage CapSpam settings"""

    @capspam.command(name="toggle")
    async def capspam_toggle(self, ctx: commands.GuildContext, *, toggle: bool):
        """
        Toggle CapSpam on/off.
        """
        if not ctx.bot_permissions.manage_messages:
            return await ctx.send(
                "I don't have ``manage_messages`` permission to let you toggle capspam filter."
            )
        if toggle:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("CapSpam has been enabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("CapSpam has been disabled.")

    @capspam.command(name="ignorelinks")
    async def capspam_ignorelinks(self, ctx: commands.GuildContext, toggle: bool):
        """
        Toggle ignoring messages with links or attachments.

        Default is enabled.
        If enabled, the bot will ignore messages with links or attachments that contain caps in the url.
        """
        await self.config.guild(ctx.guild).ignore_links.set(toggle)
        en = "enabled" if toggle else "disabled"
        await ctx.send(f"Ignoring messages with links or attachments has been {en}.")

    @capspam.command(name="allowedmentions", aliases=["allowedmention", "mention"])
    async def capspam_allowedmentions(self, ctx: commands.GuildContext, toggle: bool):
        """
        Toggle allowed mentions in the warning message.

        Default is enabled.
        If allowed mentions are enabled, the bot will mention the user when sending the warning message.
        """
        await self.config.guild(ctx.guild).allowed_mentions.set(toggle)
        en = "enabled" if toggle else "disabled"
        await ctx.send(f"Allowed mentions has been {en}.")

    @capspam.command(name="deleteafter")
    async def capspam_deleteafter(
        self, ctx: commands.GuildContext, secounds: commands.Range[int, 10, 120]
    ):
        """
        Set the time to delete the warning message.

        Default is 10 seconds.
        Timeout must be between 10 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(secounds)
        await ctx.send(f"Timeout has been set to `{secounds}` secounds.")

    @capspam.command(name="ignorechannel", usage="<add|remove> <channel>")
    async def capspam_ignorechannel(
        self,
        ctx: commands.GuildContext,
        add_or_remove: Literal["add", "remove"],
        channels: Union[
            discord.TextChannel,
            discord.ForumChannel,
            discord.Thread,
            discord.VoiceChannel,
        ],
    ):
        """
        Add or remove channel(s) from the ignore list.

        If a channel is in the ignore list, the bot will not check messages in that channel.

        **Example:**
        `[p]capspam ignorechannel add #channel`
        `[p]capspam ignorechannel remove #channel`

        **arguments:**
        - `<add|remove>`: Add or remove the channel.
        - `<channel>`: The channel to add or remove.
        """
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()
        if add_or_remove == "add":
            if channels.id in ignored_channels:
                return await ctx.send("Channel is already in the ignore list.")
            ignored_channels.append(channels.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channels.mention} has been added to the ignore list.")
        else:
            if channels.id not in ignored_channels:
                return await ctx.send("Channel is not in the ignore list.")
            ignored_channels.remove(channels.id)
            await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
            await ctx.send(f"{channels.mention} has been removed from the ignore list.")

    @capspam.command(name="limit")
    async def capspam_limit(self, ctx: commands.GuildContext, limit: int):
        """
        Set the limit of caps allowed in a message.

        Default limit is set to 3.
        """
        if limit < 1 or limit > 100:
            return await ctx.send("Limit must be between 1 and 100.")
        await self.config.guild(ctx.guild).limit.set(limit)
        await ctx.send(f"Limit has been set to `{limit}`.")

    @capspam.command("view", aliases=["settings", "setting", "info"])
    @commands.bot_has_permissions(embed_links=True)
    async def capspam_view(self, ctx: commands.GuildContext):
        """
        Show the informations about CapSpam in your server.
        """
        all = await self.config.guild(ctx.guild).all()
        await ctx.send(
            f"# CapSpam Settings for {ctx.guild.name}\n"
            f"**Enabled**: {all['enabled']}\n"
            f"**Limit**: {all['limit']}\n"
            f"**Warn Message Toggle**: {all['warn_msg_toggle']}\n"
            f"**Modlog Channel**: {ctx.guild.get_channel(all['modlog_channel']).mention if all['modlog_channel'] else 'Not Set'}\n"
            f"**Delete After**: {all['timeout']} seconds\n"
            f"**Allowed Mentions**: {all['allowed_mentions']}\n"
            f"**Warn Message**: {all['warn_message']}\n"
            f"**Ignored Channels**: {humanize_list([ctx.guild.get_channel(c).mention for c in all['ignored_channels']]) if all['ignored_channels'] else 'None'}"
        )

    @capspam.command(name="warnmsg", aliases=["warnmessage", "warn"])
    async def capspam_warnmsg(
        self, ctx: commands.GuildContext, *, message: Optional[str] = None
    ):
        """
        Set the message to send when a user is warned.

        If no message is provided, the default message will be used.
        """
        if message is not None and len(message) > 1024:
            return await ctx.send("Message cannot be longer than 1024 characters.")
        if not message:
            await self.config.guild(ctx.guild).warn_message.clear()
            return await ctx.send("The message has been reset to the default.")
        await self.config.guild(ctx.guild).warn_message.set(message)
        await ctx.send("The message has been set.")

    @capspam.command(name="warnmsgtoggle", aliases=["warnmessagetoggle"])
    async def capspam_warnmsgtoggle(self, ctx: commands.GuildContext, toggle: bool):
        """
        Toggle the warning message.

        Default is disabled.

        If the warning message is enabled, the bot will send a message when a user is warned.
        """
        if toggle:
            await self.config.guild(ctx.guild).warn_msg_toggle.set(True)
            await ctx.send("Warn message has been enabled.")
        else:
            await self.config.guild(ctx.guild).warn_msg_toggle.set(False)
            await ctx.send("Warn message has been disabled.")

    @capspam.command(name="modlog")
    async def capspam_modlog(
        self, ctx: commands.GuildContext, channel: Optional[discord.TextChannel]
    ):
        """
        Set modlog channel for CapSpam.

        If no channel is provided, the modlog channel will be reset.
        """
        if channel is None:
            await self.config.guild(ctx.guild).modlog_channel.clear()
            await ctx.send("Modlog channel has been reset.")
            return
        await self.config.guild(ctx.guild).modlog_channel.set(channel.id)
        await ctx.send(f"Modlog channel has been set to {channel.mention}.")

    @capspam.command(name="export", hidden=True)
    async def capspam_export(self, ctx: commands.GuildContext):
        """
        Export the CapSpam settings.

        Returned in a JSON format.
        """
        data = await self.config.guild(ctx.guild).all()
        file = discord.File(io.StringIO(str(data)), f"capspam-{ctx.guild.id}.json")
        await ctx.send(f"Report for guild ID: {ctx.guild.id}", file=file)

    @commands.bot_has_permissions(embed_links=True)
    @capspam.command(with_app_command=False)
    async def version(self, ctx: commands.Context):
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
