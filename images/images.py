from random import choice

import aiohttp
import discord
from redbot.core import commands

from .constants import NATURE, PICVIEW, SPACE

MARTINE_API = "https://api.martinebot.com/v1/images/subreddit?name="
MARTINE_ICON = "https://cdn.martinebot.com/current/website-assets/avatar.png"


class Images(commands.Cog):
    """Image cog that shows images."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "3.4.6"
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
        await ctx.trigger_typing()
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
                description=f"From r/{response['data']['subreddit']['name']} | Posted by: {response['data']['author']['name']}",
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting an image.")

    @commands.command(aliases=["natures"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def nature(self, ctx):
        """Send a random nature images."""
        await ctx.trigger_typing()
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
                description=f"From r/{response['data']['subreddit']['name']} | Posted by: {response['data']['author']['name']}",
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting an image.")

    @commands.command(aliases=["pics", "pic", "cityviews"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def cityview(self, ctx):
        """Send a random city / village images."""
        await ctx.trigger_typing()
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
                description=f"From r/{response['data']['subreddit']['name']} | Posted by: {response['data']['author']['name']}",
                url=response["data"]["post_url"],
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting an image.")
