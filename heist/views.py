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
import contextlib
import datetime

import discord
from red_commons.logging import getLogger
from redbot.core import bank, commands

from .handlers import schedule_resolve
from .leveling import get_level
from .meta import _PARAM_META
from .utils import HEISTS, ITEMS, RECIPES, fmt


log = getLogger("red.cogs.heist.views")
CREW_SIZE = 4
LOBBY_TIMEOUT = 180  # 3 minutes
HEISTS_PER_PAGE = 7
_ALL_SHOP_PAGES = [
    ("🛡️ Shields", "shield"),
    ("🔧 Tools", "tool"),
]


def _risk_indicator(police_chance: float, risk: float) -> str:
    combined = police_chance + risk
    if combined < 0.15:
        return "🟢 Low"
    elif combined < 0.35:
        return "🟡 Medium"
    elif combined < 0.55:
        return "🟠 High"
    return "🔴 Extreme"


def _cooldown_display(td: datetime.timedelta) -> str:
    secs = td.total_seconds()
    if secs < 3600:
        return f"{int(secs // 60)}m"
    return f"{secs / 3600:.1f}h"


class _HeistNavBtn(discord.ui.Button):
    def __init__(self, direction: str, view: "HeistSelectionView", disabled: bool = False):
        match direction:
            case "prev":
                label, emoji = "Previous", "◀️"
            case "next":
                label, emoji = "Next", "▶️"
        super().__init__(
            label=label, emoji=emoji, style=discord.ButtonStyle.secondary, disabled=disabled
        )
        self.direction = direction
        self.heist_view = view

    async def callback(self, interaction: discord.Interaction):
        match self.direction:
            case "prev" if self.heist_view.page > 0:
                self.heist_view.page -= 1
            case "next" if self.heist_view.page < self.heist_view.total_pages - 1:
                self.heist_view.page += 1
        self.heist_view._build_content()
        await interaction.response.edit_message(view=self.heist_view)


class _HeistSelect(discord.ui.Select):
    def __init__(self, cog, options: list):
        self.cog = cog
        super().__init__(placeholder="Choose your target...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        heist_type = self.values[0]
        data = await self.cog.get_heist_settings(heist_type)
        user = interaction.user

        if await self.cog._has_active_heist(user, interaction.channel.id):
            return await interaction.followup.send(
                "You have an active heist ongoing. Wait for it to finish.", ephemeral=True
            )

        now = datetime.datetime.now(datetime.timezone.utc)
        cooldowns = await self.cog.config.user(user).heist_cooldowns()
        last_timestamp = cooldowns.get(heist_type)
        if last_timestamp:
            last_time = datetime.datetime.fromtimestamp(last_timestamp, tz=datetime.timezone.utc)
            if now - last_time < data["cooldown"]:
                remaining = data["cooldown"] - (now - last_time)
                end_timestamp = int((now + remaining).timestamp())
                return await interaction.followup.send(
                    f"On cooldown! Ready <t:{end_timestamp}:R>.", ephemeral=True
                )

        balance = await bank.get_balance(user)
        currency_name = await bank.get_currency_name(interaction.guild)
        max_loss = data["max_loss"]
        tax_agreed = False

        if balance < max_loss:
            view = _ConfirmDebtView(user, timeout=60)
            tax = int(max_loss * 0.2)
            total_debt = max_loss + tax
            prompt = await interaction.followup.send(
                f"⚠️ Your balance ({balance:,} {currency_name}) is too low to cover a potential "
                f"loss of up to {max_loss:,} {currency_name}.\n"
                f"If you fail, you will owe up to **{total_debt:,}** {currency_name} (including 20% tax).\n"
                f"-# The final amount is calculated after the heist.",
                view=view,
                ephemeral=True,
            )
            view.message = prompt
            await view.wait()
            if not view.confirmed:
                return await prompt.edit(content="Heist cancelled.", view=None)
            tax_agreed = True

        cooldowns[heist_type] = now.timestamp()
        await self.cog.config.user(user).heist_cooldowns.set(cooldowns)
        end_time = now + data["duration"]
        end_timestamp = int(end_time.timestamp())
        await self.cog.config.user(user).active_heist.set(
            {
                "type": heist_type,
                "end_time": end_time.timestamp(),
                "channel_id": interaction.channel.id,
                "tax_agreed": tax_agreed,
            }
        )

        started_view = _HeistStartedView(data, heist_type, end_timestamp)
        await interaction.followup.send(view=started_view)

        if user.id in self.cog.pending_tasks:
            log.warning("Duplicate heist task for user %s, cancelling old", user.id)
            self.cog.pending_tasks[user.id].cancel()
        task = asyncio.create_task(
            schedule_resolve(
                self.cog,
                user.id,
                data["duration"].total_seconds(),
                heist_type,
                interaction.channel,
            )
        )
        self.cog.pending_tasks[user.id] = task

        with contextlib.suppress(discord.HTTPException):
            for item in self.view.children:
                item.disabled = True
            await interaction.message.edit(view=self.view)


class _HeistStartedView(discord.ui.LayoutView):
    def __init__(self, data: dict, heist_type: str, end_timestamp: int):
        super().__init__(timeout=None)
        body = (
            f"## {data['emoji']} {fmt(heist_type)} - In Progress\n"
            f"You're in. No turning back now.\n\n"
            f"**Results:** <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)\n"
            f"**Success chance:** {data['min_success']}–{data['max_success']}%\n"
            f"**Potential loss:** {data['min_loss']:,}–{data['max_loss']:,}"
        )
        self.add_item(discord.ui.Container(discord.ui.TextDisplay(body)))


class HeistSelectionView(discord.ui.LayoutView):
    def __init__(
        self,
        cog,
        ctx: commands.Context,
        heist_settings: dict,
        currency_name: str,
        player_level: int = 1,
    ):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self.currency_name = currency_name
        self.player_level = player_level
        self.all_heists = list(heist_settings.items())
        self.total_pages = max(1, -(-len(self.all_heists) // HEISTS_PER_PAGE))
        self.page = 0
        self._build_content()

    def _build_content(self, disabled: bool = False):
        self.clear_items()
        start = self.page * HEISTS_PER_PAGE
        page_heists = self.all_heists[start : start + HEISTS_PER_PAGE]

        from .leveling import level_success_bonus

        lv_bonus = level_success_bonus(self.player_level)
        lv_str = ( # noqs: F841
            f"+{lv_bonus * 100:.0f}% from Lv.{self.player_level}"
            if lv_bonus > 0
            else f"Lv.{self.player_level}"
        )

        lines = [
            f"## 🎯 Choose Your Heist - Page {self.page + 1}/{self.total_pages}\n"
        ]
        for name, data in page_heists:
            loot_item = name if name in ITEMS and ITEMS[name][1].get("type") == "loot" else None
            if loot_item:
                reward_str = f"{ITEMS[loot_item][1]['min_sell']:,}–{ITEMS[loot_item][1]['max_sell']:,} {self.currency_name} (loot)"
            else:
                reward_str = f"{data['min_reward']:,}–{data['max_reward']:,} {self.currency_name}"
            risk_label = _risk_indicator(data["police_chance"], data["risk"])
            cooldown_str = _cooldown_display(data["cooldown"])
            duration_min = int(data["duration"].total_seconds() // 60)
            eff_min = min(data["min_success"] + int(lv_bonus * 100), 100)
            eff_max = min(data["max_success"] + int(lv_bonus * 100), 100)
            lines.append(
                f"**{data['emoji']} {fmt(name)}** - {risk_label}\n"
                f"-# Reward: {reward_str} · Success: {eff_min}–{eff_max}%"
                f" · Cooldown: {cooldown_str} · Duration: {duration_min}m\n"
            )

        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=data["emoji"],
                description=_risk_indicator(data["police_chance"], data["risk"]),
            )
            for name, data in page_heists
        ]
        select = _HeistSelect(self.cog, options)
        select.disabled = disabled
        select_row = discord.ui.ActionRow(select)

        nav_row = discord.ui.ActionRow()
        if self.page > 0:
            nav_row.add_item(_HeistNavBtn("prev", self, disabled=disabled))
        if self.page < self.total_pages - 1:
            nav_row.add_item(_HeistNavBtn("next", self, disabled=disabled))

        components: list = [
            discord.ui.TextDisplay("\n".join(lines)),
            discord.ui.Separator(),
            select_row,
        ]
        if nav_row.children:
            components.append(nav_row)

        self.add_item(discord.ui.Container(*components))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id, *list(self.cog.bot.owner_ids)]:
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)


