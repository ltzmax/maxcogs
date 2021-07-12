from random import choice

import aiohttp
import discord
from redbot.core import commands

MARTINE_API = "https://api.martinebot.com/v1/images/subreddit?name="
MARTINE_ICON = "https://cdn.martinebot.com/current/website-assets/avatar.png"

SPACE = [
    "spaceporn",
    "astrophotography",
    "LandscapeAstro",
    "spaceengine",
]


class SpaceImages(commands.Cog):
    """Image cog that shows space images."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.2.0"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def space(self, ctx):
        """Send a random space image."""
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as session:
            async with session.get(MARTINE_API + choice(SPACE)) as resp:
                if resp.status == 410:
                    return await ctx.send("Failed to fetch API. Unknown error.")
                if resp.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                data = await resp.json()
                title = data["data"].get("title")
                subreddit = data["data"]["subreddit"]["name"]
                images = data["data"]["image_url"]

            emb = discord.Embed(title=f"{title}", url=f"{images}")
            emb.set_footer(
                text=f"Powered by martinebot.com API | From r/{subreddit}",
                icon_url=MARTINE_ICON,
            )
            emb.colour = await ctx.embed_color()
            emb.set_image(url=images)
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting an image.")
