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

from typing import Any, Final, Optional, Union

import discord
from red_commons.logging import getLogger
from redbot.core import Config, app_commands, commands

from .view import UnlockView


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.5.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "log_channel": None,
            "use_embed": False,
        }
        self.config.register_guild(**default_guild)
        self.logger = getLogger("red.maxcogs.lockdown")

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
            self.logger.warning(
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
    async def logchannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
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
        await self.log_channel(ctx, ctx.guild, event=log_event, reason=reason)

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
        # If reason is provided, check if the last part is a role mention
        if reason and role is None:
            parts = reason.strip().split()
            if parts and parts[-1].startswith("<@&") and parts[-1].endswith(">"):
                role_id = parts[-1][3:-1]
                try:
                    role = ctx.guild.get_role(int(role_id))
                    if role:
                        reason = " ".join(parts[:-1]).strip() or None
                except ValueError as e:
                    self.logger.error(
                        f"Failed to convert role ID {role_id} to int. Reason: {e}", exc_info=True
                    )
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
        # If reason is provided, check if the last part is a role mention
        if reason and role is None:
            parts = reason.strip().split()
            if parts and parts[-1].startswith("<@&") and parts[-1].endswith(">"):
                role_id = parts[-1][3:-1]
                try:
                    role = ctx.guild.get_role(int(role_id))
                    if role:
                        reason = " ".join(parts[:-1]).strip() or None
                except ValueError as e:
                    self.logger.error(
                        f"Failed to convert role ID {role_id} to int. Reason: {e}", exc_info=True
                    )
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
        await self.log_channel(ctx, ctx.guild, event="Thread Closed", reason=reason)

    @thread.command()
    async def lockdown(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Lock a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Successfully locked {ctx.channel.mention}.")
        await ctx.channel.edit(locked=True)
        await self.log_channel(ctx, ctx.guild, event="Thread Locked", reason=reason)

    @thread.command()
    async def open(self, ctx: commands.Context, *, reason: Optional[str] = None):
        """Open a thread post."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This channel is not a thread.")
        await ctx.send(f"Successfully opened {ctx.channel.mention}.")
        await ctx.channel.edit(locked=False, archived=False)
        await self.log_channel(ctx, ctx.guild, event="Thread Opened", reason=reason)
