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

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.views import ConfirmView


class OwnerCommands(commands.Cog):
    @commands.is_owner()
    @commands.group(with_app_command=False)
    async def ownerset(self, ctx: commands.Context):
        """Owner commands for Easter Hunt."""

    @ownerset.command(name="dbsize", hidden=True)
    async def ownerset_check_db_size(self, ctx):
        """Check the size of the EasterHunt database."""
        if not self.db.db_path.exists():
            return await ctx.send("Database file not found.")

        size_bytes = self.db.db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        await ctx.send(f"Database size: {size_mb:.2f} MB ({humanize_number(size_bytes)} bytes)")

    @ownerset.command(name="setshards")
    async def ownerset_setshards(self, ctx: commands.Context, user: discord.Member, amount: int):
        """Set a user's shard amount."""
        await self.db.set_user_field(user.id, "shards", amount)
        await ctx.send(f"Set {user.name}'s shards to {humanize_number(amount)}")

    @ownerset.command(name="setgems")
    async def ownerset_setgems(self, ctx: commands.Context, user: discord.Member, amount: int):
        """Set a user's hidden gems amount."""
        await self.db.set_user_field(user.id, "gems", amount)
        await ctx.send(f"Set {user.name}'s gems to {humanize_number(amount)}")

    @ownerset.command(name="setimage")
    async def ownerset_setimage(self, ctx: commands.Context, egg_type: str, url: str):
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
            await self.db.set_egg_image(egg_type, None)
            return await ctx.send(
                f"Custom image for {egg_type.title()} Egg has been reset to default.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        await self.db.set_egg_image(egg_type, url)
        await ctx.send(
            f"Custom image for {egg_type.title()} Egg has been set to: <{url}>",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @ownerset.command(name="resetuser")
    @commands.bot_has_permissions(embed_links=True)
    async def ownerset_resetuser(self, ctx: commands.Context, user: discord.Member):
        """
        Reset a specific user's Easter hunt data.
        """
        eggs = await self.db.get_eggs(user.id)
        shards = await self.db.get_user_field(user.id, "shards")
        gems = await self.db.get_user_field(user.id, "gems")
        if not any(eggs.values()) and shards == 0 and gems == 0:
            return await ctx.send(
                f"{user.mention} doesn't have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm User Reset",
            description=f"Are you sure you want to reset {user.mention}'s Easter hunt data? This will clear all their eggs, shards, gems, pity counters, and streaks. This action cannot be undone!",
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

        await self.db.delete_user_data(user.id)
        await ctx.send(
            f"{user.mention}'s Easter hunt data has been reset by {ctx.author.mention}!"
        )

    @ownerset.command(name="resetshift")
    @commands.bot_has_permissions(embed_links=True)
    async def ownerset_resetshift(self, ctx: commands.Context, user: discord.Member):
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

        await self.db.set_user_field(user.id, "active_hunt", False)
        await self.db.set_user_field(user.id, "active_work", False)
        await self.db.set_user_field(user.id, "last_work", 0)
        await ctx.send(
            f"{user.mention}'s Easter hunt and work data has been reset by {ctx.author.mention}!"
        )

    @ownerset.command(name="resetall")
    @commands.bot_has_permissions(embed_links=True)
    async def ownerset_resetall(self, ctx: commands.Context):
        """
        Reset all Easter hunt data for all users and global config.
        """
        user_count = await self.db.get_user_count()
        if user_count == 0:
            return await ctx.send(
                "No users have any data to reset!",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        view = ConfirmView(ctx.author, disable_buttons=True, timeout=30)
        embed = discord.Embed(
            title="Confirm Global Reset",
            description="Are you sure you want to reset ALL Easter hunt data? This will clear all user data (eggs, shards, gems, pity counters, streaks) and global config (custom image URLs) for everyone. This action cannot be undone!",
            color=discord.Color.red(),
        )
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()
        if view.result is None:
            return await ctx.send("Global reset cancelled due to timeout.")
        if not view.result:
            return await ctx.send("Global reset cancelled.")
        await self.db.reset_all()
        await ctx.send(
            f"All Easter hunt data and global config have been reset by {ctx.author.mention}!"
        )

    @ownerset.command(name="setachievement")
    async def ownerset_setachievement(
        self, ctx: commands.Context, user: discord.Member, key: str, value: bool
    ):
        """
        Set a specific achievement for a user (true/false).

        Use the achievement key from [p]easterhunt achievements.
        """
        achievements = await self.db.get_achievements(user.id)
        if key not in achievements:
            return await ctx.send(f"Invalid achievement key: {key}")
        achievements[key] = value
        await self.db.set_achievements(user.id, achievements)
        status = "unlocked" if value else "locked"
        await ctx.send(f"Set {user.name}'s {key} achievement to {status}.")