class _ShopNavBtn(discord.ui.Button):
    def __init__(self, direction: str, shop_view: "ShopView", disabled: bool = False):
        match direction:
            case "prev":
                label, emoji = "Previous", "◀️"
            case "next":
                label, emoji = "Next", "▶️"
        super().__init__(
            label=label, emoji=emoji, style=discord.ButtonStyle.secondary, disabled=disabled
        )
        self.direction = direction
        self.shop_view = shop_view

    async def callback(self, interaction: discord.Interaction):
        match self.direction:
            case "prev" if self.shop_view.page > 0:
                self.shop_view.page -= 1
            case "next" if self.shop_view.page < len(self.shop_view.pages) - 1:
                self.shop_view.page += 1
        # Refresh costs from config so custom prices are always current
        self.shop_view.costs = {
            name: await self.shop_view.cog.get_item_cost(name)
            for name, (_, data) in ITEMS.items()
            if "cost" in data
        }
        self.shop_view._build_content()
        await interaction.response.edit_message(view=self.shop_view)


class _ShopSelect(discord.ui.Select):
    def __init__(self, cog, options: list):
        self.cog = cog
        super().__init__(placeholder="Select an item to purchase...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        item_type = self.values[0]
        emoji, _data = ITEMS[item_type]
        cost = await self.cog.get_item_cost(item_type)
        balance = await bank.get_balance(interaction.user)
        currency_name = await bank.get_currency_name(interaction.guild)

        if balance < cost:
            return await interaction.response.send_message(
                f"Not enough funds. Need **{cost:,}** {currency_name}, you have **{balance:,}**.",
                ephemeral=True,
            )

        await bank.withdraw_credits(interaction.user, cost)
        inventory = await self.cog.config.user(interaction.user).inventory()
        inventory[item_type] = inventory.get(item_type, 0) + 1
        await self.cog.config.user(interaction.user).inventory.set(inventory)

        await interaction.response.send_message(
            f"Purchased {emoji} **{fmt(item_type)}** for **{cost:,}** {currency_name}. Added to inventory.",
            ephemeral=True,
        )
        with contextlib.suppress(discord.HTTPException):
            for item in self.view.children:
                item.disabled = True
            await interaction.message.edit(view=self.view)


class ShopView(discord.ui.LayoutView):
    def __init__(self, cog, ctx: commands.Context, currency_name: str, costs: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.currency_name = currency_name
        self.costs = costs  # {item_name: resolved_cost}
        self.message = None
        self.pages = [
            (label, itype)
            for label, itype in _ALL_SHOP_PAGES
            if any(data["type"] == itype and "cost" in data for _, data in ITEMS.values())
        ]
        self.page = 0
        self._build_content()

    def _build_content(self, disabled: bool = False):
        self.clear_items()
        section_label, item_type = self.pages[self.page]
        total = len(self.pages)

        items = [
            (name, emoji, data)
            for name, (emoji, data) in ITEMS.items()
            if data["type"] == item_type and "cost" in data
        ]

        lines = [f"## 🛒 Heist Shop - {section_label}  ({self.page + 1}/{total})\n"]
        for name, emoji, data in items:
            cost = self.costs.get(name, data.get("cost", 0))
            line = f"**{emoji} {fmt(name)}** - {cost:,} {self.currency_name}\n"
            if item_type == "shield":
                line += f"-# Reduces loss by {data['reduction'] * 100:.1f}% (single use)\n"
            elif item_type == "tool":
                line += f"-# +{data['boost'] * 100:.0f}% success on {fmt(data['for_heist'])} (single use)\n"
            elif item_type == "consumable":
                line += f"-# Reduces risk by {data['risk_reduction'] * 100:.0f}% (single use)\n"
            lines.append(line)

        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=emoji,
                description=(
                    f"Reduces loss by {data['reduction'] * 100:.1f}%"
                    if item_type == "shield"
                    else (
                        f"+{data['boost'] * 100:.0f}% for {fmt(data['for_heist'])}"
                        if item_type == "tool"
                        else f"Reduces risk by {data['risk_reduction'] * 100:.0f}%"
                    )
                ),
            )
            for name, emoji, data in items
        ]
        select = _ShopSelect(self.cog, options)
        select.disabled = disabled

        nav_row = discord.ui.ActionRow()
        if self.page > 0:
            nav_row.add_item(_ShopNavBtn("prev", self, disabled=disabled))
        if self.page < len(self.pages) - 1:
            nav_row.add_item(_ShopNavBtn("next", self, disabled=disabled))

        components: list = [
            discord.ui.TextDisplay("".join(lines)),
            discord.ui.Separator(),
            discord.ui.ActionRow(select),
        ]
        if nav_row.children:
            components.append(nav_row)

        self.add_item(discord.ui.Container(*components))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id, *list(self.cog.bot.owner_ids)]:
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)


