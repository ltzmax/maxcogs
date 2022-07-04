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


class Quote(commands.Cog):
    """Get a random quote."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    __version__ = "0.0.5"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """thanks sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command(aliases=["quotes"])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def quote(self, ctx):
        """
        Get a random quote.
        """
        base_url = "https://api.quotable.io/random"
        async with ctx.typing():
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                data = await response.json()
                quote = data["content"]
                author = data["author"]
                embed = discord.Embed(
                    description="{}\n\n- {}".format(quote, author),
                    color=discord.Color.random(),
                )
                embed.set_footer(text="Quote provided by Quotable.io")
                await ctx.send(embed=embed)
