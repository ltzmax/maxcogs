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
from datetime import datetime, timedelta
from typing import Any, Dict, Final, List, Literal, Optional, Union

import discord
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord import utils as discord_utils
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate

from .dashboard_integration import DashboardIntegration
from .view import IgnoredNewsChannelsView

logger = getLogger("red.maxcogs.autopublisher")


class AutoPublisher(DashboardIntegration, commands.Cog):
    """Automatically publish messages in news channels."""

    __version__: Final[str] = "3.2.0"
    __author__: Final[str] = "MAX, AAA3A"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

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
        self.scheduler = AsyncIOScheduler()
        self.bot.loop.create_task(self._initialize_scheduler())

    async def _initialize_scheduler(self) -> None:
        """Initialize the scheduler after cog is loaded."""
        try:
            await self._schedule_resets()
            logger.info("Scheduler initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)

    async def _get_owner_timezone(self) -> pytz.timezone:
        """Retrieve the owner's timezone from config, default to UTC."""
        timezone_str = await self.config.timezone()
        try:
            tz = pytz.timezone(timezone_str)
            logger.debug(f"Retrieved timezone: {timezone_str}")
            return tz
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Invalid timezone in config: {timezone_str}, falling back to UTC")
            return pytz.UTC

    async def _schedule_resets(self) -> None:
        """Schedule periodic count resets in the owner's timezone."""
        owner_tz = await self._get_owner_timezone()
        self.scheduler.remove_all_jobs()  # Clear existing jobs to avoid duplicates
        self.scheduler.add_job(
            self.reset_count,
            "cron",
            day_of_week="sun",
            hour=0,
            minute=0,
            timezone=owner_tz,
            args=["weekly"],
            id="weekly_reset",
        )
        self.scheduler.add_job(
            self.reset_count,
            "cron",
            day=1,
            hour=0,
            minute=0,
            timezone=owner_tz,
            args=["monthly"],
            id="monthly_reset",
        )
        self.scheduler.add_job(
            self.reset_count,
            "cron",
            month=1,
            day=1,
            hour=0,
            minute=0,
            timezone=owner_tz,
            args=["yearly"],
            id="yearly_reset",
        )
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started with jobs: weekly, monthly, yearly")

    def cog_unload(self) -> None:
        """Clean up scheduler on cog unload."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.debug("Scheduler shut down")

    async def reset_count(self, period: Literal["weekly", "monthly", "yearly"]) -> None:
        """Reset the specified count period, checking date in owner's timezone."""
        owner_tz = await self._get_owner_timezone()
        now_in_owner_tz = datetime.now(owner_tz)
        async with self.config.all() as data:
            if period == "weekly":
                data["published_weekly_count"] = 0
                logger.info("Weekly count reset.")
            elif period == "monthly":
                if now_in_owner_tz.day == 1:
                    data["published_monthly_count"] = 0
                    logger.info("Monthly count reset.")
                else:
                    logger.debug(
                        f"Skipped monthly reset: not the 1st day (current day: {now_in_owner_tz.day})."
                    )
            elif period == "yearly":
                if now_in_owner_tz.month == 1 and now_in_owner_tz.day == 1:
                    data["published_yearly_count"] = 0
                    logger.info("Yearly count reset.")
                else:
                    logger.debug(
                        f"Skipped yearly reset: not Jan 1 (current date: {now_in_owner_tz.month}/{now_in_owner_tz.day})."
                    )

    async def increment_published_count(self) -> None:
        """Increment all published message counts."""
        async with self.config.all() as data:
            for key in [
                "published_count",
                "published_weekly_count",
                "published_monthly_count",
                "published_yearly_count",
            ]:
                data[key] = data.get(key, 0) + 1
            data["last_count_time"] = datetime.utcnow().isoformat()

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
        if (
            not settings["toggle"]
            or message.channel.id in settings["ignored_channels"]
            or await self.bot.cog_disabled_in_guild(self, message.guild)
            or not message.guild.me.guild_permissions.manage_messages
            or not message.guild.me.guild_permissions.view_channel
            or not message.guild.me.guild_permissions.read_message_history
            or not message.guild.me.guild_permissions.send_messages
            or not message.channel.is_news()
            or "NEWS" not in message.guild.features
        ):
            if "NEWS" not in message.guild.features and settings["toggle"]:
                await guild_config.toggle.set(False)
                logger.warning(
                    f"Disabled AutoPublisher in {message.guild.name} (no NEWS feature)."
                )
            return

        try:
            await asyncio.sleep(0.5)
            await asyncio.wait_for(message.publish(), timeout=60)
            await self.increment_published_count()
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
            await self.config.set_raw("timezone", value=timezone)
            await ctx.send(
                f"Timezone set to {timezone}. Please reload the cog to apply changes:\n"
                "`{prefix}reload autopublisher`\n".format(prefix=ctx.clean_prefix),
                "-# You will see correct timezone without reload but scheduler will not work until reload is done.",
            )
        except pytz.exceptions.UnknownTimeZoneError:
            await ctx.send(
                "Invalid timezone. Please use a valid timezone like 'US/Pacific', 'Europe/London', or 'UTC'. "
                "See <https://whatismyti.me> for your timezone."
            )
            logger.error(f"Invalid timezone set attempt {timezone}", exc_info=True)

    @commands.is_owner()
    @autopublisher.command(name="stats")
    async def stats(self, ctx: commands.Context) -> None:
        """Show statistics for published messages."""
        owner_tz = await self._get_owner_timezone()
        data = await self.config.all()
        last_count_time = data.get("last_count_time")
        last_published = "Never"
        if last_count_time:
            try:
                last_count_dt = datetime.fromisoformat(last_count_time)
                last_count_dt = last_count_dt.replace(tzinfo=pytz.UTC).astimezone(owner_tz)
                last_published = discord_utils.format_dt(last_count_dt, "R")
            except ValueError:
                last_published = "Invalid timestamp"

        table_data = [
            ["Weekly", humanize_number(data["published_weekly_count"])],
            ["Monthly", humanize_number(data["published_monthly_count"])],
            ["Yearly", humanize_number(data["published_yearly_count"])],
            ["Total Published", humanize_number(data["published_count"])],
        ]
        table = tabulate(table_data, headers=["Period", "Count"], tablefmt="simple")

        now = datetime.now(owner_tz)
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 0:
            days_until_sunday = 7
        next_weekly = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=days_until_sunday
        )
        next_weekly_ts = int(next_weekly.timestamp())
        next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=32
        )
        next_month = next_month.replace(day=1)
        next_monthly_ts = int(next_month.timestamp())
        next_year = now.year + 1 if now.month > 1 or (now.month == 1 and now.day > 1) else now.year
        next_yearly = now.replace(
            year=next_year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_yearly_ts = int(next_yearly.timestamp())

        await ctx.send(
            f"{box(table, lang='prolog')}\n"
            f"Timezone: `{owner_tz.zone}`\n"
            f"Next Weekly Reset: <t:{next_weekly_ts}:R> (<t:{next_weekly_ts}:f>)\n"
            f"Next Monthly Reset: <t:{next_monthly_ts}:R> (<t:{next_monthly_ts}:f>)\n"
            f"Next Yearly Reset: <t:{next_yearly_ts}:R> (<t:{next_yearly_ts}:f>)\n"
            f"Last Published: {last_published}"
        )

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
                    emoji="<:icons_info:880113401207095346>",
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
                    emoji="<:icons_info:880113401207095346>",
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
            view.ctx = ctx
            msg = "Select news channels to ignore/unignore.\nUse `[p]autopub ignorechannel #channel(s)` to manage manually."
            view.message = await ctx.send(msg.replace("[p]", ctx.clean_prefix), view=view)

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

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command()
    async def version(self, ctx: commands.Context) -> None:
        """Show the cog version."""
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"Author: {self.__author__}\nVersion: {self.__version__}", lang="yaml"
            ),
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(style=discord.ButtonStyle.gray, label="Docs", url=self.__docs__)
        )
        await ctx.send(embed=embed, view=view)

    @autopublisher.command()
    async def reset(self, ctx: commands.Context) -> None:
        """Reset guild-specific AutoPublisher settings."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Reset AutoPublisher settings?", view=view)
        await view.wait()
        await (
            ctx.send("Settings reset.")
            if view.result and await self.config.guild(ctx.guild).clear()
            else ctx.send("Reset cancelled.")
        )

    @commands.is_owner()
    @autopublisher.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def resetcount(self, ctx: commands.Context) -> None:
        """Reset global published message counts."""
        embed = discord.Embed(
            title="Reset Count",
            description="Reset all published message counts?\n\n**Warning:** This is irreversible without backups.",
            color=await ctx.embed_color(),
        )
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self.config.clear_all_globals()
            await self.config.register_global(
                **self.config.defaults["GLOBAL"]
            )  # Re-register defaults
            await ctx.send("Counts reset.")
        else:
            await ctx.send("Reset cancelled.")
