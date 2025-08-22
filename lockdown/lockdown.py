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
from redbot.core import Config, app_commands, commands

from .view import UnlockView

logger = getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.6.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
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

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lockdownset(self, ctx: commands.Context):
        """Lockdown settings commands."""

    @lockdownset.command()
    async def useembed(self, ctx: commands.Context, value: bool):
        """Set whether to use embeds or not."""
        await self.config.guild(ctx.guild).use_embed.set(value)
        await ctx.send(f"Use embeds set to {value}.")

    @lockdownset.command()
    async def settings(self, ctx: commands.Context):
        """Get the current log channel."""
        all = await self.config.guild(ctx.guild).all()
        use_embed = all["use_embed"]
        await ctx.send(f"## Settings\nUse embeds: {use_embed}")

    async def manage_lock(
        self,
        ctx: commands.Context,
        action: str,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ) -> None:
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            return await ctx.send(
                f"❌ You can't {action} a thread channel(s) with this command.\nUse `{ctx.clean_prefix}thread {action}` instead."
            )

        target_role = role or ctx.guild.default_role
        is_lock = action == "lock"
        title = f"Channel {'Locked' if is_lock else 'Unlocked'} for {target_role.name}"
        description = f"{'🔒' if is_lock else '🔓'} {'Locked' if is_lock else 'Unlocked'} channel {ctx.channel.mention} for {target_role.name}."
        color = 0xFF0000 if is_lock else 0x00FF00
        log_event = f"Channel {'Locked' if is_lock else 'Unlocked'} for {target_role.name}"
        already_set_message = f"❌ This channel is already {'locked' if is_lock else 'unlocked'} for {target_role.mention.lstrip('@')}."
        send_messages = False if is_lock else None
        overwrites = ctx.channel.overwrites_for(target_role) or discord.PermissionOverwrite()

        if overwrites.send_messages == send_messages:
            return await ctx.send(
                already_set_message,
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )
        if reason:
            embed.add_field(
                name="Reason:",
                value=f"{reason if len(reason) < 2024 else 'Reason is too long.'}",
            )
        embed.set_footer(text=f"{action.capitalize()}ed by {ctx.author}")

        if is_lock and target_role == ctx.guild.default_role:
            view = UnlockView(ctx)
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed)

        try:
            overwrites.send_messages = send_messages
            await ctx.channel.set_permissions(target_role, overwrite=overwrites)
        except discord.Forbidden as e:
            return await ctx.send(
                f"❌ I don't have permission to set permissions for {target_role.mention} in {ctx.channel.mention}."
            )
            logger.warning(
                f"Failed to set permissions for {target_role.name} in {ctx.guild.name} ({ctx.guild.id}): {e}",
                exc_info=True,
            )

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
        reason="The reason why you're locking this channel (optional)",
        role="The role to lock the channel for (defaults to @everyone)",
    )
    async def lock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Lock a channel for a specific role or everyone.

        If no role is specified, the channel is locked for @everyone.
        Please note the button will only work for the @everyone role and not for any other role you specify to lock the channel.
        If you want to unlock a channel with the role you locked it for, you have to use the `[p]unlock` command.

        **Examples**:
        - `[p]lock` - Locks for @everyone with no reason.
        - `[p]lock @Member` - Locks for @Member with no reason.
        - `[p]lock Reason: spam in this channel` - Locks for @everyone with reason.
        - `[p]lock Reason: spam in this channel @Member` - Locks for @Member with reason.
        """
        reason, role = await self._parse_reason_and_role(reason, role, ctx.guild)
        await self.manage_lock(ctx, "lock", reason=reason, role=role)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're unlocking this channel",
        role="The role to unlock the channel for (defaults to @everyone)",
    )
    async def unlock(
        self,
        ctx: commands.Context,
        *,
        reason: Optional[str] = None,
        role: Optional[discord.Role] = None,
    ):
        """
        Unlock a channel for a specific role or everyone.

        If no role is specified, the channel is unlocked for @everyone.

        **Examples**:
        - `[p]unlock` - Unlocks for @everyone with no reason.
        - `[p]unlock @Member` - Unlocks for @Member with no reason.
        - `[p]unlock Reason: spam in this channel` - Unlocks for @everyone with reason.
        - `[p]unlock Reason: spam in this channel @Member` - Unlocks for @Member with reason.
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
        """Close and archive a thread post.

        If you want to only lock a thread post, you'll have to use `[p]lock` command.
        """
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Archived and closed {ctx.channel.mention}.")
        await ctx.channel.edit(locked=True, archived=True)

    @thread.command()
    async def lockdown(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Lock a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Successfully locked {ctx.channel.mention}.")
        await ctx.channel.edit(locked=True)

    @thread.command()
    async def open(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Open a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Successfully opened {ctx.channel.mention}.")
        await ctx.channel.edit(locked=False, archived=False)
