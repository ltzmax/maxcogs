import discord

from datetime import datetime
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_timedelta


class Count(commands.Cog):
    """A countdown cog."""

    __author__ = "MAX, Predä"
    __version__ = "0.0.3"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["xmas"])
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def christmas(self, ctx: commands.Context):
        """Sends how many days left until next Christmas."""
        now = datetime.utcnow()
        xmas = datetime(now.year, 12, 25)
        if now.date() == xmas.date():
            await ctx.send(
                "Merry Christmas everyone.\N{CHRISTMAS TREE}\N{WRAPPED PRESENT}"
            )
            return
        if xmas < now:
            xmas = xmas.replace(year=now.year + 1)

        em = discord.Embed(
            color=await ctx.embed_colour(),
            title="Time left until Christmas.\N{CHRISTMAS TREE}\N{WRAPPED PRESENT}",
            description=humanize_timedelta(timedelta=xmas - now),
        )
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException:
            await ctx.send(embed=em)

    @commands.command(aliases=["dbday"])
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def countdown(self, ctx: commands.Context):
        """Sends how many time left until Discord's Anniversary."""
        now = datetime.utcnow()
        disc = datetime(now.year, 5, 13)
        if now.date() == disc.date():
            await ctx.send("Happy birthday Discord.\N{PARTY POPPER}")
            return
        if disc < now:
            disc = disc.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.blurple(),
            title="Time left until Discord's Anniversary.\N{PARTY POPPER}\N{CONFETTI BALL}\N{BIRTHDAY CAKE}",
            description=humanize_timedelta(timedelta=disc - now),
        )
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException:
            await ctx.send(embed=em)

    @commands.command()
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def halloween(self, ctx: commands.Context):
        """Sends how many time left until Halloween."""
        now = datetime.utcnow()
        hallo = datetime(now.year, 10, 31)
        if now.date() == hallo.date():
            await ctx.send("Happy Holloween.🎃")
            return
        if hallo < now:
            hallo = hallo.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.orange(),
            title="Time left until halloween.🎃",
            description=humanize_timedelta(timedelta=hallo - now),
        )
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException:
            await ctx.send(embed=em)

    @commands.command()
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def earthday(self, ctx: commands.Context):
        """Sends how many time left until Earthday."""
        now = datetime.utcnow()
        earth = datetime(now.year, 10, 31)
        if now.date() == earth.date():
            await ctx.send(
                "Have a good Earth Day.\N{EARTH GLOBE AMERICAS}\N{VARIATION SELECTOR-16}"
            )
            return
        if earth < now:
            earth = earth.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.orange(),
            title="Time left until Earth Day.\N{EARTH GLOBE AMERICAS}\N{VARIATION SELECTOR-16}",
            description=humanize_timedelta(timedelta=earth - now),
        )
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException:
            await ctx.send(embed=em)
