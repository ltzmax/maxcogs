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

import discord
from redbot.core import commands

from ..events import EventView, get_event_multiplier
from ..utils import HEISTS, ITEMS, fmt
from ..views import HeistConfigView, ItemPriceConfigView


class OwnerCommands:
    """Mixin containing all owner-only heistset commands."""

    @commands.group(with_app_command=False)
    @commands.is_owner()
    async def heistset(self, ctx):
        """Manage global heist settings."""

    @heistset.command(name="set")
    async def heistset_set(self, ctx: commands.Context):
        """Configure a heist's parameters.

        Select the heist, then the parameter, then enter the new value.
        """
        view = HeistConfigView(self, ctx)
        view.message = await ctx.send(view=view, ephemeral=True)

    @heistset.command(name="price")
    async def heistset_price(self, ctx: commands.Context):
        """Configure item shop prices.

        Select the item and enter the new price.
        """
        view = ItemPriceConfigView(self, ctx)
        view.message = await ctx.send(view=view, ephemeral=True)

    @heistset.command(name="reset")
    async def heistset_reset(self, ctx: commands.Context, heist_type: str | None = None):
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
    async def heistset_resetprice(self, ctx: commands.Context, item_name: str | None = None):
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

    @heistset.command(name="cooldownreset")
    async def heistset_cooldownreset(
        self, ctx: commands.Context, member: discord.Member, heist_type: str | None = None
    ):
        """Reset heist cooldowns for a user.

        If no heist_type is provided, resets all cooldowns for that user.

        **Arguments**
        - `<member>` The member whose cooldowns to reset.
        - `[heist_type]` The specific heist to reset. Omit to reset all.
        """
        if heist_type:
            heist_type = heist_type.lower().replace(" ", "_")
            if heist_type not in HEISTS:
                return await ctx.send(f"Invalid heist type: `{heist_type}`.")
            async with self.config.user(member).heist_cooldowns() as cooldowns:
                cooldowns.pop(heist_type, None)
            await ctx.send(f"Reset **{fmt(heist_type)}** cooldown for {member.display_name}.")
        else:
            await self.config.user(member).heist_cooldowns.set({})
            await ctx.send(f"Reset all heist cooldowns for {member.display_name}.")

    @heistset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def heistset_show(self, ctx: commands.Context, heist_type: str | None = None):
        """Show current settings for a heist or all heists."""
        heist_type = heist_type.lower().replace(" ", "_") if heist_type else None
        if heist_type and heist_type not in HEISTS:
            return await ctx.send(f"Invalid heist type: {heist_type}")

        embed = discord.Embed(
            title="Heist Settings",
            description=f"Settings for {'all heists' if not heist_type else heist_type.replace('_', ' ').title()} (custom values marked with ⭐)",
            color=await ctx.embed_color(),
        )

        heists_to_show = (
            [heist_type]
            if heist_type
            else [n for n in sorted(HEISTS.keys()) if not HEISTS[n].get("crew_size")]
        )
        current_settings = await self.config.heist_settings()
        for name in heists_to_show:
            data = await self.get_heist_settings(name)
            custom = current_settings.get(name, {})
            defaults = HEISTS.get(name, {})
            _timedelta_params = {"cooldown", "duration", "jail_time"}
            is_custom = {}
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
            ]:
                if param not in custom:
                    is_custom[param] = False
                    continue
                default_val = defaults.get(param)
                if param in _timedelta_params:
                    default_secs = (
                        default_val.total_seconds()
                        if isinstance(default_val, datetime.timedelta)
                        else 0.0
                    )
                    is_custom[param] = custom[param] != default_secs
                else:
                    is_custom[param] = custom[param] != (default_val or 0)
            loot_item = name if name in ITEMS and ITEMS[name][1]["type"] == "loot" else None
            reward_text = (
                f"{ITEMS[loot_item][1]['min_sell']:,}-{ITEMS[loot_item][1]['max_sell']:,} credits"
                if loot_item
                else f"{data['min_reward']:,}-{data['max_reward']:,} credits{' ⭐' if is_custom['min_reward'] or is_custom['max_reward'] else ''}"
            )
            field_value = (
                f"Reward: {reward_text}\n"
                f"Risk: {data['risk'] * 100:.0f}%{' ⭐' if is_custom['risk'] else ''}\n"
                f"Success: {data['min_success']}-{data['max_success']}%{' ⭐' if is_custom['min_success'] or is_custom['max_success'] else ''}\n"
                f"Cooldown: {data['cooldown'].total_seconds() / 3600:.1f}h{' ⭐' if is_custom['cooldown'] else ''}\n"
                f"Duration: {int(data['duration'].total_seconds() // 60)} min{' ⭐' if is_custom['duration'] else ''}\n"
                f"Police Chance: {data['police_chance'] * 100:.0f}%{' ⭐' if is_custom['police_chance'] else ''}\n"
                f"Jail Time: {data['jail_time'].total_seconds() / 3600:.1f}h{' ⭐' if is_custom['jail_time'] else ''}\n"
                f"Loss: {data['min_loss']:,}-{data['max_loss']:,} credits"
            )
            embed.add_field(
                name=f"{data['emoji']} {name.replace('_', ' ').title()}",
                value=field_value,
                inline=True,
            )
        await ctx.send(embed=embed)

    @heistset.group(name="event")
    async def heistset_event(self, ctx):
        """Manage heist reward events."""

    @heistset_event.command(name="start")
    async def heistset_event_start(
        self, ctx: commands.Context, multiplier: int, duration: int
    ):
        """Start a reward event.

        **Arguments**
        - `<multiplier>` Reward multiplier (2–5).
        - `<duration>` Duration in minutes.
        """
        if not 2 <= multiplier <= 5:
            return await ctx.send("Multiplier must be between 2 and 5.")
        if duration < 1:
            return await ctx.send("Duration must be at least 1 minute.")
        ends_at = (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=duration)
        ).timestamp()
        await self.config.event_multiplier.set(multiplier)
        await self.config.event_ends_at.set(ends_at)
        end_ts = int(ends_at)
        await ctx.send(
            f"🎉 **{multiplier}x reward event** started! Ends <t:{end_ts}:R> (<t:{end_ts}:f>)."
        )

    @heistset_event.command(name="stop")
    async def heistset_event_stop(self, ctx: commands.Context):
        """Stop the current reward event."""
        await self.config.event_multiplier.set(1)
        await self.config.event_ends_at.set(None)
        await ctx.send("Event stopped.")

    @heistset_event.command(name="status")
    async def heistset_event_status(self, ctx: commands.Context):
        """Show current event status."""
        view = await EventView.create(self, ctx)
        view.message = await ctx.send(view=view)

    @heistset.command(name="showprices")
    @commands.bot_has_permissions(embed_links=True)
    async def heistset_showprices(self, ctx: commands.Context, item_name: str | None = None):
        """Show current prices for an item or all shop items."""
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
            embed.add_field(
                name=f"{emoji} {name.replace('_', ' ').title()}",
                value=f"Cost: {cost:,}{' ⭐' if is_custom else ''}",
                inline=True,
            )
        await ctx.send(embed=embed)
