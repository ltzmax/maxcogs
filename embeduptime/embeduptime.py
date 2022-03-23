# Thanks Red-DiscordBot for their hard work.
# This uptimer is a fork of red, which uses embed.
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
import logging
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_timedelta

log = logging.getLogger("red.maxcogs.embeduptime")


class EmbedUptime(commands.Cog):
    """Shows [botname]'s uptime."""

    __version__ = "0.2.0"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=78634567)
        default_global = {
            "reply": True,
        }
        self.config.register_global(**default_global)

    async def cog_unload(self):
        global uptime
        if uptime:
            try:
                await self.bot.remove_command("uptime")
            except Exception as e:
                log.info(e)
            await self.bot.add_command(uptime)

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
    @commands.bot_has_permissions(embed_links=True)
    async def uptimeset_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)

    @staticmethod
    async def maybe_reply(
        ctx: commands.Context,
        message: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        mention_author: Optional[bool] = False,
    ) -> None:
        """Try to reply to a message.

        Parameters
        ----------
        ctx : redbot.core.commands.Context
            The command invocation context.

        message : Optional[str] = None
            The message to send.

        embed : Optional[discord.Embed] = None
            The embed to send in the message.

        mention_author : Optional[bool] = False
            Whether to mention the author of the message. Defaults to False.
        """
        try:
            await ctx.reply(message, embed=embed, mention_author=mention_author)
        except discord.NotFound as e:
            await ctx.send(message, embed=embed)
            log.info(e)

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


async def setup(bot):
    eu = EmbedUptime(bot)
    global uptime
    uptime = bot.remove_command("uptime")
    await bot.add_cog(eu)
