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
import logging
import random
import re
import time
from datetime import datetime, timedelta
from typing import Final, Optional

import aiohttp
import discord
from redbot.core import Config, bank, commands, errors
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu

from .hunt import (
    calculate_hunt_probabilities,
    check_hunt_cooldown,
    process_hunt_outcome,
    update_hunt_streak,
)
from .view import EasterWork

log = logging.getLogger("red.maxcogs.easterhunt")

# This cog was writen with the help from a very good friend of me, who did not want to be named.
# He made the pity counter system, streak system and the rarity system for the eggs.
# The rest of the code was made by myself.


class EasterHunt(commands.Cog):
    """
    Easter hunt cog that provides a fun Easter-themed game where users can hunt for eggs, work for egg shards, give eggs to others or steal, and earn achievements.
    It includes various commands for interacting with the game, managing progress, and viewing leaderboards.
    """

    __version__: Final[str] = "1.5.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = (
        "https://github.com/ltzmax/maxcogs/tree/master/easterhunt/EasterHunt.md."
    )

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=345628097922, force_registration=True)
        default_user = {
            "shards": 0,
            "eggs": {
                "common": 0,
                "silver": 0,
                "gold": 0,
                "shiny": 0,
                "legendary": 0,
                "mythical": 0,
            },
            "last_hunt": 0,
            "last_work": 0,
            "last_daily": 0,
            "last_give": 0,
            "active_hunt": False,
            "active_work": False,
            "pity_counter": {"silver": 0, "gold": 0, "shiny": 0, "legendary": 0, "mythical": 0},
            "hunt_streak": 0,
            "last_hunt_time": 0,
            "achievements": {
                "shiny_egg_hunter": False,
                "legendary_hunter": False,
                "mythical_master": False,
            },
        }
        default_global = {
            "egg_images": {
                "nothing": None,
                "common": None,
                "silver": None,
                "gold": None,
                "shiny": None,
                "legendary": None,
                "mythical": None,
            }
        }
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)
        self.active_tasks = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks Sinbad!
        """
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Handle data deletion requests; nothing to delete here."""
        pass

    async def cog_load(self):
        """Check and reset stale active_work states on cog load."""
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot and await self.config.user(member).active_work():
                    work_end = await self.config.user(member).last_work()
                    current_time = time.time()
                    if work_end <= current_time:
                        # Job should have ended; reset state
                        await self.config.user(member).active_work.set(False)
                        await self.config.user(member).last_work.set(0)
                        await self.config.user(member).last_work.set(current_time)
                    else:
                        # Job is still active; restart it
                        remaining_time = work_end - current_time
                        if remaining_time > 0:
                            self.active_tasks[member.id] = self.bot.loop.create_task(
                                self.resume_job(member, remaining_time)
                            )

    async def cog_unload(self):
        """Clean up tasks and reset active_work on cog unload."""
        await self.session.close()
        for user_id, task in self.active_tasks.items():
            task.cancel()
            member = self.bot.get_user(user_id)
            if member:
                await self.config.user(member).active_work.set(False)
                await self.config.user(member).last_work.set(0)
                await self.config.user(member).last_work.set(time.time())
        self.active_tasks.clear()

    async def resume_job(self, user, remaining_time):
        """Resume a job that was interrupted by a restart/reload."""
        try:
            await asyncio.sleep(remaining_time)
            # Job has ended; update state
            current_time = time.time()
            await self.config.user(user).last_work.set(current_time)
        except asyncio.CancelledError:
            pass
        finally:
            await self.config.user(user).active_work.set(False)
            await self.config.user(user).last_work.set(0)
            del self.active_tasks[user.id]

    @commands.group()
    @commands.guild_only()
    async def easterhunt(self, ctx):
        """Easter Hunt commands"""

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def hunt(self, ctx):
        """
        Go on an Easter egg hunt and wait for the results!

        Every hunt lasts a minute, it's all random for what it brings back!
        You do not get egg shards for hunting, only eggs to top leaderboard, use `[p]easterhunt work` and `[p]easterhunt daily` for egg shards.

        **Various egg types**:
        - common egg, silver egg, gold egg, shiny egg, legendary egg, and mythical egg.
        """
        user = ctx.author

        if await self.config.user(user).active_hunt():
            return await ctx.send(
                "you're already on a hunt! Wait for the Easter Bunny to return!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        if await self.config.user(user).active_work():
            return await ctx.send(
                "you're on work, you cannot hunt until you've finished work!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        current_time = time.time()
        can_hunt, cooldown_message = await check_hunt_cooldown(self.config, user, current_time)
        if not can_hunt:
            return await ctx.send(
                cooldown_message,
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        end_time = int((datetime.now() + timedelta(minutes=1)).timestamp())
        await self.config.user(user).active_hunt.set(True)
        await ctx.send(
            f"You sets off on an Easter egg hunt! Searching the fields... 🐰🌾\ni will be back <t:{end_time}:R>.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
        )

        try:
            await discord.utils.sleep_until(datetime.now() + timedelta(minutes=1))
            current_streak = await update_hunt_streak(self.config, user, current_time)
            adjusted_chances, pity_counters, can_roll_legendary, can_roll_mythical = (
                await calculate_hunt_probabilities(self.config, user, current_streak)
            )
            outcomes = ["nothing", "common", "silver", "gold", "shiny", "legendary", "mythical"]
            weights = [adjusted_chances[outcome] for outcome in outcomes]
            result = random.choices(outcomes, weights=weights, k=1)[0]
            if pity_counters.get("silver", 0) >= 50:
                result = "silver"
            elif pity_counters.get("gold", 0) >= 75:
                result = "gold"
            elif pity_counters.get("shiny", 0) >= 150:
                result = "shiny"
            elif can_roll_legendary and pity_counters.get("legendary", 0) >= 150:
                result = "legendary"
            elif can_roll_mythical and pity_counters.get("mythical", 0) >= 500:
                result = "mythical"

            embed = await process_hunt_outcome(
                self.config, user, result, pity_counters, can_roll_legendary, can_roll_mythical
            )
            embed.set_footer(text=f"Hunt Streak: {current_streak}")

            await ctx.send(
                embed=embed, reference=ctx.message.to_reference(fail_if_not_exists=False)
            )

            await self.config.user(user).last_hunt.set(current_time)
            await self.config.user(user).last_hunt_time.set(current_time)

        finally:
            await self.config.user(user).active_hunt.set(False)

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def progress(self, ctx):
        """Check your Easter Hunt progress!"""
        user = ctx.author
        pity_counters = await self.config.user(user).pity_counter() or {}
        streak = await self.config.user(user).hunt_streak() or 0
        eggs = await self.config.user(user).eggs() or {}

        can_roll_legendary = (
            eggs.get("silver", 0) >= 20 and eggs.get("gold", 0) >= 10 and eggs.get("shiny", 0) >= 1
        )
        can_roll_mythical = can_roll_legendary and eggs.get("legendary", 0) >= 1

        displayed_eggs = {
            "common": eggs.get("common", 0),  # No cap for Common Eggs
            "silver": min(eggs.get("silver", 0), 20),  # Cap at 20
            "gold": min(eggs.get("gold", 0), 10),  # Cap at 10
            "shiny": min(eggs.get("shiny", 0), 1),  # Cap at 1
            "legendary": min(eggs.get("legendary", 0), 1),  # Cap at 1
            "mythical": min(eggs.get("mythical", 0), 1),  # Cap at 1
        }
        embed = discord.Embed(
            title="Easter Hunt Progress",
            color=await ctx.embed_colour(),
            description=(
                f"**Hunt Streak**: {streak}\n"
                f"**Pity Counters** (Hunts since last drop):\n"
                f"- Silver: {pity_counters.get('silver', 0)}/50\n"
                f"- Gold: {pity_counters.get('gold', 0)}/75\n"
                f"- Shiny: {pity_counters.get('shiny', 0)}/150\n"
                f"- Legendary: {pity_counters.get('legendary', 0)}/150 "
                f"({'Eligible' if can_roll_legendary else 'Not Eligible'})\n"
                f"- Mythical: {pity_counters.get('mythical', 0)}/500 "
                f"({'Eligible' if can_roll_mythical else 'Not Eligible'})\n"
                f"**Egg Collection**:\n"
                f"- Common: {displayed_eggs['common']}\n"
                f"- Silver: {displayed_eggs['silver']}/20\n"
                f"- Gold: {displayed_eggs['gold']}/10\n"
                f"- Shiny: {displayed_eggs['shiny']}/1\n"
                f"- Legendary: {displayed_eggs['legendary']}/1\n"
                f"- Mythical: {displayed_eggs['mythical']}/1"
            ),
        )
        await ctx.send(embed=embed)

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def view(self, ctx):
        """Check your Easter haul!"""
        shards = await self.config.user(ctx.author).shards()
        eggs = await self.config.user(ctx.author).eggs()
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Easter Stash", colour=await ctx.embed_colour()
        )
        embed.add_field(name="Egg Shards", value=str(shards), inline=False)
        embed.add_field(name="Common Eggs", value=str(eggs["common"]))
        embed.add_field(name="Silver Eggs", value=str(eggs["silver"]), inline=False)
        embed.add_field(name="Gold Eggs", value=str(eggs["gold"]), inline=False)
        embed.add_field(name="Shiny Eggs", value=str(eggs["shiny"]))
        embed.add_field(name="Legendary Eggs", value=str(eggs["legendary"]), inline=False)
        embed.add_field(name="Mythical Eggs", value=str(eggs["mythical"]), inline=False)
        embed.set_footer(
            text="Use {prefix}easterhunt progress to check your hunt progress!".format(
                prefix=ctx.clean_prefix
            )
        )
        await ctx.send(embed=embed)

    @easterhunt.command(aliases=["achievement"])
    @commands.bot_has_permissions(embed_links=True)
    async def achievements(self, ctx, user: Optional[discord.Member] = None):
        """
        Check if you've completed any Easter Hunt!

        You can check your own or someone else's achievements.
        You will need shiny, legendary, and mythical eggs to complete these achievements and get the rewards.

        Why are not all the eggs listed?
        - The rarest of the eggs are the ones that are the achievements in the game, and they are the ones that you can get rewards for completing the achievements while the rest are just for fun and aren't giving any rewards since their rarity is not high enough.
        """
        if user is None:
            user = ctx.author
        eggs = await self.config.user(user).eggs()
        user_achievements = await self.config.user(user).achievements()
        shards = await self.config.user(user).shards()
        achievements = [
            {
                "key": "shiny_egg_hunter",
                "name": "Shiny Egg Hunter",
                "description": "Obtain 3 Shiny Eggs",
                "condition": eggs["shiny"] >= 3,
                "reward": 100000,
            },
            {
                "key": "legendary_hunter",
                "name": "Legendary Hunter",
                "description": "Obtain 1 Legendary Egg",
                "condition": eggs["legendary"] >= 1,
                "reward": 1000,
            },
            {
                "key": "mythical_master",
                "name": "Mythical Master",
                "description": "Obtain 1 Mythical Egg",
                "condition": eggs["mythical"] >= 1,
                "reward": 2000,
            },
        ]

        for achievement in achievements:
            if achievement["condition"] and not user_achievements[achievement["key"]]:
                new_shards = shards + achievement["reward"]
                await self.config.user(user).shards.set(new_shards)
                user_achievements[achievement["key"]] = True
                await self.config.user(user).achievements.set(user_achievements)
                await ctx.send(
                    f"🎉 Congratulations {user.mention}! You've unlocked the **{achievement['name']}** achievement "
                    f"and received {achievement['reward']} egg shards!"
                )
                shards = new_shards

        embed = discord.Embed(
            title="Easter Hunt Achievements",
            color=await ctx.embed_colour(),
            description="Complete these achievements to earn egg shards!",
        )

        for achievement in achievements:
            status = "✅" if achievement["condition"] else "❌"
            reward_status = (
                f"(Reward: {achievement['reward']} Egg Shards)"
                if not user_achievements[achievement["key"]]
                else "(Reward Claimed)"
            )
            embed.add_field(
                name=f"{achievement['name']} {status}",
                value=f"{achievement['description']} {reward_status}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @easterhunt.command()
    async def daily(self, ctx):
        """
        Claim your daily Easter gift!

        You can claim every 12 hours.
        The amount of shards you get is from 5 to 20, it's all random of what you get.
        """
        user = ctx.author
        last_daily = await self.config.user(user).last_daily()
        current_time = time.time()
        cooldown_remaining = 43200 - (current_time - last_daily)
        if cooldown_remaining > 0:
            cooldown_end = int(current_time + cooldown_remaining)
            return await ctx.send(
                f"the Easter Bunny’s still egg-hausted from hopping around! Check back <t:{cooldown_end}:R> for more goodies.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        shards = random.randint(5, 20)
        end_time = int((datetime.now() + timedelta(hours=12)).timestamp())
        await self.config.user(user).shards.set(await self.config.user(user).shards() + shards)
        await ctx.send(
            f"The Easter Bunny hops by and drops {shards} Egg Shards in your basket! Egg-citing, right? Come back <t:{end_time}:R> for another yolky surprise!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )
        await self.config.user(user).last_daily.set(current_time)

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def give(self, ctx, user: discord.Member, egg_type: str, amount: int = 1):
        """
        Give some of your eggs to another user!

        **Arguments**:
        - `user`: The user to give the eggs to.
        - `egg_type`: The type of egg to give (common, silver, gold, shiny).
        - `amount`: The number of eggs to give (default is 1).

        **Notes**:
        - You can only give Common, Silver, Gold, or Shiny Eggs. Legendary and Mythical Eggs cannot be traded.
        - You must have at least the number of eggs you're trying to give.
        - There’s a 5 secoud cooldown between giving eggs.
        """
        giver = ctx.author
        if user == giver:
            return await ctx.send(
                "You can't give eggs to yourself! 🥚",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        if user.bot:
            return await ctx.send(
                "You can't give eggs to a bot! 🤖",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        last_give = await self.config.user(giver).last_give()
        current_time = time.time()
        cooldown_remaining = 5 - (current_time - last_give)
        if cooldown_remaining > 0:
            cooldown_end = int(current_time + cooldown_remaining)
            return await ctx.send(
                f"You need to wait before giving more eggs! Try again <t:{cooldown_end}:R>.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        egg_type = egg_type.lower()
        tradable_eggs = ["common", "silver", "gold", "shiny"]
        if egg_type not in tradable_eggs:
            return await ctx.send(
                "You can only give Common, Silver, Gold, or Shiny Eggs! "
                "Legendary and Mythical Eggs cannot be traded. 🥚"
            )

        if amount < 1:
            return await ctx.send(
                "You must give at least 1 egg! 🥚",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        giver_eggs = await self.config.user(giver).eggs()
        if giver_eggs[egg_type] < amount:
            return await ctx.send(
                f"You don’t have enough {egg_type.capitalize()} Eggs to give! "
                f"You have {giver_eggs[egg_type]}, but you’re trying to give {amount}.🥚",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        await self.config.user(giver).eggs.set_raw(egg_type, value=giver_eggs[egg_type] - amount)
        receiver_eggs = await self.config.user(user).eggs()
        await self.config.user(user).eggs.set_raw(egg_type, value=receiver_eggs[egg_type] + amount)

        await self.config.user(giver).last_give.set(current_time)
        embed = discord.Embed(
            title="Egg Gift 🎁",
            color=await ctx.embed_colour(),
            description=(
                f"{giver.mention} has given {amount} {egg_type.capitalize()} Egg(s) to {user.mention}! 🥚\n"
                f"{user.mention} now has {receiver_eggs[egg_type] + amount} {egg_type.capitalize()} Egg(s)."
            ),
        )
        await ctx.send(
            embed=embed,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @easterhunt.command()
    async def tradeshards(self, ctx, amount: int):
        """
        Trade your easter shards for credits.

        1 easter shards is worth 20 credits, these credits will be added to your `[p]bank balance`.
        """
        if amount <= 0:
            return await ctx.send("Please enter a positive number of shards to trade!")

        current_shards = await self.config.user(ctx.author).shards()
        if current_shards < amount:
            return await ctx.send(
                f"You don't have enough shards! You currently have {current_shards} shards.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        credit = amount * 20
        new_shard_amount = current_shards - amount

        currency_name = await bank.get_currency_name(ctx.guild)
        await self.config.user(ctx.author).shards.set(new_shard_amount)
        try:
            await bank.deposit_credits(ctx.author, credit)
        except errors.BalanceTooHigh:
            log.error("User's balance is too high to get any credits.")
        await ctx.send(
            f"Successfully traded {amount} shards for {credit} {currency_name}!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 800, commands.BucketType.user)
    async def resetme(self, ctx):
        """
        Reset your own Easter hunt data (eggs, shards, pity counters, etc.).
        """
        data = await self.config.user(ctx.author).all()
        if (
            not data["eggs"]
            and not data["shards"]
            and not data["pity_counter"]
            and not data["achievements"]
        ):
            return await ctx.send(
                "You don't have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm Reset",
            description="Are you sure you want to reset your Easter hunt data? This will clear all your eggs, shards, pity counters, and streaks. This action cannot be undone!",
            color=discord.Color.red(),
        )
        msg = await ctx.send(
            embed=embed, view=view, reference=ctx.message.to_reference(fail_if_not_exists=False)
        )

        await view.wait()
        if view.result is None:
            return await ctx.send("Reset cancelled due to timeout.")
        if not view.result:
            return await ctx.send("Reset cancelled.")
        await self.config.user(ctx.author).clear()
        await ctx.send(
            f"Your Easter hunt data has been reset!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
        )

    @commands.is_owner()
    @easterhunt.group()
    async def owner(self, ctx):
        """Owner commands for Easter Hunt."""

    @owner.command(name="setshards")
    async def owner_setshards(self, ctx, user: discord.Member, amount: int):
        """Set a user's shard amount."""
        await self.config.user(user).shards.set(amount)
        await ctx.send(f"Set {user.name}'s shards to {humanize_number(amount)}")

    @owner.command(name="setimage")
    async def owner_setimage(self, ctx, egg_type: str, url: str):
        """
        Set a custom image URL for an egg type.

        **Egg Types**: nothing (This is when it doesn't find anything in the fields), common, silver, gold, shiny, legendary, mythical.
        **URL**: The direct URL to the image (or "reset" to clear the custom URL)

        Example: [p]easterhunt setimage silver https://i.maxapp.tv/b6182522w.png
        To reset: [p]easterhunt setimage silver reset
        """
        egg_type = egg_type.lower()
        valid_egg_types = ["nothing", "common", "silver", "gold", "shiny", "legendary", "mythical"]

        if egg_type not in valid_egg_types:
            return await ctx.send(
                f"Invalid egg type! Please use one of: {', '.join(valid_egg_types)}",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        if url.lower() == "reset":
            await self.config.egg_images.set_raw(egg_type, value=None)
            return await ctx.send(
                f"Custom image for {egg_type.title()} Egg has been reset to default.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        url_pattern = re.compile(
            r"^(https?://[^\s/$.?#].[^\s]*\.(?:png|jpg|jpeg|gif))$", re.IGNORECASE
        )
        if not url_pattern.match(url):
            return await ctx.send(
                "Invalid URL! Please provide a direct link to an image (e.g., ending in .png, .jpg, .jpeg, or .gif).",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        try:
            async with self.session.get(url) as response:
                if response.status != 200 or "image" not in response.content_type:
                    return await ctx.send(
                        "The URL does not point to a valid image! Please try again.",
                        reference=ctx.message.to_reference(fail_if_not_exists=False),
                        mention_author=False,
                    )
        except Exception as e:
            return await ctx.send(
                f"Failed to validate the URL. Please try again.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
            log.error(f"Error validating image URL: {e}")

        await self.config.egg_images.set_raw(egg_type, value=url)
        await ctx.send(
            f"Custom image for {egg_type.title()} Egg has been set to: <{url}>",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @owner.command(name="resetuser")
    @commands.bot_has_permissions(embed_links=True)
    async def owner_resetuser(self, ctx, user: discord.Member):
        """
        Reset a specific user's Easter hunt data.
        """
        if not await self.config.user(user).eggs() and not await self.config.user(user).shards():
            return await ctx.send(
                f"{user.mention} doesn't have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm User Reset",
            description=f"Are you sure you want to reset {user.mention}'s Easter hunt data? This will clear all their eggs, shards, pity counters, and streaks. This action cannot be undone!",
            color=discord.Color.red(),
        )
        msg = await ctx.send(
            embed=embed, view=view, reference=ctx.message.to_reference(fail_if_not_exists=False)
        )

        await view.wait()
        if view.result is None:
            return await ctx.send("Reset cancelled due to timeout.")
        if not view.result:
            return await ctx.send("Reset cancelled.")

        await self.config.user(user).clear()
        await ctx.send(
            f"{user.mention}'s Easter hunt data has been reset by {ctx.author.mention}!"
        )

    @owner.command(name="resetshift")
    @commands.bot_has_permissions(embed_links=True)
    async def owner_resetshift(self, ctx, user: discord.Member):
        """
        Reset a specific user's shift time and active states.
        """
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm User Reset",
            description=f"Are you sure you want to reset {user.mention}'s shifts?",
            color=discord.Color.red(),
        )
        msg = await ctx.send(
            embed=embed, view=view, reference=ctx.message.to_reference(fail_if_not_exists=False)
        )

        await view.wait()
        if view.result is None:
            return await ctx.send("Reset cancelled due to timeout.")
        if not view.result:
            return await ctx.send("Reset cancelled.")

        await self.config.user(user).active_hunt.set(False)
        await self.config.user(user).active_work.set(False)
        await self.config.user(user).last_work.set(0)
        await ctx.send(
            f"{user.mention}'s Easter hunt and work data has been reset by {ctx.author.mention}!"
        )

    @owner.command(name="resetall")
    @commands.bot_has_permissions(embed_links=True)
    async def owner_resetall(self, ctx):
        """
        Reset all Easter hunt data for all users and global config.
        """
        if not await self.config.all_users():
            return await ctx.send(
                "No users have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm Global Reset",
            description="Are you sure you want to reset ALL Easter hunt data? This will clear all user data (eggs, shards, pity counters, streaks) and global config (custom image URLs) for everyone. This action cannot be undone!",
            color=discord.Color.red(),
        )
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()
        if view.result is None:
            return await ctx.send("Global reset cancelled due to timeout.")
        if not view.result:
            return await ctx.send("Global reset cancelled.")
        await self.config.clear_all_users()
        await self.config.clear_all_globals()
        await ctx.send(
            f"All Easter hunt data and global config have been reset by {ctx.author.mention}!"
        )

    @easterhunt.command(aliases=["lb"])
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx):
        """Display the top egg collectors in this guild!

        Only Common, Silver, and Gold Eggs are counted in the total for the leaderboard.
        Shiny, Legendary, and Mythical Eggs are special achievement eggs and are not included.
        """
        guild = ctx.guild
        all_users = await self.config.all_users()
        leaderboard_data = []
        for user_id, data in all_users.items():
            member = guild.get_member(user_id)
            if member:
                eggs = data.get("eggs", {})
                total_eggs = eggs.get("common", 0) + eggs.get("silver", 0) + eggs.get("gold", 0)
                if total_eggs > 0:
                    leaderboard_data.append((member, total_eggs))

        if not leaderboard_data:
            return await ctx.send(
                "No one in this guild has collected any eggs yet! Time to start hunting!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        leaderboard_data.sort(key=lambda x: x[1], reverse=True)
        pages = []
        for i in range(0, len(leaderboard_data), 15):
            page_entries = leaderboard_data[i : i + 15]
            embed = discord.Embed(
                title="Easter Egg Leaderboard",
                color=await ctx.embed_color(),
                description="Who’s got the most eggs in the basket? (Only Common, Silver, and Gold Eggs count!)",
            )
            for rank, (member, total_eggs) in enumerate(page_entries, start=i + 1):
                embed.add_field(
                    name=f"#{rank}: {member.display_name}",
                    value=f"{humanize_number(total_eggs)} Eggs",
                    inline=False,
                )
            pages.append(embed)
        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def work(self, ctx):
        """
        Work for the Easter Bunny with a fun job!

        You earn shards from working, you can trade it in for currency!
        """
        user = ctx.author
        if await self.config.user(user).active_work():
            return await ctx.send(
                f"{user.mention}, you’re already on the job! Finish your shift first!"
            )

        if await self.config.user(user).active_hunt():
            return await ctx.send(
                f"{user.mention}, wait until you finish your active hunting before you can work!"
            )

        last_work = await self.config.user(user).last_work()
        current_time = time.time()
        cooldown_remaining = 300 - (current_time - last_work)
        if cooldown_remaining > 0:
            cooldown_end = int(current_time + cooldown_remaining)
            return await ctx.send(
                f"{user.mention}, you’re too egg-xhausted from your last shift! Rest until <t:{cooldown_end}:R>."
            )

        view = EasterWork(self, user)
        embed = discord.Embed(
            title="the Easter Bunny’s hiring! Pick a job",
            colour=await ctx.embed_colour(),
            description="1. **Stealer**: Snag eggs from unsuspecting users.\n2. **Store Clerk**: Sell eggs at the Egg Emporium.\n3. **Egg Giver**: Spread Easter cheer with free eggs.",
        )
        embed.set_footer(text="every of your shift last 5 minutes.")
        view.message = await ctx.send(embed=embed, view=view)

    async def find_target_player(self, user, guild):
        """Find a random player with eggs to steal from, excluding the user."""
        potential_targets = []
        for member in guild.members:
            if member.bot or member.id == user.id:
                continue
            eggs = await self.config.user(member).eggs()
            total_eggs = sum(eggs.get(egg_type, 0) for egg_type in eggs)
            if total_eggs > 0:
                potential_targets.append((member, eggs))

        if not potential_targets:
            return None, None

        target, target_eggs = random.choice(potential_targets)
        available_egg_types = [egg_type for egg_type, count in target_eggs.items() if count > 0]
        if not available_egg_types:
            return None, None
        egg_type = random.choice(available_egg_types)
        return target, egg_type

    async def start_job(self, interaction, job_type, user):
        try:
            work_ends = time.time() + 300  # 5 minutes from now
            await self.config.user(user).active_work.set(True)
            await self.config.user(user).last_work.set(work_ends)
            await interaction.response.send_message(
                f"{user.mention} starts working as a {job_type.replace('_', ' ').title()}! Shift begins... 🐰💼\nYou finish your shift <t:{int(work_ends)}:R>"
            )

            # Start the job as a tracked task
            self.active_tasks[user.id] = self.bot.loop.create_task(
                self.run_job(interaction, job_type, user, work_ends)
            )
        except Exception as e:
            log.error(f"Error starting job for {user}: {e}")
            await interaction.channel.send(
                f"{user.mention}, something went wrong starting your shift! It has been cancelled."
            )
            await self.config.user(user).active_work.set(False)
            await self.config.user(user).last_work.set(0)
            if user.id in self.active_tasks:
                del self.active_tasks[user.id]

    async def run_job(self, interaction, job_type, user, work_ends):
        try:
            await asyncio.sleep(300)  # 5 minutes
            current_time = time.time()

            if job_type == "stealer":
                if random.random() < 0.3:
                    target, stolen_egg_type = await self.find_target_player(
                        user, interaction.guild
                    )
                    if target and stolen_egg_type:
                        await self.config.user(target).eggs[stolen_egg_type].set(
                            await self.config.user(target).eggs[stolen_egg_type]() - 1
                        )
                        await self.config.user(user).eggs[stolen_egg_type].set(
                            await self.config.user(user).eggs[stolen_egg_type]() + 1
                        )
                        await interaction.channel.send(
                            f"{user.mention} sneaks back from stealing! You nabbed a {stolen_egg_type.title()} Egg from {target.name}!"
                        )
                        await interaction.channel.send(
                            f"{target.name} lost a {stolen_egg_type.title()} Egg to {user.mention}!"
                        )
                    else:
                        await interaction.channel.send(
                            f"{user.mention} couldn’t find anyone to steal from! Better luck next shift!"
                        )
                else:
                    if random.random() < 0.6:
                        egg_type = random.choice(["common", "silver"])
                        await self.config.user(user).eggs[egg_type].set(
                            await self.config.user(user).eggs[egg_type]() + 1
                        )
                        await interaction.channel.send(
                            f"{user.mention} sneaks back from stealing! You nabbed a {egg_type.title()} Egg from a distracted bunny!"
                        )
                    else:
                        await interaction.channel.send(
                            f"{user.mention} got caught red-handed by an angry bunny! No eggs for you—better luck next shift!"
                        )
            elif job_type == "store_clerk":
                shards = random.randint(5, 10)
                await self.config.user(user).shards.set(
                    await self.config.user(user).shards() + shards
                )
                await interaction.channel.send(
                    f"{user.mention} finishes a shift at the Egg Emporium! Sold some eggs and earned {shards} Egg Shards—nice hustle!"
                )
            elif job_type == "egg_giver":
                shards = random.randint(3, 7)
                await self.config.user(user).shards.set(
                    await self.config.user(user).shards() + shards
                )
                await interaction.channel.send(
                    f"{user.mention} hops around giving out Common Eggs! The bunnies loved it—you earned {shards} Egg Shards for your kindness!"
                )

            await self.config.user(user).last_work.set(current_time)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Error in run_job for {user}: {e}")
            await interaction.channel.send(
                f"{user.mention}, something went wrong during your shift! It has been cancelled."
            )
        finally:
            await self.config.user(user).active_work.set(False)
            await self.config.user(user).last_work.set(0)
            if user.id in self.active_tasks:
                del self.active_tasks[user.id]
