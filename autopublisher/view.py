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
        await interaction.response.send_message(
            ":white_check_mark: Ignored discord news channel(s) removed!", ephemeral=True
        )
        self.ignored_channels = []
        self.select.default_values = []


class StatsView(discord.ui.LayoutView):
    """View for displaying AutoPublisher statistics."""

    def __init__(self, cog: commands.Cog) -> None:
        super().__init__(timeout=180)
        self.cog: commands.Cog = cog
        self.ctx: commands.Context | None = None
        self.message: discord.Message | None = None
        self.owner_tz: pytz.timezone | None = None
        self.refresh_button = discord.ui.Button(
            label="Refresh", style=discord.ButtonStyle.green, emoji="🔄"
        )
        self.refresh_button.callback = self.refresh_callback
        self.close_button = discord.ui.Button(
            label="Close", style=discord.ButtonStyle.red, emoji="✖️"
        )
        self.close_button.callback = self.close_callback
        self._build_container("Never")

    def _build_container(self, last_published: str) -> None:
        """Build or rebuild the container with current components."""
        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(discord.ui.TextDisplay("AutoPublisher Statistics"))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(last_published))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.ActionRow(self.refresh_button, self.close_button))
        self.clear_items()
        self.add_item(self.container)

    async def start(self, ctx: commands.Context) -> None:
        """Initialize the view with stats data."""
        self.ctx = ctx
        self.owner_tz = await get_owner_timezone(self.cog.config)
        await self._update_view()

    async def _update_view(self) -> None:
        """Update the view with current stats."""
        data = await self.cog.config.all()
        table_data = [
            ["Weekly", humanize_number(data["published_weekly_count"])],
            ["Monthly", humanize_number(data["published_monthly_count"])],
            ["Yearly", humanize_number(data["published_yearly_count"])],
            ["Total Published", humanize_number(data["published_count"])],
        ]
        table = tabulate(table_data, headers=["Period", "Count"], tablefmt="simple")
        boxed_table = box(table, lang="prolog")
        last_published = "Last Published: Never"
        last_count_time = data.get("last_count_time")
        if last_count_time:
            try:
                last_count_dt = datetime.fromisoformat(last_count_time)
                last_count_dt = last_count_dt.replace(tzinfo=pytz.UTC).astimezone(self.owner_tz)
                last_published = f"Last Published: {discord.utils.format_dt(last_count_dt, 'R')}"
            except ValueError:
                last_published = "Last Published: Invalid timestamp"

        next_weekly_ts, next_monthly_ts, next_yearly_ts = get_next_reset_times(self.owner_tz)
        reset_info = (
            f"Timezone: `{self.owner_tz.zone}`\n"
            f"{last_published}\n"
            f"Next Weekly Reset: <t:{next_weekly_ts}:R> (<t:{next_weekly_ts}:f>)\n"
            f"Next Monthly Reset: <t:{next_monthly_ts}:R> (<t:{next_monthly_ts}:f>)\n"
            f"Next Yearly Reset: <t:{next_yearly_ts}:R> (<t:{next_yearly_ts}:f>)"
        )
        title = "Autopublisher Stats"
        title_info = f"{header(title, 'medium')}"

        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(discord.ui.TextDisplay(title_info))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(boxed_table))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(reset_info))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.ActionRow(self.refresh_button, self.close_button))
        self.clear_items()
        self.add_item(self.container)

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
        self.refresh_button.disabled = True
        self.close_button.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(f"Failed to update view on timeout: {e}")

    async def refresh_callback(self, interaction: discord.Interaction) -> None:
        """Refresh the stats display."""
        await interaction.response.defer()
        await self._update_view()
        await self.message.edit(view=self)
        await interaction.followup.send("Stats refreshed!", ephemeral=True)

    async def close_callback(self, interaction: discord.Interaction) -> None:
        """Close the view."""
        self.refresh_button.disabled = True
        self.close_button.disabled = True
        await interaction.response.defer()
        await self.message.edit(view=self)
        await interaction.followup.send(
            "Stats view closed. Redo the command to refresh again.", ephemeral=True
        )
        self.stop()
