import datetime
import discord

from redbot.core import commands
from redbot.core.utils.chat_formatting import (
    humanize_timedelta,
)

class Count(commands.Cog):
    """Christmas, halloween and Discord birthday's day countdown."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["xmas"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.has_permissions(embed_links=True)
    async def christmas(self, ctx: commands.Context):
        """Sends how many days left until next Christmas."""
        now = datetime.datetime.utcnow()
        xmas = datetime.datetime(now.year, 12, 24)
        if now.date() == xmas.date():
            await ctx.send("Merry Christmas everyone.\N{CHRISTMAS TREE}\N{WRAPPED PRESENT}\nToday is christmas day and therefore the countdown has ended and will return again tomorrow to let you count until next christmas. have a wonderful Happy holiday.\N{BLACK HEART SUIT}\N{VARIATION SELECTOR-16}")
            return
        if xmas < now:
            xmas = xmas.replace(year=now.year + 1)

        em = discord.Embed(
            color=await ctx.embed_colour(),
            title="Time left until Christmas.\N{CHRISTMAS TREE}\N{WRAPPED PRESENT}",
            description=humanize_timedelta(timedelta=xmas - now),
            )
        em.set_image(url="https://media.giphy.com/media/XBKQjIpKNNMOIY0nRt/giphy.gif")
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.command(aliases=["dbday"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.has_permissions(embed_links=True)
    async def countdown(self, ctx: commands.Context):
        """Sends how many time left until Discord's Anniversary.
        This is the countdown when discord has birtday."""
        now = datetime.datetime.utcnow()
        disc = datetime.datetime(now.year, 5, 13)
        if now.date() == disc.date():
            await ctx.send("Today is the day, Happy birthday Discord.\N{PARTY POPPER}")
            return
        if disc < now:
            disc = disc.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.blurple(),
            title="Time left until Discord's Anniversary.\N{PARTY POPPER}\N{CONFETTI BALL}\N{BIRTHDAY CAKE}",
            description=humanize_timedelta(timedelta=disc - now),
        )
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.command(aliases=["hallow"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.has_permissions(embed_links=True)
    async def halloween(self, ctx: commands.Context):
        """Sends how many time left until Halloween.
        Happy halloween, that's all wee need to say."""
        now = datetime.datetime.utcnow()
        hallo = datetime.datetime(now.year, 10, 31)
        if now.date() == hallo.date():
            await ctx.send("Happy Holloween.🎃 Today is the day for you to go and grap all the snacks.")
            return
        if hallo < now:
            hallo = hallo.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.orange(),
            title="Time left until halloween.🎃",
            description=humanize_timedelta(timedelta=hallo - now),
        )
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.command(aliases=["earth"])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.has_permissions(embed_links=True)
    async def earthday(self, ctx: commands.Context):
        """Sends how many time left until Earthday."""
        now = datetime.datetime.utcnow()
        earth = datetime.datetime(now.year, 10, 31)
        if now.date() == earth.date():
            await ctx.send("Today is the day of Earth Day.\N{EARTH GLOBE AMERICAS}\N{VARIATION SELECTOR-16}")
            return
        if earth < now:
            earth = earth.replace(year=now.year + 1)

        em = discord.Embed(
            color=discord.Color.orange(),
            title="Time left until Earth Day.\N{EARTH GLOBE AMERICAS}\N{VARIATION SELECTOR-16}",
            description=humanize_timedelta(timedelta=earth - now),
        )
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")
