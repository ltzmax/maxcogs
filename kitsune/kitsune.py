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
import logging

import aiohttp
import discord
from redbot.core import commands

log = logging.getLogger("red.maxcogs.kitsune")

NEKOS_API = "https://nekos.best/api/v2/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


class Kitsune(commands.Cog):
    """Sending Kitsune images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    __version__ = "0.0.4"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def kitsune(self, ctx):
        """Send a random kitsune image."""
        async with self.session.get(NEKOS_API + "kitsune") as response:
            if response.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
            url = await response.json()

            artist_name = url["results"][0]["artist_name"]
            source_url = url["results"][0]["source_url"]
            artist_href = url["results"][0]["artist_href"]

            emb = discord.Embed(
                title="Here's a pic of kitsune",
                description=f"**Artist:** [{artist_name}]({artist_href})\n**Source:** {source_url}",
            )
            emb.colour = await ctx.embed_color()
            emb.set_image(url=url["results"][0]["url"])
            emb.set_footer(text="Powered by nekos.best", icon_url=ICON)
            try:
                await ctx.send(embed=emb)
            except discord.HTTPException as e:
                await ctx.send(
                    "I was unable to send image, check logs for more details."
                )
                log.error(e)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def kitsuneversion(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)
