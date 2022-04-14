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
import datetime

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_timedelta

from .abc import MixinMeta

class Commands(MixinMeta):
    """Commands in this cog."""

    @commands.group()
    @commands.is_owner()
    async def uptimeset(self, ctx):
        """Settings to change replies."""

    @uptimeset.command(name="toggle", aliases=["replies", "reply"])
    async def uptimeset_toggle(self, ctx: commands.Context, *, toggle: bool):
        """Toggle replies on/off.

        Note: Replies are enabled by default.

        **Example:**
        `[p]uptimeset toggle True`

        **Arguments:**
        `<toggle>` - `True` to enable or `False` to disable.
        """
        await self.config.reply.set(toggle)
        await ctx.send(f"Replies is now {'enabled' if toggle else 'disabled'}.")

    @uptimeset.command(name="version")
    async def uptimeset_version(self, ctx):
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

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        reply = await self.config.reply()
        name = ctx.bot.user.name
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        msg = f"{uptime_str}\n" f"Since: <t:{int(uptime.timestamp())}:F>"
        emb = discord.Embed(
            title=f"{name} has been up for:",
            description=msg,
            colour=await ctx.embed_color(),
        )
        if reply:
            await self.maybe_reply(ctx=ctx, embed=emb)
        else:
            await ctx.send(embed=emb)
