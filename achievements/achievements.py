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
import logging

from typing import Any, Final
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu
from .abc import CompositeMetaClass
from .unlock import achievements
from .events import EventsMixin
from .admin_commands import AdminCommands
from .custom_commands import CustomCommands

DEFAULT_EMOJI_CHECK = "✅"
DEFAULT_EMOJI_X = "❌"

log = logging.getLogger("red.maxcogs.achievements")


class Achievements(
    commands.Cog,
    AdminCommands,
    CustomCommands,
    EventsMixin,
    metaclass=CompositeMetaClass,
):
    """Earn achievements by chatting in channels."""

    __version__: Final[str] = "1.4.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/achievements"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_notify": None,
            "use_default_achievements": True,
            "custom_achievements": {},
            "toggle": False,
            "toggle_achievements_notifications": False,
            "blacklisted_channels": [],
            "default_emoji_check": DEFAULT_EMOJI_CHECK,
            "default_emoji_x": DEFAULT_EMOJI_X,
        }
        default_member = {
            "message_count": 0,
            "unlocked_achievements": [],
            "ignore_me": [],
        }
        self.config.register_member(**default_member)
        self.config.register_guild(**default_guild)
        self.achievements = achievements

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: Any, user_id: int) -> None:
        await self.config.member_from_ids(user_id).clear()

    @commands.group(aliases=["achieve"])
    async def achievements(self, ctx):
        """Achievements commands."""

    @achievements.command()
    @commands.guild_only()
    async def ignoreme(self, ctx):
        """Ignore yourself from earning achievements.

        This will prevent you from earning achievements until you run the command again.
        It will stop from counting your messages and unlocking achievements.
        """
        ignore_me = await self.config.member(ctx.author).ignore_me()
        if ctx.author.id in ignore_me:
            ignore_me.remove(ctx.author.id)
            await self.config.member(ctx.author).ignore_me.set(ignore_me)
            await ctx.send("You will now earn achievements.")
        else:
            ignore_me.append(ctx.author.id)
            await self.config.member(ctx.author).ignore_me.set(ignore_me)
            await ctx.send("You will no longer earn achievements.")

    @commands.guild_only()
    @achievements.command(name="list")
    @commands.bot_has_permissions(embed_links=True)
    async def list_achievements(self, ctx):
        """List all available achievements."""

        # Check if we should use default achievements or custom ones
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()

        if use_default_achievements:
            # Use default achievements
            achievements = self.achievements
        else:
            # Use custom achievements
            achievements = await self.config.guild(ctx.guild).custom_achievements()

        # Fetch the author's unlocked achievements
        unlocked_achievements = await self.config.member(
            ctx.author
        ).unlocked_achievements()
        if unlocked_achievements is None:
            unlocked_achievements = []

        default_emoji_check = await self.config.guild(ctx.guild).default_emoji_check()
        default_emoji_x = await self.config.guild(ctx.guild).default_emoji_x()

        achievements_list = [
            f"{default_emoji_check if key in unlocked_achievements else default_emoji_x} `{key}`: {humanize_number(value)} messages"
            for key, value in achievements.items()
        ]
        if not achievements_list:
            return await ctx.send("No achievements available.")
        pages = []
        page = ""
        for achievement in achievements_list:
            if len(page + achievement + "\n") > 2024:
                pages.append(page)
                page = achievement + "\n"
            else:
                page += achievement + "\n"
        if page:
            pages.append(page)
        embeds = [
            discord.Embed(
                title="Achievements", description=page, color=await ctx.embed_color()
            ).set_footer(text=f"Page: {i+1}/{len(pages)}")
            for i, page in enumerate(pages)
        ]
        await SimpleMenu(
            embeds,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @achievements.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def profile(self, ctx, member: discord.Member = None):
        """Check your profile or someone else's."""
        if member is None:
            member = ctx.author

        if member.bot:
            return await ctx.send("Bots don't have profiles.")

        count = await self.get_message_count(member)
        # Calculate next rank

        # Check if we should use default achievements or custom ones
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()

        if use_default_achievements:
            # Use default achievements
            achievements = self.achievements
        else:
            # Use custom achievements
            achievements = await self.config.guild(ctx.guild).custom_achievements()

        sorted_ranks = sorted(achievements.items(), key=lambda x: x[1])
        next_rank = None
        for rank, rank_count in sorted_ranks:
            if count < rank_count:
                next_rank = rank
                break

        embed = discord.Embed(
            title=f"{member}'s Profile", color=await ctx.embed_color()
        )
        embed.add_field(name="Messages:", value=humanize_number(count), inline=False)
        if next_rank:
            embed.add_field(
                name="Next Rank:",
                value=f"`{next_rank}`: {rank_count - count} Messages Left\n`Required`: {rank_count} Messages",
                inline=False,
            )
        embed.set_thumbnail(
            url=member.default_avatar.url if not member.avatar else member.avatar.url
        )
        ignored = member.id in await self.config.member(member).ignore_me()
        if ignored:
            embed.set_footer(text="This member is ignoring from earning achievements.")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @achievements.command(aliases=["lb"])
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx):
        """Check the leaderboard."""
        members = await self.config.all_members(ctx.guild)

        members = {member_id: data for member_id, data in members.items() if ctx.guild.get_member(member_id) is not None}
        sorted_members = sorted(
            members.items(), key=lambda x: x[1]["message_count"], reverse=True
        )
        pages = []
        for i in range(0, len(sorted_members), 20):
            leaderboard = ""
            for member_id, data in sorted_members[i:i+20]:
                member = ctx.guild.get_member(member_id)
                leaderboard += f"{sorted_members.index((member_id, data)) + 1}. {member.mention}: {humanize_number(data['message_count'])} {'messages' if data['message_count'] != 1 else 'message'}\n"
            if leaderboard:
                embed = discord.Embed(
                    title="Leaderboard",
                    description=leaderboard,
                    color=await ctx.embed_color(),
                )
                embed.set_footer(
                    text=f"Page: {i//20 + 1}/{len(sorted_members)//20 + 1}"
                )
                pages.append(embed)

        if not pages:
            return await ctx.send("No leaderboard available.")

        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @achievements.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def unlocked(self, ctx, member: discord.Member = None):
        """Check your unlocked achievements or someone else's."""
        if member is None:
            member = ctx.author
        pages = []
        unlocked_achievements = await self.config.member(member).unlocked_achievements()
        if unlocked_achievements is None:
            unlocked_achievements = []
        unlocked = ""
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()
        default_emoji_check = await self.config.guild(ctx.guild).default_emoji_check()
        for achievement in unlocked_achievements:
            if (
                use_default_achievements
                and not self.achievements
                or (not use_default_achievements and self.achievements)
            ):
                unlocked += f"{default_emoji_check} `{achievement}`\n"
        if unlocked:
            for page in range(0, len(unlocked), 1024):
                embed = discord.Embed(
                    title=f"{member}'s Unlocked Achievements",
                    description=unlocked[page : page + 1024],
                    color=await ctx.embed_color(),
                )
                embed.set_footer(
                    text=f"Page: {page//1024 + 1}/{len(unlocked)//1024 + 1}"
                )
                pages.append(embed)
            await SimpleMenu(
                pages,
                disable_after_timeout=True,
                timeout=120,
            ).start(ctx)
        else:
            await ctx.send("No unlocked achievements.")