class _ConfirmYesBtn(discord.ui.Button):
    def __init__(self, cv: "ConfirmLayoutView"):
        super().__init__(label="Yes", style=discord.ButtonStyle.success)
        self.cv = cv

    async def callback(self, interaction: discord.Interaction):
        self.cv.confirmed = True
        self.cv._disable()
        await interaction.response.edit_message(view=self.cv)
        self.cv.stop()


class _ConfirmNoBtn(discord.ui.Button):
    def __init__(self, cv: "ConfirmLayoutView"):
        super().__init__(label="No", style=discord.ButtonStyle.danger)
        self.cv = cv

    async def callback(self, interaction: discord.Interaction):
        self.cv.confirmed = False
        self.cv._disable()
        await interaction.response.edit_message(view=self.cv)
        self.cv.stop()


class ConfirmLayoutView(discord.ui.LayoutView):
    """Components v2 confirm view."""

    def __init__(self, user: discord.User, body_text: str, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.user = user
        self.confirmed: bool | None = None
        self.message = None
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(body_text),
                discord.ui.Separator(),
                discord.ui.ActionRow(_ConfirmYesBtn(self), _ConfirmNoBtn(self)),
            )
        )

    def _disable(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        self.confirmed = None
        self._disable()
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You are not the author of this.", ephemeral=True
            )
            return False
        return True


class _ConfirmDebtView(discord.ui.View):
    """Lightweight confirm used inside ephemeral followup for debt warning."""

    def __init__(self, user: discord.User, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.user = user
        self.confirmed: bool | None = None
        self.message = None

    @discord.ui.button(label="Proceed anyway", style=discord.ButtonStyle.danger)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.confirmed = None
        for item in self.children:
            item.disabled = True
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You are not the author of this.", ephemeral=True
            )
            return False
        return True


