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
from typing import Any, Final, Optional, Union

import discord
from redbot.core import Config, app_commands, commands

from .view import UnlockView

log = logging.getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.1.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = (
        "https://github.com/ltzmax/maxcogs/blob/master/docs/Lockdown.md"
    )

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "log_channel": None,
            "use_embed": False,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def log_channel(
        self,
        ctx: commands.Context,
        guild: discord.Guild,
        event: str,
        reason: Optional[str] = None,
    ) -> None:
        log_channel = await self.config.guild(guild).log_channel()
        if not log_channel:
            return
        log_channel = guild.get_channel(log_channel)
        if not log_channel:
            return
        if (
            not log_channel.permissions_for(guild.me).send_messages
            or not log_channel.permissions_for(guild.me).embed_links
        ):
            log.warning(
                f"I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            return
        embed = discord.Embed(
            title=event,
            description=f"{'**Reason**: ' + reason if reason else ''}",
            color=0xFF0000,
        )
        moderator_name = ctx.author.name
        log_message = f"{event} by {moderator_name}"
        embed.add_field(name="Log Message:", value=log_message)
        embed.add_field(name="Channel:", value=ctx.channel.mention, inline=False)
        embed.set_footer(text=f"Moderator's ID: {ctx.author.id}")
        await log_channel.send(embed=embed)

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lockdownset(self, ctx: commands.Context):
        """Lockdown settings commands."""

    @lockdownset.command()
    async def logchannel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ):
        """Set the channel for logging lockdowns."""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel.clear()
            return await ctx.send("Log channel cleared.")
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}.")

    @lockdownset.command()
    async def useembed(self, ctx: commands.Context, value: bool):
        """Set whether to use embeds or not."""
        await self.config.guild(ctx.guild).use_embed.set(value)
        await ctx.send(f"Use embeds set to {value}.")

    @lockdownset.command()
    async def settings(self, ctx: commands.Context):
        """Get the current log channel."""
        all = await self.config.guild(ctx.guild).all()
        log_channel = all["log_channel"]
        use_embed = all["use_embed"]
        await ctx.send(
            f"## Settings\nLog channel: {ctx.guild.get_channel(log_channel).mention if log_channel else 'None'}\nUse embeds: {use_embed}"
        )

    async def manage_lock(
        self, ctx: commands.Context, action: str, reason: Optional[str] = None
    ) -> None:
        actions = {
            "lock": {
                "title": "Channel Locked",
                "description": f"🔒 Locked channel {ctx.channel.mention} for everyone",
                "color": 0xFF0000,
                "log_event": "Channel Locked",
                "send_messages": False,
                "already_set_message": "❌ This channel is already locked.",
            },
            "unlock": {
                "title": "Channel Unlocked",
                "description": f"🔓 Unlocked channel {ctx.channel.mention} for everyone",
                "color": 0x00FF00,
                "log_event": "Channel Unlocked",
                "send_messages": None,
                "already_set_message": "❌ This channel is already unlocked.",
            },
        }
        action_props = actions.get(action)
        if await self.config.guild(ctx.guild).use_embed():
            embed = discord.Embed(
                title=action_props["title"],
                description=action_props["description"],
                color=action_props["color"],
            )
            if reason:
                embed.add_field(
                    name="Reason:",
                    value=f"{reason if len(reason) < 2024 else 'Reason is too long.'}",
                )
            embed.set_footer(text=f"{action.capitalize()}ed by {ctx.author}")
            if action == "lock":
                view = UnlockView(ctx, reason)
                message = await ctx.send(embed=embed, view=view)
                view.message = message
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"{action_props['description']}\n{'Reason: ' + reason if reason else ''}"
            )

        if isinstance(ctx.channel, discord.Thread):
            await ctx.channel.edit(locked=(action == "lock"))
        else:
            overwrites = (
                ctx.channel.overwrites_for(ctx.guild.default_role)
                or discord.PermissionOverwrite()
            )
            if overwrites.send_messages == action_props["send_messages"]:
                return await ctx.send(action_props["already_set_message"])
            overwrites.send_messages = action_props["send_messages"]
            await ctx.channel.set_permissions(
                ctx.guild.default_role, overwrite=overwrites
            )

        # Log the event
        log_event = action_props["log_event"]
        await self.log_channel(ctx, ctx.guild, event=log_event, reason=reason)

    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command(aliases=["lockdown"])
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're locking this channel",
    )
    async def lock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
    ):
        """
        Lock a channel for everyone.
        """
        await self.manage_lock(ctx, "lock", reason=reason)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're unlocking this channel",
    )
    async def unlock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        channel: Optional[Union[discord.TextChannel, discord.Thread]] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Unlock a channel for everyone.
        """
        await self.manage_lock(ctx, "unlock", reason=reason)

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(manage_channels=True)
    async def thread(self, ctx: commands.Context):
        """Manage thread(s) with [botname]."""

    @thread.command()
    async def close(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Close and archive a thread post.

        If you want to only lock a thread post, you'll have to use `[p]lock` command.
        """
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Archived and closed this thread post!")
        await ctx.channel.edit(locked=True, archived=True)
        await self.log_channel(ctx, ctx.guild, event="Thread Closed", reason=reason)
