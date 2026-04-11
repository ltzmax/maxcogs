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
from redbot.core.utils.chat_formatting import box, header

from ..container import NS_DEFAULT_WARNING


class SpoilerCommands:
    """NoSpoiler command group — mixed into MessageGuard."""

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx: commands.Context) -> None:
        """Manage spoiler filter settings for the server."""

    @nospoiler.command(name="toggle")
    async def ns_toggle(self, ctx: commands.Context) -> None:
        """Toggle the spoiler filter on or off."""
        if not ctx.bot_permissions.manage_messages:
            return await ctx.send("I need `manage_messages` permission to use the spoiler filter.")
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("ns_enabled", False)
        await self._update_cache(ctx.guild, "ns_enabled", new_value)
        await ctx.send(f"Spoiler filter is now {'enabled' if new_value else 'disabled'}.")

    @nospoiler.command(name="togglewarnmsg")
    async def ns_togglewarnmsg(self, ctx: commands.Context, toggle: bool | None = None) -> None:
        """Toggle the spoiler warning message on or off."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = toggle if toggle is not None else not cfg.get("ns_spoiler_warn", False)
        await self._update_cache(ctx.guild, "ns_spoiler_warn", new_value)
        await ctx.send(f"Spoiler warning message is now {'enabled' if new_value else 'disabled'}.")

    @nospoiler.command(name="useembed")
    async def ns_useembed(self, ctx: commands.Context, toggle: bool | None = None) -> None:
        """Toggle whether the spoiler warning uses an embed."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = toggle if toggle is not None else not cfg.get("ns_use_embed", False)
        await self._update_cache(ctx.guild, "ns_use_embed", new_value)
        await ctx.send(f"Spoiler warning embed is now {'enabled' if new_value else 'disabled'}.")

    @nospoiler.command(name="deleteafter")
    async def ns_deleteafter(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ) -> None:
        """Set how long before the spoiler warning is deleted (10–120 seconds)."""
        await self._update_cache(ctx.guild, "ns_timeout", seconds)
        await ctx.send(f"Spoiler warning timeout set to {seconds} seconds.")

    @nospoiler.command(name="message")
    async def ns_message(self, ctx: commands.Context, *, message: str | None = None) -> None:
        """Set or reset the custom spoiler warning message."""
        new_message = message or NS_DEFAULT_WARNING
        await self._update_cache(ctx.guild, "ns_spoiler_warn_message", new_message)
        await ctx.send("Spoiler warning message has been " + ("set." if message else "reset."))

    @nospoiler.command(name="setlog")
    async def ns_setlog(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Set or clear the log channel for NoSpoiler deletions."""
        channel_id = channel.id if channel else None
        await self._update_cache(ctx.guild, "ns_log_channel", channel_id)
        if channel:
            await ctx.send(f"NoSpoiler log channel set to {channel.mention}.")
        else:
            await ctx.send("NoSpoiler log channel cleared.")

    @nospoiler.command(name="togglelog")
    async def ns_togglelog(self, ctx: commands.Context) -> None:
        """Toggle logging of deleted spoiler messages."""
        cfg = self._get_cache(ctx.guild.id)
        if not cfg.get("ns_log_channel"):
            return await ctx.send("Set a log channel first with `nospoiler setlog`.")
        new_value = not cfg.get("ns_log_enabled", False)
        await self._update_cache(ctx.guild, "ns_log_enabled", new_value)
        await ctx.send(f"NoSpoiler logging {'enabled' if new_value else 'disabled'}.")

    @nospoiler.command(name="settings", aliases=["view", "views"])
    async def ns_settings(self, ctx: commands.Context) -> None:
        """Display current spoiler filter settings."""
        cfg = self._get_cache(ctx.guild.id)
        warn_msg = cfg.get("ns_spoiler_warn_message", NS_DEFAULT_WARNING)
        spoiler_warning_message = (
            box(warn_msg, lang="yaml") if len(warn_msg) < 2000 else "Message too long to display."
        )
        title = "NoSpoiler Settings"
        header_text = header(title, "medium")
        log_channel = ctx.guild.get_channel(cfg.get("ns_log_channel") or 0)
        await ctx.send(
            f"{header_text}\n"
            f"- **Enabled**: {cfg.get('ns_enabled', False)}\n"
            f"- **Spoiler Warning**: {cfg.get('ns_spoiler_warn', False)}\n"
            f"- **Use Embed**: {cfg.get('ns_use_embed', False)}\n"
            f"- **Delete After**: {cfg.get('ns_timeout', 10)} seconds\n"
            f"- **Logging**: {cfg.get('ns_log_enabled', False)}\n"
            f"- **Log Channel**: {log_channel.mention if log_channel else 'Not set'}\n"
            f"- **Spoiler Warning Message**:\n{spoiler_warning_message}"
        )
