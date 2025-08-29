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

import random
from typing import Dict, Tuple

import discord


async def check_hunt_cooldown(db, user_id: int, current_time: float) -> tuple[bool, str | None]:
    """Check if the user can hunt again, returning (can_hunt, message)."""
    last_hunt = await db.get_user_field(user_id, "last_hunt")
    cooldown_remaining = 300 - (current_time - last_hunt)
    if cooldown_remaining > 0:
        cooldown_end = int(current_time + cooldown_remaining)
        return False, f"The Easter Bunny needs a break! Try again <t:{cooldown_end}:R>."
    return True, None


async def update_hunt_streak(db, user_id: int, current_time: float) -> int:
    """Update and return the user's hunt streak."""
    last_hunt_time = await db.get_user_field(user_id, "last_hunt_time")
    current_streak = await db.get_user_field(user_id, "hunt_streak")

    if last_hunt_time and (current_time - last_hunt_time) <= 900:
        new_streak = current_streak + 1
    else:
        new_streak = 1

    await db.set_user_field(user_id, "hunt_streak", new_streak)
    return new_streak


async def calculate_hunt_probabilities(
    db, user_id: int, current_streak: int
) -> Tuple[Dict[str, int], Dict[str, int], bool, bool]:
    """Calculate adjusted probabilities with pity and streak bonuses."""
    pity_counters = await db.get_pity_counters(user_id)
    eggs = await db.get_eggs(user_id)
    for egg_type in ["silver", "gold", "shiny", "legendary", "mythical"]:
        pity_counters[egg_type] = pity_counters.get(egg_type, 0) + 1

    can_roll_legendary = all(
        eggs.get(key, 0) >= value for key, value in {"silver": 20, "gold": 10, "shiny": 1}.items()
    )
    can_roll_mythical = can_roll_legendary and eggs.get("legendary", 0) >= 1

    weights = {
        "nothing": 5000,
        "common": 4000,
        "silver": 500,
        "gold": 300,
        "shiny": 12,
        "legendary": 50 if can_roll_legendary else 0,
        "mythical": 10 if can_roll_mythical else 0,
    }

    pity_increments = {
        "silver": 50,
        "gold": 30,
        "shiny": 1,
        "legendary": 10,
        "mythical": 2,
    }
    for egg_type, increment in pity_increments.items():
        if egg_type in ["legendary", "mythical"] and not (
            can_roll_legendary if egg_type == "legendary" else can_roll_mythical
        ):
            continue
        weights[egg_type] += pity_counters.get(egg_type, 0) * increment

    streak_bonus = (current_streak // 5) * (10000 // 100)
    for egg_type in (
        ["silver", "gold", "shiny"]
        + (["legendary"] if can_roll_legendary else [])
        + (["mythical"] if can_roll_mythical else [])
    ):
        weights[egg_type] += streak_bonus

    total_rare = sum(weights[t] for t in weights if t not in ["nothing", "common"])
    weights["common"] = max(1000, 4000 - total_rare // 2)
    current_total = sum(weights.values())
    weights["nothing"] = max(0, 10000 - current_total)
    if sum(weights.values()) != 10000:
        weights["nothing"] += 10000 - sum(weights.values())

    return weights, pity_counters, can_roll_legendary, can_roll_mythical


async def process_hunt_outcome(
    db,
    user_id: int,
    result: str,
    pity_counters: Dict[str, int],
    can_roll_legendary: bool,
    can_roll_mythical: bool,
) -> discord.Embed:
    """Process the hunt result, update config, and return an embed."""
    egg_images = await db.get_egg_images()
    image_url = egg_images.get(result)
    color = {
        "nothing": 0x808080,
        "common": 0xFFFFFF,
        "silver": 0xC0C0C0,
        "gold": 0xFFD700,
        "shiny": 0xFF00FF,
        "legendary": 0x00FFFF,
        "mythical": 0xFF4500,
    }[result]
    descriptions = {
        "nothing": "You return from the hunt... but the fields were empty! Better luck next time! 🐰",
        "common": "You return from the hunt! You found {eggs_found} Common Eggs! Nice haul!",
        "silver": "You return from the hunt! Wow, a Silver Egg! Lucky you!",
        "gold": "You return from the hunt! JACKPOT! You unearthed a rare Gold Egg!",
        "shiny": "You return from the hunt! UNBELIEVABLE! You discovered a dazzling Shiny Egg!",
        "legendary": "You return from the hunt! MYTHICAL FIND! You discovered an ultra-rare Legendary Egg! 🐉✨",
        "mythical": "You return from the hunt! BEYOND LEGENDARY! You discovered an otherworldly Mythical Egg! 🌟🔥",
    }
    description = descriptions[result]
    if result == "nothing":
        pass
    elif result == "common":
        eggs_found = random.randint(3, 10)
        current = await db.get_egg_count(user_id, "common")
        await db.set_egg_count(user_id, "common", current + eggs_found)
        description = description.format(eggs_found=eggs_found)
    else:
        current = await db.get_egg_count(user_id, result)
        await db.set_egg_count(user_id, result, current + 1)
        reset_types = {
            "silver": ["silver"],
            "gold": ["silver", "gold"],
            "shiny": ["silver", "gold", "shiny"],
            "legendary": ["silver", "gold", "shiny", "legendary"],
            "mythical": ["silver", "gold", "shiny", "legendary", "mythical"],
        }.get(result, [])
        for t in reset_types:
            pity_counters[t] = 0

    await db.set_pity_counters(user_id, pity_counters)

    embed = discord.Embed(title="Hunt Result", color=color, description=description)
    if image_url:
        embed.set_image(url=image_url)
    return embed


async def find_target_player(db, user_id: int, guild) -> tuple[discord.Member | None, str | None]:
    """Find a random player with eggs to steal from, excluding the user."""
    potential_targets = []
    async with db.conn.cursor() as cursor:
        await cursor.execute(
            """
            SELECT DISTINCT user_id
            FROM user_eggs
            WHERE user_id != ? AND count > 0
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        for (target_id,) in rows:
            member = guild.get_member(target_id)
            if member and not member.bot:
                eggs = await db.get_eggs(member.id)
                potential_targets.append((member, eggs))

    if not potential_targets:
        return None, None

    target, target_eggs = random.choice(potential_targets)
    available_egg_types = [egg_type for egg_type, count in target_eggs.items() if count > 0]
    if not available_egg_types:
        return None, None
    egg_type = random.choice(available_egg_types)
    return target, egg_type
