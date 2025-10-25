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
from collections import defaultdict
from datetime import datetime
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView, SimpleMenu
from tabulate import tabulate


class UserCommands(commands.Cog):
    @commands.hybrid_group()
    @commands.guild_only()
    async def counting(self, ctx: commands.Context) -> None:
        """Commands for the counting game."""

    @counting.command(name="stats")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stats(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        """Show counting stats for a user."""
        user = user or ctx.author
        if user.bot:
            return await ctx.send("Bots cannot count.")
        settings = await self.settings.get_user_settings(user)
        if not settings["count"]:
            return await ctx.send(f"{user.display_name} has not counted yet.")
        last_count = (
            datetime.fromisoformat(settings["last_count_timestamp"])
            if settings["last_count_timestamp"]
            else None
        )
        time_str = discord.utils.format_dt(last_count, "R") if last_count else "Never"
        table = tabulate(
            [
                ["User", user.display_name],
                ["Total Counts", cf.humanize_number(settings["count"])],
            ],
            headers=["Stat", "Value"],
            tablefmt="simple",
            stralign="left",
        )
        await ctx.send(f"Last counted: {time_str}\n{box(table, lang='prolog')}")

    @counting.command(name="resetme", with_app_command=False)
    @commands.cooldown(1, 360, commands.BucketType.user)
    async def resetme(self, ctx: commands.Context) -> None:
        """
        Reset your own counting stats.

        This will clear your count and last counted timestamp.
        This action cannot be undone, so use it carefully with the confirmation prompt.
        """
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset your counting stats? This cannot be undone.", view=view
        )
        await view.wait()
        if view.result:
            await self.settings.clear_user(ctx.author)
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @counting.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx: commands.Context) -> None:
        """
        Show the counting leaderboard for the server.

        Displays the top users with the highest counts, paginated by 15.
        Note: Only users who have counted at least once since the leaderboard tracking began will appear.
        If you counted before this feature was added, you'll need to count again to be included.
        """
        settings = await self.settings.get_guild_settings(ctx.guild)
        leaderboard = settings.get("leaderboard", {})

        if leaderboard and any(isinstance(k, str) for k in leaderboard):
            new_leaderboard = defaultdict(int)
            name_to_id = {}
            for member in ctx.guild.members:
                dl = member.display_name.lower()
                nl = member.name.lower()
                if dl not in name_to_id:
                    name_to_id[dl] = member.id
                if nl not in name_to_id:
                    name_to_id[nl] = member.id
            unmapped_count = 0
            for key, count in leaderboard.items():
                if isinstance(key, int):
                    new_leaderboard[key] += count
                else:
                    lower_key = key.lower()
                    if lower_key in name_to_id:
                        uid = name_to_id[lower_key]
                        new_leaderboard[uid] += count
                    else:
                        new_leaderboard[key] += count
                        unmapped_count += 1

            # Persist the migrated data
            await self.settings.update_guild(ctx.guild, "leaderboard", dict(new_leaderboard))
            settings = await self.settings.get_guild_settings(ctx.guild)
            leaderboard = settings.get("leaderboard", {})
            if unmapped_count > 0:
                await ctx.send(
                    f"Note: {unmapped_count} legacy name entries couldn't be migrated (name changes?).\nThey remain as separate entries. Count again to consolidate under your current ID."
                )

        if not leaderboard:
            return await ctx.send("No counts recorded yet. Get counting!")

        sorted_items = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        all_keys = [key for key, _ in sorted_items]
        display_names = await self._build_display_names(ctx, all_keys)

        pages = []
        page_size = 15
        for i in range(0, len(sorted_items), page_size):
            page_items = sorted_items[i : i + page_size]
            table_data = [
                [
                    str(pos),
                    display_names.get(key, f"Unknown ({key})"),
                    cf.humanize_number(count),
                ]
                for pos, (key, count) in enumerate(page_items, start=i + 1)
            ]
            table = tabulate(
                table_data,
                headers=["Position", "User", "Count"],
                tablefmt="simple",
                stralign="left",
            )
            page_num = (i // page_size) + 1
            total_pages = (len(sorted_items) + page_size - 1) // page_size
            embed = discord.Embed(
                title=f"Counting Leaderboard - Page {page_num}/{total_pages}",
                description=box(table, lang="prolog"),
                color=await ctx.embed_color(),
            )
            pages.append(embed)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    async def _build_display_names(self, ctx: commands.Context, keys: list) -> dict:
        """
        Efficiently build a mapping of key (int user_id or str legacy_name) to display_name.

        For int keys: Prioritizes guild members, then parallel-fetches missing via API.
        For str keys: Uses the string itself (legacy name).
        """
        display_names = {}
        str_keys = [k for k in keys if isinstance(k, str)]
        for sk in str_keys:
            display_names[sk] = sk

        int_keys = [k for k in keys if isinstance(k, int)]
        if not int_keys:
            return display_names

        relevant_members = {
            m.id: m.display_name for m in ctx.guild.members if m.id in set(int_keys)
        }
        display_names.update(relevant_members)
        missing_ids = [uid for uid in int_keys if uid not in relevant_members]
        if missing_ids:
            fetch_tasks = [self.bot.fetch_user(uid) for uid in missing_ids]
            fetched_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            for result, uid in zip(fetched_results, missing_ids):
                if isinstance(result, (discord.User, discord.Member)):
                    display_names[uid] = result.display_name
                else:
                    display_names[uid] = f"Unknown User ({uid})"
        return display_names