class _HeistConfigSelect(discord.ui.Select):
    def __init__(self, config_view: "HeistConfigView", disabled: bool = False):
        self.config_view = config_view
        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=data.get("emoji", "❓"),
                default=(config_view.selected_heist == name),
            )
            for name, data in HEISTS.items()
        ]
        super().__init__(
            placeholder="Select a heist...",
            options=options[:25],
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        self.config_view.selected_heist = self.values[0]
        self.config_view._build_content()
        await interaction.response.edit_message(view=self.config_view)


class _ParamSelect(discord.ui.Select):
    def __init__(self, config_view: "HeistConfigView", disabled: bool = False):
        self.config_view = config_view
        options = [
            discord.SelectOption(
                label=label,
                value=key,
                description=hint,
                default=(config_view.selected_param == key),
            )
            for key, (label, hint) in _PARAM_META.items()
        ]
        super().__init__(
            placeholder="Select a parameter...",
            options=options,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        self.config_view.selected_param = self.values[0]
        self.config_view._build_content()
        await interaction.response.edit_message(view=self.config_view)


class _SetValueBtn(discord.ui.Button):
    def __init__(self, config_view: "HeistConfigView", disabled: bool = False):
        ready = config_view.selected_heist and config_view.selected_param
        super().__init__(
            label="Set Value",
            style=discord.ButtonStyle.primary,
            emoji="✏️",
            disabled=disabled or not ready,
        )
        self.config_view = config_view

    async def callback(self, interaction: discord.Interaction):
        heist = self.config_view.selected_heist
        param = self.config_view.selected_param
        current = await self.config_view.cog.get_heist_settings(heist)
        raw = current.get(param)
        # Display friendly current value
        if param in ("risk", "police_chance"):
            current_str = f"{raw * 100:.1f}"
        elif param in ("cooldown", "duration", "jail_time"):
            current_str = str(int(raw.total_seconds()))
        else:
            current_str = str(raw)
        await interaction.response.send_modal(
            _HeistValueModal(self.config_view.cog, heist, param, current_str)
        )


class _HeistValueModal(discord.ui.Modal):
    value: discord.ui.TextInput = discord.ui.TextInput(
        label="New Value",
        placeholder="Enter a number",
        max_length=12,
    )

    def __init__(self, cog, heist_type: str, param: str, current_str: str):
        label, hint = _PARAM_META[param]
        super().__init__(title=f"{fmt(heist_type)} - {label}")
        self.cog = cog
        self.heist_type = heist_type
        self.param = param
        self.value.placeholder = f"Current: {current_str} ({hint})"

    async def on_submit(self, interaction: discord.Interaction):
        param = self.param
        heist_type = self.heist_type
        try:
            raw = float(self.value.value)
        except ValueError:
            return await interaction.response.send_message(
                "That must be a member.", ephemeral=True
            )

        current_settings = await self.cog.config.heist_settings.get_raw(heist_type, default={})
        default_settings = HEISTS.get(heist_type, {})

        if param in ("risk", "police_chance"):
            v = raw / 100.0
            if not 0 <= v <= 1.0:
                return await interaction.response.send_message(
                    f"{_PARAM_META[param][0]} must be between 0 and 100.", ephemeral=True
                )
        elif param in ("min_success", "max_success"):
            v = int(raw)
            if not 0 <= v <= 100:
                return await interaction.response.send_message(
                    f"{_PARAM_META[param][0]} must be between 0 and 100.", ephemeral=True
                )
        else:
            v = int(raw)
            if v < 0:
                return await interaction.response.send_message(
                    f"{_PARAM_META[param][0]} cannot be negative.", ephemeral=True
                )
            if param in ("cooldown", "jail_time") and v < 60:
                return await interaction.response.send_message(
                    f"{_PARAM_META[param][0]} must be at least 60 seconds.", ephemeral=True
                )
            if param == "duration" and v < 30:
                return await interaction.response.send_message(
                    "Duration must be at least 30 seconds.", ephemeral=True
                )

        if param == "max_reward":
            min_r = current_settings.get("min_reward", default_settings.get("min_reward", 0))
            if v < min_r:
                return await interaction.response.send_message(
                    f"Max reward cannot be less than min reward ({min_r:,}).", ephemeral=True
                )
        elif param == "min_reward":
            max_r = current_settings.get(
                "max_reward", default_settings.get("max_reward", float("inf"))
            )
            if v > max_r:
                return await interaction.response.send_message(
                    f"Min reward cannot be greater than max reward ({max_r:,}).", ephemeral=True
                )
        if param == "max_success":
            min_s = current_settings.get("min_success", default_settings.get("min_success", 0))
            if v < min_s:
                return await interaction.response.send_message(
                    f"Max success cannot be less than min success ({min_s}).", ephemeral=True
                )
        elif param == "min_success":
            max_s = current_settings.get("max_success", default_settings.get("max_success", 100))
            if v > max_s:
                return await interaction.response.send_message(
                    f"Min success cannot be greater than max success ({max_s}).", ephemeral=True
                )

        async with self.cog.config.heist_settings() as settings:
            settings[heist_type][param] = v

        display = f"{v * 100:.1f}%" if param in ("risk", "police_chance") else f"{v:,}"
        await interaction.response.send_message(
            f"✅ Set **{_PARAM_META[param][0]}** for **{fmt(heist_type)}** to **{display}**.",
            ephemeral=True,
        )


class HeistConfigView(discord.ui.LayoutView):
    """Components v2 heist settings panel."""

    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self.selected_heist: str | None = None
        self.selected_param: str | None = None
        self._build_content()

    def _current_summary(self) -> str:
        if not self.selected_heist:
            return "-# Select a heist and parameter to edit its value."
        data = HEISTS.get(self.selected_heist, {})
        emoji = data.get("emoji", "❓")
        lines = [f"**{emoji} {fmt(self.selected_heist)}**"]
        loot_item = (
            self.selected_heist
            if self.selected_heist in ITEMS and ITEMS[self.selected_heist][1].get("type") == "loot"
            else None
        )
        for key, (label, _) in _PARAM_META.items():
            if key in ("min_reward", "max_reward") and loot_item:
                loot_data = ITEMS[loot_item][1]
                val = f"{loot_data['min_sell']:,}–{loot_data['max_sell']:,} (loot sell)"
                marker = " ◄" if key == self.selected_param else ""
                lines.append(f"-# {label}: {val}{marker}")
                continue
            raw = data.get(key)
            if raw is None:
                continue
            if key in ("risk", "police_chance"):
                val = f"{raw * 100:.0f}%"
            elif hasattr(raw, "total_seconds"):
                val = f"{int(raw.total_seconds())}s"
            else:
                val = f"{raw:,}" if isinstance(raw, int) else str(raw)
            marker = " ◄" if key == self.selected_param else ""
            lines.append(f"-# {label}: {val}{marker}")
        return "\n".join(lines)

    def _build_content(self, disabled: bool = False):
        self.clear_items()

        header = "## ⚙️ Heist Settings"
        summary = self._current_summary()

        heist_row = discord.ui.ActionRow(_HeistConfigSelect(self, disabled=disabled))
        param_row = discord.ui.ActionRow(_ParamSelect(self, disabled=disabled))
        btn_row = discord.ui.ActionRow(_SetValueBtn(self, disabled=disabled))

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{header}\n{summary}"),
                discord.ui.Separator(),
                heist_row,
                param_row,
                btn_row,
            )
        )

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


