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

import asyncio
from typing import Final

import discord
import pytz
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.views import ConfirmView

from .dashboard_integration import DashboardIntegration
from .utils import (
    get_next_reset_times,
    get_owner_timezone,
    increment_published_count,
    initialize_scheduler,
    reset_count,
    schedule_resets,
)
from .view import IgnoredNewsChannelsView, StatsView

logger = getLogger("red.maxcogs.autopublisher")


class AutoPublisher(DashboardIntegration, commands.Cog):
    """Automatically publish messages in news channels."""

    __version__: Final[str] = "3.4.0"
    __author__: Final[str] = "MAX, AAA3A"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/autopublisher/README.md"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=15786223, force_registration=True)
        default_guild = {
            "toggle": False,
            "ignored_channels": [],
        }
        default_global = {
            "published_count": 0,
            "published_weekly_count": 0,
            "published_monthly_count": 0,
            "published_yearly_count": 0,
            "last_count_time": None,
            "timezone": "UTC",
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.scheduler = None
        self.bot.loop.create_task(self._initialize_scheduler())

    async def _initialize_scheduler(self) -> None:
        """Initialize the scheduler after cog is loaded."""
        self.scheduler = await initialize_scheduler(self)
        await schedule_resets(self)

    def cog_unload(self) -> None:
        """Clean up scheduler on cog unload."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.remove_all_jobs()
            self.scheduler.shutdown()
            logger.debug("Scheduler shut down")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Format help with cog metadata."""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nVersion: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message) -> None:
        """Auto-publish messages in news channels."""
        if not message.guild or not isinstance(message.channel, discord.TextChannel):
            return

        guild_config = self.config.guild(message.guild)
        settings = await guild_config.all()
        perms = message.channel.permissions_for(message.guild.me)
        if (
            not settings["toggle"]
            or message.channel.id in settings["ignored_channels"]
            or await self.bot.cog_disabled_in_guild(self, message.guild)
            or not perms.manage_messages
            or not perms.view_channel
            or not perms.read_message_history
            or not perms.send_messages
            or not message.channel.is_news()
            or "NEWS" not in message.guild.features
        ):
            if "NEWS" not in message.guild.features and settings["toggle"]:
                await guild_config.toggle.set(False)
                logger.warning(
                    f"Disabled AutoPublisher in {message.guild.name} (no NEWS feature)."
                )
            return

        if message.flags.crossposted:
            return

        try:
            await asyncio.sleep(0.5)
            await asyncio.wait_for(message.publish(), timeout=60)
            await increment_published_count(self.config)
        except (discord.HTTPException, discord.Forbidden, asyncio.TimeoutError) as e:
            logger.error(f"Failed to publish message in {message.channel.id}: {e}", exc_info=True)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(aliases=["aph", "autopub"])
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher settings."""

    @commands.is_owner()
    @autopublisher.command(name="settimezone")
    async def set_timezone(self, ctx: commands.Context, timezone: str) -> None:
        """
        Set the bot's timezone for reset schedules.

        Default timezone is UTC if not set by user or invalid.
        Use the format `Continent/City`.
        Find your timezone here: https://whatismyti.me/
        """
        try:
            pytz.timezone(timezone)
            await self.config.timezone.set(timezone)
            message = (
                f"Timezone set to {timezone}. Please reload the cog to apply changes:\n"
                f"`{ctx.clean_prefix}reload autopublisher`\n"
                "-# You will see correct timezone without reload but scheduler will not work until reload is done."
            )
            await ctx.send(message)
        except pytz.exceptions.UnknownTimeZoneError:
            await ctx.send(
                "Invalid timezone. Please use a valid timezone like 'US/Pacific', 'Europe/London', or 'UTC'. "
                "See <https://whatismyti.me> for your timezone."
            )
            logger.error(f"Invalid timezone set attempt {timezone}", exc_info=True)

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(name="stats")
    async def stats(self, ctx: commands.Context) -> None:
        """
        Show statistics for published messages.

        This shows global stats across all servers in an interactive view.
        """
        view = StatsView(self)
        await view.start(ctx)
        view.message = await ctx.send(view=view)

    @autopublisher.command()
    @commands.bot_has_permissions(manage_messages=True, view_channel=True)
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle AutoPublisher on or off."""
        if "NEWS" not in ctx.guild.features:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    label="Learn More",
                    url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                    emoji="ℹ️",
                )
            )
            return await ctx.send("This server lacks the News Channel feature.", view=view)

        guild_config = self.config.guild(ctx.guild)
        toggle = not await guild_config.toggle()
        await guild_config.toggle.set(toggle)
        await ctx.send(f"AutoPublisher is now {'enabled' if toggle else 'disabled'}.")

    @autopublisher.command()
    async def ignorechannel(
        self, ctx: commands.Context, channels: commands.Greedy[discord.TextChannel] = None
    ) -> None:
        """Ignore or unignore news channels for AutoPublisher."""
        if "NEWS" not in ctx.guild.features:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    label="Learn More",
                    url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                    emoji="ℹ️",
                )
            )
            return await ctx.send("This server lacks the News Channel feature.", view=view)

        news_channels = [ch for ch in ctx.guild.text_channels if ch.is_news()]
        if not news_channels:
            return await ctx.send("No news channels available to ignore.")

        guild_config = self.config.guild(ctx.guild)
        ignored = set(await guild_config.ignored_channels())

        if channels:
            for channel in channels:
                if not channel.is_news():
                    continue
                if channel.id in ignored:
                    ignored.remove(channel.id)
                else:
                    ignored.add(channel.id)
            await guild_config.ignored_channels.set(list(ignored))
            await ctx.send(
                f"Updated ignored news channels: {humanize_list([ch.mention for ch in channels if ch.is_news()])}."
            )
        else:
            view = IgnoredNewsChannelsView(self)
            await view.start(ctx)
            view.message = await ctx.send(view=view)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(aliases=["view"])
    async def settings(self, ctx: commands.Context) -> None:
        """Display current AutoPublisher settings."""
        data = await self.config.guild(ctx.guild).all()
        ignored_mentions = [
            ctx.guild.get_channel(ch).mention
            for ch in data["ignored_channels"]
            if ctx.guild.get_channel(ch)
        ]
        embed = discord.Embed(
            title="AutoPublisher Settings",
            color=await ctx.embed_color(),
            description=f"**Enabled:** {data['toggle']}\n**Ignored Channels:** {humanize_list(ignored_mentions) or 'None'}",
        )
        await ctx.send(embed=embed)

    @autopublisher.command()
    async def reset(self, ctx: commands.Context) -> None:
        """Reset guild-specific AutoPublisher settings."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Reset AutoPublisher settings?", view=view)
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            await ctx.send("Settings reset.")
        else:
            await ctx.send("Reset cancelled.")

    @commands.is_owner()
    @autopublisher.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def resetcount(self, ctx: commands.Context) -> None:
        """Reset global published message counts."""
        embed = discord.Embed(
            title="Reset Count",
            description="Reset all published message counts?\n**Warning:** This is irreversible without backups.",
            color=await ctx.embed_color(),
        )
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self.config.clear_all_globals()
            # Re-register defaults
            await self.config.register_global(
                published_count=0,
                published_weekly_count=0,
                published_monthly_count=0,
                published_yearly_count=0,
                last_count_time=None,
                timezone="UTC",
            )
            await ctx.send("Counts reset.")
        else:
            await ctx.send("Reset cancelled.")
