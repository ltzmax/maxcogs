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
from typing import Final

import discord
from red_commons.logging import getLogger
from redbot.core import Config, bank, commands

from .commands.owner_commands import OwnerCommands
from .commands.user_commands import UserCommands
from .handlers import resolve_heist, schedule_resolve
from .utils import HEISTS, ITEMS
from .views import ConfirmLayoutView


log = getLogger("red.cogs.heist")


def _simple_view(text: str) -> discord.ui.LayoutView:
    v = discord.ui.LayoutView(timeout=None)
    v.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
    return v


class Heist(UserCommands, OwnerCommands, commands.Cog):
    """A game where players commit heists to steal valuable items or currency, using tools to boost success and shields to reduce losses, with a risk of getting caught by police!"""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/#heist"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=11236022492481444, force_registration=True)
        default_user = {
            "shield": None,
            "shield_end": None,
            "heist_cooldowns": {},
            "active_heist": None,
            "inventory": {},
            "debt": 0,
            "jail": None,
            "equipped": {"shield": None, "tool": None, "consumable": None},
            "heat": 0,
            "material_heat": 0,
            "heat_last_set": None,
        }
        default_global = {
            "heist_settings": {
                name: {
                    "risk": data["risk"],
                    "min_reward": data["min_reward"],
                    "max_reward": data["max_reward"],
                    "cooldown": data["cooldown"].total_seconds(),
                    "min_success": data["min_success"],
                    "max_success": data["max_success"],
                    "duration": data["duration"].total_seconds(),
                    "police_chance": data["police_chance"],
                    "jail_time": data["jail_time"].total_seconds(),
                }
                for name, data in HEISTS.items()
            },
            "item_settings": {
                name: {"cost": data["cost"]} for name, (_, data) in ITEMS.items() if "cost" in data
            },
        }
        self.config.register_user(**default_user)
        self.config.register_global(**default_global)
        self.pending_tasks = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Delete all user-specific data for the specified user_id."""
        await self.config.user_from_id(user_id).clear()

    async def _has_active_shield(self, user: discord.Member) -> bool:
        equipped = await self.config.user(user).equipped()
        equipped_shield = equipped["shield"]
        if equipped_shield:
            inventory = await self.config.user(user).inventory()
            if inventory.get(equipped_shield, 0) > 0:
                return True
        return False

    async def _get_equipped_tool(self, user: discord.Member, heist_type: str) -> tuple:
        equipped = await self.config.user(user).equipped()
        equipped_tool = equipped["tool"]
        if equipped_tool:
            inventory = await self.config.user(user).inventory()
            if (
                inventory.get(equipped_tool, 0) > 0
                and ITEMS[equipped_tool][1].get("for_heist") == heist_type
            ):
                return equipped_tool, ITEMS[equipped_tool][1]["boost"]
        return None, 0.0

    async def _has_equipped_consumable(self, user: discord.Member) -> bool:
        equipped = await self.config.user(user).equipped()
        equipped_consumable = equipped["consumable"]
        if equipped_consumable:
            inventory = await self.config.user(user).inventory()
            if inventory.get(equipped_consumable, 0) > 0:
                return True
        return False

    async def _consume_item(self, member: discord.Member, item_name: str):
        inventory = await self.config.user(member).inventory()
        if inventory.get(item_name, 0) > 0:
            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            await self.config.user(member).inventory.set(inventory)

    async def _has_active_heist(self, user: discord.Member, channel_id: int | None = None) -> bool:
        active = await self.config.user(user).active_heist()
        if not active:
            return False
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        if now >= active["end_time"]:
            if active.get("channel_id"):
                channel = self.bot.get_channel(active["channel_id"])
                if channel:
                    await resolve_heist(self, user, active["type"], channel, channel_id)
            return False
        return True

    async def _is_in_jail(self, user: discord.Member) -> bool:
        jail = await self.config.user(user).jail()
        if not jail:
            return False
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        if now >= jail["end_time"]:
            await self.config.user(user).jail.clear()
            return False
        return True

    async def _get_effective_heat(self, user: discord.Member) -> int:
        """Return heat decayed by 1 per 2 hours idle, and persist the result."""
        heat = await self.config.user(user).heat()
        if heat <= 0:
            return 0
        last_set = await self.config.user(user).heat_last_set()
        if last_set is None:
            return heat
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        hours_idle = (now - last_set) / 3600
        decay = int(hours_idle / 2)
        if decay > 0:
            new_heat = max(0, heat - decay)
            await self.config.user(user).heat.set(new_heat)
            await self.config.user(user).heat_last_set.set(now)
            return new_heat
        return heat

    async def check_debt(self, ctx: commands.Context) -> bool:
        """Check if user has debt and prompt for payment."""
        debt = await self.config.user(ctx.author).debt()
        if debt <= 0:
            return True
        balance = await bank.get_balance(ctx.author)
        currency_name = await bank.get_currency_name(ctx.guild)
        body = (
            f"## 💸 Outstanding Debt\n"
            f"You owe **{debt:,} {currency_name}** in debt.\n"
            f"Your current balance is **{balance:,} {currency_name}**.\n\n"
            f"Pay **{min(balance, debt):,} {currency_name}** now?"
        )
        view = ConfirmLayoutView(ctx.author, body, timeout=60)
        view.message = await ctx.send(view=view)
        await view.wait()
        if view.confirmed is None:
            await view.message.edit(view=_simple_view("Debt payment timed out."))
            return False
        if not view.confirmed:
            await view.message.edit(view=_simple_view("Debt payment declined."))
            return False
        pay_amount = min(balance, debt)
        await bank.withdraw_credits(ctx.author, pay_amount)
        remaining_debt = debt - pay_amount
        await self.config.user(ctx.author).debt.set(remaining_debt)
        await view.message.edit(
            view=_simple_view(
                f"Paid **{pay_amount:,}** {currency_name} towards your debt. "
                f"(**{remaining_debt:,}** {currency_name} remaining.)"
            )
        )
        return remaining_debt == 0

    async def check_jail(self, ctx: commands.Context, jailed_user: discord.Member) -> bool:
        """Check if a user is in jail and prompt for bailout."""
        if jailed_user.bot:
            await ctx.send("Bots can't be in jail!")
            return False
        if not await self._is_in_jail(jailed_user):
            return True
        jail = await self.config.user(jailed_user).jail()
        balance = await bank.get_balance(ctx.author)
        currency_name = await bank.get_currency_name(ctx.guild)
        bail_amount = jail["bail_amount"]
        tax = int(bail_amount * 0.15)
        total_bail = bail_amount + tax
        end_timestamp = int(jail["end_time"])
        is_self = jailed_user == ctx.author
        target = "You are" if is_self else f"**{jailed_user.display_name}** is"
        body = (
            f"## 🚨 {'Behind Bars' if is_self else 'Bail Request'}\n"
            f"{target} in jail until <t:{end_timestamp}:f> (<t:{end_timestamp}:R>).\n\n"
            f"**Bail amount:** {bail_amount:,} + {tax:,} (15% tax) = **{total_bail:,}** {currency_name}\n"
            f"**Your balance:** {balance:,} {currency_name}\n\n"
            f"Pay bail now?"
        )
        view = ConfirmLayoutView(ctx.author, body, timeout=60)
        view.message = await ctx.send(view=view)
        await view.wait()
        if view.confirmed is None:
            await view.message.edit(view=_simple_view("Bailout timed out."))
            return False
        if not view.confirmed:
            await view.message.edit(view=_simple_view("Bailout declined."))
            return False
        if balance < total_bail:
            await view.message.edit(
                view=_simple_view(
                    f"You need **{total_bail:,}** {currency_name} to bail out "
                    f"{'yourself' if is_self else jailed_user.display_name}, "
                    f"but you only have **{balance:,}**."
                )
            )
            return False
        await bank.withdraw_credits(ctx.author, total_bail)
        await self.config.user(jailed_user).jail.clear()
        await self.config.user(jailed_user).heat.set(0)
        await self.config.user(jailed_user).material_heat.set(0)
        await view.message.edit(
            view=_simple_view(
                f"{ctx.author.mention} paid **{total_bail:,}** {currency_name} — "
                f"{'you are' if is_self else f'{jailed_user.display_name} is'} free!"
            )
        )
        return True

    async def get_heist_settings(self, heist_type: str) -> dict:
        """Retrieve heist settings, merging defaults with custom config."""
        defaults = HEISTS.get(heist_type, {})
        custom = await self.config.heist_settings.get_raw(heist_type, default={})
        return {
            "emoji": defaults.get("emoji", "❓"),
            "risk": custom.get("risk", defaults.get("risk", 0.0)),
            "min_reward": int(custom.get("min_reward", defaults.get("min_reward", 0))),
            "max_reward": int(custom.get("max_reward", defaults.get("max_reward", 0))),
            "cooldown": datetime.timedelta(
                seconds=custom.get(
                    "cooldown",
                    defaults.get("cooldown", datetime.timedelta()).total_seconds(),
                )
            ),
            "min_success": int(custom.get("min_success", defaults.get("min_success", 0))),
            "max_success": int(custom.get("max_success", defaults.get("max_success", 100))),
            "duration": datetime.timedelta(
                seconds=custom.get(
                    "duration",
                    defaults.get("duration", datetime.timedelta()).total_seconds(),
                )
            ),
            "min_loss": defaults.get("min_loss", 0),
            "max_loss": defaults.get("max_loss", 0),
            "police_chance": custom.get("police_chance", defaults.get("police_chance", 0.0)),
            "material_drop_chance": defaults.get("material_drop_chance", 0.0),
            "material_tiers": defaults.get("material_tiers"),
            "jail_time": datetime.timedelta(
                seconds=custom.get(
                    "jail_time",
                    defaults.get("jail_time", datetime.timedelta()).total_seconds(),
                )
            ),
        }

    async def get_item_cost(self, item_name: str) -> int:
        """Retrieve item cost, merging default with custom config."""
        default_cost = ITEMS.get(item_name, (None, {}))[1].get("cost", 0)
        custom = await self.config.item_settings.get_raw(item_name, default={})
        return int(custom.get("cost", default_cost))

    async def cog_load(self):
        all_users = await self.config.all_users()
        for user_id, data in all_users.items():
            active = data.get("active_heist")
            if active:
                now = datetime.datetime.now(datetime.timezone.utc).timestamp()
                if now >= active["end_time"]:
                    user = self.bot.get_user(user_id)
                    if active.get("channel_id"):
                        channel = self.bot.get_channel(active["channel_id"])
                        if channel:
                            if user:
                                await resolve_heist(self, user, active["type"], channel)
                            else:
                                await self.config.user_from_id(user_id).active_heist.clear()
                                log.warning(
                                    "Could not resolve heist for uncached user %s on cog load",
                                    user_id,
                                )
                else:
                    remaining = active["end_time"] - now
                    if active.get("channel_id"):
                        channel = self.bot.get_channel(active["channel_id"])
                        if channel:
                            if user_id in self.pending_tasks:
                                log.warning(
                                    "Duplicate task for user %s on cog_load, cancelling old",
                                    user_id,
                                )
                                self.pending_tasks[user_id].cancel()
                            task = asyncio.create_task(
                                schedule_resolve(self, user_id, remaining, active["type"], channel)
                            )
                            self.pending_tasks[user_id] = task

    async def cog_unload(self):
        for task in list(self.pending_tasks.values()):
            task.cancel()
        self.pending_tasks.clear()
