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

import datetime
import random

import discord
from redbot.core import bank, commands
from redbot.core.utils.chat_formatting import humanize_number

from ..leveling import MAX_LEVEL, get_level, level_success_bonus, xp_bar, xp_progress
from ..utils import HEISTS, ITEMS, fmt
from ..views import CraftView, CrewLobbyView, EquipView, HeistSelectionView, ShopView


def _heat_bar(heat: int, max_heat: int = 20, length: int = 20) -> str:
    """Render heat as a dot progress bar."""
    filled = min(round(heat / max_heat * length), length)
    bar = "●" * filled + "○" * (length - filled)
    pct = min(heat / max_heat * 100, 100)
    return f"`{bar}` {pct:.0f}%"


class UserCommands:
    """Mixin containing all player-facing heist commands."""

    @commands.hybrid_group()
    @commands.guild_only()
    async def heist(self, ctx):
        """Heist game."""

    @heist.command(name="equip")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def heist_equip(self, ctx: commands.Context):
        """Equip or unequip items from your inventory.

        Shows only items you currently own. Each slot (shield, tool)
        has its own select menu. Use the unequip buttons to clear a slot.
        """
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't equip during a heist."
            )

        inventory = await self.config.user(ctx.author).inventory()
        equipped = await self.config.user(ctx.author).equipped()
        view = EquipView(self, ctx, inventory, equipped)
        view.message = await ctx.send(view=view)

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

        currency_name = await bank.get_currency_name(ctx.guild)
        costs = {
            name: await self.get_item_cost(name)
            for name, (_, data) in ITEMS.items()
            if "cost" in data
        }
        view = ShopView(self, ctx, currency_name, costs)
        view.message = await ctx.send(view=view)

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
                equipped[item_type] = None
        await self.config.user(ctx.author).equipped.set(equipped)
        if warnings:
            await ctx.send("\n".join(warnings))

        _raw_settings = await self.config.heist_settings()
        heist_settings = {}
        for name in HEISTS:
            if HEISTS[name].get("crew_size"):
                continue
            defaults = HEISTS[name]
            custom = _raw_settings.get(name, {})
            heist_settings[name] = {
                "emoji": defaults.get("emoji", "❓"),
                "risk": custom.get("risk", defaults.get("risk", 0.0)),
                "min_reward": int(custom.get("min_reward", defaults.get("min_reward", 0))),
                "max_reward": int(custom.get("max_reward", defaults.get("max_reward", 0))),
                "cooldown": datetime.timedelta(
                    seconds=custom.get("cooldown", defaults["cooldown"].total_seconds())
                ),
                "min_success": int(custom.get("min_success", defaults.get("min_success", 0))),
                "max_success": int(custom.get("max_success", defaults.get("max_success", 100))),
                "duration": datetime.timedelta(
                    seconds=custom.get("duration", defaults["duration"].total_seconds())
                ),
                "min_loss": defaults.get("min_loss", 0),
                "max_loss": defaults.get("max_loss", 0),
                "police_chance": custom.get("police_chance", defaults.get("police_chance", 0.0)),
                "material_drop_chance": defaults.get("material_drop_chance", 0.0),
                "jail_time": datetime.timedelta(
                    seconds=custom.get("jail_time", defaults["jail_time"].total_seconds())
                ),
            }

        currency_name = await bank.get_currency_name(ctx.guild)
        player_xp = await self.config.user(ctx.author).xp()
        player_level = get_level(player_xp)
        view = HeistSelectionView(self, ctx, heist_settings, currency_name, player_level)
        view.message = await ctx.send(view=view)

    @heist.command(name="crew")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def crew_heist(self, ctx: commands.Context):
        """Organise a 4-player crew robbery for massive rewards.

        Start a lobby: 3 others must join before you can begin.
        Each player's tools and shields apply independently.
        Rewards are split equally among all crew members.
        """
        if not await self.check_debt(ctx):
            return
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send("You have an active heist ongoing. Wait for it to finish.")

        data = await self.get_heist_settings("crew_robbery")
        currency_name = await bank.get_currency_name(ctx.guild)
        await self.config.user(ctx.author).active_heist.set(
            {
                "type": "crew_robbery",
                "end_time": datetime.datetime.now(datetime.timezone.utc).timestamp()
                + data["duration"].total_seconds(),
                "channel_id": ctx.channel.id,
                "lobby": True,
            }
        )
        view = CrewLobbyView(self, ctx, data, currency_name)
        view.message = await ctx.send(view=view)

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

        equipped = await self.config.user(ctx.author).equipped()
        sections: dict[str, list[str]] = {
            "🛡️ Shields": [],
            "🔧 Tools": [],
            "💊 Consumables": [],
            "💰 Loot": [],
            "🧱 Materials": [],
        }

        for item, count in inventory.items():
            emoji, data = ITEMS.get(item, ("❓", {"type": "unknown"}))
            is_equipped = (
                equipped.get("shield") == item
                or equipped.get("tool") == item
                or equipped.get("consumable") == item
            )
            equipped_tag = " *(equipped)*" if is_equipped else ""
            name_str = f"**{emoji} {fmt(item)} ×{count}**{equipped_tag}"

            match data["type"]:
                case "shield":
                    desc = f"-# Reduces loss by {data['reduction'] * 100:.1f}% (single use)"
                    sections["🛡️ Shields"].append(f"{name_str}\n{desc}\n")
                case "tool":
                    desc = f"-# +{data['boost'] * 100:.0f}% success on {fmt(data['for_heist'])} (single use)"
                    sections["🔧 Tools"].append(f"{name_str}\n{desc}\n")
                case "consumable":
                    desc = f"-# Reduces risk by {data['risk_reduction'] * 100:.0f}% (single use)"
                    sections["💊 Consumables"].append(f"{name_str}\n{desc}\n")
                case "loot":
                    desc = f"-# Sell for {data['min_sell']:,}–{data['max_sell']:,} {currency_name}"
                    sections["💰 Loot"].append(f"{name_str}\n{desc}\n")
                case "material":
                    desc = f"-# Craft or sell for {data['min_sell']:,}–{data['max_sell']:,} {currency_name}"
                    sections["🧱 Materials"].append(f"{name_str}\n{desc}\n")
                case _:
                    sections["💰 Loot"].append(f"{name_str}\n")

        components: list = [discord.ui.TextDisplay(f"## 🎒 {ctx.author.display_name}'s Inventory")]

        if debt > 0:
            components.append(discord.ui.Separator())
            components.append(discord.ui.TextDisplay(f"**💸 Debt:** {debt:,} {currency_name}"))

        for section_name, items in sections.items():
            if items:
                components.append(discord.ui.Separator())
                components.append(discord.ui.TextDisplay(f"**{section_name}**\n" + "".join(items)))

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(discord.ui.Container(*components))
        await ctx.send(view=view)

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
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def craft_item(self, ctx: commands.Context):
        """Craft upgraded shields or tools using materials from heists."""
        if not await self.check_jail(ctx, ctx.author):
            return
        if await self._has_active_heist(ctx.author, ctx.channel.id):
            return await ctx.send(
                "You have an active heist ongoing. You can't craft while on heist."
            )

        inventory = await self.config.user(ctx.author).inventory()
        view = CraftView(self, ctx, inventory)
        view.message = await ctx.send(view=view)

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
                    f"Active {emoji} {equipped_shield.replace('_', ' ').title()} shield: "
                    f"Reduces loss by {data['reduction'] * 100:.1f}% (single use). You have {count}."
                )
        await ctx.send("No active shield.")

    @heist.command(name="profile")
    async def heist_status(self, ctx: commands.Context):
        """Check your active heist profile."""
        active = await self.config.user(ctx.author).active_heist()
        jail = await self.config.user(ctx.author).jail()
        heat = await self._get_effective_heat(ctx.author)
        stats = await self.config.user(ctx.author).stats()

        lines = [f"## 📊 {ctx.author.display_name}'s Profile"]

        if active:
            end_ts = int(active["end_time"])
            lines.append(
                f"\n**🎭 Active Heist:** {fmt(active['type'])}\n"
                f"Completes <t:{end_ts}:R> (<t:{end_ts}:f>)"
            )
        else:
            lines.append("\n**🎭 Active Heist:** None")

        if jail:
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            if now < jail["end_time"]:
                end_ts = int(jail["end_time"])
                bail = jail["bail_amount"]
                tax = int(bail * 0.15)
                lines.append(
                    f"\n**🚨 In Jail** until <t:{end_ts}:f> (<t:{end_ts}:R>)\n"
                    f"-# Bail: {bail:,} + {tax:,} tax = {bail + tax:,}"
                )
            else:
                await self.config.user(ctx.author).jail.clear()
                lines.append("\n**🚨 Jail:** Free")
        else:
            lines.append("\n**🚨 Jail:** Free")

        total = stats.get("success", 0) + stats.get("fail", 0) + stats.get("caught", 0)
        lines.append(
            f"\n**📈 Heist Stats**\n"
            f"✅ Success: {humanize_number(stats.get('success', 0))}\n"
            f"❌ Failed: {humanize_number(stats.get('fail', 0))}\n"
            f"🚨 Caught: {humanize_number(stats.get('caught', 0))}\n"
            f"Total: {humanize_number(total)}"
        )
        lines.append(f"\n**🌡️ Heat:**\n{_heat_bar(heat)}")

        xp = await self.config.user(ctx.author).xp()
        lvl, into, span, pct = xp_progress(xp)
        lv_bonus = level_success_bonus(lvl)
        lines.append(
            f"\n**🎓 Level {lvl}** / {MAX_LEVEL}\n"
            f"{xp_bar(pct)} {humanize_number(into)}/{humanize_number(span)} XP"
            + (f"  ·  +{lv_bonus * 100:.0f}% success bonus" if lv_bonus > 0 else "")
        )

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(discord.ui.Container(discord.ui.TextDisplay("\n".join(lines))))
        await ctx.send(view=view)

    @heist.command(name="level")
    async def heist_level(self, ctx: commands.Context, member: discord.Member = commands.Author):
        """Check heist level and XP progress."""
        xp = await self.config.user(member).xp()
        lvl, into, span, pct = xp_progress(xp)
        lv_bonus = level_success_bonus(lvl)

        # This will need to be here, please do not remove or move.
        from ..leveling import XP_TABLE

        if lvl >= MAX_LEVEL:
            next_line = "-# Max level reached!"
        else:
            xp_needed = XP_TABLE[lvl] - xp
            next_line = f"-# {humanize_number(xp_needed)} XP until level {lvl + 1}"

        lines = [
            f"## 🎓 {member.display_name}'s Level",
            f"\n**Level {lvl}** / {MAX_LEVEL}",
            f"{xp_bar(pct)} {humanize_number(into)}/{humanize_number(span)} XP",
            next_line,
        ]
        if lv_bonus > 0:
            lines.append(f"\n**Bonus:** +{lv_bonus * 100:.0f}% success chance on all heists")
        else:
            lines.append(
                "\n-# Earn XP by completing heists to gain success bonuses (+0.5% per level, max +20% at Lv.40)"
            )

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(discord.ui.Container(discord.ui.TextDisplay("\n".join(lines))))
        await ctx.send(view=view)

    @heist.command(name="cooldowns", aliases=["cooldown"])
    @commands.bot_has_permissions(embed_links=True)
    async def check_cooldowns(self, ctx: commands.Context):
        """Check cooldowns for all heists."""
        if not await self.check_jail(ctx, ctx.author):
            return
        cooldowns = await self.config.user(ctx.author).heist_cooldowns()
        now = datetime.datetime.now(datetime.timezone.utc)

        ready_lines = []
        cd_lines = []

        for heist_type in sorted(HEISTS.keys(), key=lambda x: fmt(x)):
            if HEISTS[heist_type].get("crew_size"):
                continue
            data = await self.get_heist_settings(heist_type)
            last_timestamp = cooldowns.get(heist_type)
            heist_label = f"{data['emoji']} {fmt(heist_type)}"
            if last_timestamp:
                last_time = datetime.datetime.fromtimestamp(
                    last_timestamp, tz=datetime.timezone.utc
                )
                if now - last_time < data["cooldown"]:
                    remaining = data["cooldown"] - (now - last_time)
                    end_ts = int((now + remaining).timestamp())
                    cd_lines.append(f"**{heist_label}** - <t:{end_ts}:R>")
                    continue
            ready_lines.append(f"**{heist_label}** - ✅ Ready")

        components: list = [discord.ui.TextDisplay("## ⏱️ Heist Cooldowns")]

        if cd_lines:
            components.append(discord.ui.Separator())
            components.append(discord.ui.TextDisplay("**On Cooldown**\n" + "\n".join(cd_lines)))

        if ready_lines:
            components.append(discord.ui.Separator())
            components.append(discord.ui.TextDisplay("**Ready**\n" + "\n".join(ready_lines)))

        if not cd_lines and not ready_lines:
            components.append(discord.ui.Separator())
            components.append(discord.ui.TextDisplay("All heists are ready!"))

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(discord.ui.Container(*components))
        await ctx.send(view=view)
