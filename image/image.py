import aiohttp
import discord
import random
from redbot.core import commands


class Image(commands.Cog):
    """Random image cog posted from reddit.

    Powered by martinebot.com API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    # Credits to Predä. for this snippet. but i snipped it from owo-cogs.
    async def _nsfw_check(self, ctx: commands.Context):
        """Message for Safe For Work (SFW) channels."""
        if not ctx.message.channel.is_nsfw():
            em = discord.Embed(
                title="\N{LOCK} NSFW commands cannot be used in non NSFW channel.",
                color=0xaa0000,
            )
        return em

        # This might be moved to it's own cog since it's nsfw and it's better off from SFW commands.
        # TODO: an anime cog with anime based sub reddits is something i think about with this.
    
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def anime(self, ctx):
        """Random anime photos.

        This is marked as nsfw due to some images can be nsfw.
        """
        if not ctx.message.channel.is_nsfw():
            await ctx.send(embed=await self._nsfw_check(ctx))
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.martinebot.com/v1/images/subreddit?name=anime_irl"
            ) as resp:
                response = await resp.json()

            embed = await ctx.embed_colour()
            embed = discord.Embed(
                title=response["data"].get("title", "[No Title]"),
                url=response["data"]["post_url"],
                color=embed,
            )
            embed.set_footer(text=f"Powered by martinebot.com API")
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def earth(self, ctx):
        """Random earth photos."""
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
            embed.set_footer(text=f"Powered by martinebot.com API")
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
        """Random space photos."""
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
            embed.set_footer(text=f"Powered by martinebot.com API")
            embed.set_image(url=response["data"]["image_url"])
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Bad reponse, please retry the command again.")
