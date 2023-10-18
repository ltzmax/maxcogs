"""
MIT License

Copyright (c) 2020-2023 phenom4n4n
Copyright (c) 2023-present ltzmax

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
from datetime import date
from typing import Literal, Optional, Final

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.chat_formatting import humanize_list

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class Ratings(commands.Cog):
    """
    Rate how simp you are.
    """
    __author__: Final[str] = humanize_list(["phenom4n4n", "ltzmax"])
    __version__: Final[str] = "1.0.2"
    __docs__: Final[
        str
    ] = "https://maxcogs.gitbook.io/maxcogs/cogs/ratings"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=2353262345234652,
            force_registration=True,
        )

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        return

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def simprate(
        self, ctx: commands.Context, member: Optional[discord.Member], *, simpable: Optional[str]
    ):
        """Find out how much someone is simping for something."""
        member = member or ctx.author
        rate = random.choice(range(1, 100))
        emoji = "😳"
        if simpable:
            message = f"{member.name} is **{rate}**% simping for {simpable} {emoji}"
        else:
            message = f"{member.name} is **{rate}**% simp {emoji}"
        embed = discord.Embed(
            title=message,
            color=await ctx.embed_color(),
            description=chat.inline(("█" * round(rate / 4)).ljust(25)) + f" {rate}% {emoji}",
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def clownrate(self, ctx: commands.Context, member: Optional[discord.Member]):
        """Reveal someone's clownery."""
        member = member or ctx.author
        rate = random.choice(range(1, 100))
        emoji = "🤡"
        embed = discord.Embed(
            title=f"{member.name}'s Clownery",
            color=await ctx.embed_color(),
            description=chat.inline(("█" * round(rate / 4)).ljust(25)) + f" {rate}% {emoji}",
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["iq"])
    @commands.bot_has_permissions(embed_links=True)
    async def iqrate(self, ctx: commands.Context, member: Optional[discord.Member]):
        """100% legit IQ test."""
        member = member or ctx.author
        random.seed(member.id + self.bot.user.id)
        if await self.bot.is_owner(member):
            iq = random.randint(200, 500)
        else:
            iq = random.randint(-10, 200)
        if iq >= 160:
            emoji = "🧠"
        elif iq >= 100:
            emoji = "🤯"
        else:
            emoji = "😔"
        embed = discord.Embed(
            title=f"{member.name}'s IQ",
            color=await ctx.embed_color(),
            description=f"{iq} {emoji}",
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["sanity"])
    @commands.bot_has_permissions(embed_links=True)
    async def sanitycheck(self, ctx: commands.Context, member: Optional[discord.Member]):
        """Check your sanity."""
        member = member or ctx.author
        random.seed(str(member.id) + str(date.today().strftime("%j")) + str(self.bot.user.id))
        sanity = random.randint(0, 100)
        embed = discord.Embed(
            title=f"{member.name}'s Sanity Check",
            color=await ctx.embed_color(),
            description=chat.inline(("█" * round(sanity / 4)).ljust(25)) + f" {sanity}%",
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def drunk(self, ctx: commands.Context, member: Optional[discord.Member]):
        """Get drunk procent.

        **Example**:
        - `[p]drunk atticus` - This will get drunk procent of atticus.

        **Arguments**:
        - `[member]` - The member you wanna check.
        """
        if member is None:
            member = ctx.author
        if member.bot:
            return await ctx.send("I'm not drunk, I'm just a bot.")
        drunk = random.randint(0, 100)
        embed = discord.Embed(
            title=f"{member.name} is {drunk}% drunk.",
            color=await ctx.embed_color(),
            description=chat.inline(("█" * round(drunk / 4)).ljust(25)) + f" {drunk}%",
        )
        await ctx.send(embed=embed)
