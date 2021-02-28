import aiohttp
import discord
from redbot.core import commands

API_URL = "https://api.martinebot.com/v1/images/subreddit?name="

class Images(commands.Cog):
    """Random image cog.
    
    This cog is powered by martinebot.com API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.1.2"
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
        """Send a random earth photo.
        
        EarthPorn is your community of landscape photographers and those who appreciate the natural beauty of our home planet."""
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + "earthporn") as resp:
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                description = f"Posted by: {response['data']['author']['name']}"
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png"
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
        """Send a random space photo.
        
        SpacePorn is a subreddit devoted to beautiful space images."""
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + "spaceporn") as resp:
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                description = f"Posted by: {response['data']['author']['name']}"
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png"
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
        """Send a random astrophotography photo.
        
        Images of space, taken by amateurs."""
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + "astrophotography") as resp:
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                description = f"Posted by: {response['data']['author']['name']}"
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png"
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command(aliases=["aniwallp"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def animewallpaper(self, ctx):
        """Send a random animewallpaper photo.
        
        Subreddit for anime and anime-style wallpapers.
        
        This is NSFW command due to some anime wallpaper are nsfw."""
        if not ctx.message.channel.is_nsfw():
            await ctx.send(embed=await self._nsfw_check(ctx))
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + "Animewallpaper") as resp:
                response = await resp.json()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                description = f"Posted by: {response['data']['author']['name']}"
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API | Upvotes {response['data']['upvotes']}",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png"
            )
            embed.colour = await ctx.embed_color()
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")