class _ItemSelect(discord.ui.Select):
    def __init__(self, price_view: "ItemPriceConfigView", page: int, disabled: bool = False):
        self.price_view = price_view
        page_items = price_view.all_items[page * 25 : (page + 1) * 25]
        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=ITEMS[name][0],
                default=(price_view.selected_item == name),
            )
            for name, _ in page_items
        ]
        super().__init__(
            placeholder="Select an item...",
            options=options,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        self.price_view.selected_item = self.values[0]
        self.price_view._build_content()
        await interaction.response.edit_message(view=self.price_view)


class _ItemPageNavBtn(discord.ui.Button):
    def __init__(self, direction: str, price_view: "ItemPriceConfigView", disabled: bool = False):
        match direction:
            case "prev":
                label, emoji = "Previous", "◀️"
            case "next":
                label, emoji = "Next", "▶️"
        super().__init__(
            label=label, emoji=emoji, style=discord.ButtonStyle.secondary, disabled=disabled
        )
        self.direction = direction
        self.price_view = price_view

    async def callback(self, interaction: discord.Interaction):
        match self.direction:
            case "prev" if self.price_view.page > 0:
                self.price_view.page -= 1
            case "next" if self.price_view.page < self.price_view.total_pages - 1:
                self.price_view.page += 1
        self.price_view._build_content()
        await interaction.response.edit_message(view=self.price_view)


class _SetPriceBtn(discord.ui.Button):
    def __init__(self, price_view: "ItemPriceConfigView", disabled: bool = False):
        super().__init__(
            label="Set Price",
            style=discord.ButtonStyle.primary,
            emoji="✏️",
            disabled=disabled or not price_view.selected_item,
        )
        self.price_view = price_view

    async def callback(self, interaction: discord.Interaction):
        item = self.price_view.selected_item
        current = await self.price_view.cog.get_item_cost(item)
        await interaction.response.send_modal(_ItemPriceModal(self.price_view.cog, item, current))


class _ItemPriceModal(discord.ui.Modal):
    new_cost: discord.ui.TextInput = discord.ui.TextInput(
        label="New Cost",
        placeholder="Enter a positive integer",
        max_length=12,
    )

    def __init__(self, cog, item_name: str, current_cost: int):
        super().__init__(title=f"Set Price - {fmt(item_name)}")
        self.cog = cog
        self.item_name = item_name
        self.new_cost.placeholder = f"Current: {current_cost:,}"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.new_cost.value)
            if value < 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Must be a non-negative integer.", ephemeral=True
            )
        async with self.cog.config.item_settings() as settings:
            settings[self.item_name]["cost"] = value
        await interaction.response.send_message(
            f"✅ Set **{fmt(self.item_name)}** price to **{value:,}**.", ephemeral=True
        )


class ItemPriceConfigView(discord.ui.LayoutView):
    """Components v2 item price panel."""

    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self.selected_item: str | None = None
        self.all_items = [(name, data) for name, (_, data) in ITEMS.items() if "cost" in data]
        self.page = 0
        self.total_pages = max(1, -(-len(self.all_items) // 25))
        self._build_content()

    def _build_content(self, disabled: bool = False):
        self.clear_items()

        header = f"## 💰 Item Prices - Page {self.page + 1}/{self.total_pages}"

        page_items = self.all_items[self.page * 25 : (self.page + 1) * 25]
        lines = []
        for name, data in page_items:
            emoji = ITEMS[name][0]
            cost = data.get("cost", 0)
            marker = " ◄" if name == self.selected_item else ""
            lines.append(f"-# {emoji} {fmt(name)}: {cost:,}{marker}")

        select_row = discord.ui.ActionRow(_ItemSelect(self, self.page, disabled=disabled))
        nav_row = discord.ui.ActionRow()
        if self.page > 0:
            nav_row.add_item(_ItemPageNavBtn("prev", self, disabled=disabled))
        if self.page < self.total_pages - 1:
            nav_row.add_item(_ItemPageNavBtn("next", self, disabled=disabled))
        nav_row.add_item(_SetPriceBtn(self, disabled=disabled))

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{header}\n" + "\n".join(lines)),
                discord.ui.Separator(),
                select_row,
                nav_row,
            )
        )

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


class _JoinCrewBtn(discord.ui.Button):
    def __init__(self, lobby: "CrewLobbyView", disabled: bool = False):
        super().__init__(
            label="Join Crew",
            style=discord.ButtonStyle.success,
            emoji="🤝",
            disabled=disabled,
        )
        self.lobby = lobby

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        cog = self.lobby.cog

        if user.id == self.lobby.organiser.id:
            return await interaction.response.send_message(
                "You're already in the crew as the organiser.", ephemeral=True
            )
        if user in self.lobby.members:
            return await interaction.response.send_message(
                "You've already joined this crew.", ephemeral=True
            )
        if len(self.lobby.members) >= CREW_SIZE:
            return await interaction.response.send_message(
                "The crew is already full.", ephemeral=True
            )

        # Strict checks
        if await cog._is_in_jail(user):
            return await interaction.response.send_message(
                "You can't join a heist while in jail.", ephemeral=True
            )
        debt = await cog.config.user(user).debt()
        if debt > 0:
            return await interaction.response.send_message(
                f"You have outstanding debt of {debt:,}. Pay it off first.", ephemeral=True
            )
        if await cog._has_active_heist(user, interaction.channel.id):
            return await interaction.response.send_message(
                "You already have an active heist.", ephemeral=True
            )

        xp = await cog.config.user(user).xp()
        if get_level(xp) < 20:
            return await interaction.response.send_message(
                "You must be **level 20** or higher to join a crew robbery.", ephemeral=True
            )

        self.lobby.members.append(user)

        # Block joining member from starting another heist while lobby is open
        await cog.config.user(user).active_heist.set(
            {
                "type": "crew_robbery",
                "end_time": self.lobby.expires_ts,
                "channel_id": interaction.channel.id,
                "lobby": True,
            }
        )

        self.lobby._build_content()
        await interaction.response.edit_message(view=self.lobby)


