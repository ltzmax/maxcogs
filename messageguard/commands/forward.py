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
from redbot.core import commands
from redbot.core.utils.views import ConfirmView, SimpleMenu


class ForwardCommands:
    """ForwardDeleter command group"""

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def forwarddeleter(self, ctx: commands.Context) -> None:
        """Manage forward deleter settings."""

    @forwarddeleter.command(name="toggle")
    async def fd_toggle(self, ctx: commands.Context) -> None:
        """Toggle forward deleter on or off."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("fd_enabled", False)
        await self._update_cache(ctx.guild, "fd_enabled", new_value)
        await ctx.send(f"Forward deleter has been {'enabled' if new_value else 'disabled'}.")

    @forwarddeleter.command(name="togglewarn")
    async def fd_togglewarn(self, ctx: commands.Context) -> None:
        """Toggle sending warnings when forwarded messages are deleted."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("fd_warn_enabled", False)
        await self._update_cache(ctx.guild, "fd_warn_enabled", new_value)
        await ctx.send(f"User warnings have been {'enabled' if new_value else 'disabled'}.")

    @forwarddeleter.command(name="setwarnmessage", aliases=["setwarnmsg"])
    async def fd_setwarnmessage(self, ctx: commands.Context, *, message: str) -> None:
        """Set a custom warning message for deleted forwarded messages."""
        if len(message) > 2000:
            return await ctx.send("Warning message must be 2000 characters or less.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Preview Warning Message",
            description=f"This is how the warning message will appear:\n{message}",
            color=await ctx.embed_color(),
        )
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self._update_cache(ctx.guild, "fd_warn_message", message)
            await msg.edit(content="Warning message updated.", embed=None, view=None)
        else:
            await msg.edit(content="Cancelled.", embed=None, view=None)

    @forwarddeleter.command(name="addrole")
    async def fd_addrole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Add a role to the forwarding whitelist."""
        if role >= ctx.guild.me.top_role:
            return await ctx.send("You can't set a role higher than or equal to mine.")
        allowed_roles = self._get_cache(ctx.guild.id).get("fd_allowed_roles", set())
        if role.id in allowed_roles:
            return await ctx.send(f"{role.name} is already whitelisted.")
        allowed_roles.add(role.id)
        await self._update_cache(ctx.guild, "fd_allowed_roles", list(allowed_roles))
        await ctx.send(f"Added {role.name} to the forwarding whitelist.")

    @forwarddeleter.command(name="removerole")
    async def fd_removerole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Remove a role from the forwarding whitelist."""
        allowed_roles = self._get_cache(ctx.guild.id).get("fd_allowed_roles", set())
        if role.id not in allowed_roles:
            return await ctx.send(f"{role.name} is not in the whitelist.")
        allowed_roles.discard(role.id)
        await self._update_cache(ctx.guild, "fd_allowed_roles", list(allowed_roles))
        await ctx.send(f"Removed {role.name} from the forwarding whitelist.")

    @forwarddeleter.command(name="allow")
    async def fd_allow(
        self,
        ctx: commands.Context,
        *channels: discord.TextChannel | discord.Thread,
    ) -> None:
        """Add channels or threads where forwarding is allowed."""
        allowed = self._get_cache(ctx.guild.id).get("fd_allowed_channels", set())
        added, already = [], []
        for ch in channels:
            if ch.id not in allowed:
                allowed.add(ch.id)
                added.append(ch.mention)
            else:
                already.append(ch.mention)
        if added:
            await self._update_cache(ctx.guild, "fd_allowed_channels", list(allowed))
        parts = []
        if added:
            parts.append(f"Allowed: {', '.join(added)}")
        if already:
            parts.append(f"Already allowed: {', '.join(already)}")
        await ctx.send("\n".join(parts) or "No changes made.")

    @forwarddeleter.command(name="disallow")
    async def fd_disallow(
        self,
        ctx: commands.Context,
        *channels: discord.TextChannel | discord.Thread,
    ) -> None:
        """Remove channels or threads from the forwarding allowed list."""
        allowed = self._get_cache(ctx.guild.id).get("fd_allowed_channels", set())
        removed, missing = [], []
        for ch in channels:
            if ch.id in allowed:
                allowed.discard(ch.id)
                removed.append(ch.mention)
            else:
                missing.append(ch.mention)
        if removed:
            await self._update_cache(ctx.guild, "fd_allowed_channels", list(allowed))
        parts = []
        if removed:
            parts.append(f"Removed: {', '.join(removed)}")
        if missing:
            parts.append(f"Not in list: {', '.join(missing)}")
        await ctx.send("\n".join(parts) or "No changes made.")

    @forwarddeleter.command(name="setlog")
    async def fd_setlog(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Set or clear the log channel for ForwardDeleter deletions."""
        channel_id = channel.id if channel else None
        await self._update_cache(ctx.guild, "fd_log_channel", channel_id)
        if channel:
            await ctx.send(f"ForwardDeleter log channel set to {channel.mention}.")
        else:
            await ctx.send("ForwardDeleter log channel cleared.")

    @forwarddeleter.command(name="togglelog")
    async def fd_togglelog(self, ctx: commands.Context) -> None:
        """Toggle logging of deleted forwarded messages."""
        cfg = self._get_cache(ctx.guild.id)
        if not cfg.get("fd_log_channel"):
            return await ctx.send("Set a log channel first with `forwarddeleter setlog`.")
        new_value = not cfg.get("fd_log_enabled", False)
        await self._update_cache(ctx.guild, "fd_log_enabled", new_value)
        await ctx.send(f"ForwardDeleter logging {'enabled' if new_value else 'disabled'}.")

    @forwarddeleter.command(name="settings")
    async def fd_settings(self, ctx: commands.Context) -> None:
        """Display Forward Deleter settings."""
        cfg = self._get_cache(ctx.guild.id)

        channels = [
            ch.mention
            for ch_id in cfg.get("fd_allowed_channels", set())
            if (ch := ctx.guild.get_channel_or_thread(ch_id))
        ]
        roles = [
            ctx.guild.get_role(r_id).mention
            for r_id in cfg.get("fd_allowed_roles", set())
            if ctx.guild.get_role(r_id)
        ]

        per_page = 10
        channel_pages = (
            ["None"]
            if not channels
            else ["\n".join(channels[i : i + per_page]) for i in range(0, len(channels), per_page)]
        )
        role_pages = (
            ["None"]
            if not roles
            else ["\n".join(roles[i : i + per_page]) for i in range(0, len(roles), per_page)]
        )

        base_embed = discord.Embed(title="Forward Deleter Settings", color=await ctx.embed_color())
        log_channel = ctx.guild.get_channel(cfg.get("fd_log_channel") or 0)
        base_embed.add_field(
            name="Status", value="Enabled" if cfg.get("fd_enabled") else "Disabled"
        )
        base_embed.add_field(
            name="Warn Users", value="Enabled" if cfg.get("fd_warn_enabled") else "Disabled"
        )
        base_embed.add_field(
            name="Logging", value="Enabled" if cfg.get("fd_log_enabled") else "Disabled"
        )
        base_embed.add_field(
            name="Log Channel", value=log_channel.mention if log_channel else "Not set"
        )

        max_pages = max(len(channel_pages), len(role_pages))
        pages = []
        warn_msg = cfg.get("fd_warn_message", "")
        for i in range(max_pages):
            page = base_embed.copy()
            page.add_field(
                name="Allowed Channels/Threads",
                value=channel_pages[i] if i < len(channel_pages) else "None",
                inline=False,
            )
            page.add_field(
                name="Allowed Roles",
                value=role_pages[i] if i < len(role_pages) else "None",
                inline=False,
            )
            page.add_field(
                name="Warn Message",
                value=warn_msg[:1000] + ("..." if len(warn_msg) > 1000 else ""),
                inline=False,
            )
            page.set_footer(text=f"Page {i + 1}/{max_pages}")
            pages.append(page)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
