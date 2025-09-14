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
from redbot.core import bank, errors
from redbot.core.utils.views import ConfirmView

from .utils import HEISTS, ITEMS

log = getLogger("red.cogs.heist.handlers")


async def schedule_resolve(
    cog, user_id: int, seconds: float, heist_type: str, channel: discord.TextChannel = None
):
    try:
        await asyncio.sleep(seconds)
        user = cog.bot.get_user(user_id)
        if user and channel:
            await resolve_heist(cog, user, heist_type, channel)
        if user_id in cog.pending_tasks:
            del cog.pending_tasks[user_id]
    except asyncio.CancelledError:
        log.debug(f"Schedule resolve task cancelled for user {user_id} on heist {heist_type}")
        raise
    except Exception as e:
        log.error(
            f"Error in schedule_resolve for user {user_id}, heist {heist_type}: {e}", exc_info=True
        )


async def resolve_heist(
    cog,
    user: discord.User,
    heist_type: str,
    channel: discord.TextChannel,
    fallback_channel_id: int = None,
):
    try:
        data = await cog.get_heist_settings(heist_type)
        member = channel.guild.get_member(user.id)
        if not member:
            log.warning(
                f"User {user.id} not found in guild {channel.guild.id} for heist {heist_type}"
            )
            return
        currency_name = await bank.get_currency_name(channel.guild)
        inventory = await cog.config.user(member).inventory()
        tool_boost = 0.0
        used_tool = None
        equipped = await cog.config.user(member).equipped()
        equipped_tool = equipped["tool"]
        if (
            equipped_tool
            and inventory.get(equipped_tool, 0) > 0
            and ITEMS[equipped_tool][1].get("for_heist") == heist_type
        ):
            tool_boost = ITEMS[equipped_tool][1]["boost"]
            used_tool = equipped_tool
            inventory[used_tool] -= 1
            if inventory[used_tool] <= 0:
                del inventory[used_tool]
            await cog.config.user(member).inventory.set(inventory)
        active = await cog.config.user(member).active_heist()
        tax_agreed = active.get("tax_agreed", False)
        base_success = random.randint(data["min_success"], data["max_success"])
        success_chance = min((base_success + int(tool_boost * 100)) / 100, 1.0)
        success = random.random() < success_chance
        loot_item = (
            heist_type if heist_type in ITEMS and ITEMS[heist_type][1]["type"] == "loot" else None
        )
        reward = 0
        msg = ""
        if success:
            if loot_item:
                inventory[loot_item] = inventory.get(loot_item, 0) + 1
                await cog.config.user(member).inventory.set(inventory)
                msg = f"Success! You stole a {loot_item.replace('_', ' ').title()} from the {heist_type.replace('_', ' ').title()}."
            else:
                reward = random.randint(data["min_reward"], data["max_reward"])
                try:
                    await bank.deposit_credits(member, reward)
                except errors.BalanceTooHigh:
                    msg = f"Success! You would have gained {reward:,} {currency_name} from the {heist_type.replace('_', ' ').title()}, but your balance is too high."
                    reward = 0
                else:
                    msg = f"Success! You gained {reward:,} {currency_name} from the {heist_type.replace('_', ' ').title()}."
        else:
            loss = random.randint(data["min_loss"], data["max_loss"])
            reduction = 0.0
            equipped_shield = equipped["shield"]
            if equipped_shield and inventory.get(equipped_shield, 0) > 0:
                reduction = ITEMS[equipped_shield][1]["reduction"]
                inventory[equipped_shield] -= 1
                if inventory[equipped_shield] <= 0:
                    del inventory[equipped_shield]
                await cog.config.user(member).inventory.set(inventory)
            loss = int(loss * (1 - reduction))
            balance = await bank.get_balance(member)
            if loss > 0:
                if balance >= loss:
                    await bank.withdraw_credits(member, loss)
                    msg = f"Failed the {heist_type.replace('_', ' ').title()}! You lost {loss:,} {currency_name}."
                else:
                    debt = await cog.config.user(member).debt()
                    debt_to_add = loss
                    if tax_agreed:
                        tax = int(loss * 0.2)
                        debt_to_add += tax
                    await cog.config.user(member).debt.set(debt + debt_to_add)
                    msg = f"Failed the {heist_type.replace('_', ' ').title()}! You owe {debt_to_add:,} {currency_name} in debt{' (including 20% tax)' if tax_agreed else ''}.\nYou will need to pay it before starting a new heist."
            else:
                msg = f"Failed the {heist_type.replace('_', ' ').title()}! But your shield prevented any loss."
        if used_tool:
            msg += (
                f" (Used {used_tool.replace('_', ' ').title()} for +{tool_boost*100:.0f}% success)"
            )

        heat = await cog.config.user(member).heat()
        heat += 1
        await cog.config.user(member).heat.set(heat)
        material_heat = await cog.config.user(member).material_heat()
        material_heat += 1
        await cog.config.user(member).material_heat.set(material_heat)
        material_drop_chance = data.get("material_drop_chance", 0.0)
        adjusted_material_drop_chance = min(material_drop_chance + (material_heat * 0.04), 0.9)
        if random.random() < adjusted_material_drop_chance:
            await cog.config.user(member).material_heat.set(0)
            materials = [k for k, v in ITEMS.items() if v[1]["type"] == "material"]
            if materials:
                dropped_material = random.choice(materials)
                drop_qty = random.randint(1, 3) if success else random.randint(1, 2)
                inventory[dropped_material] = inventory.get(dropped_material, 0) + drop_qty
                await cog.config.user(member).inventory.set(inventory)
                msg += f"\nFound {drop_qty} {dropped_material.replace('_', ' ').title()} material!"

        base_police_chance = data["police_chance"]
        adjusted_police_chance = min(base_police_chance + (heat * 0.02), 0.9)
        if random.random() < adjusted_police_chance:
            await cog.config.user(member).heat.set(0)
            bail_amount = int(data["max_loss"] * random.uniform(0.5, 1.0))
            jail_duration = data["jail_time"]
            end_time = datetime.datetime.now(datetime.timezone.utc) + jail_duration
            await cog.config.user(member).jail.set(
                {"end_time": end_time.timestamp(), "bail_amount": bail_amount}
            )
            msg += f"\nBut you got caught by the police!"
            if success:
                if loot_item:
                    inventory[loot_item] = inventory.get(loot_item, 0) - 1
                    if inventory.get(loot_item, 0) <= 0 and loot_item in inventory:
                        del inventory[loot_item]
                    msg += f" Lost the stolen {loot_item.replace('_', ' ').title()}."
                elif reward > 0:
                    await bank.withdraw_credits(member, reward)
                    msg += f" Lost the gained {reward:,} {currency_name}."
            else:
                loot_items = [
                    k for k in inventory if ITEMS.get(k, (None, {}))[1]["type"] == "loot"
                ]
                if loot_items:
                    conf_item = random.choice(loot_items)
                    inventory[conf_item] -= 1
                    if inventory[conf_item] <= 0:
                        del inventory[conf_item]
                    msg += f" Police confiscated your {conf_item.replace('_', ' ').title()}."
            await cog.config.user(member).inventory.set(inventory)
            tax = int(bail_amount * 0.15)
            total_bail = bail_amount + tax
            end_timestamp = int(end_time.timestamp())
            msg += f" You are in jail until <t:{end_timestamp}:f> (<t:{end_timestamp}:R>). Bail out with `heist bailout` for {bail_amount:,} + {tax:,} (15%) tax = {total_bail:,} {currency_name}."

        try:
            embed = discord.Embed(
                title="Heist finished",
                description=f"{msg}",
                color=0xA020F0 if "caught" not in msg else 0xFF0000,
            )
            await channel.send(f"{member.mention}", embed=embed)
        except discord.Forbidden:
            log.warning(f"Cannot send heist result to channel {channel.id} for user {member.id}")
            if fallback_channel_id:
                fallback_channel = cog.bot.get_channel(fallback_channel_id)
                if fallback_channel:
                    try:
                        await fallback_channel.send(f"{member.mention} {msg}")
                    except discord.Forbidden:
                        log.warning(
                            f"Cannot send heist result to fallback channel {fallback_channel_id} for user {member.id}"
                        )
    except Exception as e:
        log.error(
            f"Error in resolve_heist for user {user.id}, heist {heist_type}: {e}", exc_info=True
        )
    finally:
        await cog.config.user(member).active_heist.clear()
