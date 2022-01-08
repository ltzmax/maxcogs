import logging

import aiohttp
import discord
import nekosbest
from redbot.core import commands

log = logging.getLogger("red.maxcogs.nekos")

NEKOS_API = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845322551347.png?size=96"


class Nekos(commands.Cog):
    """Sending nekos images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = nekosbest.Client()

    __version__ = "0.1.6"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command(aliases=["nekos"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def neko(self, ctx):
        """Send a random neko image."""
        neko = await self.session.get_image("nekos")
        emb = discord.Embed(
            title="Here's a pic of neko",
        )
        emb.colour = await ctx.embed_color()
        emb.set_footer(
            text="Powered by nekos.best",
            icon_url=ICON,
        )
        if neko.url:
            emb.set_image(url=neko.url)
        else:
            emb.description = "I was unable to get image, can you try again?"
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        item = discord.ui.Button(
            style=style,
            label="Artist",
            url=neko.artist_name,
        )
        item = discord.ui.Button(
            style=style,
            label="Source",
            url=neko.source_url,
        )
        view.add_item(item=item)
        view.add_item(item=item)
        # Badest way to do i guess (?) lets improve that later.
        await ctx.send(embed=emb, view=view)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def nekosversion(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)
