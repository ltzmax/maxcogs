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
    async def stats(self, ctx: commands.Context, user: discord.Member | None = None) -> None:
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

    @counting.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Show the counting leaderboard for the server.

        Displays the top 15 users with the highest counts.
        Please note that the leaderboard only includes users who have counted at least once.
        """
        user_cache: dict = self.settings._user_cache
        entries = []
        for user_id, data in user_cache.items():
            if not data or data.get("count", 0) <= 0:
                continue
            member = ctx.guild.get_member(user_id)
            if member is None or member.bot:
                continue
            entries.append((member, data["count"]))
        if not entries:
            return await ctx.send("No one has counted yet in this server.")
        entries.sort(key=lambda x: x[1], reverse=True)
        invoker_pos = next(
            (i + 1 for i, (m, _) in enumerate(entries) if m.id == ctx.author.id), None
        )
        footer_base = f"Total counters: {len(entries)}"
        if invoker_pos and invoker_pos > 15:
            invoker_count = next(c for m, c in entries if m.id == ctx.author.id)
            footer_base += (
                f" · Your rank: #{invoker_pos} ({cf.humanize_number(invoker_count)} counts)"
            )
        per_page = 15
        total_pages = max(1, -(-len(entries) // per_page))
        pages = []
        for page_num, i in enumerate(range(0, len(entries), per_page), start=1):
            chunk = entries[i : i + per_page]
            table_data = [
                [i + rank, member.display_name, cf.humanize_number(count)]
                for rank, (member, count) in enumerate(chunk, start=1)
            ]
            table = tabulate(
                table_data,
                headers=["#", "User", "Count"],
                tablefmt="simple",
                stralign="left",
                numalign="left",
            )
            embed = discord.Embed(
                title="🏆 Counting Global Leaderboard",
                description=box(table, lang="prolog"),
                color=await ctx.embed_color(),
            )
            embed.set_footer(text=f"Page {page_num}/{total_pages} · {footer_base}")
            pages.append(embed)
        await SimpleMenu(pages=pages, disable_after_timeout=True, timeout=120).start(ctx)

    @counting.command(name="resetme", with_app_command=False)
    @commands.cooldown(1, 460, commands.BucketType.user)
    async def resetme(self, ctx: commands.Context) -> None:
        """
        Reset your own counting stats.

        This will clear your count and last counted timestamp.
        This action cannot be undone, so use it carefully with the confirmation prompt.
        """
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset your counting stats? This cannot be undone.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.settings.clear_user(ctx.author)
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")
