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
import random
from typing import Final

import discord
from redbot.core import Config, bank, commands
from redbot.core.utils.views import ConfirmView

from .handlers import resolve_heist, schedule_resolve
from .utils import HEISTS, ITEMS, RECIPES
from .views import HeistConfigView, HeistView, ItemPriceConfigView, ShopView


class Heist(commands.Cog):
    """A game where players commit heists to steal valuable items or currency, using tools to boost success and shields to reduce losses, with a risk of getting caught by police!"""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/heist/README.md"

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
        """
        Thanks Sinbad!
        """
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

    async def _has_active_heist(self, user: discord.Member, channel_id: int = None) -> bool:
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

    async def cog_load(self):
        all_users = await self.config.all_users()
        for user_id, data in all_users.items():
            active = data.get("active_heist")
            if active:
                now = datetime.datetime.now(datetime.timezone.utc).timestamp()
                if now >= active["end_time"]:
                    user = self.bot.get_user(user_id)
                    if user and active.get("channel_id"):
                        channel = self.bot.get_channel(active["channel_id"])
                        if channel:
                            await resolve_heist(self, user, active["type"], channel)
                else:
                    remaining = active["end_time"] - now
                    if active.get("channel_id"):
                        channel = self.bot.get_channel(active["channel_id"])
                        if channel:
                            task = asyncio.create_task(
                                schedule_resolve(self, user_id, remaining, active["type"], channel)
                            )
                            self.pending_tasks[user_id] = task

    async def cog_unload(self):
        for task in list(self.pending_tasks.values()):
            task.cancel()
        self.pending_tasks.clear()

    async def check_debt(self, ctx: commands.Context) -> bool:
        """Check if user has debt and prompt for payment."""
        debt = await self.config.user(ctx.author).debt()
        if debt <= 0:
            return True
        balance = await bank.get_balance(ctx.author)
        currency_name = await bank.get_currency_name(ctx.guild)
        view = ConfirmView(ctx.author, timeout=60, disable_buttons=True)
        prompt_msg = await ctx.send(
            f"You owe {debt:,} {currency_name} in debt. Your balance is {balance:,} {currency_name}. Do you want to pay now?",
            view=view,
        )
        await view.wait()
        if view.result is None:
            await prompt_msg.edit(content="Debt payment timed out.", view=None)
            return False
        if not view.result:
            await prompt_msg.edit(content="Debt payment declined.", view=None)
            return False
        pay_amount = min(balance, debt)
        await bank.withdraw_credits(ctx.author, pay_amount)
        remaining_debt = debt - pay_amount
        await self.config.user(ctx.author).debt.set(remaining_debt)
        await prompt_msg.edit(
            content=f"Paid {pay_amount:,} {currency_name} towards your debt. ({remaining_debt:,} {currency_name} dept remains.)",
            view=None,
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
        prompt_msg_content = (
            f"{'You are' if jailed_user == ctx.author else f'{jailed_user.display_name} is'} in jail until <t:{end_timestamp}:f> (<t:{end_timestamp}:R>). "
            f"Your balance is {balance:,} {currency_name}. "
            f"Bail out for {bail_amount:,} + {tax:,} (15%) tax = {total_bail:,} {currency_name}?"
        )
        view = ConfirmView(ctx.author, timeout=60, disable_buttons=True)
        prompt_msg = await ctx.send(prompt_msg_content, view=view)
        await view.wait()
        if view.result is None:
            await prompt_msg.edit(content="Bailout timed out.", view=None)
            return False
        if not view.result:
            await prompt_msg.edit(content="Bailout declined.", view=None)
            return False
        if balance < total_bail:
            await prompt_msg.edit(
                content=f"You need {total_bail:,} {currency_name} to bail out {'yourself' if jailed_user == ctx.author else jailed_user.display_name}, but you only have {balance:,} {currency_name}.",
                view=None,
            )
            return False
        await bank.withdraw_credits(ctx.author, total_bail)
        await self.config.user(jailed_user).jail.clear()
        await self.config.user(jailed_user).heat.set(0)
        await self.config.user(jailed_user).material_heat.set(0)
        await prompt_msg.edit(
            content=f"{ctx.author.mention} paid {total_bail:,} {currency_name} to bail out {'yourself' if jailed_user == ctx.author else jailed_user.display_name}. {'You are' if jailed_user == ctx.author else 'They are'} free!",
            view=None,
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
                    "cooldown", defaults.get("cooldown", datetime.timedelta()).total_seconds()
                )
            ),
            "min_success": int(custom.get("min_success", defaults.get("min_success", 0))),
            "max_success": int(custom.get("max_success", defaults.get("max_success", 100))),
            "duration": datetime.timedelta(
                seconds=custom.get(
                    "duration", defaults.get("duration", datetime.timedelta()).total_seconds()
                )
            ),
            "min_loss": defaults.get("min_loss", 0),
            "max_loss": defaults.get("max_loss", 0),
            "police_chance": custom.get("police_chance", defaults.get("police_chance", 0.0)),
            "jail_time": datetime.timedelta(
                seconds=custom.get(
                    "jail_time", defaults.get("jail_time", datetime.timedelta()).total_seconds()
                )
            ),
        }

    async def get_item_cost(self, item_name: str) -> int:
        """Retrieve item cost, merging default with custom config."""
        default_cost = ITEMS.get(item_name, (None, {}))[1].get("cost", 0)
        custom = await self.config.item_settings.get_raw(item_name, default={})
        return int(custom.get("cost", default_cost))

    @commands.hybrid_group()
    @commands.guild_only()
    async def heist(self, ctx):
        """Heist game."""

    @heist.group(name="equip")
    async def heist_equip(self, ctx: commands.Context):
        """Equip items for heists."""

    @heist_equip.command(name="shield")
    async def equip_shield(self, ctx: commands.Context, shield_type: str):
        """Equip a shield from your inventory."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't equip during a heist"
            )
        shield_type = shield_type.lower().replace(" ", "_")
        if shield_type not in ITEMS or ITEMS[shield_type][1]["type"] != "shield":
            return await ctx.send("Invalid shield type.")
        inventory = await self.config.user(ctx.author).inventory()
        if inventory.get(shield_type, 0) <= 0:
            return await ctx.send(
                f"You don't have a {shield_type.replace('_', ' ').title()} in your inventory."
            )
        equipped = await self.config.user(ctx.author).equipped()
        equipped["shield"] = shield_type
        await self.config.user(ctx.author).equipped.set(equipped)
        await ctx.send(f"Equipped {shield_type.replace('_', ' ').title()} as your shield.")

    @heist_equip.command(name="tool")
    async def equip_tool(self, ctx: commands.Context, tool_type: str):
        """Equip a tool from your inventory."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't equip during a heist"
            )
        tool_type = tool_type.lower().replace(" ", "_")
        if tool_type not in ITEMS or ITEMS[tool_type][1]["type"] != "tool":
            return await ctx.send("Invalid tool type.")
        inventory = await self.config.user(ctx.author).inventory()
        if inventory.get(tool_type, 0) <= 0:
            return await ctx.send(
                f"You don't have a {tool_type.replace('_', ' ').title()} in your inventory."
            )
        equipped = await self.config.user(ctx.author).equipped()
        equipped["tool"] = tool_type
        await self.config.user(ctx.author).equipped.set(equipped)
        await ctx.send(f"Equipped {tool_type.replace('_', ' ').title()} as your tool.")

    @heist_equip.command(name="consumable")
    async def equip_consumable(self, ctx: commands.Context, consumable_type: str):
        """Equip a consumable from your inventory."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't equip during a heist"
            )
        consumable_type = consumable_type.lower().replace(" ", "_")
        if consumable_type not in ITEMS or ITEMS[consumable_type][1]["type"] != "consumable":
            return await ctx.send("Invalid consumable type.")
        inventory = await self.config.user(ctx.author).inventory()
        if inventory.get(consumable_type, 0) <= 0:
            return await ctx.send(
                f"You don't have a {consumable_type.replace('_', ' ').title()} in your inventory."
            )
        equipped = await self.config.user(ctx.author).equipped()
        equipped["consumable"] = consumable_type
        await self.config.user(ctx.author).equipped.set(equipped)
        await ctx.send(f"Equipped {consumable_type.replace('_', ' ').title()} as your consumable.")

    @heist_equip.command(name="unequip")
    async def equip_unequip_item(self, ctx: commands.Context, item_type: str):
        """Unequip a specific item type."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't equip during a heist"
            )
        item_type = item_type.lower()
        if item_type not in ["shield", "tool", "consumable"]:
            return await ctx.send("Invalid item type. Use 'shield', 'tool', or 'consumable'.")
        equipped = await self.config.user(ctx.author).equipped()
        if equipped[item_type] is None:
            return await ctx.send(f"No {item_type} equipped.")
        equipped[item_type] = None
        await self.config.user(ctx.author).equipped.set(equipped)
        await ctx.send(f"Unequipped your {item_type}.")

    @heist.command(name="shop", aliases=["shopping"])
    @commands.bot_has_permissions(embed_links=True)
    async def buy_item(self, ctx: commands.Context):
        """Buy items like shields or tools to aid in heists."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if not await self.check_debt(ctx):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send("You cannot go shopping while on a heist.")

        view = ShopView(self, ctx)
        currency_name = await bank.get_currency_name(ctx.guild)
        embed = discord.Embed(
            title="Available Items",
            description="Select an item to purchase.",
            color=await ctx.embed_color(),
        )
        shop_items = [
            (name, (emoji, data))
            for name, (emoji, data) in ITEMS.items()
            if data["type"] in ["shield", "tool", "consumable"] and "cost" in data
        ]
        for name, (emoji, data) in shop_items[:25]:
            cost = await self.get_item_cost(name)
            effect = ""
            if data["type"] == "shield":
                effect = f"Reduces loss by {data['reduction']*100:.1f}% (single use)"
            elif data["type"] == "tool":
                effect = f"Boosts success by {data['boost']*100:.0f}% for {data['for_heist'].replace('_', ' ').title()} (single use)"
            elif data["type"] == "consumable":
                effect = f"Reduces risk by {data['risk_reduction']*100:.0f}% (single use)"
            embed.add_field(
                name=f"{emoji} {name.replace('_', ' ').title()}",
                value=f"**Cost**: {cost:,} {currency_name}\n**Effect**: {effect}",
                inline=True,
            )
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @heist.command(name="start")
    @commands.bot_has_permissions(embed_links=True)
    async def do_heist(self, ctx: commands.Context):
        """Attempt a heist to steal items."""
        if not await self.check_debt(ctx):
            return
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send("You have an active heist ongoing. Wait for it to finish.")

        equipped = await self.config.user(ctx.author).equipped()
        inventory = await self.config.user(ctx.author).inventory()
        warnings = []
        for item_type in ["shield", "tool", "consumable"]:
            equipped_item = equipped[item_type]
            if equipped_item and inventory.get(equipped_item, 0) <= 0:
                warnings.append(
                    f"Your equipped {item_type} ({equipped_item.replace('_', ' ').title()}) is out of stock and will not be used."
                )
                equipped[item_type] = None  # Unequip
        await self.config.user(ctx.author).equipped.set(equipped)
        if warnings:
            await ctx.send("\n".join(warnings))

        heist_settings = {}
        for name in HEISTS.keys():
            heist_settings[name] = await self.get_heist_settings(name)

        view = HeistView(self, ctx, heist_settings)
        currency_name = await bank.get_currency_name(ctx.guild)
        embed = discord.Embed(
            title="Select a Heist",
            description="Choose a heist type. Higher levels have better rewards but higher risk and lower success rates.",
            color=await ctx.embed_color(),
        )
        for name, data in heist_settings.items():
            loot_item = name if name in ITEMS and ITEMS[name][1]["type"] == "loot" else None
            if loot_item:
                min_reward = ITEMS[loot_item][1]["min_sell"]
                max_reward = ITEMS[loot_item][1]["max_sell"]
            else:
                min_reward = data["min_reward"]
                max_reward = data["max_reward"]
            cooldown_minutes = data["cooldown"].total_seconds() / 60
            cooldown_display = (
                f"{int(cooldown_minutes)}m"
                if cooldown_minutes < 60
                else f"{int(cooldown_minutes // 60)}h"
            )
            embed.add_field(
                name=f"{data['emoji']} {name.replace('_', ' ').title()}",
                value=(
                    f"**Reward**: {min_reward:,}-{max_reward:,} {currency_name}\n"
                    f"**Risk**: {data['risk']*100:.0f}%\n"
                    f"**Cooldown**: {cooldown_display}\n"
                    f"**Success**: {data['min_success']}-{data['max_success']}%\n"
                    f"**Duration**: {int(data['duration'].total_seconds() // 60)} min"
                ),
                inline=True,
            )
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @heist.command(name="bailout")
    async def bailout(self, ctx: commands.Context, member: discord.Member = None):
        """Pay bail to get yourself or another user out of jail."""
        jailed_user = member if member else ctx.author
        if not await self._is_in_jail(jailed_user):
            return await ctx.send(f"{jailed_user.display_name} is not in jail!")
        await self.check_jail(ctx, jailed_user)

    @heist.command(name="inventory", aliases=["inv"])
    @commands.bot_has_permissions(embed_links=True)
    async def check_inventory(self, ctx: commands.Context):
        """Check your stolen items and tools."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't check inventory during heist"
            )
        inventory = await self.config.user(ctx.author).inventory()
        debt = await self.config.user(ctx.author).debt()
        currency_name = await bank.get_currency_name(ctx.guild)
        if not inventory and debt <= 0:
            return await ctx.send("Your inventory is empty and you have no debt.")

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Inventory",
            description="Items you can sell or use.",
            color=await ctx.embed_color(),
        )
        if debt > 0:
            embed.add_field(name="Debt", value=f"Owed: {debt:,} {currency_name}", inline=False)
        equipped = await self.config.user(ctx.author).equipped()
        for item, count in inventory.items():
            emoji, data = ITEMS.get(item, ("❓", {"type": "unknown"}))
            desc = ""
            is_equipped = False
            if data["type"] == "tool":
                desc = f"Boosts {data['for_heist'].replace('_', ' ').title()} success by {data['boost']*100:.0f}% (single use)"
                if equipped["tool"] == item:
                    is_equipped = True
            elif data["type"] == "shield":
                desc = f"Reduces loss by {data['reduction']*100:.1f}% (single use)"
                if equipped["shield"] == item:
                    is_equipped = True
            elif data["type"] == "consumable":
                desc = f"Reduces risk by {data['risk_reduction']*100:.0f}% (single use)"
                if equipped["consumable"] == item:
                    is_equipped = True
            elif data["type"] == "loot":
                desc = f"Sell for {data['min_sell']:,} to {data['max_sell']:,} {currency_name}"
            elif data["type"] == "material":
                desc = f"Material for crafting. Sell for {data['min_sell']:,} to {data['max_sell']:,} {currency_name}"
            else:
                desc = "Unknown item"
            if is_equipped:
                desc += " (equipped)"
            embed.add_field(
                name=f"{emoji} {item.replace('_', ' ').title()} (x{count})",
                value=desc,
                inline=True,
            )
        await ctx.send(embed=embed)

    @heist.command(name="sell")
    async def sell_item(self, ctx: commands.Context, item: str, amount: int = 1):
        """Sell a stolen item or material for currency."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't sell while on heist."
            )
        inventory = await self.config.user(ctx.author).inventory()
        item = item.lower().replace(" ", "_")
        if item not in ITEMS or ITEMS[item][1]["type"] not in ["loot", "material"]:
            return await ctx.send("Invalid item type. Only loot and materials can be sold.")
        if inventory.get(item, 0) < amount:
            return await ctx.send(
                f"You don't have enough {item.replace('_', ' ').title()} to sell."
            )
        data = ITEMS[item][1]
        sell_price = sum(random.randint(data["min_sell"], data["max_sell"]) for _ in range(amount))
        await bank.deposit_credits(ctx.author, sell_price)
        inventory[item] -= amount
        if inventory[item] <= 0:
            del inventory[item]
        await self.config.user(ctx.author).inventory.set(inventory)
        currency_name = await bank.get_currency_name(ctx.guild)
        await ctx.send(
            f"Sold {amount} {item.replace('_', ' ').title()} for {sell_price:,} {currency_name}."
        )

    @heist.command(name="craft")
    async def craft_item(self, ctx: commands.Context, recipe_name: str):
        """
        Craft upgraded shields or tools using materials from heists.

        Craftable items are stronger than shop-bought items but require specific materials.

        **Vaild craftable items**:
        - `reinforced_wooden_shield`, `enhanced_pickpocket_gloves`, `reinforced_iron_shield`, `reinforced_steel_shield`, `reinforced_titanium_shield`, `reinforced_diamond_shield`, `enhanced_crowbar`, `enhanced_glass_cutter`, `enhanced_brass_knuckles`, `enhanced_laser_jammer`, `enhanced_hacking_device`, `enhanced_store_key`, `enhanced_lockpick_kit`, `enhanced_grappling_hook`, `enhanced_bike_tool`, `enhanced_car_tool` and `enhanced_motorcycle_tool`.
        """
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't craft while on heist."
            )
        recipe_name = recipe_name.lower().replace(" ", "_")
        if recipe_name not in RECIPES:
            return await ctx.send("Invalid recipe.")
        recipe = RECIPES[recipe_name]
        inventory = await self.config.user(ctx.author).inventory()
        missing = []
        for mat, qty in recipe["materials"].items():
            if inventory.get(mat, 0) < qty:
                missing.append(
                    f"{mat.replace('_', ' ').title()} (need {qty}, have {inventory.get(mat, 0)})"
                )
        if missing:
            return await ctx.send(f"Missing materials: {', '.join(missing)}")
        for mat, qty in recipe["materials"].items():
            inventory[mat] -= qty
            if inventory[mat] <= 0:
                del inventory[mat]
        result = recipe["result"]
        inventory[result] = inventory.get(result, 0) + recipe["quantity"]
        await self.config.user(ctx.author).inventory.set(inventory)
        await ctx.send(f"Crafted {recipe['quantity']} {result.replace('_', ' ').title()}!")

    @heist.command(name="shield")
    async def check_shield(self, ctx: commands.Context):
        """Check your active shield status."""
        if not await self.check_jail(ctx, ctx.author):
            return
        equipped = await self.config.user(ctx.author).equipped()
        equipped_shield = equipped["shield"]
        if equipped_shield:
            inventory = await self.config.user(ctx.author).inventory()
            count = inventory.get(equipped_shield, 0)
            if count > 0:
                emoji, data = ITEMS[equipped_shield]
                return await ctx.send(
                    f"Active {emoji} {equipped_shield.replace('_', ' ').title()} shield: Reduces loss by {data['reduction']*100:.1f}% (single use). You have {count}."
                )
        await ctx.send("No active shield.")

    @heist.command(name="status")
    async def heist_status(self, ctx: commands.Context):
        """Check your active heist status."""
        active = await self.config.user(ctx.author).active_heist()
        jail = await self.config.user(ctx.author).jail()
        msg = ""
        if active:
            end_time = datetime.datetime.fromtimestamp(
                active["end_time"], tz=datetime.timezone.utc
            )
            remaining = end_time - datetime.datetime.now(datetime.timezone.utc)
            msg += (
                f"Active {active['type'].replace('_', ' ').title()} heist. Ends in {remaining}.\n"
            )
        if jail:
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            if now < jail["end_time"]:
                end_timestamp = int(jail["end_time"])
                msg += f"In jail until <t:{end_timestamp}:f> (<t:{end_timestamp}:R>)."
            else:
                await self.config.user(ctx.author).jail.clear()
        if not msg:
            msg = "No active heist or jail time."
        await ctx.send(msg)

    @heist.command(name="cooldowns", aliases=["cooldown"])
    @commands.bot_has_permissions(embed_links=True)
    async def check_cooldowns(self, ctx: commands.Context):
        """Check cooldowns for all heists."""
        if not await self.check_jail(ctx, ctx.author):
            return
        cooldowns = await self.config.user(ctx.author).heist_cooldowns()
        now = datetime.datetime.now(datetime.timezone.utc)
        embed = discord.Embed(
            title="Heist Cooldowns",
            description="",
            color=await ctx.embed_color(),
        )
        any_on_cooldown = False
        for heist_type in sorted(HEISTS.keys(), key=lambda x: x.replace("_", " ").title()):
            data = await self.get_heist_settings(heist_type)
            last_timestamp = cooldowns.get(heist_type)
            heist_name = heist_type.replace("_", " ").title()
            if last_timestamp:
                last_time = datetime.datetime.fromtimestamp(
                    last_timestamp, tz=datetime.timezone.utc
                )
                if now - last_time < data["cooldown"]:
                    remaining = data["cooldown"] - (now - last_time)
                    end_time = now + remaining
                    end_timestamp = int(end_time.timestamp())
                    embed.description += (
                        f"{data['emoji']} `{heist_name + ':':<18}`: <t:{end_timestamp}:R>\n"
                    )
                    any_on_cooldown = True
                else:
                    embed.description += f"{data['emoji']} `{heist_name + ':':<18}`: Ready\n"
            else:
                embed.description += f"{data['emoji']} `{heist_name + ':':<18}`: Ready\n"
        if not any_on_cooldown:
            embed.description = "All heists are ready!"
        await ctx.send(embed=embed)

    @commands.group(with_app_command=False)
    @commands.is_owner()
    async def heistset(self, ctx):
        """Manage global heist settings."""

    @heistset.command(name="set")
    async def heistset_set(self, ctx: commands.Context):
        """
        Modify a parameter for a specific heist type using a modal.

        You can edit multiple prices until the interaction times out.

        **Arguments**
        - heist_type: Valid options:
            - `pocket_steal`, `atm_smash`, `store_robbery`, `jewelry_store`, `fight_club`, `art_gallery`, `casino_vault`, `museum_relic`, `luxury_yacht`, `street_bike`, `street_motorcycle`, `street_car`, `corporate`, `bank`, `elite`.
        - param: The parameter to change. Valid options:
            - `risk`: Failure probability (0–100, percentage).
           - `min_reward`: Minimum reward amount (credits, non-negative).
           - `max_reward`: Maximum reward amount (credits, non-negative, must be above min_reward).
           - `cooldown`: Time before the heist can be attempted again (seconds, minimum 60).
           - `min_success`: Minimum success chance (0–100, percentage).
           - `max_success`: Maximum success chance (0–100, percentage, must be above min_success).
           - `duration`: Time to complete the heist (seconds, minimum 30).
           - `police_chance`: Chance of getting caught (0–100, percentage).
           - `jail_time`: Jail duration if caught (seconds, minimum 60).
        - value: The new value for the parameter (percentage for risk/success, credits for rewards, seconds for cooldown/duration).
        """
        view = HeistConfigView(self, ctx)
        message = await ctx.send(
            "Click the button to configure heist settings.", view=view, ephemeral=True
        )
        view.message = message

    @heistset.command(name="price")
    async def heistset_price(self, ctx: commands.Context):
        """
        Modify the price of an item in the shop using a modal.

        You can edit multiple prices until the interaction times out.
        **Vaild options**:
        - `wooden_shield`, `iron_shield`, `steel_shield`, `titanium_shield`, `diamond_shield`, `full`, `bike_tool`, `car_tool`, `motorcycle_tool`, `pickpocket_gloves`, `crowbar`, `glass_cutter`, `brass_knuckles`, `laser_jammer`, `hacking_device`, `store_key`, `lockpick_kit` and `grappling_hook`
        """
        view = ItemPriceConfigView(self, ctx)
        message = await ctx.send(
            "Click the button to configure item prices.", view=view, ephemeral=True
        )
        view.message = message

    @heistset.command(name="reset")
    async def heistset_reset(self, ctx: commands.Context, heist_type: str = None):
        """Reset heist settings to default values.

        If no heist_type is provided, resets all heists.
        """
        async with self.config.heist_settings() as settings:
            if heist_type:
                heist_type = heist_type.lower().replace(" ", "_")
                if heist_type not in HEISTS:
                    return await ctx.send(f"Invalid heist type: {heist_type}")
                settings[heist_type] = {
                    "risk": HEISTS[heist_type]["risk"],
                    "min_reward": HEISTS[heist_type]["min_reward"],
                    "max_reward": HEISTS[heist_type]["max_reward"],
                    "cooldown": HEISTS[heist_type]["cooldown"].total_seconds(),
                    "min_success": HEISTS[heist_type]["min_success"],
                    "max_success": HEISTS[heist_type]["max_success"],
                    "duration": HEISTS[heist_type]["duration"].total_seconds(),
                    "police_chance": HEISTS[heist_type]["police_chance"],
                    "jail_time": HEISTS[heist_type]["jail_time"].total_seconds(),
                }
                await ctx.send(
                    f"Reset settings for {heist_type.replace('_', ' ').title()} to defaults."
                )
            else:
                settings.clear()
                settings.update(
                    {
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
                    }
                )
                await ctx.send("Reset all heist settings to defaults.")

    @heistset.command(name="resetprice")
    async def heistset_resetprice(self, ctx: commands.Context, item_name: str = None):
        """Reset item prices to default values.

        If no item_name is provided, resets all item prices.
        """
        async with self.config.item_settings() as settings:
            if item_name:
                item_name = item_name.lower().replace(" ", "_")
                if item_name not in ITEMS or "cost" not in ITEMS[item_name][1]:
                    return await ctx.send(f"Invalid item: {item_name}")
                settings[item_name] = {"cost": ITEMS[item_name][1]["cost"]}
                await ctx.send(
                    f"Reset price for {item_name.replace('_', ' ').title()} to default."
                )
            else:
                settings.clear()
                settings.update(
                    {
                        name: {"cost": data["cost"]}
                        for name, (_, data) in ITEMS.items()
                        if "cost" in data
                    }
                )
                await ctx.send("Reset all item prices to defaults.")

    @heistset.command(name="show")
    @commands.bot_has_permissions(embed_links=True)
    async def heistset_show(self, ctx: commands.Context, heist_type: str = None):
        """Show current settings for a heist or all heists.

        Parameters:
        - heist_type: The heist to show (e.g., pocket_steal). Omit for all heists.
        """
        heist_type = heist_type.lower().replace(" ", "_") if heist_type else None
        if heist_type and heist_type not in HEISTS:
            return await ctx.send(f"Invalid heist type: {heist_type}")

        embed = discord.Embed(
            title="Heist Settings",
            description=f"Settings for {'all heists' if not heist_type else heist_type.replace('_', ' ').title()} (custom values marked with ⭐)",
            color=await ctx.embed_color(),
        )

        heists_to_show = [heist_type] if heist_type else sorted(HEISTS.keys())
        current_settings = await self.config.heist_settings()
        for name in heists_to_show:
            data = await self.get_heist_settings(name)
            custom = current_settings.get(name, {})
            defaults = HEISTS.get(name, {})
            is_custom = {
                param: param in custom
                and (
                    custom[param] != defaults.get(param, datetime.timedelta()).total_seconds()
                    if param in ["cooldown", "duration", "jail_time"]
                    else custom[param] != defaults.get(param, 0)
                )
                for param in [
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
            }
            loot_item = name if name in ITEMS and ITEMS[name][1]["type"] == "loot" else None
            reward_text = (
                f"{ITEMS[loot_item][1]['min_sell']:,}-{ITEMS[loot_item][1]['max_sell']:,} credits"
                if loot_item
                else f"{data['min_reward']:,}-{data['max_reward']:,} credits{' ⭐' if is_custom['min_reward'] or is_custom['max_reward'] else ''}"
            )
            field_value = (
                f"Reward: {reward_text}\n"
                f"Risk: {data['risk']*100:.0f}%{' ⭐' if is_custom['risk'] else ''}\n"
                f"Success: {data['min_success']}-{data['max_success']}%{' ⭐' if is_custom['min_success'] or is_custom['max_success'] else ''}\n"
                f"Cooldown: {data['cooldown'].total_seconds() / 3600:.1f}h{' ⭐' if is_custom['cooldown'] else ''}\n"
                f"Duration: {int(data['duration'].total_seconds() // 60)} min{' ⭐' if is_custom['duration'] else ''}\n"
                f"Police Chance: {data['police_chance']*100:.0f}%{' ⭐' if is_custom['police_chance'] else ''}\n"
                f"Jail Time: {data['jail_time'].total_seconds() / 3600:.1f}h{' ⭐' if is_custom['jail_time'] else ''}\n"
                f"Loss: {data['min_loss']:,}-{data['max_loss']:,} credits"
            )
            embed.add_field(
                name=f"{data['emoji']} {name.replace('_', ' ').title()}",
                value=field_value,
                inline=True,
            )
        await ctx.send(embed=embed)

    @heistset.command(name="showprices")
    @commands.bot_has_permissions(embed_links=True)
    async def heistset_showprices(self, ctx: commands.Context, item_name: str = None):
        """Show current prices for an item or all shop items.

        Parameters:
        - item_name: The item to show (e.g., wooden_shield). Omit for all items.
        """
        item_name = item_name.lower().replace(" ", "_") if item_name else None
        shop_items = {name: data for name, (_, data) in ITEMS.items() if "cost" in data}
        if item_name and item_name not in shop_items:
            return await ctx.send(f"Invalid item: {item_name}")

        embed = discord.Embed(
            title="Shop Item Prices",
            description=f"Prices for {'all items' if not item_name else item_name.replace('_', ' ').title()} (custom values marked with ⭐)",
            color=await ctx.embed_color(),
        )
        embed.set_footer(
            text="Use [p]heistset price to modify values or [p]heistset resetprice to revert to defaults."
        )

        items_to_show = [item_name] if item_name else sorted(shop_items.keys())
        current_settings = await self.config.item_settings()
        for name in items_to_show:
            data = shop_items[name]
            custom = current_settings.get(name, {})
            default_cost = data["cost"]
            is_custom = "cost" in custom and custom["cost"] != default_cost
            cost = custom.get("cost", default_cost)
            emoji = ITEMS[name][0]
            field_value = f"Cost: {cost:,}{' ⭐' if is_custom else ''}"
            embed.add_field(
                name=f"{emoji} {name.replace('_', ' ').title()}",
                value=field_value,
                inline=True,
            )
        await ctx.send(embed=embed)
