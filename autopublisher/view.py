"""
MIT License

Copyright (c) 2024-present AAA3A
Copyright (c) 2022-2024 ltzmax

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

from datetime import datetime

import discord
import pytz
from red_commons.logging import getLogger
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, header, humanize_number
from tabulate import tabulate

from .utils import get_next_reset_times, get_owner_timezone

log = getLogger("red.maxcogs.autopublisher.view")


class IgnoredNewsChannelsView(discord.ui.LayoutView):
    """View for selecting ignored news channels."""

    def __init__(self, cog: commands.Cog) -> None:
        super().__init__(timeout=180)
        self.cog: commands.Cog = cog
        self.ctx: commands.Context | None = None
        self.message: discord.Message | None = None
        self.ignored_channels: list[discord.TextChannel] = []

        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(
            discord.ui.TextDisplay(
                "Select news channels to ignore/unignore.\n"
                "Use the Confirm button to save changes.\n"
                "Alternatively, use the command with `[p]autopublisher channel #channel(s)` to manage manually."
            )
        )
        self.container.add_item(discord.ui.Separator())
        self.select = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.news],
            placeholder="Select the news channels to ignore.",
            min_values=0,
            max_values=25,
        )
        self.select.callback = self.select_callback
        self.container.add_item(discord.ui.ActionRow(self.select))
        self.container.add_item(discord.ui.Separator())
        self.confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.success)
        self.confirm_button.callback = self.save_callback
        self.unignore_button = discord.ui.Button(
            label="Unignore", style=discord.ButtonStyle.danger
        )
        self.unignore_button.callback = self.unignore_callback
        self.container.add_item(discord.ui.ActionRow(self.confirm_button, self.unignore_button))
        self.add_item(self.container)

    async def start(self, ctx: commands.Context) -> None:
        """Start the view with default ignored channels."""
        self.ctx: commands.Context = ctx
        ignored_ids = await self.cog.config.guild(self.ctx.guild).ignored_channels()
        self.ignored_channels = [
            channel
            for channel_id in ignored_ids
            if (channel := self.ctx.guild.get_channel(channel_id))
        ]
        default_values = [
            discord.SelectDefaultValue(type="channel", id=channel.id)
            for channel in self.ignored_channels
        ]
        self.select.default_values = default_values

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is allowed to interact."""
        if interaction.user.id not in [self.ctx.author.id] + list(self.ctx.bot.owner_ids):
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.select.disabled = True
        self.confirm_button.disabled = True
        self.unignore_button.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(e)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Callback for channel selection."""
        await interaction.response.defer(ephemeral=True)
        self.ignored_channels = self.select.values
        await interaction.followup.send(
            "Click Confirm to save the selected discord news channel(s).",
            ephemeral=True,
        )

    async def save_callback(self, interaction: discord.Interaction) -> None:
        """Save the ignored channels."""
        new_ignored_channels = [channel.id for channel in self.ignored_channels]
        current_ignored = await self.cog.config.guild(self.ctx.guild).ignored_channels()

        if sorted(new_ignored_channels) == sorted(current_ignored):
            return await interaction.response.send_message(
                "No changes were made.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set(new_ignored_channels)
        self.select.default_values = [
            discord.SelectDefaultValue(type="channel", id=channel.id)
            for channel in self.ignored_channels
        ]
        await interaction.response.send_message(
            ":white_check_mark: Ignored discord news channel(s) saved!", ephemeral=True
        )

    async def unignore_callback(self, interaction: discord.Interaction) -> None:
        """Unignore all channels."""
        current_ignored = await self.cog.config.guild(self.ctx.guild).ignored_channels()
        if not current_ignored:
            return await interaction.response.send_message(
                "No discord news channel(s) are currently ignored.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set([])
        self.ignored_channels = []
        self.select.default_values = []
        await interaction.response.send_message(
            ":white_check_mark: Ignored discord news channel(s) removed!", ephemeral=True
        )
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(f"Failed to update view after unignore: {e}")


def _build_metrics_panel(
    weekly: int,
    monthly: int,
    yearly: int,
    total: int,
    owner_tz: "pytz.timezone",
    last_count_time: str | None,
    next_weekly_ts: int,
    next_monthly_ts: int,
    next_yearly_ts: int,
) -> tuple[str, str]:
    """
    autopublisher stats bar chart and rates panel builder.
    """
    BAR_WIDTH = 20
    FILL = "●"
    EMPTY = "○"

    def bar(val: int) -> str:
        filled = min(round(val / 60), BAR_WIDTH)
        return FILL * filled + EMPTY * (BAR_WIDTH - filled)

    def rate(val: int, days: int) -> str:
        return f"{val / days:.1f}" if days > 0 else "N/A"

    import calendar
    from datetime import datetime
    from datetime import timezone as dt_timezone

    now = datetime.now(owner_tz)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    day_of_year = now.timetuple().tm_yday
    week_day = now.weekday() + 1

    weekly_avg = rate(weekly, 7)
    monthly_avg = rate(monthly, days_in_month)
    yearly_avg = rate(yearly, day_of_year)
    daily_rate = yearly / day_of_year if day_of_year > 0 and yearly > 0 else 0
    yearly_projected_max = max(daily_rate * 365, 1)

    def yearly_bar(val: int) -> str:
        filled = min(round((val / yearly_projected_max) * BAR_WIDTH), BAR_WIDTH)
        return FILL * filled + EMPTY * (BAR_WIDTH - filled)

    def total_bar(val: int) -> str:
        filled = min(round((val / 100_000) * BAR_WIDTH), BAR_WIDTH)
        return FILL * filled + EMPTY * (BAR_WIDTH - filled)

    pct_weekly_of_monthly = f"{(weekly / monthly * 100):.1f}%" if monthly else "N/A"
    pct_yearly_of_total = f"{(yearly  / total   * 100):.1f}%" if total else "N/A"

    last_pub = "Never"
    if last_count_time:
        try:
            dt = datetime.fromisoformat(last_count_time)
            dt = dt.replace(tzinfo=dt_timezone.utc)
            ts = int(dt.timestamp())
            last_pub = f"<t:{ts}:R> (<t:{ts}:f>)"
        except ValueError:
            last_pub = "Invalid timestamp"

    W = 44  # panel inner width

    def row(label: str, val: int) -> str:
        label_col = f"{label:<9}"
        count_col = f"{humanize_number(val):>7}"
        return f"{label_col} {bar(val)} {count_col}"

    def kv(label: str, value: str) -> str:
        return f"{label:<26}  {value}"

    chart_lines = [
        "AUTOPUBLISHER STATS ".center(W),
        "",
        row("Weekly", weekly),
        row("Monthly", monthly),
        f"{'Yearly':<9} {yearly_bar(yearly)} {humanize_number(yearly):>7}",
        f"{'Total':<9} {total_bar(total)} {humanize_number(total):>7}",
        "",
        "RATES  (derived from current period totals)",
        kv("Weekly avg / day", weekly_avg),
        kv("Monthly avg / day", monthly_avg),
        kv("Yearly avg / day", yearly_avg),
        kv("Weekly % of monthly", pct_weekly_of_monthly),
        kv("Yearly % of total", pct_yearly_of_total),
    ]
    chart_str = "\n".join(chart_lines)
    schedule_lines = [
        "**🗓️  Reset Schedule**",
        f"Timezone `{owner_tz.zone}`",
        f"Last published {last_pub}",
        f"Next weekly reset <t:{next_weekly_ts}:R> (<t:{next_weekly_ts}:f>)",
        f"Next monthly reset <t:{next_monthly_ts}:R> (<t:{next_monthly_ts}:f>)",
        f"Next yearly reset <t:{next_yearly_ts}:R> (<t:{next_yearly_ts}:f>)",
    ]
    schedule_str = "\n".join(schedule_lines)
    return chart_str, schedule_str


class MetricsView(discord.ui.LayoutView):
    """Metrics view for AutoPublisher."""

    def __init__(self, cog: commands.Cog) -> None:
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx: commands.Context | None = None
        self.message: discord.Message | None = None
        self.owner_tz: "pytz.timezone | None" = None

        self.refresh_button = discord.ui.Button(
            label="Refresh", style=discord.ButtonStyle.green, emoji="🔄"
        )
        self.refresh_button.callback = self.refresh_callback
        self._build_placeholder()

    def _build_placeholder(self) -> None:
        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(discord.ui.TextDisplay("Loading metrics…"))
        self.container.add_item(discord.ui.ActionRow(self.refresh_button))
        self.clear_items()
        self.add_item(self.container)

    async def start(self, ctx: commands.Context) -> None:
        self.ctx = ctx
        self.owner_tz = await get_owner_timezone(self.cog.config)
        await self._update_view()

    async def _update_view(self) -> None:
        data = await self.cog.config.all()
        weekly = data.get("published_weekly_count", 0)
        monthly = data.get("published_monthly_count", 0)
        yearly = data.get("published_yearly_count", 0)
        total = data.get("published_count", 0)
        last_count_time = data.get("last_count_time")

        next_weekly_ts, next_monthly_ts, next_yearly_ts = get_next_reset_times(self.owner_tz)

        chart_str, schedule_str = _build_metrics_panel(
            weekly,
            monthly,
            yearly,
            total,
            self.owner_tz,
            last_count_time,
            next_weekly_ts,
            next_monthly_ts,
            next_yearly_ts,
        )
        panel_box = box(chart_str, lang="prolog")
        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(discord.ui.TextDisplay(panel_box))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(schedule_str))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.ActionRow(self.refresh_button))
        self.clear_items()
        self.add_item(self.container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id] + list(self.ctx.bot.owner_ids):
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        self.refresh_button.disabled = True
        if self.message is None:
            return
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error("Failed to update metrics view on timeout: %s", e)

    async def refresh_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await self._update_view()
        await self.message.edit(view=self)
        await interaction.followup.send("Stats refreshed!", ephemeral=True)
