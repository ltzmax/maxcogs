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

import contextlib
import datetime

import discord
from red_commons.logging import getLogger

log = getLogger("red.cogs.heist.events")


async def get_event_multiplier(config) -> tuple[int, float | None]:
    """Return (multiplier, ends_at_timestamp) for the active event.

    Returns (1, None) if no event is active or it has expired.
    Auto-clears expired events from config.
    """
    ends_at = await config.event_ends_at()
    if ends_at is None:
        return 1, None
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if now > ends_at:
        await config.event_multiplier.set(1)
        await config.event_ends_at.set(None)
        return 1, None
    return await config.event_multiplier(), ends_at


class _StartEventModal(discord.ui.Modal, title="Start Heist Event"):
    multiplier: discord.ui.TextInput = discord.ui.TextInput(
        label="Multiplier (2–5)",
        placeholder="e.g. 2",
        max_length=1,
        required=True,
    )
    duration: discord.ui.TextInput = discord.ui.TextInput(
        label="Duration (minutes)",
        placeholder="e.g. 60",
        max_length=5,
        required=True,
    )

    def __init__(self, event_view: "EventView"):
        super().__init__()
        self.event_view = event_view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mult = int(self.multiplier.value)
            if not 2 <= mult <= 5:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Multiplier must be an integer between 2 and 5.", ephemeral=True
            )
        try:
            mins = int(self.duration.value)
            if mins < 1:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Duration must be a positive integer (minutes).", ephemeral=True
            )

        ends_at = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=mins)
        ).timestamp()

        await self.event_view.cog.config.event_multiplier.set(mult)
        await self.event_view.cog.config.event_ends_at.set(ends_at)

        end_ts = int(ends_at)
        await interaction.response.send_message(
            f"🎉 **{mult}x reward event** started! Ends <t:{end_ts}:R> (<t:{end_ts}:f>).",
            ephemeral=True,
        )
        self.event_view._build_content()
        with contextlib.suppress(discord.HTTPException):
            await self.event_view.message.edit(view=self.event_view)


class _StartEventBtn(discord.ui.Button):
    def __init__(self, event_view: "EventView", disabled: bool = False):
        super().__init__(
            label="Start Event",
            style=discord.ButtonStyle.success,
            emoji="🎉",
            disabled=disabled,
        )
        self.event_view = event_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(_StartEventModal(self.event_view))


class _StopEventBtn(discord.ui.Button):
    def __init__(self, event_view: "EventView", disabled: bool = False):
        super().__init__(
            label="Stop Event",
            style=discord.ButtonStyle.danger,
            emoji="🛑",
            disabled=disabled,
        )
        self.event_view = event_view

    async def callback(self, interaction: discord.Interaction):
        await self.event_view.cog.config.event_multiplier.set(1)
        await self.event_view.cog.config.event_ends_at.set(None)
        await interaction.response.send_message("Event stopped.", ephemeral=True)
        self.event_view._build_content()
        with contextlib.suppress(discord.HTTPException):
            await self.event_view.message.edit(view=self.event_view)


class EventView(discord.ui.LayoutView):
    """Owner panel for managing heist reward events."""

    def __init__(self, cog, ctx):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self._build_content()

    def _build_content(self, disabled: bool = False):
        self.clear_items()
        mult = self._cached_mult
        ends_at = self._cached_ends_at

        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        active = ends_at is not None and mult > 1 and now < ends_at

        if active:
            end_ts = int(ends_at)
            status = (
                f"## 🎉 Event Active - {mult}x Rewards\n"
                f"Ends <t:{end_ts}:R> (<t:{end_ts}:f>)\n\n"
                f"-# All heist cash rewards are multiplied by {mult}."
            )
        else:
            status = (
                "## 🎉 Heist Events\n"
                "No event currently active.\n\n"
                "-# Start an event to multiply all cash rewards for a set duration."
            )

        action_row = discord.ui.ActionRow(
            _StartEventBtn(self, disabled=disabled or active),
            _StopEventBtn(self, disabled=disabled or not active),
        )
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(status),
                discord.ui.Separator(),
                action_row,
            )
        )

    @classmethod
    async def create(cls, cog, ctx) -> "EventView":
        view = cls.__new__(cls)
        discord.ui.LayoutView.__init__(view, timeout=180)
        view.cog = cog
        view.ctx = ctx
        view.message = None
        mult, ends_at = await get_event_multiplier(cog.config)
        view._cached_mult = mult
        view._cached_ends_at = ends_at
        view._build_content()
        return view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.cog.bot.owner_ids:
            await interaction.response.send_message(
                "You are not authorized to use this.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)
