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

import discord
from red_commons.logging import getLogger
from redbot.core import bank, errors

from .utils import ITEMS, fmt


log = getLogger("red.cogs.heist.handlers")


async def schedule_resolve(
    cog,
    user_id: int,
    seconds: float,
    heist_type: str,
    channel: discord.TextChannel = None,
):
    try:
        await asyncio.sleep(seconds)
        user = cog.bot.get_user(user_id)
        if user and channel:
            await resolve_heist(cog, user, heist_type, channel)
        if user_id in cog.pending_tasks:
            del cog.pending_tasks[user_id]
    except asyncio.CancelledError:
        log.info("Schedule resolve task cancelled for user %s on heist %s", user_id, heist_type)
        raise
    except Exception as e:
        log.error(
            "Error in schedule_resolve for user %s, heist %s: %s",
            user_id,
            heist_type,
            e,
            exc_info=True,
        )


async def resolve_heist(
    cog,
    user: discord.User,
    heist_type: str,
    channel: discord.TextChannel,
    fallback_channel_id: int | None = None,
):
    member = None
    try:
        data = await cog.get_heist_settings(heist_type)
        member = channel.guild.get_member(user.id)
        if not member:
            log.warning(
                "User %s not found in guild %s for heist %s",
                user.id,
                channel.guild.id,
                heist_type,
            )
            return

        currency_name = await bank.get_currency_name(channel.guild)
        user_config = cog.config.user(member)
        inventory = await user_config.inventory()
        equipped = await user_config.equipped()
        active = await user_config.active_heist()
        heat = await user_config.heat()
        material_heat = await user_config.material_heat()
        debt = await user_config.debt()
        tax_agreed = active.get("tax_agreed", False)

        tool_boost = 0.0
        used_tool = None
        equipped_tool = equipped["tool"]
        if (
            equipped_tool
            and inventory.get(equipped_tool, 0) > 0
            and ITEMS.get(equipped_tool, (None, {}))[1].get("for_heist") == heist_type
        ):
            tool_data = ITEMS[equipped_tool][1]
            tool_boost = tool_data.get("boost", 0.0)
            used_tool = equipped_tool
            inventory[used_tool] = max(0, inventory.get(used_tool, 0) - 1)
            if inventory[used_tool] == 0:
                inventory.pop(used_tool, None)
            await user_config.inventory.set(inventory)

        base_success = random.randint(data["min_success"], data["max_success"])
        success_chance = min((base_success + int(tool_boost * 100)) / 100, 1.0)
        success = random.random() < success_chance

        loot_item = (
            heist_type
            if heist_type in ITEMS and ITEMS[heist_type][1].get("type") == "loot"
            else None
        )

        reward = 0
        msg_parts = []

        if success:
            if loot_item:
                inventory[loot_item] = inventory.get(loot_item, 0) + 1
                await user_config.inventory.set(inventory)
                msg_parts.append(
                    f"Success! You stole a {fmt(loot_item)} from the {fmt(heist_type)}."
                )
            else:
                reward = random.randint(data["min_reward"], data["max_reward"])
                try:
                    await bank.deposit_credits(member, reward)
                    msg_parts.append(
                        f"Success! You gained {reward:,} {currency_name} from the {fmt(heist_type)}."
                    )
                except errors.BalanceTooHigh:
                    msg_parts.append(
                        f"Success! You would have gained {reward:,} {currency_name}, "
                        "but your balance is too high."
                    )
                    reward = 0
        else:
            loss = random.randint(data["min_loss"], data["max_loss"])
            reduction = 0.0
            equipped_shield = equipped["shield"]
            if equipped_shield and inventory.get(equipped_shield, 0) > 0:
                shield_data = ITEMS.get(equipped_shield, (None, {}))[1]
                reduction = shield_data.get("reduction", 0.0)
                inventory[equipped_shield] = max(0, inventory.get(equipped_shield, 0) - 1)
                if inventory[equipped_shield] == 0:
                    inventory.pop(equipped_shield, None)
                await user_config.inventory.set(inventory)

            loss = int(loss * (1 - reduction))

            balance = await bank.get_balance(member)
            if loss > 0:
                if balance >= loss:
                    await bank.withdraw_credits(member, loss)
                    msg_parts.append(f"Failed! You lost {loss:,} {currency_name}.")
                else:
                    debt_to_add = loss
                    tax = 0
                    if tax_agreed:
                        tax = int(loss * 0.2)
                        debt_to_add += tax

                    new_debt = debt + debt_to_add
                    await user_config.debt.set(new_debt)
                    msg = f"Failed! You owe {debt_to_add:,} {currency_name} in debt"
                    if tax > 0:
                        msg += f" (incl. {tax:,} tax)"
                    msg += "."
                    msg_parts.append(msg)
            else:
                msg_parts.append("Failed — but your shield prevented any loss.")

        if used_tool:
            msg_parts.append(f"(Used {fmt(used_tool)} → +{tool_boost * 100:.0f}% success chance)")

        heat += 1
        await user_config.heat.set(heat)

        material_heat += 1
        await user_config.material_heat.set(material_heat)

        material_drop_chance = data.get("material_drop_chance", 0.0)
        adjusted_chance = min(material_drop_chance + (material_heat * 0.04), 0.9)
        if random.random() < adjusted_chance:
            await user_config.material_heat.set(0)
            materials = [k for k, v in ITEMS.items() if v[1].get("type") == "material"]
            if materials:
                dropped = random.choice(materials)
                qty = random.randint(1, 3) if success else random.randint(1, 2)
                inventory[dropped] = inventory.get(dropped, 0) + qty
                await user_config.inventory.set(inventory)
                msg_parts.append(f"Found {qty}× {fmt(dropped)} material!")

        caught = False
        base_police_chance = data["police_chance"]
        adjusted_police = min(base_police_chance + (heat * 0.02), 0.9)
        if random.random() < adjusted_police:
            caught = True
            await user_config.heat.set(0)

            bail_amount = int(data["max_loss"] * random.uniform(0.5, 1.0))
            jail_duration = data["jail_time"]
            end_time = datetime.datetime.now(datetime.timezone.utc) + jail_duration
            await user_config.jail.set(
                {"end_time": end_time.timestamp(), "bail_amount": bail_amount}
            )

            msg_parts.append("But you got **caught** by the police!")

            if success:
                if loot_item:
                    current = inventory.get(loot_item, 0)
                    if current > 0:
                        inventory[loot_item] = current - 1
                        if inventory[loot_item] <= 0:
                            inventory.pop(loot_item, None)
                        msg_parts.append(f"Lost the stolen {fmt(loot_item)}.")
                elif reward > 0:
                    await bank.withdraw_credits(member, reward)
                    msg_parts.append(f"Lost the gained {reward:,} {currency_name}.")
            else:
                loot_items = [
                    k for k in inventory if ITEMS.get(k, (None, {}))[1].get("type") == "loot"
                ]
                if loot_items:
                    item = random.choice(loot_items)
                    current = inventory.get(item, 0)
                    if current > 0:
                        inventory[item] = current - 1
                        if inventory[item] <= 0:
                            inventory.pop(item, None)
                        msg_parts.append(f"Police confiscated your {fmt(item)}.")

            await user_config.inventory.set(inventory)

            tax = int(bail_amount * 0.15)
            total_bail = bail_amount + tax
            end_ts = int(end_time.timestamp())
            msg_parts.append(
                f"In jail until <t:{end_ts}:f> (<t:{end_ts}:R>). "
                f"Bail: {bail_amount:,} + {tax:,} tax = **{total_bail:,}** {currency_name}."
            )

        msg = "\n".join(msg_parts).strip()
        color = 0xFF0000 if caught else 0xA020F0

        embed = discord.Embed(
            title="Heist Result",
            description=msg,
            color=color,
        )

        try:
            await channel.send(f"{member.mention}", embed=embed)
        except discord.Forbidden:
            log.warning("Cannot send to %s", channel.id)
            if fallback_channel_id:
                fb = cog.bot.get_channel(fallback_channel_id)
                if fb:
                    try:
                        await fb.send(f"{member.mention} {msg}")
                    except Exception:
                        log.warning("Fallback %s also failed", fallback_channel_id)

    except Exception as e:
        log.error("resolve_heist error for %s - %s: %s", user.id, heist_type, e, exc_info=True)
    finally:
        # Only clear active_heist if member was successfully resolved
        if member is not None:
            await cog.config.user(member).active_heist.clear()
        else:
            await cog.config.user_from_id(user.id).active_heist.clear()
