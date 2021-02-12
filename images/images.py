import aiohttp
import discord
from redbot.core import commands


class Images(commands.Cog):
    """Random image cog.
    
    Powered by martinebot.com API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return


    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def earth(self, ctx):
        """Send a random earth photo.
        
        EarthPorn is your community of landscape photographers and those who appreciate the natural beauty of our home planet."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.martinebot.com/v1/images/subreddit?name=earthporn"
            ) as resp:
                response = await resp.json()
            embed = await ctx.embed_colour()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                color=embed,
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png",
            )
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
            async with session.get(
                "https://api.martinebot.com/v1/images/subreddit?name=spaceporn"
            ) as resp:
                response = await resp.json()
            embed = await ctx.embed_colour()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                color=embed,
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png",
            )
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
            async with session.get(
                "https://api.martinebot.com/v1/images/subreddit?name=astrophotography"
            ) as resp:
                response = await resp.json()
            embed = await ctx.embed_colour()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                color=embed,
            )
            embed.set_footer(
                text=f"Powered by martinebot.com API",
                icon_url="https://cdn.martinebot.com/current/website-assets/avatar.png",
            )
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")
