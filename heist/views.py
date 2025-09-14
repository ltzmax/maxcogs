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
import datetime
import logging
import random

import discord
from red_commons.logging import getLogger
from redbot.core import bank, commands
from redbot.core.utils.views import ConfirmView

from .handlers import schedule_resolve
from .utils import HEISTS, ITEMS

log = getLogger("red.cogs.heist.views")


class ShopView(discord.ui.View):
    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.add_item(ShopSelect(cog))

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
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException as e:
                log.error(f"Failed to update shop view on timeout: {e}")


class ShopSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(
                label=name.replace("_", " ").title(),
                value=name,
                description=f"Cost: {data['cost']:,}"
                + (
                    f" | Reduces loss by {data['reduction']*100:.1f}% for {data['duration_hours']}h"
                    if data["type"] == "shield"
                    else f" | Boosts {data['for_heist'].replace('_', ' ').title()} success by {data['boost']*100:.0f}% (consumable)"
                ),
                emoji=emoji,
            )
            for name, (emoji, data) in ITEMS.items()
            if data["type"] in ["shield", "tool"]
            and "cost" in data  # Only include purchasable items to not break select menu.
        ]
        super().__init__(
            placeholder="Select an item...", options=options[:25]
        )  # Limit to 25 options due to discord's limits.

    async def callback(self, interaction: discord.Interaction):
        item_type = self.values[0]
        emoji, data = ITEMS[item_type]
        cost = data["cost"]
        balance = await bank.get_balance(interaction.user)
        currency_name = await bank.get_currency_name(interaction.guild)
        if balance < cost:
            await interaction.response.send_message(
                f"You don't have enough currency! Need {cost:,} {currency_name}, have {balance:,} {currency_name}.",
                ephemeral=True,
            )
            return  # Keep view active for reselections
        await bank.withdraw_credits(interaction.user, cost)
        if data["type"] == "shield":
            if await self.cog._has_active_shield(interaction.user):
                await interaction.response.send_message(
                    "You already have an active shield.", ephemeral=True
                )
                return  # Keep view active for reselections
            duration = datetime.timedelta(hours=data.get("duration_hours", 48))
            end_time = (datetime.datetime.now(datetime.timezone.utc) + duration).timestamp()
            await self.cog.config.user(interaction.user).shield.set(item_type)
            await self.cog.config.user(interaction.user).shield_end.set(end_time)
            await interaction.response.send_message(
                f"Purchased {emoji} {item_type.replace('_', ' ').title()} for {cost:,} {currency_name}! Active for {data.get('duration_hours', 48)} hours.",
                ephemeral=True,
            )
        elif data["type"] == "tool":
            inventory = await self.cog.config.user(interaction.user).inventory()
            inventory[item_type] = inventory.get(item_type, 0) + 1
            await self.cog.config.user(interaction.user).inventory.set(inventory)
            await interaction.response.send_message(
                f"Purchased {emoji} {item_type.replace('_', ' ').title()} for {cost:,} {currency_name}! Added to inventory.",
                ephemeral=True,
            )
        for item in self.view.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self.view)
        except discord.HTTPException as e:
            log.error(f"Failed to update shop view after purchase: {e}")


