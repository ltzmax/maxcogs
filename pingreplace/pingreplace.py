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
import random
import discord
import logging

from redbot.core import commands
from .pokemon.pokemon import pokemon_names

log = logging.getLogger("red.maxcogs.pingreplace")

class Pingreplace(commands.Cog):
    """Replace the ping pong word with random pokemon names and shows bot's latency."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.0.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    async def cog_unload(self):
        global pingreplace
        if pingreplace:
            try:
                await self.bot.remove_command("ping")
            except Exception as e:
                log.info(e)
            await self.bot.add_command(ping)

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Shows the bot's ping."""
        poke = random.choice(pokemon_names)
        ping = round(self.bot.latency * 1000)
        msg = (f"{poke} `{ping}ms`")
        async with ctx.typing():   
            await ctx.send(msg)

    @commands.command(hidden=True)
    async def pingversion(self, ctx):
        """Shows the cog version."""
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Cog Version:",
                description=f"Author: {self.__author__}\nVersion: {self.__version__}",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(f"Cog Version: {self.__version__}\nAuthor: {self.__author__}")

async def setup(bot):
    ping = Pingreplace(bot)
    global uptime
    uptime = bot.remove_command("uptime")
    await bot.add_cog(ping)