class _BeginCrewBtn(discord.ui.Button):
    def __init__(self, lobby: "CrewLobbyView", disabled: bool = False):
        super().__init__(
            label=f"Begin Heist ({0}/{CREW_SIZE})",
            style=discord.ButtonStyle.danger,
            emoji="🚀",
            disabled=disabled,
        )
        self.lobby = lobby

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.lobby.organiser.id:
            return await interaction.response.send_message(
                "Only the organiser can begin the heist.", ephemeral=True
            )
        if len(self.lobby.members) < CREW_SIZE:
            return await interaction.response.send_message(
                f"Need {CREW_SIZE} crew members. Currently {len(self.lobby.members)}/{CREW_SIZE}.",
                ephemeral=True,
            )

        # Final checks on all members
        cog = self.lobby.cog
        for member in self.lobby.members:
            if await cog._is_in_jail(member):
                return await interaction.response.send_message(
                    f"{member.display_name} just got thrown in jail. Crew disbanded.",
                    ephemeral=True,
                )
            if await cog._has_active_heist(member, interaction.channel.id):
                return await interaction.response.send_message(
                    f"{member.display_name} started another heist. Crew disbanded.",
                    ephemeral=True,
                )

        data = self.lobby.data
        now = datetime.datetime.now(datetime.timezone.utc)
        end_time = now + data["duration"]
        end_timestamp = int(end_time.timestamp())

        # Set active heist for all members
        for member in self.lobby.members:
            await cog.config.user(member).active_heist.set(
                {
                    "type": "crew_robbery",
                    "end_time": end_time.timestamp(),
                    "channel_id": interaction.channel.id,
                    "tax_agreed": False,
                }
            )

        # Disable the lobby
        self.lobby._build_content(disabled=True)
        await interaction.response.edit_message(view=self.lobby)

        # Send started confirmation
        started_view = _CrewStartedView(
            data, self.lobby.members, end_timestamp, self.lobby.currency_name
        )
        await interaction.followup.send(view=started_view)

        # Schedule resolve
        async def _run():
            await asyncio.sleep(data["duration"].total_seconds())
            from .handlers import resolve_crew_heist

            await resolve_crew_heist(cog, self.lobby.members, "crew_robbery", interaction.channel)
            for m in self.lobby.members:
                if m.id in cog.pending_tasks:
                    del cog.pending_tasks[m.id]

        task = asyncio.create_task(_run())
        for member in self.lobby.members:
            if member.id in cog.pending_tasks:
                log.warning("Duplicate task for crew member %s, cancelling old", member.id)
                cog.pending_tasks[member.id].cancel()
            cog.pending_tasks[member.id] = task


class _CrewStartedView(discord.ui.LayoutView):
    def __init__(self, data: dict, members: list, end_timestamp: int, currency_name: str):
        super().__init__(timeout=None)
        names = ", ".join(m.display_name for m in members)
        body = (
            f"## 👥 Crew Robbery - In Progress\n"
            f"The crew is in. No turning back now.\n\n"
            f"**Crew:** {names}\n"
            f"**Results:** <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)\n"
            f"**Potential haul:** {data['min_reward']:,}–{data['max_reward']:,} {currency_name} (split {len(members)} ways)\n"
            f"**Potential loss:** {data['min_loss']:,}–{data['max_loss']:,} {currency_name} (split {len(members)} ways)"
        )
        self.add_item(discord.ui.Container(discord.ui.TextDisplay(body)))


class CrewLobbyView(discord.ui.LayoutView):
    """Components v2 lobby for the crew heist."""

    def __init__(self, cog, ctx: commands.Context, data: dict, currency_name: str):
        super().__init__(timeout=LOBBY_TIMEOUT)
        self.cog = cog
        self.ctx = ctx
        self.data = data
        self.currency_name = currency_name
        self.organiser = ctx.author
        self.members: list[discord.Member] = [ctx.author]
        self.message = None
        self.expires_ts = int(
            datetime.datetime.now(datetime.timezone.utc).timestamp() + LOBBY_TIMEOUT
        )
        self._build_content()

    def _build_content(self, disabled: bool = False):
        self.clear_items()
        filled = len(self.members)
        slots = []
        for i in range(CREW_SIZE):
            if i < filled:
                slots.append(f"**{i + 1}.** {self.members[i].display_name} ✅")
            else:
                slots.append(f"**{i + 1}.** *Waiting...*")

        expires_ts = self.expires_ts
        body = (
            f"## 👥 Crew Robbery - Lobby\n"
            f"Need {CREW_SIZE} players to begin. Lobby closes <t:{expires_ts}:R>.\n\n"
            f"**Potential haul:** {self.data['min_reward']:,}–{self.data['max_reward']:,} {self.currency_name}\n"
            f"**Split:** ~{self.data['min_reward'] // CREW_SIZE:,}-{self.data['max_reward'] // CREW_SIZE:,} per person\n"
            f"**Risk:** {_risk_indicator(self.data['police_chance'], self.data['risk'])}\n\n"
            + "\n".join(slots)
        )

        join_btn = _JoinCrewBtn(self, disabled=disabled or filled >= CREW_SIZE)
        begin_btn = _BeginCrewBtn(self, disabled=disabled or filled < CREW_SIZE)
        begin_btn.label = f"Begin Heist ({filled}/{CREW_SIZE})"

        action_row = discord.ui.ActionRow(join_btn, begin_btn)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(body),
                discord.ui.Separator(),
                action_row,
            )
        )

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)
        # Clear the lobby placeholder active_heist for all members
        for member in self.members:
            with contextlib.suppress(Exception):
                active = await self.cog.config.user(member).active_heist()
                if active and active.get("lobby"):
                    await self.cog.config.user(member).active_heist.clear()


