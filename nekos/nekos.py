"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging

import aiohttp
import discord
import nekosbest
from redbot.core import commands

log = logging.getLogger("red.maxcogs.nekos")

NEKOS_API = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


class Nekos(commands.Cog):
    """Sending nekos images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = nekosbest.Client()

    __version__ = "0.1.7"
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
            description=f"Artist: [{neko.artist_name}]({neko.artist_href})\nSource: {neko.source_url}",
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
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException as e:
            await ctx.send(
                "Something went wrong while trying to post. Check console for details."
            )
            log.error(e)

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
