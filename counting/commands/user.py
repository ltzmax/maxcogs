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

from datetime import datetime
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import SimpleMenu
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

        Displays the top 15 users with the highest counts.
        Please note that the leaderboard only includes users who have counted at least once. if you have counted before this command was added, you will not be on the leaderboard until you count again.
        """
        settings = await self.settings.get_guild_settings(ctx.guild)
        leaderboard = settings.get("leaderboard", {})

        if not leaderboard:
            return await ctx.send("No counts recorded yet.")

        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        pages = []
        page_size = 15
        for i in range(0, len(sorted_leaderboard), page_size):
            page_leaderboard = sorted_leaderboard[i : i + page_size]
            table = tabulate(
                [
                    [
                        str(pos),
                        await self._get_display_name(ctx, user_id),
                        cf.humanize_number(count),
                    ]
                    for pos, (user_id, count) in enumerate(page_leaderboard, start=i + 1)
                ],
                headers=["Position", "User", "Count"],
                tablefmt="simple",
                stralign="left",
            )
            embed = discord.Embed(
                title="Counting Leaderboard",
                description=box(table, lang="prolog"),
                color=await ctx.embed_color(),
            )
            pages.append(embed)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    async def _get_display_name(self, ctx: commands.Context, user_id: int) -> str:
        """Helper method to get a user's display name, handling cases where get_member fails."""
        member = ctx.guild.get_member(user_id)
        if member:
            return member.display_name
        try:
            user = await self.bot.fetch_user(user_id)
            return user.display_name if user else f"Unknown User ({user_id})"
        except discord.errors.NotFound:
            return f"Unknown User ({user_id})"
