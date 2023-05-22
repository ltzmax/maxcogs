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
import asyncio

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from .embed import api_call, embedgen


class NekosBest(commands.Cog):
    """Sends random images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    __version__ = "0.1.20"
    __author__ = "MAX"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/nekosbest/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="nekostversion", aliases=["nekosbestv"], hidden=True)
    async def nekosbest_version(self, ctx: commands.Context):
        """Shows the version of the cog"""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def waifu(self, ctx):
        """Send a random waifu image."""
        url = await api_call(self, ctx, "waifu")
        await embedgen(self, ctx, url, "waifu")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def nekos(self, ctx):
        """Send a random neko image."""
        url = await api_call(self, ctx, "neko")
        await embedgen(self, ctx, url, "neko")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def kitsune(self, ctx):
        """Send a random kitsune image."""
        url = await api_call(self, ctx, "kitsune")
        await embedgen(self, ctx, url, "kitsune")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def husbando(self, ctx):
        """Send a random husbando image."""
        url = await api_call(self, ctx, "husbando")
        await embedgen(self, ctx, url, "husbando")
