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
            "Are you sure you want to reset your counting stats? This cannot be undone.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.settings.clear_user(ctx.author)
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")
