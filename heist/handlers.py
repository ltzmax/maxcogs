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
import random

import discord
from red_commons.logging import getLogger
from redbot.core import bank, errors

from .events import get_event_multiplier
from .leveling import award_xp, level_success_bonus, xp_bar, xp_progress
from .meta import (
    _CREW_FLAVOUR_CAUGHT,
    _CREW_FLAVOUR_FAIL,
    _CREW_FLAVOUR_SUCCESS,
    _FLAVOUR_CAUGHT,
    _FLAVOUR_FAIL,
    _FLAVOUR_MATERIAL,
    _FLAVOUR_SHIELD,
    _FLAVOUR_SUCCESS,
    _FLAVOUR_TOOL,
)
from .utils import ITEMS, fmt


log = getLogger("red.cogs.heist.handlers")


def _build_result_view(
    heist_type: str,
    heist_emoji: str,
    member_mention: str,
    success: bool,
    caught: bool,
    msg_parts: list[str],
    colour: int,
) -> discord.ui.LayoutView:
    """Components v2 LayoutView for a heist result."""
    if caught:
        narrative = random.choice(_FLAVOUR_CAUGHT)
    elif success:
        narrative = random.choice(_FLAVOUR_SUCCESS)
    else:
        narrative = random.choice(_FLAVOUR_FAIL)

    status = "✅ Success" if success else "❌ Failed"
    if caught:
        status += " - 🚨 Caught"

    header = f"## {heist_emoji} {fmt(heist_type)} - {status}\n{member_mention}\n*{narrative}*"

    components: list = [
        discord.ui.TextDisplay(header),
    ]

    if msg_parts:
        components.append(discord.ui.Separator())
        components.append(discord.ui.TextDisplay("\n".join(msg_parts)))

    view = discord.ui.LayoutView(timeout=None)
    view.add_item(discord.ui.Container(*components, accent_colour=discord.Colour(colour)))
    return view


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
        heat = await cog._get_effective_heat(member)
        material_heat = await user_config.material_heat()
        debt = await user_config.debt()
        tax_agreed = active.get("tax_agreed", False)
        event_multiplier, _event_ends_at = await get_event_multiplier(cog.config)

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
                equipped["tool"] = None
                await user_config.equipped.set(equipped)
            await user_config.inventory.set(inventory)

        member_xp = await user_config.xp()
        member_level = xp_progress(member_xp)[0]
        lv_bonus = level_success_bonus(member_level)

        base_success = random.randint(data["min_success"], data["max_success"])
        success_chance = min((base_success + int(tool_boost * 100)) / 100 + lv_bonus, 1.0)
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
                msg_parts.append(f"You stole a **{fmt(loot_item)}** from the {fmt(heist_type)}.")
            else:
                base_reward = random.randint(data["min_reward"], data["max_reward"])
                reward = base_reward * event_multiplier
                try:
                    await bank.deposit_credits(member, reward)
                    if event_multiplier > 1:
                        msg_parts.append(
                            f"**+{reward:,} {currency_name}** added to your balance. "
                            f"🎉 {event_multiplier}x event! (base: {base_reward:,} {currency_name})"
                        )
                    else:
                        msg_parts.append(f"**+{reward:,} {currency_name}** added to your balance.")
                except errors.BalanceTooHigh:
                    msg_parts.append(
                        f"You would have gained {reward:,} {currency_name}, "
                        "but your balance is already at the maximum."
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
                    equipped["shield"] = None
                    await user_config.equipped.set(equipped)
                await user_config.inventory.set(inventory)
                msg_parts.append(random.choice(_FLAVOUR_SHIELD))

            loss = int(loss * (1 - reduction))

            balance = await bank.get_balance(member)
            if loss > 0:
                if balance >= loss:
                    await bank.withdraw_credits(member, loss)
                    msg_parts.append(
                        f"**−{loss:,} {currency_name}** deducted from your bank balance."
                    )
                else:
                    debt_to_add = loss
                    tax = 0
                    if tax_agreed:
                        tax = int(loss * 0.2)
                        debt_to_add += tax
                    new_debt = debt + debt_to_add
                    await user_config.debt.set(new_debt)
                    debt_msg = f"**{debt_to_add:,} {currency_name}** added to your debt"
                    if tax > 0:
                        debt_msg += f" (incl. {tax:,} tax)"
                    debt_msg += f". Total debt: **{new_debt:,}**."
                    msg_parts.append(debt_msg)
            else:
                msg_parts.append("Your shield absorbed everything. No losses this time.")

        if used_tool:
            msg_parts.append(
                f"{random.choice(_FLAVOUR_TOOL)}\n"
                f"-# {fmt(used_tool)} used (+{tool_boost * 100:.0f}% success boost)"
            )

        heat += 1
        now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
        await user_config.heat.set(heat)
        await user_config.heat_last_set.set(now_ts)
        material_heat += 1
        await user_config.material_heat.set(material_heat)

        material_drop_chance = data.get("material_drop_chance", 0.0)
        adjusted_chance = min(material_drop_chance + (material_heat * 0.04), 0.9)
        if random.random() < adjusted_chance:
            await user_config.material_heat.set(0)
            materials = data.get("material_tiers") or [
                k for k, v in ITEMS.items() if v[1].get("type") == "material"
            ]
            if materials:
                dropped = random.choice(materials)
                qty = random.randint(1, 3) if success else random.randint(1, 2)
                inventory[dropped] = inventory.get(dropped, 0) + qty
                await user_config.inventory.set(inventory)
                msg_parts.append(
                    f"{random.choice(_FLAVOUR_MATERIAL)}\n-# Found {qty}× {fmt(dropped)}"
                )

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

            if success:
                if loot_item:
                    current = inventory.get(loot_item, 0)
                    if current > 0:
                        inventory[loot_item] = current - 1
                        if inventory[loot_item] <= 0:
                            inventory.pop(loot_item, None)
                        msg_parts.append(f"Police confiscated the **{fmt(loot_item)}**.")
                elif reward > 0:
                    await bank.withdraw_credits(member, reward)
                    msg_parts.append(f"Police seized **{reward:,} {currency_name}** from you.")
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
                        msg_parts.append(f"Police confiscated your **{fmt(item)}**.")

            await user_config.inventory.set(inventory)

            tax = int(bail_amount * 0.15)
            total_bail = bail_amount + tax
            end_ts = int(end_time.timestamp())
            msg_parts.append(
                f"**In jail** until <t:{end_ts}:f> (<t:{end_ts}:R>).\n"
                f"Bail: {bail_amount:,} + {tax:,} tax = **{total_bail:,}** {currency_name}."
            )

        if caught:
            colour = 0xFF0000
        elif success:
            colour = 0xA020F0
        else:
            colour = 0xFF6600

        # Update lifetime stats
        async with user_config.stats() as stats:
            if caught:
                stats["caught"] = stats.get("caught", 0) + 1
            elif success:
                stats["success"] = stats.get("success", 0) + 1
            else:
                stats["fail"] = stats.get("fail", 0) + 1

        # Award XP
        old_level, new_level, xp_gained = await award_xp(cog, member, heist_type, success, caught)
        new_xp = await user_config.xp()
        lvl, into, span, pct = xp_progress(new_xp)
        if caught:
            msg_parts.append("-# 🎓 No XP earned (caught)")
        else:
            level_up_str = (
                f" — **Level up! {old_level} -> {new_level}** 🎉" if new_level > old_level else ""
            )
            msg_parts.append(
                f"-# 🎓 +{xp_gained} XP{level_up_str} · Lv.{lvl} {xp_bar(pct)} {into:,}/{span:,}"
            )

        heist_emoji = data.get("emoji", "🎭")
        result_view = _build_result_view(
            heist_type=heist_type,
            heist_emoji=heist_emoji,
            member_mention=member.mention,
            success=success,
            caught=caught,
            msg_parts=msg_parts,
            colour=colour,
        )

        try:
            await channel.send(view=result_view)
        except discord.Forbidden:
            log.warning("Cannot send to %s", channel.id)
            if fallback_channel_id:
                fb = cog.bot.get_channel(fallback_channel_id)
                if fb:
                    try:
                        await fb.send(view=result_view)
                    except Exception:
                        log.warning("Fallback %s also failed", fallback_channel_id)

    except Exception as e:
        log.error("resolve_heist error for %s - %s: %s", user.id, heist_type, e, exc_info=True)
    finally:
        if member is not None:
            await cog.config.user(member).active_heist.clear()
        else:
            await cog.config.user_from_id(user.id).active_heist.clear()


async def resolve_crew_heist(
    cog,
    members: list,
    heist_type: str,
    channel,
):
    """Resolve a crew heist for all members and send a combined result."""
    try:
        data = await cog.get_heist_settings(heist_type)
        currency_name = await bank.get_currency_name(channel.guild)
        event_multiplier, _event_ends_at = await get_event_multiplier(cog.config)
        base_success = random.randint(data["min_success"], data["max_success"])
        success_chance = base_success / 100
        success = random.random() < success_chance

        total_reward = 0
        if success:
            base_total = random.randint(data["min_reward"], data["max_reward"])
            total_reward = base_total * event_multiplier
        total_loss = random.randint(data["min_loss"], data["max_loss"]) if not success else 0

        per_member_reward = total_reward // len(members) if success else 0
        per_member_loss = total_loss // len(members) if not success else 0

        member_lines = []
        caught_members = []
        any_caught = False

        for member in members:
            user_config = cog.config.user(member)
            inventory = await user_config.inventory()
            equipped = await user_config.equipped()
            heat = await cog._get_effective_heat(member)
            debt = await user_config.debt()
            active = await user_config.active_heist()
            tax_agreed = active.get("tax_agreed", False) if active else False
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

            lines = [f"**{member.display_name}**"]

            if success:
                actual_reward = per_member_reward
                if tool_boost > 0:
                    actual_reward = int(actual_reward * (1 + tool_boost))
                try:
                    await bank.deposit_credits(member, actual_reward)
                    lines.append(f"+{actual_reward:,} {currency_name}")
                except errors.BalanceTooHigh:
                    lines.append("Balance already at maximum.")
            else:
                loss = per_member_loss
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
                if balance >= loss:
                    await bank.withdraw_credits(member, loss)
                    lines.append(f"-{loss:,} {currency_name}")
                else:
                    debt_add = loss
                    if tax_agreed:
                        tax = int(loss * 0.2)
                        debt_add += tax
                    await user_config.debt.set(debt + debt_add)
                    lines.append(f"Debt +{debt_add:,} {currency_name}")

            heat += 1
            now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
            await user_config.heat.set(heat)
            await user_config.heat_last_set.set(now_ts)

            base_police_chance = data["police_chance"]
            adjusted_police = min(base_police_chance + (heat * 0.02), 0.9)
            member_caught = random.random() < adjusted_police

            if member_caught:
                any_caught = True
                caught_members.append(member)
                await user_config.heat.set(0)
                bail_amount = int(data["max_loss"] * random.uniform(0.5, 1.0))
                jail_duration = data["jail_time"]
                end_time = datetime.datetime.now(datetime.timezone.utc) + jail_duration
                await user_config.jail.set(
                    {
                        "end_time": end_time.timestamp(),
                        "bail_amount": bail_amount,
                    }
                )
                end_ts = int(end_time.timestamp())
                tax = int(bail_amount * 0.15)
                lines.append(f"🚨 Caught - jail until <t:{end_ts}:R>")
            else:
                lines.append("✅ Got away clean")

            material_heat = await user_config.material_heat()
            material_heat += 1
            await user_config.material_heat.set(material_heat)
            material_drop_chance = data.get("material_drop_chance", 0.0)
            adjusted_chance = min(material_drop_chance + (material_heat * 0.04), 0.9)
            if random.random() < adjusted_chance:
                await user_config.material_heat.set(0)
                materials = data.get("material_tiers") or [
                    k for k, v in ITEMS.items() if v[1].get("type") == "material"
                ]
                if materials:
                    dropped = random.choice(materials)
                    qty = random.randint(1, 2)
                    inventory[dropped] = inventory.get(dropped, 0) + qty
                    await user_config.inventory.set(inventory)
                    lines.append(f"-# Found {qty}× {fmt(dropped)}")

            await user_config.active_heist.clear()
            async with user_config.stats() as stats:
                if member_caught:
                    stats["caught"] = stats.get("caught", 0) + 1
                elif success:
                    stats["success"] = stats.get("success", 0) + 1
                else:
                    stats["fail"] = stats.get("fail", 0) + 1

            old_lv, new_lv, xp_gained = await award_xp(
                cog, member, heist_type, success, member_caught
            )
            new_xp = await cog.config.user(member).xp()
            lvl, _into, _span, _pct = xp_progress(new_xp)
            if member_caught:
                lines.append("-# 🎓 No XP earned (caught)")
            else:
                lv_up = f" · Level up! {old_lv} -> {new_lv} 🎉" if new_lv > old_lv else ""
                lines.append(f"-# 🎓 +{xp_gained} XP · Lv.{lvl}{lv_up}")

            member_lines.append("\n".join(lines))

        if any_caught:
            narrative = random.choice(_CREW_FLAVOUR_CAUGHT)
            colour = 0xFF0000
        elif success:
            narrative = random.choice(_CREW_FLAVOUR_SUCCESS)
            colour = 0xA020F0
        else:
            narrative = random.choice(_CREW_FLAVOUR_FAIL)
            colour = 0xFF6600

        status = "✅ Success" if success else "❌ Failed"
        if any_caught:
            status += " - 🚨 Some Caught"

        mentions = " ".join(m.mention for m in members)
        header = f"## 👥 Crew Robbery - {status}\n{mentions}\n*{narrative}*"

        components: list = [discord.ui.TextDisplay(header)]

        if success:
            components.append(discord.ui.Separator())
            haul_text = (
                f"**Total haul:** {total_reward:,} {currency_name} split {len(members)} ways\n"
                f"**Per member:** ~{per_member_reward:,} {currency_name}"
            )
            if event_multiplier > 1:
                haul_text += f"\n-# 🎉 {event_multiplier}x event active!"
            components.append(discord.ui.TextDisplay(haul_text))
        else:
            components.append(discord.ui.Separator())
            components.append(
                discord.ui.TextDisplay(
                    f"**Total loss:** {total_loss:,} {currency_name} split {len(members)} ways"
                )
            )

        components.append(discord.ui.Separator())
        components.append(
            discord.ui.TextDisplay("**Individual results:**\n" + "\n\n".join(member_lines))
        )

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(discord.ui.Container(*components, accent_colour=discord.Colour(colour)))

        try:
            await channel.send(view=view)
        except discord.Forbidden:
            log.warning("Cannot send crew result to %s", channel.id)

    except Exception as e:
        log.error("resolve_crew_heist error: %s", e, exc_info=True)
        for member in members:
            with contextlib.suppress(Exception):
                await cog.config.user(member).active_heist.clear()
