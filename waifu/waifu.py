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
from redbot.core import Config, commands

from .embed import api_call, embedgen

class Waifu(commands.Cog):
    """Sending waifu images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=78634567)
        default_global = {
            "buttons": True,
        }
        self.config.register_global(**default_global)

    async def cog_unload(self):
        await self.session.close()

    __version__ = "0.2.0"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    # Before you ask "Why is this the same code as nekos and kitune?"
    # read same line in nekos.py.

    @commands.group()
    @commands.is_owner()
    async def waifuset(self, ctx):
        """Settings to toggle button."""

    @waifuset.command(aliases=["button"])
    async def toggle(self, ctx: commands.Context, *, toggle: bool):
        """Toggle button on/off.

        Note: buttons are enabled by default.

        **Example:**
        `[p]waifuset toggle True`

        **Arguments:**
        `<toggle>` - `True` to enable or `False` to disable.
        """
        await self.config.buttons.set(toggle)
        await ctx.send(f"Buttons is now {'enabled' if toggle else 'disabled'}.")

    @waifuset.command(name="version")
    @commands.bot_has_permissions(embed_links=True)
    async def waifuset_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def waifu(self, ctx):
        """Send a random waifu image."""
        url = await api_call(self, ctx)
        await embedgen(self, ctx, url)
