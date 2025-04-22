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

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Final, Optional

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate


class MessageType(Enum):
    EDIT = "edit"
    COUNT = "count"
    SAMEUSER = "sameuser"
    RUIN_COUNT = "ruincount"


class Counting(commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "1.9.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/counting.html"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9008567, force_registration=True)

        default_guild: Dict[str, Any] = {
            "count": 0,
            "channel": None,
            "toggle": False,
            "delete_after": 5,
            "default_edit_message": "You can't edit your messages here.",
            "default_next_number_message": "Next number should be {next_count}.",
            "default_same_user_message": "You cannot count consecutively. Wait for someone else.",
            "toggle_edit_message": False,
            "toggle_next_number_message": False,
            "same_user_to_count": False,
            "last_user_id": None,
            "toggle_reactions": False,
            "default_reaction": "✅",
            "use_silent": False,
            "min_account_age": 0,
            "allow_ruin": False,
            "ruin_role_id": None,
            "ruin_message": "{user} ruined the count at {count}! Starting back at 1.",
        }
        default_user: Dict[str, Any] = {
            "count": 0,
            "last_count_timestamp": None,
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.logger = getLogger("red.maxcogs.counting")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Format the help message with cog details.
        Thanks Sinbad!
        """
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Handle data deletion requests; nothing to delete here."""
        pass

    async def _send_message(
        self,
        channel: discord.TextChannel,
        content: str,
        *,
        delete_after: Optional[int] = None,
        silent: bool = False,
    ) -> Optional[discord.Message]:
        """Send a message with error handling."""
        try:
            return await channel.send(content, delete_after=delete_after, silent=silent)
        except discord.Forbidden:
            self.logger.warning(
                f"Missing send permissions in {channel.guild.name}#{channel.name} ({channel.id})"
            )
        except discord.HTTPException as e:
            self.logger.warning(f"Failed to send message in {channel.id}: {e}", exc_info=True)
        return None

    async def _delete_message(self, message: discord.Message) -> None:
        """Delete a message with error handling."""
        try:
            await message.delete()
        except discord.HTTPException as e:
            self.logger.warning(
                f"Failed to delete message {message.id} in {message.channel.id}: {e}",
                exc_info=True,
            )

    async def _add_reaction(self, message: discord.Message, reaction: str) -> None:
        """Add a reaction with a slight delay."""
        await asyncio.sleep(0.3)
        try:
            await message.add_reaction(reaction)
        except discord.HTTPException as e:
            self.logger.warning(
                f"Failed to add reaction to {message.id} in {message.channel.id}: {e}"
            )

    async def _handle_invalid_count(
        self,
        message: discord.Message,
        response: str,
        settings: Dict[str, Any],
        send_response: bool = True,
    ) -> None:
        """Handle invalid counts by deleting and optionally responding."""
        await self._delete_message(message)
        if send_response:
            await self._send_message(
                message.channel,
                response,
                delete_after=settings["delete_after"],
                silent=settings["use_silent"],
            )

    async def _handle_count_ruin(
        self,
        message: discord.Message,
        settings: dict,
    ) -> None:
        """Handle when someone ruins the count"""
        guild_config = self.config.guild(message.guild)
        await guild_config.count.set(0)
        role_id = settings["ruin_role_id"]
        if role_id and message.channel.permissions_for(message.guild.me).manage_roles:
            try:
                role = message.guild.get_role(role_id)
                if role and role < message.guild.me.top_role:
                    await message.author.add_roles(role)
            except discord.HTTPException as e:
                self.logger.warning(f"Failed to assign ruin role: {e}", exc_info=True)

        response = settings["ruin_message"].format(
            user=message.author.mention, count=settings["count"]
        )
        await self._send_message(
            message.channel,
            response,
            delete_after=settings["delete_after"],
            silent=settings["use_silent"],
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle counting logic when a message is sent."""
        if message.author.bot or not message.guild:
            return

        guild_config = self.config.guild(message.guild)
        settings = await guild_config.all()
        if not settings["toggle"] or message.channel.id != settings["channel"]:
            return

        perms = message.channel.permissions_for(message.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            self.logger.warning(f"Missing permissions in {message.channel.id}")
            return

        if settings["min_account_age"]:
            account_age = (discord.utils.utcnow() - message.author.created_at).days
            if account_age < settings["min_account_age"]:
                await self._handle_invalid_count(
                    message,
                    f"Account must be at least {settings['min_account_age']} days old to count.",
                    settings,
                    send_response=True,
                )
                return

        expected_count = settings["count"] + 1
        if settings["same_user_to_count"] and settings["last_user_id"] == message.author.id:
            await self._handle_invalid_count(
                message, settings["default_same_user_message"], settings
            )
            return

        if message.content.isdigit():
            message_count = int(message.content)
            if message_count == expected_count:
                user_config = self.config.user(message.author)
                await asyncio.gather(
                    guild_config.count.set(expected_count),
                    guild_config.last_user_id.set(message.author.id),
                    user_config.count.set(await user_config.count() + 1),
                    user_config.last_count_timestamp.set(datetime.utcnow().isoformat()),
                )
                if settings["toggle_reactions"] and perms.add_reactions:
                    await self._add_reaction(message, settings["default_reaction"])
            elif settings["allow_ruin"]:
                await self._delete_message(message)
                await self._handle_count_ruin(message, settings)
            else:
                response = settings["default_next_number_message"].format(
                    next_count=expected_count
                )
                await self._handle_invalid_count(
                    message, response, settings, settings["toggle_next_number_message"]
                )
        elif settings["allow_ruin"]:
            await self._delete_message(message)
            await self._handle_count_ruin(message, settings)
        else:
            response = settings["default_next_number_message"].format(next_count=expected_count)
            await self._handle_invalid_count(
                message, response, settings, settings["toggle_next_number_message"]
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """Handle edited messages in the counting channel."""
        if after.author.bot or not after.guild:
            return

        guild_config = self.config.guild(after.guild)
        settings = await guild_config.all()
        if not settings["toggle"] or after.channel.id != settings["channel"]:
            return

        perms = after.channel.permissions_for(after.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            return

        await self._delete_message(after)
        if settings["allow_ruin"]:
            await self._handle_count_ruin(after, settings)
        elif settings["toggle_edit_message"]:
            await self._send_message(
                after.channel,
                settings["default_edit_message"],
                delete_after=settings["delete_after"],
                silent=settings["use_silent"],
            )

    @commands.hybrid_group()
    @commands.guild_only()
    async def counting(self, ctx: commands.Context) -> None:
        """Commands for the counting game."""

    @counting.command(name="current")
    async def count_current(self, ctx: commands.Context) -> None:
        """Show the current count."""
        count = await self.config.guild(ctx.guild).count()
        await ctx.send(f"The current count is {cf.humanize_number(count)}.")

    @counting.command(name="stats")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def count_stats(
        self, ctx: commands.Context, user: Optional[discord.Member] = None
    ) -> None:
        """Get counting stats for a user."""
        user = user or ctx.author
        if user.bot:
            return await ctx.send("Bots don’t count!")

        user_config = self.config.user(user)
        count, timestamp = await asyncio.gather(
            user_config.count(), user_config.last_count_timestamp()
        )

        if not count:
            return await ctx.send(f"{user.display_name} hasn’t counted yet.")

        last_count = datetime.fromisoformat(timestamp) if timestamp else None
        time_str = discord.utils.format_dt(last_count, "R") if last_count else "Never"

        table_data = [
            ["User", user.display_name],
            ["Your Count Total", cf.humanize_number(count)],
        ]

        table = tabulate(
            table_data,
            headers=["Stat", "Value"],
            tablefmt="simple",
            stralign="left",
        )
        await ctx.send(f"Last counted: {time_str}\n{box(table, lang='prolog')}")

    @counting.command(name="resetme")
    async def reset_me(self, ctx: commands.Context) -> None:
        """Reset your own counting stats."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Reset your counting stats?", view=view)
        await view.wait()

        if view.result:
            await self.config.user(ctx.author).clear()
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def countingset(self, ctx: commands.Context) -> None:
        """Settings for the counting game."""

    @countingset.command(name="ruincount")
    async def toggle_ruin(self, ctx: commands.Context):
        """Toggle whether users can ruin the count"""
        guild_config = self.config.guild(ctx.guild)
        current = await guild_config.allow_ruin()
        await guild_config.allow_ruin.set(not current)
        await ctx.send(f"Count ruining is now {'enabled' if not current else 'disabled'}")

    @countingset.command(name="ruinrole")
    @commands.bot_has_permissions(manage_roles=True)
    async def set_ruin_role(self, ctx: commands.Context, role: Optional[discord.Role] = None):
        """Set or clear the role assigned when someone ruins the count"""
        guild_config = self.config.guild(ctx.guild)
        if role is None:
            await guild_config.ruin_role_id.set(None)
            await ctx.send("Ruin role cleared")
        else:
            bot_top_role = ctx.guild.me.top_role
            if role >= bot_top_role:
                return await ctx.send(
                    f"Cannot set {role.name} as ruin role - it must be below my highest role ({bot_top_role.name})"
                )

            await guild_config.ruin_role_id.set(role.id)
            await ctx.send(f"Ruin role set to {role.name}")

    @countingset.command(name="channel")
    async def set_channel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Set or clear the counting channel."""
        config = self.config.guild(ctx.guild)
        if not channel:
            await config.channel.clear()
            return await ctx.send("Counting channel cleared.")

        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            return await ctx.send(
                f"I need send and manage messages permissions in {channel.mention}."
            )

        await config.channel.set(channel.id)
        msg = f"Counting channel set to {channel.mention}."
        if not await config.toggle():
            msg += f"\nEnable counting with `{ctx.clean_prefix}countingset toggle`."
        await ctx.send(msg)

    @countingset.command(name="toggle")
    async def toggle_counting(self, ctx: commands.Context) -> None:
        """Toggle the counting game on or off."""
        config = self.config.guild(ctx.guild)
        toggle = not await config.toggle()
        await config.toggle.set(toggle)

        msg = f"Counting is now {toggle and 'enabled' or 'disabled'}."
        if toggle and not await config.channel():
            msg += f"\nSet a channel with `{ctx.clean_prefix}countingset channel`."
        await ctx.send(msg)

    @countingset.command(name="deleteafter")
    async def set_delete_after(
        self, ctx: commands.Context, seconds: commands.Range[int, 5, 300]
    ) -> None:
        """Set the delete-after time for invalid messages."""
        await self.config.guild(ctx.guild).delete_after.set(seconds)
        await ctx.send(f"Invalid messages will be deleted after {seconds} seconds.")

    @countingset.command(name="togglesilent")
    async def toggle_silent(self, ctx: commands.Context) -> None:
        """Toggle silent mode for bot messages."""
        config = self.config.guild(ctx.guild)
        silent = not await config.use_silent()
        await config.use_silent.set(silent)
        await ctx.send(f"Silent mode is now {silent and 'enabled' or 'disabled'}.")

    @countingset.command(name="togglereact")
    async def toggle_react(self, ctx: commands.Context) -> None:
        """Toggle reactions for correct counts."""
        config = self.config.guild(ctx.guild)
        toggle = not await config.toggle_reactions()
        await config.toggle_reactions.set(toggle)
        msg = f"Reactions are now {toggle and 'enabled' or 'disabled'}."
        if toggle:
            msg += "\nEnsure I have reaction permissions in the counting channel."
        await ctx.send(msg)

    @countingset.command(name="setreaction")
    async def set_reaction(self, ctx: commands.Context, emoji: str) -> None:
        """Set the reaction emoji for correct counts."""
        try:
            await ctx.message.add_reaction(emoji)
            await self.config.guild(ctx.guild).default_reaction.set(emoji)
            await ctx.send(f"Reaction set to {emoji}.")
        except discord.HTTPException:
            await ctx.send(f"'{emoji}' isn’t a valid emoji.")

    @countingset.command(name="togglesameuser")
    async def toggle_same_user(self, ctx: commands.Context) -> None:
        """Toggle if the same user can count consecutively."""
        config = self.config.guild(ctx.guild)
        toggle = not await config.same_user_to_count()
        await config.same_user_to_count.set(toggle)
        await ctx.send(
            f"Consecutive counting by the same user is now {toggle and 'disallowed' or 'allowed'}."
        )

    @countingset.command(name="minage")
    async def set_min_age(
        self, ctx: commands.Context, days: commands.Range[int, 0, 365] = 0
    ) -> None:
        """Set a minimum account age (in days) to count (0 to disable)."""
        await self.config.guild(ctx.guild).min_account_age.set(days)
        await ctx.send(
            f"Minimum account age set to {days} days{' (disabled)' if days == 0 else ''}."
        )

    @countingset.command(name="setmessage")
    async def set_message(self, ctx: commands.Context, msg_type: str, *, message: str) -> None:
        """
        Set custom messages for specific events.

        **Available message types:**
        - `edit`: Message shown when a user edits their message in the counting channel.
        - `count`: Message shown when a user sends an incorrect number.
        - `sameuser`: Message shown when a user tries to count consecutively.
        - `ruincount`: Message shown when a user ruin the message count.

        **Examples:**
        - `[p]countingset setmessage edit You can't edit your messages here.`
        - `[p]countingset setmessage count Next number should be {next_count}`
        - `[p]countingset setmessage sameuser You cannot count until another user have counted`
        - `[p]countingset setmessage ruincount {user} you ruinded the count, starting from {count}!`

        **Arguments:**
        - `<msg_type>`: The type of message to set (edit, count, or sameuser).
        - `<message>`: The message content to set.
        """
        config = self.config.guild(ctx.guild)
        msg_type = msg_type.lower()

        try:
            mtype = MessageType(msg_type)
            key = {
                MessageType.EDIT: "default_edit_message",
                MessageType.COUNT: "default_next_number_message",
                MessageType.SAMEUSER: "default_same_user_message",
                MessageType.RUIN_COUNT: "ruin_message",
            }[mtype]
            await config.set_raw(key, value=message)
            await ctx.send(f"Message for '{msg_type}' updated.")
        except ValueError:
            await ctx.send(f"Invalid type. Use: {', '.join(mt.value for mt in MessageType)}.")

    @countingset.command(name="togglemessage")
    async def toggle_message(self, ctx: commands.Context, msg_type: str) -> None:
        """
        Toggle visibility of specific messages.

        - `<msg_type>`: vaild msg_type is `edit` and `count`.
        """
        config = self.config.guild(ctx.guild)
        msg_type = msg_type.lower()

        if msg_type == "edit":
            toggle = not await config.toggle_edit_message()
            await config.toggle_edit_message.set(toggle)
            await ctx.send(f"Edit message visibility is now {toggle and 'enabled' or 'disabled'}.")
        elif msg_type == "count":
            toggle = not await config.toggle_next_number_message()
            await config.toggle_next_number_message.set(toggle)
            await ctx.send(
                f"Next number message visibility is now {toggle and 'enabled' or 'disabled'}."
            )
        else:
            await ctx.send("Invalid type. Use: edit, count.")

    @countingset.command(name="reset")
    async def reset(self, ctx: commands.Context) -> None:
        """Reset all counting settings and user data."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Reset all counting data?", view=view)
        await view.wait()

        if view.result:
            await asyncio.gather(
                self.config.guild(ctx.guild).clear(), self.config.clear_all_users()
            )
            await ctx.send("All counting data reset.")
        else:
            await ctx.send("Reset cancelled.")

    @countingset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def show_settings(self, ctx: commands.Context) -> None:
        """Display current counting settings."""
        settings = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(settings["channel"]) if settings["channel"] else None

        embed = discord.Embed(title="Counting Settings", color=await ctx.embed_color())
        embed.add_field(
            name="Channel", value=channel.mention if channel else "Not set", inline=True
        )
        embed.add_field(name="Enabled", value=str(settings["toggle"]), inline=True)
        embed.add_field(
            name="Current Count", value=cf.humanize_number(settings["count"]), inline=True
        )
        embed.add_field(name="Delete After", value=f"{settings['delete_after']}s", inline=True)
        embed.add_field(name="Silent Mode", value=str(settings["use_silent"]), inline=True)
        embed.add_field(name="Reactions", value=str(settings["toggle_reactions"]), inline=True)
        embed.add_field(name="Reaction Emoji", value=settings["default_reaction"], inline=True)
        embed.add_field(
            name="Same User Counts", value=str(settings["same_user_to_count"]), inline=True
        )
        embed.add_field(
            name="Min Account Age", value=f"{settings['min_account_age']} days", inline=True
        )
        embed.add_field(name="Ruin Role", value=f"{settings['ruin_role_id']}", inline=True)
        embed.add_field(name="Ruin Count", value=f"{settings['allow_ruin']}", inline=True)
        embed.add_field(
            name="Messages",
            value="\n".join(
                f"**{k.capitalize()}**: {v}"
                for k, v in [
                    ("Edit", settings["default_edit_message"]),
                    ("Count", settings["default_next_number_message"]),
                    ("Same User", settings["default_same_user_message"]),
                    ("Ruin Count", settings["ruin_message"]),
                ]
            ),
            inline=False,
        )
        await ctx.send(embed=embed)