class _EquipSelect(discord.ui.Select):
    """Select menu for a single equipment slot, populated from inventory."""

    def __init__(
        self,
        cog,
        equip_view: "EquipView",
        slot: str,
        inventory: dict,
        equipped: dict,
        disabled: bool = False,
    ):
        self.cog = cog
        self.equip_view = equip_view
        self.slot = slot

        item_type = slot  # slot name matches item type name
        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=ITEMS[name][0],
                description=_equip_desc(name, ITEMS[name][1]),
                default=(equipped.get(slot) == name),
            )
            for name, count in inventory.items()
            if count > 0 and name in ITEMS and ITEMS[name][1].get("type") == item_type
        ]

        slot_labels = {"shield": "🛡️ Shield", "tool": "🔧 Tool", "consumable": "💊 Consumable"}
        if options:
            super().__init__(
                placeholder=f"Equip a {slot_labels[slot]}...",
                options=options[:25],
                disabled=disabled,
            )
        else:
            super().__init__(
                placeholder=f"No {slot}s in inventory",
                options=[discord.SelectOption(label="None", value="__none__")],
                disabled=True,
            )

    async def callback(self, interaction: discord.Interaction):
        item = self.values[0]
        if item == "__none__":
            return await interaction.response.defer()

        equipped = await self.cog.config.user(interaction.user).equipped()
        equipped[self.slot] = item
        await self.cog.config.user(interaction.user).equipped.set(equipped)

        inventory = await self.cog.config.user(interaction.user).inventory()
        self.equip_view._build_content(inventory, equipped)
        await interaction.response.edit_message(view=self.equip_view)


class _UnequipBtn(discord.ui.Button):
    def __init__(
        self, cog, equip_view: "EquipView", slot: str, equipped: dict, disabled: bool = False
    ):
        self.cog = cog
        self.equip_view = equip_view
        self.slot = slot
        slot_labels = {"shield": "Shield", "tool": "Tool", "consumable": "Consumable"}
        is_equipped = equipped.get(slot) is not None
        super().__init__(
            label=f"Unequip {slot_labels[slot]}",
            style=discord.ButtonStyle.secondary,
            disabled=disabled or not is_equipped,
        )

    async def callback(self, interaction: discord.Interaction):
        equipped = await self.cog.config.user(interaction.user).equipped()
        equipped[self.slot] = None
        await self.cog.config.user(interaction.user).equipped.set(equipped)

        inventory = await self.cog.config.user(interaction.user).inventory()
        self.equip_view._build_content(inventory, equipped)
        await interaction.response.edit_message(view=self.equip_view)


def _equip_desc(name: str, data: dict) -> str:
    match data.get("type"):
        case "shield":
            return f"Reduces loss by {data['reduction'] * 100:.1f}%"
        case "tool":
            return f"+{data['boost'] * 100:.0f}% for {fmt(data['for_heist'])}"
        case "consumable":
            return f"Reduces risk by {data['risk_reduction'] * 100:.0f}%"
        case _:
            return ""