class HeistView(discord.ui.View):
    def __init__(self, cog, ctx: commands.Context, heist_settings: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.heist_settings = heist_settings
        self.message = None
        options = [
            discord.SelectOption(
                label=name.replace("_", " ").title(),
                value=name,
                emoji=data["emoji"],
                description=(
                    f"Reward: {ITEMS[name][1]['min_sell']:,}-{ITEMS[name][1]['max_sell']:,} credits"
                    if name in ITEMS and ITEMS[name][1]["type"] == "loot"
                    else f"Reward: {data['min_reward']:,}-{data['max_reward']:,}"
                ),
            )
            for name, data in heist_settings.items()
        ]
        self.add_item(HeistSelect(cog, options))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is allowed to interact."""
        if interaction.user.id not in [self.ctx.author.id] + list(self.cog.bot.owner_ids):
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException as e:
                log.error(f"Failed to update heist view on timeout: {e}")


class HeistSelect(discord.ui.Select):
    def __init__(self, cog, options):
        self.cog = cog
        super().__init__(placeholder="Select a heist...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        heist_type = self.values[0]
        log.debug(f"User {interaction.user.id} selected heist: {heist_type}")
        data = await self.cog.get_heist_settings(heist_type)
        user = interaction.user

        if await self.cog._has_active_heist(user, interaction.channel.id):
            await interaction.followup.send(
                "You have an active heist ongoing. Wait for it to finish.", ephemeral=True
            )
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        cooldowns = await self.cog.config.user(user).heist_cooldowns()
        last_timestamp = cooldowns.get(heist_type)
        if last_timestamp:
            last_time = datetime.datetime.fromtimestamp(last_timestamp, tz=datetime.timezone.utc)
            if now - last_time < data["cooldown"]:
                remaining = data["cooldown"] - (now - last_time)
                end_time = now + remaining
                end_timestamp = int(end_time.timestamp())
                log.debug(
                    f"Heist {heist_type} on cooldown for user {user.id}, ready at {end_timestamp}"
                )
                await interaction.followup.send(
                    f"On cooldown! Ready <t:{end_timestamp}:R>.", ephemeral=True
                )
                return

        balance = await bank.get_balance(user)
        currency_name = await bank.get_currency_name(interaction.guild)
        max_loss = data["max_loss"]
        tax_agreed = False
        if balance < max_loss:
            view = ConfirmView(user, timeout=60, disable_buttons=True)
            tax = int(max_loss * 0.2)
            total_debt = max_loss + tax
            prompt_msg = await interaction.followup.send(
                f"Your balance ({balance:,} {currency_name}) is too low to cover a potential loss of up to {max_loss:,} {currency_name} for the {heist_type.replace('_', ' ').title()}. "
                f"Proceed and pay up to {total_debt:,} {currency_name} (including 20% tax) later if you fail?\n-# Please note the final price you will need to pay is shown after the heist is done.",
                view=view,
                ephemeral=True,
            )
            await view.wait()
            if view.result is None or not view.result:
                log.debug(f"Debt agreement cancelled for user {user.id}")
                await prompt_msg.edit(
                    content="Heist cancelled. You will not be charged when you start a new heist.",
                    view=None,
                )
                return
            tax_agreed = True

        cooldowns[heist_type] = now.timestamp()
        await self.cog.config.user(user).heist_cooldowns.set(cooldowns)
        end_time = now + data["duration"]
        end_timestamp = int(end_time.timestamp())
        channel_id = interaction.channel.id
        await self.cog.config.user(user).active_heist.set(
            {
                "type": heist_type,
                "end_time": end_time.timestamp(),
                "channel_id": channel_id,
                "tax_agreed": tax_agreed,
            }
        )
        embed = discord.Embed(
            title="Heist Started",
            description=f"{data['emoji']} {heist_type.replace('_', ' ').title()} started! Results will be sent <t:{end_timestamp}:R>.",
            color=0x7CFC00,
        )
        await interaction.followup.send(embed=embed)
        await interaction.followup.send(
            f"Started {heist_type.replace('_', ' ').title()}!", ephemeral=True
        )

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
        try:
            log.debug(f"Attempting to disable dropdown for interaction {interaction.id}")
            for item in self.view.children:
                item.disabled = True
            await interaction.message.edit(view=self.view)
            log.debug(f"Successfully updated dropdown for interaction {interaction.id}")
        except discord.HTTPException as e:
            log.error(
                f"Failed to update heist view after heist start for interaction {interaction.id}: {e}"
            )


class HeistConfigView(discord.ui.View):
    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self.add_item(HeistConfigButton(cog))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is allowed to interact."""
        if interaction.user.id not in [self.ctx.author.id] + list(self.cog.bot.owner_ids):
            await interaction.response.send_message(
                "You are not authorized to use this.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class HeistConfigButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Configure Settings", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.cog.bot.owner_ids:
            return await interaction.response.send_message(
                "You are not authorized to use this.", ephemeral=True
            )
        modal = HeistSetModal(self.cog)
        await interaction.response.send_modal(modal)


class HeistSetModal(discord.ui.Modal, title="Configure Heist Settings"):
    heist_type = discord.ui.TextInput(label="Heist Type", placeholder="e.g. pocket_steal")
    param = discord.ui.TextInput(label="Parameter", placeholder="e.g. risk, min_reward")
    value = discord.ui.TextInput(label="Value", placeholder="Enter a number (must be seconds)")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        heist_type = self.heist_type.value.lower().replace(" ", "_")
        param = self.param.value.lower()
        try:
            value = float(self.value.value)
        except ValueError:
            return await interaction.response.send_message(
                "Invalid value: must be a number.", ephemeral=True
            )

        if heist_type not in HEISTS:
            return await interaction.response.send_message(
                f"Invalid heist type: {heist_type}", ephemeral=True
            )

        valid_params = [
            "risk",
            "min_reward",
            "max_reward",
            "cooldown",
            "min_success",
            "max_success",
            "duration",
            "police_chance",
            "jail_time",
        ]
        if param not in valid_params:
            return await interaction.response.send_message(
                f"Invalid parameter: {param}. Choose from {', '.join(valid_params)}",
                ephemeral=True,
            )

        current_settings = await self.cog.config.heist_settings.get_raw(heist_type, default={})
        default_settings = HEISTS.get(heist_type, {})

        if param in ["risk", "police_chance"]:
            value = value / 100.0
            if not 0 <= value <= 1.0:
                return await interaction.response.send_message(
                    f"{param.title()} must be between 0 and 100.", ephemeral=True
                )
        elif param in ["min_success", "max_success"]:
            value = int(value)
            if not 0 <= value <= 100:
                return await interaction.response.send_message(
                    f"{param.title()} must be between 0 and 100.", ephemeral=True
                )
        elif param in ["min_reward", "max_reward", "cooldown", "duration", "jail_time"]:
            value = int(value)
            if value < 0:
                return await interaction.response.send_message(
                    f"{param.title()} cannot be negative.", ephemeral=True
                )
            if param in ["cooldown", "jail_time"] and value < 60:
                return await interaction.response.send_message(
                    f"{param.title()} must be at least 60 seconds.", ephemeral=True
                )
            if param == "duration" and value < 30:
                return await interaction.response.send_message(
                    "Duration must be at least 30 seconds.", ephemeral=True
                )

        if param == "max_reward":
            min_reward = current_settings.get("min_reward", default_settings.get("min_reward", 0))
            if value < min_reward:
                return await interaction.response.send_message(
                    f"Max reward ({value}) cannot be less than min reward ({min_reward}).",
                    ephemeral=True,
                )
        elif param == "min_reward":
            max_reward = current_settings.get(
                "max_reward", default_settings.get("max_reward", float("inf"))
            )
            if value > max_reward:
                return await interaction.response.send_message(
                    f"Min reward ({value}) cannot be greater than max reward ({max_reward}).",
                    ephemeral=True,
                )

        if param == "max_success":
            min_success = current_settings.get(
                "min_success", default_settings.get("min_success", 0)
            )
            if value < min_success:
                return await interaction.response.send_message(
                    f"Max success ({value}) cannot be less than min success ({min_success}).",
                    ephemeral=True,
                )
        elif param == "min_success":
            max_success = current_settings.get(
                "max_success", default_settings.get("max_success", 100)
            )
            if value > max_success:
                return await interaction.response.send_message(
                    f"Min success ({value}) cannot be greater than max success ({max_success}).",
                    ephemeral=True,
                )

        async with self.cog.config.heist_settings() as settings:
            settings[heist_type][param] = value
        await interaction.response.send_message(
            f"Set {param} for {heist_type.replace('_', ' ').title()} to {value if param not in ['risk', 'police_chance'] else value * 100}.",
            ephemeral=True,
        )


class ItemPriceConfigView(discord.ui.View):
    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.message = None
        self.add_item(ItemPriceConfigButton(cog))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id] + list(self.cog.bot.owner_ids):
            await interaction.response.send_message(
                "You are not authorized to use this.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class ItemPriceConfigButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Configure Prices", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.cog.bot.owner_ids:
            return await interaction.response.send_message(
                "You are not authorized to use this.", ephemeral=True
            )
        modal = ItemPriceSetModal(self.cog)
        await interaction.response.send_modal(modal)


class ItemPriceSetModal(discord.ui.Modal, title="Configure Item Price"):
    item_name = discord.ui.TextInput(label="Item Name", placeholder="e.g. wooden_shield")
    new_cost = discord.ui.TextInput(label="New Cost", placeholder="Enter a positive integer")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        item_name = self.item_name.value.lower().replace(" ", "_")
        try:
            value = int(self.new_cost.value)
            if value < 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Invalid cost: must be a non-negative integer.", ephemeral=True
            )

        shop_items = {name: data for name, (_, data) in ITEMS.items() if "cost" in data}
        if item_name not in shop_items:
            return await interaction.response.send_message(
                f"Invalid item: {item_name}", ephemeral=True
            )

        async with self.cog.config.item_settings() as settings:
            settings[item_name]["cost"] = value
        await interaction.response.send_message(
            f"Set cost for {item_name.replace('_', ' ').title()} to {value:,}.",
            ephemeral=True,
        )
