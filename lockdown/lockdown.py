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

import discord
import logging

from typing import Optional, Union, Any, Final
from redbot.core import commands, Config, app_commands

log = logging.getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.0.8"
    __author__: Final[str] = "MAX"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Lockdown.md"

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
            title=f"{event}",
            description=reason,
            color=0xFF0000,
        )
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
        self,
        ctx: commands.Context,
        action: str,
        reason: Optional[str] = None,
        channel: Optional[Union[discord.TextChannel, discord.Thread]] = None,
        role: Optional[discord.Role] = None,
    ):
        if role is None:
            role = ctx.guild.default_role

        bot_role = ctx.guild.get_member(ctx.me.id).top_role
        if role >= bot_role:
            return await ctx.send(
                f"I can't {action} a channel for a role higher than or equal to my top role."
            )

        top_role = ctx.guild.get_member(ctx.author.id).top_role
        if role >= top_role:
            return await ctx.send(
                f"You can't {action} a channel for a role higher than or equal to your top role."
            )

        if channel is None:
            channel = ctx.channel

        embed_title = "Channel Locked" if action == "lock" else "Channel Unlocked"
        embed_description = f"{'🔒' if action == 'lock' else '🔓'} {'Locked' if action == 'lock' else 'Unlocked'} channel {channel.mention} for {role.mention if role != ctx.guild.default_role else 'everyone'}"
        log_event = "Channel Locked" if action == "lock" else "Channel Unlocked"

        if await self.config.guild(ctx.guild).use_embed():
            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=0xFF0000 if action == "lock" else 0x00FF00,
            )
            if reason:
                embed.add_field(
                    name="Reason:",
                    value=f"{reason if len(reason) < 1024 else 'Reason is too long.'}",
                )
            embed.set_footer(text=f"{action.capitalize()}ed by {ctx.author}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"{embed_description}\n{'Reason: ' + reason if reason else ''}"
            )

        if isinstance(channel, discord.Thread):
            if action == "lock":
                await ctx.channel.edit(locked=True)
            elif action == "unlock":
                await ctx.channel.edit(locked=False)
        else:
            overwrites = channel.overwrites_for(role)
            if overwrites is None:
                overwrites = discord.PermissionOverwrite()

            if action == "lock":
                if overwrites.send_messages is False:
                    return await ctx.send(
                        f"❌ {'Role' if role != ctx.guild.default_role else 'Channel'} is already locked."
                    )
                overwrites.send_messages = False
            elif action == "unlock":
                if overwrites.send_messages is None:
                    return await ctx.send(
                        f"❌ {'Role' if role != ctx.guild.default_role else 'Channel'} is already unlocked."
                    )
                overwrites.send_messages = None
            await channel.set_permissions(role, overwrite=overwrites)

        await self.log_channel(
            guild=ctx.guild,
            event=log_event,
            reason=f"{channel.mention} was {action}ed by {ctx.author.mention}"
            + (f" for Reason: {reason}" if reason else ""),
        )

    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command(aliases=["lockdown"])
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're locking this channel",
        channel="The channel to lockdown.",
        role="The role to lockdown.",
    )
    async def lock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        channel: Optional[Union[discord.TextChannel, discord.Thread]] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Lock a channel for a role or everyone.

        If no channel is provided, the current channel will be locked for the provided role else the default role.
        """
        await self.manage_lock(ctx, "lock", reason=reason, channel=channel, role=role)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're unlocking this channel",
        channel="The channel to unlock.",
        role="The role to unlock.",
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
        Unlock a channel for a role or everyone.

        If no channel is provided, the current channel will be unlocked for the provided role else the default role.
        """
        await self.manage_lock(ctx, "unlock", reason=reason, channel=channel, role=role)

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(manage_channels=True)
    async def thread(self, ctx: commands.Context):
        """Manage thread(s) with [botname].""""

    @thread.command()
    async def close(self, ctx: commands.Context):
        """Close and archive a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Archived and closed {channel.mention}!")
        await ctx.channel.edit(locked=True, archived=True)
