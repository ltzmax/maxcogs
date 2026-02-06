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
from typing import Final

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.commands.converter import parse_timedelta

log = getLogger("red.maxcogs.vanish")


class Vanish(commands.Cog):
    """
    This will allow you to self-timeout yourself, similar to Twitch's timeout command from streamelemets and fossabot and probably hundered of other twitch bots.

    Note to admins: It is not recommended to set the timeout duration to very high values as users will not be able to interact in any way in the server during the timeout period.
    """

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/vanish/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=987485415)
        default_guild = {
            "toggle": False,
            "vanish_duration": "1m",
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(moderate_members=True)
    async def vanish(self, ctx: commands.Context):
        """
        Timeout yourself, just like you do on twitch.

        It won't delete your messages like it does on twitch but you will be unable to send messages or react to messages for the configured duration.
        """
        toggle = await self.config.guild(ctx.guild).toggle()
        if not toggle:
            return await ctx.send("The vanish command is currently disabled in this server.")

        member = ctx.author
        duration_str = await self.config.guild(ctx.guild).vanish_duration()
        delta = parse_timedelta(
            duration_str,
            minimum=datetime.timedelta(seconds=60),
            maximum=datetime.timedelta(days=28),
        )
        if delta is None:
            log.error(f"Invalid vanish duration for guild {ctx.guild.id}: {duration_str}")

        # moderators, administrators and the guild owner cannot timeout themselves.
        if (
            ctx.author.guild_permissions.moderate_members
            or ctx.author.guild_permissions.administrator
            or ctx.author.guild_permissions.kick_members
            or ctx.author.guild_permissions.ban_members
            or ctx.author == ctx.guild.owner
        ):
            return await ctx.send(
                "You cannot timeout yourself as you have moderation, administrative permissions or you are the guild owner."
            )

        await member.timeout_for(duration=delta, reason="Self-timeout via vanish command")
        await ctx.send(f"You have vanished (timed out) yourself for {duration_str}.")

    @commands.admin()
    @commands.group()
    @commands.guild_only()
    async def vanishconfig(self, ctx: commands.Context):
        """Configuration commands for the Vanish cog."""

    @vanishconfig.command()
    @commands.bot_has_permissions(moderate_members=True)
    async def toggle(self, ctx: commands.Context, on_off: bool):
        """
        Enable or disable the vanish command in the server.

        Disabled by default.

        **Arguments:**
        - `<on_off>`: `True` to enable, `False` to disable.
        """
        await self.config.guild(ctx.guild).toggle.set(on_off)
        status = "enabled" if on_off else "disabled"
        await ctx.send(f"The vanish command has been {status} in this server.")

    @vanishconfig.command()
    async def timeout(self, ctx: commands.Context, duration: str):
        """
        Set the default vanish timeout duration for the server.

        default is 1 minute.
        Duration must be between 60 seconds and 28 days.
        Moderators, administrators and the guild owner cannot timeout themselves using the vanish command.

        NOTE: It is not recommended to set this value to very high values as users will not be able to interact in any way in the server during the timeout period.

        **Examples:**
        - `[p]vanishconfig timeout 10m` (10 minutes)
        - `[p]vanishconfig timeout 1h` (1 hour)

        **Arguments:**
        - `<duration>`: The duration for the timeout (e.g., 10m, 1h, 2d).
        """
        delta = parse_timedelta(
            duration, minimum=datetime.timedelta(seconds=60), maximum=datetime.timedelta(days=28)
        )
        if delta is None:
            log.error(f"Invalid vanish duration input by {ctx.author} in guild {ctx.guild.id}: {duration}")
            return await ctx.send(
                "Invalid duration format or out of bounds (must be between 60s and 28 days). Use formats like 10m, 1h, 2d, etc."
            )

        await self.config.guild(ctx.guild).vanish_duration.set(duration)
        await ctx.send(f"Vanish duration set to {duration}.")
