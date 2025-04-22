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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate

from .view import IgnoredNewsChannelsView


class AutoPublisher(commands.Cog):
    """Automatically publish messages in news channels."""

    __version__: Final[str] = "2.9.0"
    __author__: Final[str] = "MAX, AAA3A"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/autopublisher.html"

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
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.scheduler = AsyncIOScheduler()
        self._schedule_resets()
        self.logger = getLogger("red.maxcogs.autopublisher")

    def _schedule_resets(self) -> None:
        """Schedule periodic count resets."""
        self.scheduler.add_job(
            self.reset_count, "cron", day_of_week="sun", hour=0, minute=0, args=["weekly"]
        )
        self.scheduler.add_job(
            self.reset_count, CronTrigger(day=1, hour=0, minute=0), args=["monthly"]
        )
        self.scheduler.add_job(
            self.reset_count, "cron", month=1, day=1, hour=0, minute=0, args=["yearly"]
        )
        self.scheduler.start()
        # self.logger.info("Scheduler started for weekly, monthly, and yearly resets.")

    def cog_unload(self) -> None:
        """Clean up scheduler on cog unload."""
        self.scheduler.shutdown()
        self.logger.debug("Scheduler shut down.")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Format help with cog metadata."""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nVersion: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    async def reset_count(self, period: Literal["weekly", "monthly", "yearly"]) -> None:
        """Reset the specified count period."""
        async with self.config.all() as data:
            if period == "weekly":
                data["published_weekly_count"] = 0
                self.logger.verbose("Weekly count reset.")
            elif period == "monthly" and datetime.now().day == 1:
                data["published_monthly_count"] = 0
                self.logger.verbose("Monthly count reset.")
            elif period == "yearly":
                data["published_yearly_count"] = 0
                self.logger.verbose("Yearly count reset.")

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
                self.logger.warning(
                    f"Disabled AutoPublisher in {message.guild.name} (no NEWS feature)."
                )
            return

        try:
            await asyncio.sleep(0.5)
            await asyncio.wait_for(message.publish(), timeout=60)
            await self.increment_published_count()
        except (discord.HTTPException, discord.Forbidden, asyncio.TimeoutError) as e:
            self.logger.error(
                f"Failed to publish message in {message.channel.id}: {e}", exc_info=True
            )

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(aliases=["aph", "autopub"])
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher settings."""

    @commands.is_owner()
    @autopublisher.command(name="stats")
    async def stats(self, ctx: commands.Context) -> None:
        """Show statistics for published messages."""
        data = await self.config.all()
        last_count_time = data.get("last_count_time")
        last_published = (
            discord.utils.format_dt(datetime.fromisoformat(last_count_time), "R")
            if last_count_time
            else "Never"
        )

        table_data = [
            ["Weekly", humanize_number(data["published_weekly_count"])],
            ["Monthly", humanize_number(data["published_monthly_count"])],
            ["Yearly", humanize_number(data["published_yearly_count"])],
            ["Total Published", humanize_number(data["published_count"])],
        ]
        table = tabulate(table_data, headers=["Period", "Count"], tablefmt="simple")

        now = datetime.now()
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 0:
            days_until_sunday = 7
        next_weekly = int(
            (
                now.replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=days_until_sunday)
            ).timestamp()
        )

        next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=32
        )
        next_month = next_month.replace(day=1)
        next_monthly = int(next_month.timestamp())
        next_year = now.year + 1 if now.month > 1 or (now.month == 1 and now.day > 1) else now.year
        next_yearly = int(datetime(next_year, 1, 1).timestamp())

        await ctx.send(
            f"{box(table, lang='prolog')}\n"
            f"Next Weekly Reset: <t:{next_weekly}:R> (<t:{next_weekly}:f>)\n"
            f"Next Monthly Reset: <t:{next_monthly}:R> (<t:{next_monthly}:f>)\n"
            f"Next Yearly Reset: <t:{next_yearly}:R> (<t:{next_yearly}:f>)\n"
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
