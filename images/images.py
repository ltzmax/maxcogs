import aiohttp
import discord

from redbot.core import commands

# API's and icons.
from .constants import MARTINE_API, MARTINE_ICON, NEKOS_API

class Images(commands.Cog):
    """Image cog that shows images from different services."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "2.2.3"
    __author__ = ["MAX"]

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    # Credits to Predä for this snippet. but i snipped it from owo-cogs.
    async def _nsfw_check(self, ctx: commands.Context):
        """Message for Safe For Work (SFW) channels."""
        if not ctx.message.channel.is_nsfw():
            em = discord.Embed(
                title="\N{LOCK} NSFW commands cannot be used in non NSFW channel.",
                color=0xaa0000,
            )
        return em

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def earth(self, ctx):
        """Send a random earth images.

        - EarthPorn is your community of landscape photographers and those who appreciate the natural beauty of our home planet."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "earthporn") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def space(self, ctx):
        """Send a random space images.

        - SpacePorn is a subreddit devoted to beautiful space images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "spaceporn") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def astro(self, ctx):
        """Send a random astrophotography images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "astrophotography") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    # Images thats not about space and earth is below from this line.

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def critique(self, ctx):
        """Send a random Critique images.

        - This is a community of passionate photographers to work together to improve one another's work."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "photocritique") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def food(self, ctx):
        """Send a random food images.

        - Images of Food taken by people that have made homemade food or just bought food to take photo and upload on reddit."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "food") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

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
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command(aliases=["city"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def cityview(self, ctx):
        """Send a random City images.
        
        - High quality images of cities."""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "CityPorn") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def fanart(self, ctx):
        """Send a random League of legends fan arts images.

        - Fan-creations of all types for League of Legends!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + "LoLFanArt") as resp:
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
                description=f"Posted by: {response['data']['author']['name']}",
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url=MARTINE_ICON,
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")
