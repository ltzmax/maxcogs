import asyncio
from random import choice

import aiohttp
import discord
from redbot.core import commands
from .constants import (
    CARS,
    MARTINE_API,
    MARTINE_ICON,
    NATURE,
    NEKOS_API,
    PICVIEW,
    SPACE,
)


class Images(commands.Cog):
    """Image cog that shows images."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "3.1.9"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def space(self, ctx):
        """Send a random space images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + choice(SPACE)) as resp:
                if resp.status == 410:
                    return await ctx.send("Failed to fetch API. Unknown error.")
                if resp.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | From r/{response['data']['subreddit']['name']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while attempting to post an image.")

    @commands.command(aliases=["natures"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def nature(self, ctx):
        """Send a random nature images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + choice(NATURE)) as resp:
                if resp.status == 410:
                    return await ctx.send("Failed to fetch API. Unknown error.")
                if resp.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | From r/{response['data']['subreddit']['name']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while attempting to post an image.")

    @commands.command(aliases=["pictures", "pics", "pic"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def picture(self, ctx):
        """Send a random synthetic images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + choice(PICVIEW)) as resp:
                if resp.status == 410:
                    return await ctx.send("Failed to fetch API. Unknown error.")
                if resp.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | From r/{response['data']['subreddit']['name']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while attempting to post an image.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def cars(self, ctx):
        """Send a random car images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + choice(CARS)) as resp:
                if resp.status == 410:
                    return await ctx.send("Failed to fetch API. Unknown error.")
                if resp.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | From r/{response['data']['subreddit']['name']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while attempting to post an image..")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def neko(self, ctx):
        """Send a random neko images.

        Powered by [nekos.best.](https://nekos.best)"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS_API + "nekos") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                url = await response.json()
            embed = discord.Embed(
                title="Here's an image from nekos.", colour=await ctx.embed_color()
            )
            embed.set_footer(text="From nekos.best")
            embed.set_image(url=url["url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while attempting to post an image.")
