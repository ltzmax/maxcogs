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

from typing import Optional

import discord
from redbot.core import commands

from ..container import RP_DEFAULT_MSG, RP_DEFAULT_TITLE


class RestrictCommands:
    """RestrictPosts command group — mixed into MessageGuard."""

    @commands.group(aliases=["restrictpost", "restrict"])
    @commands.guild_only()
    @commands.admin_or_can_manage_channel()
    async def restrictposts(self, ctx: commands.Context) -> None:
        """Settings for restricted channel management."""

    @restrictposts.command(name="channel")
    async def rp_channel(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """
        Add, remove, or clear restricted channels where only attachments/links are allowed.

        Specify a channel to toggle it in/out of the list.
        Run without a channel to clear all restricted channels.
        """
        cfg = self._get_cache(ctx.guild.id)
        channel_ids = list(cfg.get("rp_channel_ids", []))

        if channel is None:
            await self._update_cache(ctx.guild, "rp_channel_ids", [])
            return await ctx.send("Cleared all restricted channels.")

        if not (
            channel.permissions_for(ctx.guild.me).send_messages
            and channel.permissions_for(ctx.guild.me).manage_messages
        ):
            return await ctx.send(
                f"I need `Send Messages` and `Manage Messages` permissions in {channel.mention}."
            )

        if channel.id in channel_ids:
            channel_ids.remove(channel.id)
            await self._update_cache(ctx.guild, "rp_channel_ids", channel_ids)
            await ctx.send(f"Removed {channel.mention} from restricted channels.")
        else:
            channel_ids.append(channel.id)
            await self._update_cache(ctx.guild, "rp_channel_ids", channel_ids)
            await ctx.send(f"Added {channel.mention} as a restricted channel.")

    @restrictposts.command(name="autothread")
    async def rp_autothread(self, ctx: commands.Context) -> None:
        """Toggle automatic thread creation for valid messages in restricted channels."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("rp_autothread", False)
        await self._update_cache(ctx.guild, "rp_autothread", new_value)
        await ctx.send(f"Auto-threading {'enabled' if new_value else 'disabled'}.")

    @restrictposts.command(name="mentionable")
    async def rp_mentionable(
        self, ctx: commands.Context, mentionable: Optional[bool] = None
    ) -> None:
        """Toggle or set whether the warning message mentions the user."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = (
            mentionable if mentionable is not None else not cfg.get("rp_mentionable", False)
        )
        await self._update_cache(ctx.guild, "rp_mentionable", new_value)
        await ctx.send(f"Mentionable status {'enabled' if new_value else 'disabled'}.")

    @restrictposts.command(name="deleteafter")
    async def rp_deleteafter(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 300] = None
    ) -> None:
        """Set or reset delete-after time for warning messages (10–300 seconds)."""
        value = seconds if seconds is not None else 10
        await self._update_cache(ctx.guild, "rp_delete_after", value)
        if seconds is None:
            await ctx.send("Delete-after reset to default (10 seconds).")
        else:
            await ctx.send(f"Delete-after set to {seconds} seconds.")

    @restrictposts.command(name="message")
    async def rp_message(self, ctx: commands.Context, *, message: Optional[str] = None) -> None:
        """Set or reset the custom warning message for deleted messages."""
        if message:
            message = message.strip() or RP_DEFAULT_MSG
            if len(message) > 2000:
                return await ctx.send("Message is too long (max 2000 characters).")
        else:
            message = RP_DEFAULT_MSG
        await self._update_cache(ctx.guild, "rp_warning_message", message)
        await ctx.send(
            "Reset warning message to default."
            if message == RP_DEFAULT_MSG
            else "Custom warning message set."
        )

    @restrictposts.command(name="defaulttitle")
    async def rp_defaulttitle(self, ctx: commands.Context, *, title: Optional[str] = None) -> None:
        """Set or reset the default title for the warning embed."""
        if title:
            title = title.strip() or RP_DEFAULT_TITLE
            if len(title) > 256:
                return await ctx.send("Title is too long (max 256 characters).")
        else:
            title = RP_DEFAULT_TITLE
        await self._update_cache(ctx.guild, "rp_default_title", title)
        await ctx.send(
            "Reset default title to default."
            if title == RP_DEFAULT_TITLE
            else "Custom default title set."
        )

    @restrictposts.command(name="embed")
    async def rp_embed(self, ctx: commands.Context) -> None:
        """Toggle sending the warning message as an embed."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("rp_toggle_embed", False)
        await self._update_cache(ctx.guild, "rp_toggle_embed", new_value)
        await ctx.send(f"Embed warning messages {'enabled' if new_value else 'disabled'}.")

    @restrictposts.command(name="togglemessage", aliases=["togglemsg"])
    async def rp_togglemessage(self, ctx: commands.Context) -> None:
        """Toggle sending a warning message in the channel when a message is deleted."""
        cfg = self._get_cache(ctx.guild.id)
        new_value = not cfg.get("rp_send_in_channel", False)
        await self._update_cache(ctx.guild, "rp_send_in_channel", new_value)
        await ctx.send(f"Channel warning messages {'enabled' if new_value else 'disabled'}.")

    @restrictposts.command(name="setlog")
    async def rp_setlog(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Set or clear the log channel for RestrictPosts deletions."""
        channel_id = channel.id if channel else None
        await self._update_cache(ctx.guild, "rp_log_channel", channel_id)
        if channel:
            await ctx.send(f"RestrictPosts log channel set to {channel.mention}.")
        else:
            await ctx.send("RestrictPosts log channel cleared.")

    @restrictposts.command(name="togglelog")
    async def rp_togglelog(self, ctx: commands.Context) -> None:
        """Toggle logging of deleted restricted-channel messages."""
        cfg = self._get_cache(ctx.guild.id)
        if not cfg.get("rp_log_channel"):
            return await ctx.send("Set a log channel first with `restrictposts setlog`.")
        new_value = not cfg.get("rp_log_enabled", False)
        await self._update_cache(ctx.guild, "rp_log_enabled", new_value)
        await ctx.send(f"RestrictPosts logging {'enabled' if new_value else 'disabled'}.")

    @restrictposts.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def rp_settings(self, ctx: commands.Context) -> None:
        """View current RestrictPosts settings."""
        cfg = self._get_cache(ctx.guild.id)
        channel_mentions = [
            ctx.guild.get_channel(cid).mention
            for cid in cfg.get("rp_channel_ids", [])
            if ctx.guild.get_channel(cid)
        ]
        channel_str = ", ".join(channel_mentions) if channel_mentions else "Not set"
        warn_msg = cfg.get("rp_warning_message", RP_DEFAULT_MSG)
        if len(warn_msg) > 100:
            warn_msg = warn_msg[:97] + "..."

        embed = discord.Embed(title="RestrictPosts Settings", color=await ctx.embed_color())
        embed.add_field(
            name="Mentionable",
            value="Enabled" if cfg.get("rp_mentionable") else "Disabled",
            inline=False,
        )
        embed.add_field(
            name="Channel Warnings",
            value="Enabled" if cfg.get("rp_send_in_channel") else "Disabled",
            inline=False,
        )
        embed.add_field(
            name="Delete After", value=f"{cfg.get('rp_delete_after', 10)} seconds", inline=False
        )
        embed.add_field(
            name="Use Embed",
            value="Enabled" if cfg.get("rp_toggle_embed") else "Disabled",
            inline=False,
        )
        embed.add_field(
            name="Auto-Threading",
            value="Enabled" if cfg.get("rp_autothread") else "Disabled",
            inline=False,
        )
        embed.add_field(name="Restricted Channel(s)", value=channel_str, inline=False)
        embed.add_field(
            name="Default Title", value=cfg.get("rp_default_title", RP_DEFAULT_TITLE), inline=False
        )
        log_channel = ctx.guild.get_channel(cfg.get("rp_log_channel") or 0)
        embed.add_field(name="Warning Message", value=warn_msg, inline=False)
        embed.add_field(
            name="Logging",
            value="Enabled" if cfg.get("rp_log_enabled") else "Disabled",
            inline=False,
        )
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "Not set",
            inline=False,
        )
        await ctx.send(embed=embed)
