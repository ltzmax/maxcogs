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
from redbot.core import commands


class ColorConverter(commands.Cog):
    """Convert a color to RGB and hex."""

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

    @commands.group()
    @commands.bot_has_permissions(embed_links=True)
    async def colorhex(self, ctx):
        """Group commands for converting hex and rgb."""

    @colorhex.command(name="hex")
    async def colorhex_hex(self, ctx, *, color: str):
        """Convert a hex color to RGB."""
        if color.startswith("#"):
            color = color[1:]
        if color.startswith("0x"):
            color = color[2:]
        if len(color) == 3:
            color = "".join(f"{c}{c}" for c in color)
        if len(color) != 6:
            return await ctx.send("Invalid color.")
        try:
            color = int(color, 16)
        except ValueError:
            return await ctx.send("Invalid color.")
        r = color >> 16
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        embed = discord.Embed(
            title="Color Hex",
            description=f"RGB ({r}, {g}, {b})",
            colour=discord.Colour(int(color)),
        )
        await ctx.send(embed=embed)

    @colorhex.command(name="rgb")
    async def colorhex_rgb(self, ctx, *, rgb: str):
        """Convert a RGB color to hex."""
        rgb = rgb.split(",")
        if len(rgb) != 3:
            return await ctx.send("Invalid color.")
        try:
            rgb = [int(c) for c in rgb]
        except ValueError:
            return await ctx.send("Invalid color.")
        if not all(0 <= c <= 255 for c in rgb):
            return await ctx.send("Invalid color.")
        color = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
        embed = discord.Embed(
            title="Color Hex",
            description=f"Hex #{hex(color)[2:].upper()}",
            colour=discord.Colour(int(color)),
        )
        await ctx.send(embed=embed)

    @colorhex.command(name="random")
    async def colorhex_random(self, ctx):
        """Get a random color."""
        color = discord.Colour.from_rgb(
            *[random.randint(0, 255) for _ in range(3)]
        ).value
        embed = discord.Embed(
            title="Color Hex",
            description=f"Hex #{hex(color)[2:].upper()}",
            colour=discord.Colour(int(color)),
        )
        await ctx.send(embed=embed)

    @colorhex.command(name="version")
    async def colorhex_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)
