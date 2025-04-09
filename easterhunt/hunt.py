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
from datetime import datetime, timedelta

import discord


async def check_hunt_cooldown(config, user, current_time):
    last_hunt = await config.user(user).last_hunt() or 0
    if not isinstance(last_hunt, (int, float)):
        last_hunt = 0
    cooldown_remaining = 300 - (current_time - last_hunt)
    if cooldown_remaining > 0:
        cooldown_end = int(current_time + cooldown_remaining)
        return False, f"the Easter Bunny needs a break! Try again <t:{cooldown_end}:R>."
    return True, None


async def update_hunt_streak(config, user, current_time):
    last_hunt_time = await config.user(user).last_hunt_time() or 0
    if not isinstance(last_hunt_time, (int, float)):
        last_hunt_time = 0
    current_streak = await config.user(user).hunt_streak() or 0
    if not isinstance(current_streak, int):
        current_streak = 0
    if last_hunt_time and (current_time - last_hunt_time) <= 360:
        await config.user(user).hunt_streak.set(current_streak + 1)
    else:
        await config.user(user).hunt_streak.set(1)
    return await config.user(user).hunt_streak()


async def calculate_hunt_probabilities(config, user, current_streak):
    pity_counters = await config.user(user).pity_counter() or {}
    eggs = await config.user(user).eggs() or {}

    pity_counters["silver"] = pity_counters.get("silver", 0) + 1
    pity_counters["gold"] = pity_counters.get("gold", 0) + 1
    pity_counters["shiny"] = pity_counters.get("shiny", 0) + 1
    pity_counters["legendary"] = pity_counters.get("legendary", 0) + 1
    pity_counters["mythical"] = pity_counters.get("mythical", 0) + 1
    can_roll_legendary = (
        eggs.get("silver", 0) >= 20 and eggs.get("gold", 0) >= 10 and eggs.get("shiny", 0) >= 1
    )
    can_roll_mythical = can_roll_legendary and eggs.get("legendary", 0) >= 1
    base_chances = {
        "nothing": 500,
        "common": 400,
        "silver": 50,
        "gold": 30,
        "shiny": 0.12,
        "legendary": 5 if can_roll_legendary else 0,
        "mythical": 1 if can_roll_mythical else 0,
    }

    adjusted_chances = base_chances.copy()
    adjusted_chances["silver"] += pity_counters.get("silver", 0) * 5
    adjusted_chances["gold"] += pity_counters.get("gold", 0) * 3
    adjusted_chances["shiny"] += pity_counters.get("shiny", 0) * 0.1
    if can_roll_legendary:
        adjusted_chances["legendary"] += pity_counters.get("legendary", 0) * 1
    if can_roll_mythical:
        adjusted_chances["mythical"] += pity_counters.get("mythical", 0) * 0.2

    streak_bonus = (current_streak // 5) * 10
    adjusted_chances["silver"] += streak_bonus
    adjusted_chances["gold"] += streak_bonus
    adjusted_chances["shiny"] += streak_bonus
    if can_roll_legendary:
        adjusted_chances["legendary"] += streak_bonus
    if can_roll_mythical:
        adjusted_chances["mythical"] += streak_bonus

    total_rare = (
        adjusted_chances["silver"]
        + adjusted_chances["gold"]
        + adjusted_chances["shiny"]
        + adjusted_chances["legendary"]
        + adjusted_chances["mythical"]
    )
    adjusted_chances["common"] = max(400 - total_rare // 2, 100)
    adjusted_chances["nothing"] = 1000 - (
        adjusted_chances["common"]
        + adjusted_chances["silver"]
        + adjusted_chances["gold"]
        + adjusted_chances["shiny"]
        + adjusted_chances["legendary"]
        + adjusted_chances["mythical"]
    )

    return adjusted_chances, pity_counters, can_roll_legendary, can_roll_mythical


async def process_hunt_outcome(
    config, user, result, pity_counters, can_roll_legendary, can_roll_mythical
):
    eggs_found = random.randint(3, 10) if result == "common" else 1
    egg_images = await config.egg_images() or {}
    if result == "nothing":
        embed = discord.Embed(
            title="Result",
            color=0x808080,
            description="You returns from the hunt... but the fields were empty! Better luck next time! 🐰",
        )
        image_url = egg_images.get("nothing")
        await config.user(user).pity_counter.set(pity_counters)
    elif result == "common":
        current_common = await config.user(user).eggs.common() or 0
        await config.user(user).eggs.common.set(current_common + eggs_found)
        embed = discord.Embed(
            title="Result",
            color=0xFFFFFF,
            description=f"You returns from the hunt! You found {eggs_found} Common Eggs! Nice haul!",
        )
        image_url = egg_images.get("common")
        await config.user(user).pity_counter.set(pity_counters)
    elif result == "silver":
        current_silver = await config.user(user).eggs.silver() or 0
        await config.user(user).eggs.silver.set(current_silver + 1)
        embed = discord.Embed(
            title="Result",
            color=0xC0C0C0,
            description="You returns from the hunt! Wow, a Silver Egg! Lucky you!",
        )
        image_url = egg_images.get("silver")
        pity_counters["silver"] = 0
        await config.user(user).pity_counter.set(pity_counters)
    elif result == "gold":
        current_gold = await config.user(user).eggs.gold() or 0
        await config.user(user).eggs.gold.set(current_gold + 1)
        embed = discord.Embed(
            title="Result",
            color=0xFFD700,
            description="You returns from the hunt! JACKPOT! You unearthed a rare Gold Egg!",
        )
        image_url = egg_images.get("gold")
        pity_counters["silver"] = 0
        pity_counters["gold"] = 0
        await config.user(user).pity_counter.set(pity_counters)
    elif result == "shiny":
        current_shiny = await config.user(user).eggs.shiny() or 0
        await config.user(user).eggs.shiny.set(current_shiny + 1)
        embed = discord.Embed(
            title="Result",
            color=0xFF00FF,
            description="You returns from the hunt! UNBELIEVABLE! You discovered a dazzling Shiny Egg!",
        )
        image_url = egg_images.get("shiny")
        pity_counters["silver"] = 0
        pity_counters["gold"] = 0
        pity_counters["shiny"] = 0
        await config.user(user).pity_counter.set(pity_counters)
    elif result == "legendary":
        current_legendary = await config.user(user).eggs.legendary() or 0
        await config.user(user).eggs.legendary.set(current_legendary + 1)
        embed = discord.Embed(
            title="Result",
            color=0x00FFFF,
            description="You returns from the hunt! MYTHICAL FIND! You discovered an ultra-rare Legendary Egg! 🐉✨",
        )
        image_url = egg_images.get("legendary")
        pity_counters["silver"] = 0
        pity_counters["gold"] = 0
        pity_counters["shiny"] = 0
        pity_counters["legendary"] = 0
        await config.user(user).pity_counter.set(pity_counters)
    else:
        current_mythical = await config.user(user).eggs.mythical() or 0
        await config.user(user).eggs.mythical.set(current_mythical + 1)
        embed = discord.Embed(
            title="Result",
            color=0xFF4500,
            description="You returns from the hunt! BEYOND LEGENDARY! You discovered an otherworldly Mythical Egg! 🌟🔥",
        )
        image_url = egg_images.get("mythical")
        pity_counters["silver"] = 0
        pity_counters["gold"] = 0
        pity_counters["shiny"] = 0
        pity_counters["legendary"] = 0
        pity_counters["mythical"] = 0
        await config.user(user).pity_counter.set(pity_counters)

    if image_url:
        embed.set_image(url=image_url)
    return embed
