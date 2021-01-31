import aiohttp
import discord
import random
from redbot.core import commands


class Anime(commands.Cog):
    """Random anime images.

    Powered by martinebot.com API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

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
    async def anime(self, ctx):
        """Random anime photos."""
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

#    @commands.command(aliases=["animewallp"])
#    @commands.cooldown(1, 3, commands.BucketType.guild)
#    @commands.max_concurrency(1, commands.BucketType.guild)
#    @commands.bot_has_permissions(embed_links=True)
#    async def animewallpaper(self, ctx):
#        """Random anime wallpaper."""
#        if not ctx.message.channel.is_nsfw():
#            await ctx.send(embed=await self._nsfw_check(ctx))
#            return

#        async with aiohttp.ClientSession() as session:
#            async with session.get(
#                "https://api.martinebot.com/v1/images/subreddit?name=Animewallpaper"
#            ) as resp:
#                response = await resp.json()

#            embed = await ctx.embed_colour()
#            embed = discord.Embed(
#                title=response["data"].get("title", "[No Title]"),
#                url=response["data"]["post_url"],
#                color=embed,
#            )
#            embed.set_footer(text=f"Powered by martinebot.com API")
#            embed.set_image(url=response["data"]["image_url"])
#        try:
#            await ctx.send(embed=embed)
#        except discord.HTTPException:
#            await ctx.send("Bad reponse, please retry the command again.")

    @commands.command(aliases=["animegirls"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def animegirl(self, ctx):
        """Random anime photos."""
        if not ctx.message.channel.is_nsfw():
            await ctx.send(embed=await self._nsfw_check(ctx))
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.martinebot.com/v1/images/subreddit?name=AnimeGirls"
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
