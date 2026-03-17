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

import re
from typing import Any, Final, Optional, Tuple, Union

import discord
from red_commons.logging import getLogger
from redbot.core import app_commands, commands

from .view import UnlockView

logger = getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.7.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.lock_views: dict[int, discord.ui.View] = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def manage_lock(
        self,
        ctx: commands.Context,
        action: str,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ) -> None:
        is_thread = isinstance(ctx.channel, discord.Thread)
        is_lock = action == "lock"
        target_role = role or ctx.guild.default_role
        role_display = target_role.name

        if is_thread:
            if target_role != ctx.guild.default_role:
                return await ctx.send(
                    "❌ Threads can only be locked/unlocked for @everyone, not specific roles."
                )
            current_locked = ctx.channel.locked
            if current_locked == is_lock:
                return await ctx.send(
                    f"❌ This thread is already {'locked' if is_lock else 'unlocked'}.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                    mention_author=False,
                )
            send_messages = None  # Not used for threads, but for embed logic
        else:
            if not isinstance(ctx.channel, discord.abc.GuildChannel):
                return await ctx.send(
                    "❌ This command can only be used in guild channels or threads."
                )
            overwrites = ctx.channel.overwrites_for(target_role) or discord.PermissionOverwrite()
            send_messages = False if is_lock else None
            if overwrites.send_messages == send_messages:
                return await ctx.send(
                    f"❌ This channel is already {'locked' if is_lock else 'unlocked'} for {role_display}.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                    mention_author=False,
                )

        title = f"{'Thread' if is_thread else 'Channel'} {'Locked' if is_lock else 'Unlocked'} for {role_display}"
        description = f"{'🔒' if is_lock else '🔓'} {'Locked' if is_lock else 'Unlocked'} {'thread' if is_thread else 'channel'} {ctx.channel.mention} for {role_display}."
        color = 0xFF0000 if is_lock else 0x00FF00

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )
        if reason:
            embed.add_field(
                name="Reason:",
                value=f"{reason if len(reason) < 1024 else 'Reason is too long.'}",
            )
        embed.set_footer(text=f"{action.capitalize()}ed by {ctx.author}")

        view = None
        if target_role == ctx.guild.default_role:
            if ctx.channel.id in self.lock_views:
                old_view = self.lock_views.pop(ctx.channel.id)
                for item in old_view.children:
                    item.disabled = True
                try:
                    await old_view.message.edit(view=old_view)
                except discord.HTTPException as e:
                    logger.warning(f"Failed to disable old view: {e}")
            if is_lock:
                view = UnlockView(ctx, is_thread=is_thread)
                view.message = await ctx.send(embed=embed, view=view)
                self.lock_views[ctx.channel.id] = view
            else:
                await ctx.send(embed=embed)
                if ctx.channel.id in self.lock_views:
                    del self.lock_views[ctx.channel.id]
        else:
            await ctx.send(embed=embed)

        try:
            if is_thread:
                await ctx.channel.edit(locked=is_lock, archived=False)
            else:
                overwrites.send_messages = send_messages
                await ctx.channel.set_permissions(target_role, overwrite=overwrites)
        except discord.Forbidden as e:
            await ctx.send(
                f"❌ I don't have permission to {'manage' if is_thread else 'set permissions for'} @{role_display} in {ctx.channel.mention}."
            )
            logger.warning(
                f"Failed to {'edit thread' if is_thread else f'set permissions for {target_role.name}'} in {ctx.guild.name} ({ctx.guild.id}): {e}",
                exc_info=True,
            )
            return

    async def _parse_reason_and_role(
        self,
        reason: Optional[str],
        role: Optional[discord.Role],
        guild: discord.Guild,
    ) -> Tuple[Optional[str], Optional[discord.Role]]:
        if reason and role is None:
            mentions = re.findall(r"<@&(\d+)>", reason)
            if mentions:
                last_mention_id = int(mentions[-1])
                role = guild.get_role(last_mention_id)
                if role:
                    reason = re.sub(r"\s*<@&\d+>\s*$", "", reason).strip()
                    if not reason:
                        reason = None
                else:
                    logger.warning(f"Role ID {last_mention_id} not found in guild {guild.id}")
        return reason, role

    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're locking this channel/thread (optional)",
        role="The role to lock the channel for (defaults to @everyone; ignored for threads)",
    )
    async def lock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Lock a channel or thread for a specific role or everyone.

        If no role is specified, it locks for @everyone.
        For threads, roles are ignored and it locks for everyone.
        Please note the button will only work for @everyone and not for any other role you specify to lock the channel.
        If you want to unlock a channel with the role you locked it for, you have to use the `[p]unlock` command.

        **Examples**:
        - `[p]lock` - Locks for @everyone with no reason.
        - `[p]lock @Member` - Locks for @Member with no reason (channels only).
        - `[p]lock Reason: spam in this channel` - Locks for @everyone with reason.
        - `[p]lock Reason: spam in this channel @Member` - Locks for @Member with reason (channels only).
        """
        reason, role = await self._parse_reason_and_role(reason, role, ctx.guild)
        await self.manage_lock(ctx, "lock", reason=reason, role=role)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're unlocking this channel/thread",
        role="The role to unlock the channel for (defaults to @everyone; ignored for threads)",
    )
    async def unlock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Unlock a channel or thread for a specific role or everyone.

        If no role is specified, it unlocks for @everyone.
        For threads, roles are ignored and it unlocks for everyone.

        **Examples**:
        - `[p]unlock` - Unlocks for @everyone with no reason.
        - `[p]unlock @Member` - Unlocks for @Member with no reason (channels only).
        - `[p]unlock Reason: spam in this channel` - Unlocks for @everyone with reason.
        - `[p]unlock Reason: spam in this channel @Member` - Unlocks for @Member with reason (channels only).
        """
        reason, role = await self._parse_reason_and_role(reason, role, ctx.guild)
        await self.manage_lock(ctx, "unlock", reason=reason, role=role)

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(manage_channels=True)
    async def thread(self, ctx: commands.Context):
        """Manage thread(s) with [botname]."""

    @thread.command()
    async def close(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Close and archive a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("❌ This channel is not a thread.")
        await ctx.send(f"Archived and closed {ctx.channel.mention}.")
        await ctx.channel.edit(locked=True, archived=True)