class EquipView(discord.ui.LayoutView):
    """Components v2 equip panel."""

    def __init__(self, cog, ctx: commands.Context, inventory: dict, equipped: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self._build_content(inventory, equipped)

    def _build_content(self, inventory: dict, equipped: dict, disabled: bool = False):
        self.clear_items()

        def _slot_line(slot: str) -> str:
            item = equipped.get(slot)
            if item and item in ITEMS:
                emoji = ITEMS[item][0]
                return f"**{slot.title()}:** {emoji} {fmt(item)}"
            return f"**{slot.title()}:** *None*"

        summary = (
            f"## ⚙️ Equipment\n"
            f"{_slot_line('shield')}\n"
            f"{_slot_line('tool')}\n"
            f"{_slot_line('consumable')}"
        )

        unequip_row = discord.ui.ActionRow(
            _UnequipBtn(self.cog, self, "shield", equipped, disabled=disabled),
            _UnequipBtn(self.cog, self, "tool", equipped, disabled=disabled),
            _UnequipBtn(self.cog, self, "consumable", equipped, disabled=disabled),
        )

        components: list = [
            discord.ui.TextDisplay(summary),
            discord.ui.Separator(),
            discord.ui.ActionRow(
                _EquipSelect(self.cog, self, "shield", inventory, equipped, disabled)
            ),
            discord.ui.ActionRow(
                _EquipSelect(self.cog, self, "tool", inventory, equipped, disabled)
            ),
            discord.ui.ActionRow(
                _EquipSelect(self.cog, self, "consumable", inventory, equipped, disabled)
            ),
            discord.ui.Separator(),
            unequip_row,
        ]
        self.add_item(discord.ui.Container(*components))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your equipment panel.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        equipped = await self.cog.config.user(self.ctx.author).equipped()
        inventory = await self.cog.config.user(self.ctx.author).inventory()
        self._build_content(inventory, equipped, disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)


class _CraftSelect(discord.ui.Select):
    def __init__(self, craft_view: "CraftView", craftable: list, disabled: bool = False):
        self.craft_view = craft_view
        options = [
            discord.SelectOption(
                label=fmt(name),
                value=name,
                emoji=ITEMS[name][0] if name in ITEMS else "🔨",
                description=_craft_desc(recipe),
            )
            for name, recipe in craftable
        ]
        super().__init__(
            placeholder="Choose a recipe...",
            options=options[:25],
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        self.craft_view.selected = self.values[0]
        self.craft_view._build_content()
        await interaction.response.edit_message(view=self.craft_view)


class _CraftBtn(discord.ui.Button):
    def __init__(self, craft_view: "CraftView", disabled: bool = False):
        super().__init__(
            label="Craft",
            style=discord.ButtonStyle.success,
            emoji="🔨",
            disabled=disabled,
        )
        self.craft_view = craft_view

    async def callback(self, interaction: discord.Interaction):
        selected = self.craft_view.selected
        if not selected:
            return await interaction.response.defer()

        recipe = RECIPES[selected]
        inventory = await self.craft_view.cog.config.user(interaction.user).inventory()

        missing = [
            f"{fmt(mat)} (need {qty}, have {inventory.get(mat, 0)})"
            for mat, qty in recipe["materials"].items()
            if inventory.get(mat, 0) < qty
        ]
        if missing:
            return await interaction.response.send_message(
                f"Missing materials: {', '.join(missing)}", ephemeral=True
            )

        for mat, qty in recipe["materials"].items():
            inventory[mat] -= qty
            if inventory[mat] <= 0:
                del inventory[mat]

        result = recipe["result"]
        inventory[result] = inventory.get(result, 0) + recipe["quantity"]
        await self.craft_view.cog.config.user(interaction.user).inventory.set(inventory)

        # Refresh view with updated inventory
        self.craft_view.inventory = inventory
        self.craft_view._build_content()
        await interaction.response.edit_message(view=self.craft_view)
        await interaction.followup.send(
            f"✅ Crafted **{recipe['quantity']}× {fmt(result)}**!", ephemeral=True
        )


class _CraftNavBtn(discord.ui.Button):
    def __init__(self, direction: str, craft_view: "CraftView", disabled: bool = False):
        match direction:
            case "prev":
                label, emoji = "Previous", "◀️"
            case "next":
                label, emoji = "Next", "▶️"
        super().__init__(
            label=label, emoji=emoji, style=discord.ButtonStyle.secondary, disabled=disabled
        )
        self.direction = direction
        self.craft_view = craft_view

    async def callback(self, interaction: discord.Interaction):
        match self.direction:
            case "prev" if self.craft_view.page > 0:
                self.craft_view.page -= 1
            case "next" if self.craft_view.page < self.craft_view.total_pages - 1:
                self.craft_view.page += 1
        self.craft_view._build_content()
        await interaction.response.edit_message(view=self.craft_view)


def _craft_desc(recipe: dict) -> str:
    mats = ", ".join(f"{qty}× {fmt(m)}" for m, qty in recipe["materials"].items())
    return mats[:100]


RECIPES_PER_PAGE = 10


class CraftView(discord.ui.LayoutView):
    """Components v2 crafting panel."""

    def __init__(self, cog, ctx: commands.Context, inventory: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.inventory = inventory
        self.selected: str | None = None
        self.page = 0
        self.all_recipes = list(RECIPES.items())
        self.total_pages = max(1, -(-len(self.all_recipes) // RECIPES_PER_PAGE))
        self.message = None
        self._build_content()

    def _can_craft(self, recipe: dict) -> bool:
        return all(self.inventory.get(mat, 0) >= qty for mat, qty in recipe["materials"].items())

    def _build_content(self, disabled: bool = False):
        self.clear_items()

        start = self.page * RECIPES_PER_PAGE
        page_recipes = self.all_recipes[start : start + RECIPES_PER_PAGE]

        lines = [f"## 🔨 Crafting - Page {self.page + 1}/{self.total_pages}\n"]
        for name, recipe in page_recipes:
            emoji = ITEMS[name][0] if name in ITEMS else "🔨"
            can = "✅" if self._can_craft(recipe) else "❌"
            mats = " · ".join(
                f"{qty}× {fmt(m)} ({self.inventory.get(m, 0)} owned)"
                for m, qty in recipe["materials"].items()
            )
            lines.append(f"**{emoji} {fmt(name)}** {can}\n-# {mats}\n")

        # Detail block for selected recipe
        detail = ""
        if self.selected and self.selected in RECIPES:
            recipe = RECIPES[self.selected]
            result_emoji = ITEMS[self.selected][0] if self.selected in ITEMS else "🔨"
            mat_lines = "\n".join(
                f"-# {fmt(m)}: need {qty}, have {self.inventory.get(m, 0)}"
                for m, qty in recipe["materials"].items()
            )
            can_craft = self._can_craft(recipe)
            detail = (
                f"\n**Selected:** {result_emoji} {fmt(self.selected)} "
                f"{'✅ Ready to craft' if can_craft else '❌ Missing materials'}\n{mat_lines}"
            )

        select_row = discord.ui.ActionRow(_CraftSelect(self, page_recipes, disabled=disabled))
        craft_btn = _CraftBtn(
            self,
            disabled=disabled
            or not self.selected
            or not self._can_craft(RECIPES.get(self.selected, {})),
        )
        nav_row = discord.ui.ActionRow()
        if self.page > 0:
            nav_row.add_item(_CraftNavBtn("prev", self, disabled=disabled))
        if self.page < self.total_pages - 1:
            nav_row.add_item(_CraftNavBtn("next", self, disabled=disabled))
        nav_row.add_item(craft_btn)

        components: list = [
            discord.ui.TextDisplay("".join(lines) + detail),
            discord.ui.Separator(),
            select_row,
            nav_row,
        ]
        self.add_item(discord.ui.Container(*components))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your crafting panel.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.HTTPException):
                await self.message.edit(view=self)
