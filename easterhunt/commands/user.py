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
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Final, Optional

import discord
from red_commons.logging import getLogger
from redbot.core import bank, commands, errors
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu

from ..achievements.achievements import achievements
from ..utils import (
    calculate_hunt_probabilities,
    check_hunt_cooldown,
    find_target_player,
    process_hunt_outcome,
    update_hunt_streak,
)
from ..view import EasterWork

log = getLogger("red.maxcogs.easterhunt")


class UserCommands(commands.Cog):
    @commands.hybrid_group(aliases=["ehunt", "easterh"])
    @commands.guild_only()
    async def easterhunt(self, ctx: commands.Context):
        """
        Easter Hunt commands

        Documentations for the rarity of the eggs and how it works can be found here: https://easterhunt.maxapp.tv
        """

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def hunt(self, ctx: commands.Context):
        """
        Go on an Easter egg hunt and wait for the results!

        Every hunt lasts a minute, it's all random for what it brings back!
        You do not get egg shards for hunting, only eggs to top leaderboard, use `[p]easterhunt work` and `[p]easterhunt daily` for egg shards.

        **Various egg types**:
        - common egg, silver egg, gold egg, shiny egg, legendary egg, and mythical egg.
        """
        user = ctx.author

        if await self.db.get_user_field(user.id, "active_hunt"):
            return await ctx.send(
                "you're already on a hunt! Wait for the Easter Bunny to return!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        if await self.db.get_user_field(user.id, "active_work"):
            return await ctx.send(
                "you're on work, you cannot hunt until you've finished work!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        current_time = time.time()
        can_hunt, cooldown_message = await check_hunt_cooldown(self.db, user.id, current_time)
        if not can_hunt:
            return await ctx.send(
                cooldown_message,
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        end_time = int((datetime.now() + timedelta(minutes=1)).timestamp())
        await self.db.set_user_field(user.id, "active_hunt", True)
        await ctx.send(
            f"You sets off on an Easter egg hunt! Searching the fields... 🐰🌾\ni will be back <t:{end_time}:R>.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
        )

        event_task = None
        try:
            event_task = asyncio.create_task(self.send_hunt_events(ctx.channel, user))
            await asyncio.sleep(60)
            current_streak = await update_hunt_streak(self.db, user.id, current_time)
            adjusted_chances, pity_counters, can_roll_legendary, can_roll_mythical = (
                await calculate_hunt_probabilities(self.db, user.id, current_streak)
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
                self.db, user.id, result, pity_counters, can_roll_legendary, can_roll_mythical
            )
            embed.set_footer(text=f"Hunt Streak: {current_streak}")

            await ctx.send(
                embed=embed, reference=ctx.message.to_reference(fail_if_not_exists=False)
            )

            await self.db.set_user_field(user.id, "last_hunt", current_time)
            await self.db.set_user_field(user.id, "last_hunt_time", current_time)

        finally:
            await self.db.set_user_field(user.id, "active_hunt", False)
            if event_task:
                event_task.cancel()

    async def send_hunt_events(self, channel, user):
        """Send random events during the hunt."""
        events = [
            f"{user.mention} spots a rustling bush... could it be an egg?",
            f"{user.mention} hears the Easter Bunny nearby!",
            f"{user.mention} finds a trail of chocolate wrappers... following it!",
            f"{user.mention} trips over a root but keeps going!",
            f"{user.mention} sees a colorful glimmer in the distance!",
            f"{user.mention} takes a moment to enjoy the spring flowers.",
            f"{user.mention} feels the thrill of the hunt!",
            f"{user.mention} wonders if anyone else is hunting today.",
            f"{user.mention} spots a butterfly and follows it for a moment.",
            f"{user.mention} hears birds chirping happily.",
            f"{user.mention} finds a small patch of clover and makes a wish.",
            f"{user.mention} feels the warm sun and keeps searching.",
            f"{user.mention} thinks they saw something shiny!",
        ]
        num_events = random.randint(3, 5)
        total_time = 60
        intervals = sorted(
            [random.uniform(10, total_time / num_events * 1.5) for _ in range(num_events)]
        )
        cumulative = sum(intervals)
        scale = total_time / cumulative if cumulative > 0 else 1
        adjusted_intervals = []
        current = 0
        for interval in intervals:
            current += interval * scale
            adjusted_intervals.append(current)
        unique_events = (
            random.sample(events * 2, num_events)
            if len(events) < num_events
            else random.sample(events, num_events)
        )
        prev_time = 0
        for i, interval in enumerate(adjusted_intervals):
            sleep_time = interval - prev_time
            await asyncio.sleep(sleep_time)
            event_msg = unique_events[i]
            await channel.send(event_msg)
            prev_time = interval

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def progress(self, ctx: commands.Context):
        """Check your Easter Hunt progress!"""
        user = ctx.author
        pity_counters = await self.db.get_pity_counters(user.id)
        streak = await self.db.get_user_field(user.id, "hunt_streak")
        eggs = await self.db.get_eggs(user.id)

        can_roll_legendary = (
            eggs.get("silver", 0) >= 20 and eggs.get("gold", 0) >= 10 and eggs.get("shiny", 0) >= 1
        )
        can_roll_mythical = can_roll_legendary and eggs.get("legendary", 0) >= 1

        pity_text = (
            f"- Silver: {pity_counters.get('silver', 0)}/50\n"
            f"- Gold: {pity_counters.get('gold', 0)}/75\n"
            f"- Shiny: {pity_counters.get('shiny', 0)}/150\n"
            f"- Legendary: {pity_counters.get('legendary', 0)}/150 ({'Eligible' if can_roll_legendary else 'Not Eligible'})\n"
            f"- Mythical: {pity_counters.get('mythical', 0)}/500 ({'Eligible' if can_roll_mythical else 'Not Eligible'})"
        )
        egg_text = (
            f"- Silver: {min(eggs.get('silver', 0), 20)}/20\n"
            f"- Gold: {min(eggs.get('gold', 0), 10)}/10\n"
            f"- Shiny: {min(eggs.get('shiny', 0), 1)}/1\n"
            f"- Legendary: {min(eggs.get('legendary', 0), 1)}/1\n"
            f"- Mythical: {min(eggs.get('mythical', 0), 1)}/1"
        )

        embed = discord.Embed(
            title=f"{user.display_name}'s Easter Hunt Progress 🐰",
            color=await ctx.embed_colour(),
        )
        embed.add_field(name="🏃 Hunt Streak", value=str(streak), inline=False)
        embed.add_field(
            name="⏳ Pity Counters (Hunts since last drop)", value=pity_text, inline=False
        )
        embed.add_field(name="🥚 Egg Collection (Towards Unlocks)", value=egg_text, inline=False)
        embed.set_footer(text="Keep hunting to boost your pity and streak!")
        await ctx.send(embed=embed)

    @easterhunt.command(aliases=["inv", "view", "views"])
    @commands.bot_has_permissions(embed_links=True)
    async def inventory(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Check your Easter haul!"""
        if not member:
            member = ctx.author

        if member.bot:
            return await ctx.send(
                "Bots don't have an Easter inventory! 🤖",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        shards = await self.db.get_user_field(ctx.author.id, "shards")
        eggs = await self.db.get_eggs(ctx.author.id)
        gems = await self.db.get_user_field(ctx.author.id, "gems")

        embed = discord.Embed(
            title=f"{ctx.author.name}'s Easter Stash 🐰",
            colour=await ctx.embed_colour(),
            description="Your collected treasures from hunts, work, and more!",
        )
        if ctx.author.display_avatar:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="🪙 Egg Shards:", value=humanize_number(shards), inline=True)
        embed.add_field(name="💎 Hidden Gems:", value=humanize_number(gems), inline=True)
        egg_list = box(
            f"{'Common:':<11} {eggs['common']} 🥚\n"
            f"{'Silver:':<11} {eggs['silver']} 🥈\n"
            f"{'Gold:':<11} {eggs['gold']} 🥇\n"
            f"{'Shiny:':<11} {eggs['shiny']} ✨\n"
            f"{'Legendary:':<11} {eggs['legendary']} 🐉\n"
            f"{'Mythical:':<11} {eggs['mythical']} 🌟",
            lang="yaml",
        )
        embed.add_field(name="🥚 Eggs Collected:", value=egg_list, inline=False)
        embed.set_footer(
            text=f"Use {ctx.clean_prefix}easterhunt progress to check your hunt progress!"
        )
        await ctx.send(embed=embed)

    @easterhunt.command(aliases=["achievement"])
    @commands.bot_has_permissions(embed_links=True)
    async def achievements(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        Check if you've completed any Easter Hunt!

        You can check your own or someone else's achievements.
        You will need shiny, legendary, and mythical eggs to complete these achievements and get the rewards.

        Why are not all the eggs listed?
        - The rarest of the eggs are the ones that are the achievements in the game, and they are the ones that you can get rewards for completing the achievements while the rest are just for fun and aren't giving any rewards since their rarity is not high enough.
        """
        if member is None:
            member = ctx.author
        eggs = await self.db.get_eggs(member.id)
        user_achievements = await self.db.get_achievements(member.id)
        shards = await self.db.get_user_field(member.id, "shards")
        gems = await self.db.get_user_field(member.id, "gems")

        for achievement in achievements:
            if achievement["condition_type"] == "egg":
                condition = (
                    eggs.get(achievement["condition_key"], 0) >= achievement["condition_value"]
                )
            elif achievement["condition_type"] == "streak":
                streak = await self.db.get_user_field(member.id, "hunt_streak")
                condition = streak >= achievement["condition_value"]
            elif achievement["condition_type"] == "gems":
                condition = gems >= achievement["condition_value"]
            else:
                condition = False

            if condition and not user_achievements.get(achievement["key"], False):
                new_shards = shards + achievement["reward"]
                await self.db.set_user_field(member.id, "shards", new_shards)
                user_achievements[achievement["key"]] = True
                await self.db.set_achievements(member.id, user_achievements)
                await ctx.send(
                    f"🎉 Congratulations {member.mention}! You've unlocked the **{achievement['name']}** achievement "
                    f"and received {achievement['reward']} egg shards!"
                )
                shards = new_shards

        embed = discord.Embed(
            title="Easter Hunt Achievements",
            color=await ctx.embed_colour(),
            description="Complete these achievements to earn egg shards!",
        )

        for achievement in achievements:
            if achievement["condition_type"] == "egg":
                condition = (
                    eggs.get(achievement["condition_key"], 0) >= achievement["condition_value"]
                )
            elif achievement["condition_type"] == "streak":
                streak = await self.db.get_user_field(member.id, "hunt_streak")
                condition = streak >= achievement["condition_value"]
            elif achievement["condition_type"] == "gems":
                condition = gems >= achievement["condition_value"]
            else:
                condition = False

            status = "✅" if condition else "❌"
            reward_status = (
                f"(Reward: {humanize_number(achievement['reward'])} Egg shards)"
                if not user_achievements.get(achievement["key"], False)
                else "(Reward Claimed)"
            )
            embed.add_field(
                name=f"{achievement['name']} {status}",
                value=f"{achievement['description']} {reward_status}",
            )
        await ctx.send(embed=embed)

    @easterhunt.command()
    async def daily(self, ctx: commands.Context):
        """
        Claim your daily Easter gift!

        You can claim every 12 hours.
        The amount of shards you get is from 5 to 140, it's all random of what you get.
        """
        user = ctx.author
        last_daily = await self.db.get_user_field(user.id, "last_daily")
        current_time = time.time()
        cooldown_remaining = 43200 - (current_time - last_daily)
        if cooldown_remaining > 0:
            cooldown_end = int(current_time + cooldown_remaining)
            return await ctx.send(
                f"the Easter Bunny’s still egg-hausted from hopping around! Check back <t:{cooldown_end}:R> for more goodies.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        shards = random.randint(5, 140)
        # Rare chance for a gem in daily
        if random.random() < 0.05:  # 5% chance
            gems = await self.db.get_user_field(user.id, "gems")
            await self.db.set_user_field(user.id, "gems", gems + 1)
            await ctx.send("You found a hidden gem in your daily gift! 💎")

        end_time = int((datetime.now() + timedelta(hours=12)).timestamp())
        current_shards = await self.db.get_user_field(user.id, "shards")
        await self.db.set_user_field(user.id, "shards", current_shards + shards)
        await ctx.send(
            f"The Easter Bunny hops by and drops {shards} Egg Shards in your basket! Egg-citing, right? Come back <t:{end_time}:R> for another yolky surprise!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )
        await self.db.set_user_field(user.id, "last_daily", current_time)

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def give(self, ctx, member: discord.Member, egg_type: str, amount: int = 1):
        """
        Give some of your eggs to another user!

        **Arguments**:
        - `member`: The user to give the eggs to.
        - `egg_type`: The type of egg to give (common, silver, gold, shiny).
        - `amount`: The number of eggs to give (default is 1).

        **Notes**:
        - You can only give Common, Silver, Gold, or Shiny Eggs. Legendary and Mythical Eggs cannot be traded.
        - You must have at least the number of eggs you're trying to give.
        - There’s a 5 second cooldown between giving eggs.
        """
        giver = ctx.author
        if member == giver:
            return await ctx.send(
                "You can't give eggs to yourself! 🥚",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        if member.bot:
            return await ctx.send(
                "You can't give eggs to a bot! 🤖",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        last_give = await self.db.get_user_field(giver.id, "last_give")
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

        giver_count = await self.db.get_egg_count(giver.id, egg_type)
        if giver_count < amount:
            return await ctx.send(
                f"You don’t have enough {egg_type.capitalize()} Eggs to give! "
                f"You have {giver_count}, but you’re trying to give {amount}.🥚",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        await self.db.set_egg_count(giver.id, egg_type, giver_count - amount)
        receiver_count = await self.db.get_egg_count(member.id, egg_type)
        await self.db.set_egg_count(member.id, egg_type, receiver_count + amount)

        await self.db.set_user_field(giver.id, "last_give", current_time)
        embed = discord.Embed(
            title="Egg Gift 🎁",
            color=await ctx.embed_colour(),
            description=(
                f"{giver.mention} has given {amount} {egg_type.capitalize()} Egg(s) to {member.mention}! 🥚\n"
                f"{member.mention} now has {receiver_count + amount} {egg_type.capitalize()} Egg(s)."
            ),
        )
        await ctx.send(
            embed=embed,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @easterhunt.command()
    async def tradeshards(self, ctx: commands.Context, amount: int):
        """
        Trade your easter shards for credits.

        1 easter shards is worth 20 credits, these credits will be added to your `[p]bank balance`.
        """
        if amount <= 0:
            return await ctx.send("Please enter a positive number of shards to trade!")

        current_shards = await self.db.get_user_field(ctx.author.id, "shards")
        if current_shards < amount:
            return await ctx.send(
                f"You don't have enough shards! You currently have {current_shards} shards.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        credit = amount * 20
        new_shard_amount = current_shards - amount

        currency_name = await bank.get_currency_name(ctx.guild)
        await self.db.set_user_field(ctx.author.id, "shards", new_shard_amount)
        try:
            await bank.deposit_credits(ctx.author, credit)
        except errors.BalanceTooHigh:
            log.error("User's balance is too high to get any credits.")
        await ctx.send(
            f"Successfully traded {humanize_number(amount)} shards for {humanize_number(credit)} {currency_name}!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @easterhunt.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sellgems(self, ctx: commands.Context, amount: int):
        """
        Sell your hidden gems for egg shards.

        Each hidden gem can be sold for 500 egg shards.
        """
        if amount <= 0:
            return await ctx.send("Please enter a positive number of gems to sell!")

        current_gems = await self.db.get_user_field(ctx.author.id, "gems")
        if current_gems < amount:
            return await ctx.send(
                f"You don't have enough hidden gems! You currently have {current_gems} gems.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        shards_earned = amount * 500
        new_gem_amount = current_gems - amount

        current_shards = await self.db.get_user_field(ctx.author.id, "shards")
        new_shard_amount = current_shards + shards_earned

        await self.db.set_user_field(ctx.author.id, "gems", new_gem_amount)
        await self.db.set_user_field(ctx.author.id, "shards", new_shard_amount)
        await ctx.send(
            f"Successfully sold {humanize_number(amount)} hidden gem(s) for {humanize_number(shards_earned)} egg shards!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @easterhunt.command(with_app_command=False)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 800, commands.BucketType.user)
    async def resetme(self, ctx: commands.Context):
        """
        Reset your own Easter hunt data (eggs, shards, pity counters, etc.).
        """
        shards = await self.db.get_user_field(ctx.author.id, "shards")
        eggs = await self.db.get_eggs(ctx.author.id)
        pity = await self.db.get_pity_counters(ctx.author.id)
        ach = await self.db.get_achievements(ctx.author.id)
        gems = await self.db.get_user_field(ctx.author.id, "gems")
        if not any(eggs.values()) and shards == 0 and not pity and not ach and gems == 0:
            return await ctx.send(
                "You don't have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm Reset",
            description="Are you sure you want to reset your Easter hunt data? This will clear all your eggs, shards, gems, pity counters, and streaks. This action cannot be undone!",
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
        await self.db.delete_user_data(ctx.author.id)
        await ctx.send(
            f"Your Easter hunt data has been reset!",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
        )

    @easterhunt.command(aliases=["lb"])
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx: commands.Context):
        """Display the top egg collectors in this guild!

        Only Common, Silver, and Gold Eggs are counted in the total for the leaderboard.
        Shiny, Legendary, and Mythical Eggs are special achievement eggs and are not included.
        """
        guild = ctx.guild
        leaderboard_data = await self.db.get_leaderboard_data()
        filtered_data = []
        for user_id, total_eggs in leaderboard_data:
            member = guild.get_member(user_id)
            if member:
                filtered_data.append((member, total_eggs))

        if not filtered_data:
            return await ctx.send(
                "No one in this guild has collected any eggs yet! Time to start hunting!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        pages = []
        for i in range(0, len(filtered_data), 15):
            page_entries = filtered_data[i : i + 15]
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
    async def work(self, ctx: commands.Context):
        """
        Work for the Easter Bunny with a fun job!

        You earn shards from working, you can trade it in for currency!
        You're lucky if you find a hidden gem while working too, those can be sold for shards that you can trade in for currency.
        """
        user = ctx.author
        if await self.db.get_user_field(user.id, "active_work"):
            return await ctx.send(
                f"{user.mention}, you’re already on the job! Finish your shift first!"
            )

        if await self.db.get_user_field(user.id, "active_hunt"):
            return await ctx.send(
                f"{user.mention}, wait until you finish your active hunting before you can work!"
            )

        last_work = await self.db.get_user_field(user.id, "last_work")
        current_time = time.time()
        cooldown_remaining = 300 - (current_time - last_work)
        if cooldown_remaining > 0:
            cooldown_end = int(current_time + cooldown_remaining)
            return await ctx.send(
                f"{user.mention}, you’re too egg-xhausted from your last shift! Rest until <t:{cooldown_end}:R>."
            )

        view = EasterWork(self, user)
        view.message = await ctx.send(view=view)

    async def start_job(self, interaction, job_type, user):
        if job_type == "gem_miner":
            user_achievements = await self.db.get_achievements(user.id)
            if not user_achievements.get("egg_collector", False):
                return await interaction.response.send_message(
                    "You need to complete the Egg Collector achievement (100 Common Eggs) to unlock Gem Miner!",
                    ephemeral=True,
                )
        try:
            work_ends = time.time() + 300
            await self.db.set_user_field(user.id, "active_work", True)
            await self.db.set_user_field(user.id, "last_work", work_ends)
            await interaction.response.send_message(
                f"{user.mention} starts working as a {job_type.replace('_', ' ').title()}! Shift begins... 🐰💼\nYou finish your shift <t:{int(work_ends)}:R>"
            )

            self.active_tasks[user.id] = self.bot.loop.create_task(
                self.run_job(interaction, job_type, user, work_ends)
            )
        except discord.HTTPException as e:
            log.error(f"Error starting job for {user}: {e}")
            await interaction.channel.send(
                f"{user.mention}, something went wrong starting your shift! It has been cancelled."
            )
            await self.db.set_user_field(user.id, "active_work", False)
            await self.db.set_user_field(user.id, "last_work", 0)
            if user.id in self.active_tasks:
                del self.active_tasks[user.id]

    async def run_job(self, interaction, job_type, user, work_ends):
        try:
            await asyncio.sleep(300)
            current_time = time.time()
            if job_type == "stealer":
                if random.random() < 0.3:
                    target, stolen_egg_type = await find_target_player(
                        self.db, user.id, interaction.guild
                    )
                    if target and stolen_egg_type:
                        target_count = await self.db.get_egg_count(target.id, stolen_egg_type)
                        user_count = await self.db.get_egg_count(user.id, stolen_egg_type)
                        await self.db.set_egg_count(
                            target.id, stolen_egg_type, max(0, target_count - 1)
                        )
                        await self.db.set_egg_count(user.id, stolen_egg_type, user_count + 1)

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
                        user_count = await self.db.get_egg_count(user.id, egg_type)
                        await self.db.set_egg_count(user.id, egg_type, user_count + 1)
                        await interaction.channel.send(
                            f"{user.mention} sneaks back from stealing! You nabbed a {egg_type.title()} Egg from a distracted bunny!"
                        )
                    else:
                        await interaction.channel.send(
                            f"{user.mention} got caught red-handed by an angry bunny! No eggs for you—better luck next shift!"
                        )
            elif job_type == "store_clerk":
                shards = random.randint(5, 25)
                current_shards = await self.db.get_user_field(user.id, "shards")
                await self.db.set_user_field(user.id, "shards", current_shards + shards)
                await interaction.channel.send(
                    f"{user.mention} finishes a shift at the Egg Emporium! Sold some eggs and earned {shards} Egg Shards—nice hustle!"
                )
            elif job_type == "egg_giver":
                shards = random.randint(3, 25)
                current_shards = await self.db.get_user_field(user.id, "shards")
                await self.db.set_user_field(user.id, "shards", current_shards + shards)
                await interaction.channel.send(
                    f"{user.mention} hops around giving out Common Eggs! The bunnies loved it—you earned {shards} Egg Shards for your kindness!"
                )
            elif job_type == "egg_painter":
                egg_type = random.choice(["common", "silver"])
                amount = random.randint(1, 25) if egg_type == "common" else 1
                user_count = await self.db.get_egg_count(user.id, egg_type)
                await self.db.set_egg_count(user.id, egg_type, user_count + amount)
                await interaction.channel.send(
                    f"{user.mention} finishes painting eggs! You created {amount} {egg_type.title()} Egg(s)!"
                )
                if random.random() < 0.1:  # 10% chance for gem
                    gems = await self.db.get_user_field(user.id, "gems")
                    await self.db.set_user_field(user.id, "gems", gems + 1)
                    await interaction.channel.send(
                        f"{user.mention} found a hidden gem while painting! 💎"
                    )
            elif job_type == "gem_miner":
                if random.random() < 0.4:  # 40% chance for gem
                    gems = await self.db.get_user_field(user.id, "gems")
                    await self.db.set_user_field(user.id, "gems", gems + 1)
                    await interaction.channel.send(f"{user.mention} mined a hidden gem! 💎")
                else:
                    if random.random() < 0.5:
                        shards = random.randint(1, 25)
                        current_shards = await self.db.get_user_field(user.id, "shards")
                        await self.db.set_user_field(user.id, "shards", current_shards + shards)
                        await interaction.channel.send(
                            f"{user.mention} found {shards} shards while mining."
                        )
                    else:
                        await interaction.channel.send(
                            f"{user.mention} dug around but found nothing this time."
                        )

            await self.db.set_user_field(user.id, "last_work", current_time)
        except asyncio.CancelledError:
            pass
        except discord.HTTPException as e:
            log.error(f"Error in run_job for {user}: {e}")
            await interaction.channel.send(
                f"{user.mention}, something went wrong during your shift! It has been cancelled."
            )
        finally:
            await self.db.set_user_field(user.id, "active_work", False)
            await self.db.set_user_field(user.id, "last_work", 0)
            if user.id in self.active_tasks:
                del self.active_tasks[user.id]
