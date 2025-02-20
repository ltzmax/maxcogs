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
import logging
from datetime import datetime
from typing import Any, Final, Literal, Optional

import discord
from discord.ext.commands.converter import EmojiConverter
from discord.ext.commands.errors import EmojiNotFound
from emoji import EMOJI_DATA
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate

log = logging.getLogger("red.maxcogs.counting")


class Counting(commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "1.7.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Counting.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9008567, force_registration=True)
        default_guild = {
            "count": 0,
            "channel": None,
            "toggle": False,
            "delete_after": 5,
            "default_edit_message": "You can't edit your messages here.",
            "default_next_number_message": "Next number should be {next_count}",
            "toggle_edit_message": False,
            "toggle_next_number_message": False,
            "same_user_to_count": False,
            "same_user_to_count_msg": "You cannot count consecutively. Please wait for someone else to count.",
            "last_user_id": None,
            "toggle_reactions": False,
            "default_reaction": "✅",
            "use_silent": False,
        }
        default_user = {
            "count": 0,
            "last_count_timestamp": None,
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def _send_message(
        self,
        channel: discord.TextChannel,
        content: str,
        delete_after: Optional[int] = None,
        silent: bool = False,
    ) -> Optional[discord.Message]:
        """Send a message with error handling."""
        try:
            return await channel.send(content, delete_after=delete_after, silent=silent)
        except discord.Forbidden as e:
            log.warning(f"No permission to send in {channel.name} ({channel.id}): {e}")
        except discord.HTTPException as e:
            log.warning(f"Error sending message in {channel.name} ({channel.id}): {e}")
        return None

    async def _delete_message(self, message: discord.Message) -> None:
        """Delete a message with error handling."""
        try:
            await message.delete()
        except discord.HTTPException as e:
            log.warning(f"Error deleting message in {message.channel.name} ({message.channel.id}): {e}")

    async def _handle_invalid_count(
        self,
        message: discord.Message,
        response: str,
        delete_after: int,
        use_silent: bool,
        send_response: bool = True,
    ) -> None:
        """Handle invalid counting attempts by deleting the message and optionally responding."""
        await self._delete_message(message)
        if send_response:
            await self._send_message(message.channel, response, delete_after, use_silent)

    async def _add_reaction(self, message: discord.Message, reaction: str) -> None:
        """Add a reaction to a message with a slight delay."""
        try:
            await asyncio.sleep(0.3)
            await message.add_reaction(reaction)
        except discord.HTTPException as e:
            log.warning(f"No permission to add reactions in {message.channel.name} ({message.channel.id}): {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Process messages to manage the counting game."""
        if message.author.bot or message.guild is None:
            return

        guild_config = self.config.guild(message.guild)
        settings = await guild_config.all()
        if not settings["toggle"] or message.channel.id != settings["channel"]:
            return

        perms = message.channel.permissions_for(message.guild.me)
        if not (perms.manage_messages and perms.send_messages):
            log.warning(f"No permissions in {message.channel.name} ({message.channel.id})")
            return

        user_config = self.config.user(message.author)
        expected_count = settings["count"] + 1

        if settings["same_user_to_count"] and settings["last_user_id"] == message.author.id:
            await self._handle_invalid_count(
                message,
                settings["same_user_to_count_msg"],
                settings["delete_after"],
                settings["use_silent"],
            )
            return

        if message.content.isdigit() and int(message.content) == expected_count:
            await guild_config.count.set(expected_count)
            await guild_config.last_user_id.set(message.author.id)
            await user_config.count.set(await user_config.count() + 1)
            await user_config.last_count_timestamp.set(datetime.now().isoformat())
            if settings["toggle_reactions"] and perms.add_reactions:
                await self._add_reaction(message, settings["default_reaction"])
        else:
            response = settings["default_next_number_message"].format(next_count=expected_count)
            await self._handle_invalid_count(
                message,
                response,
                settings["delete_after"],
                settings["use_silent"],
                settings["toggle_next_number_message"],
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """Prevent editing in the counting channel by deleting edited messages."""
        if after.author.bot or after.guild is None or after.channel is None:
            return

        guild_config = self.config.guild(after.guild)
        settings = await guild_config.all()
        if not settings["toggle"] or after.channel.id != settings["channel"]:
            return

        perms = after.channel.permissions_for(after.guild.me)
        if not (perms.manage_messages and perms.send_messages):
            log.warning(f"No permissions in {after.channel.name} ({after.channel.id})")
            return

        await self._delete_message(after)
        if settings["toggle_edit_message"]:
            await self._send_message(
                after.channel,
                settings["default_edit_message"],
                settings["delete_after"],
                settings["use_silent"],
            )

    @commands.guild_only()
    @commands.hybrid_group()
    async def counting(self, ctx):
        """Counting commands"""

    @counting.command(name="countstats", aliases=["stats"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def count_stats(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Get your current counting statistics."""
        user = user or ctx.author

        if user.bot:
            return await ctx.send("Bots do not count.")

        member = ctx.guild.get_member(user.id)
        if not member:
            return await ctx.send("User is not in this server.")

        user_config = self.config.user(user)
        user_data = await user_config.all()

        user_count = user_data.get("count", 0)
        last_count_timestamp = user_data.get("last_count_timestamp", None)

        if not user_count:
            return await ctx.send(f"{user.display_name} has not counted yet.")

        last_count_time = datetime.fromisoformat(last_count_timestamp)
        time = discord.utils.format_dt(last_count_time, style="R")

        await ctx.send(
            f"{user.display_name}'s Counting Stats\n"
            f"Count: {humanize_number(user_count)}\n"
            f"Last Counted: {time}",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @counting.command(name="resetme", with_app_command=False)
    async def reset_me(self, ctx: commands.Context):
        """Reset your counting stats."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset your counting stats?", view=view
        )
        await view.wait()
        if view.result:
            user_config = self.config.user(ctx.author)
            await user_config.count.set(0)
            await user_config.last_count_timestamp.clear()
            await ctx.send(
                "Your counting stats have been reset.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        else:
            await ctx.send(
                "Reset cancelled.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def countingset(self, ctx):
        """Counting settings commands."""

    @countingset.command()
    async def togglereact(self, ctx):
        """Toggle the reactions for correct numbers."""
        config = self.config.guild(ctx.guild)
        toggle = await config.toggle_reactions()
        await config.toggle_reactions.set(not toggle)
        await ctx.send(
            f"Reactions for the counting is now {'enabled' if not toggle else 'disabled'}\n"
            f"{'Please make sure the bot has the necessary permissions to add reactions in the counting channel.' if not toggle else ''}"
        )

    @countingset.command()
    async def setreaction(self, ctx, emoji_input: str):
        """Set the reaction for correct numbers."""
        if emoji_input:
            try:
                # Use EmojiConverter to convert the emoji argument
                emoji_obj = await EmojiConverter().convert(ctx, emoji_input)
                emoji_str = str(emoji_obj)
            except EmojiNotFound:
                if emoji_input in EMOJI_DATA:
                    emoji_str = emoji_input
                else:
                    return await ctx.send(f"'{emoji_input}' is not a valid emoji.")
        config = self.config.guild(ctx.guild)
        await config.default_reaction.set(emoji_input)
        await ctx.send(f"Reaction for correct numbers has been set to {emoji_input}")

    @countingset.command()
    async def togglesilent(self, ctx: commands.Context):
        """
        Toggle silent mode for counting messages.

        Silent is discords new feature.
        """
        config = self.config.guild(ctx.guild)
        toggle = await config.use_silent()
        await config.use_silent.set(not toggle)
        await ctx.send(
            f"Silent messages for counting messages is now {'enabled' if not toggle else 'disabled'}"
        )

    @countingset.command(name="toggle")
    async def toggle_counting(self, ctx: commands.Context):
        """Toggle counting in the channel"""
        guild_config = self.config.guild(ctx.guild)
        is_enabled = await guild_config.toggle()
        await guild_config.toggle.set(not is_enabled)

        message = f"Counting is now {'enabled' if not is_enabled else 'disabled'}"
        if not await guild_config.channel() and not is_enabled:
            message += f"\nPlease set a counting channel using `{ctx.clean_prefix}countingset channel` to enable counting."
        await ctx.send(message)

    @countingset.command()
    async def channel(self, ctx, channel: Optional[discord.TextChannel]):
        """Set the counting channel"""
        if channel is None:
            await self.config.guild(ctx.guild).channel.clear()
            return await ctx.send("Counting channel has been cleared")

        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            or not channel.permissions_for(ctx.guild.me).manage_messages
        ):
            return await ctx.send(
                "I don't have permission to send messages or manage messages in {channel}".format(
                    channel=channel.mention
                )
            )

        message = f"Counting channel has been set to {channel.mention}"
        if not await self.config.guild(ctx.guild).toggle():
            message += f"\nPlease enable counting using `{ctx.clean_prefix}countingset toggle` to enable counting."
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(message)

    @countingset.command()
    async def deleteafter(self, ctx, seconds: commands.Range[int, 5, 300]):
        """
        Set the number of seconds to delete the incorrect message

        Default is 5 seconds
        """
        config = self.config.guild(ctx.guild)
        await config.delete_after.set(seconds)
        await ctx.send(f"Messages will now be deleted after {seconds} seconds")

    @countingset.command()
    async def reset(self, ctx):
        """Reset the settings for the counting."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset the counting settings?\nThis will reset the counting channel, count, and all settings.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            all_users = await self.config.all_users()
            for user_id in all_users:
                await self.config.user_from_id(user_id).clear()
            await ctx.send("Counting settings have been reset.")
        else:
            await ctx.send("Reset cancelled")

    @countingset.command(name="setmessage")
    async def set_message(self, ctx: commands.Context, message_type: str, *, message: str) -> None:
        """
        Set the default message for a specific type.

        **Available message types:**
        - `edit`: Message shown when a user edits their message in the counting channel.
        - `count`: Message shown when a user sends an incorrect number.
        - `sameuser`: Message shown when a user tries to count consecutively.

        **Examples:**
        - `[p]countingset setmessage edit You can't edit your messages here.`
        - `[p]countingset setmessage count Next number should be {next_count}`

        **Arguments:**
        - `message_type`: The type of message to set (edit, count, or sameuser).
        - `message`: The message content to set.
        """
        if not message.strip():
            await ctx.send("The message cannot be empty.")
            return

        config = self.config.guild(ctx.guild)
        message_types = {
            "edit": "default_edit_message",
            "count": "default_next_number_message",
            "sameuser": "same_user_to_count_msg",
        }

        type_lower = message_type.lower()
        if type_lower in message_types:
            await config.set_raw(message_types[type_lower], value=message)
            await ctx.send(f"Default message for '{type_lower}' has been set.")
        else:
            available_types = ", ".join(message_types.keys())
            await ctx.send(f"Invalid message type. Available types: {available_types}")

    @countingset.command()
    async def togglemessage(self, ctx, setting: str):
        """
        Toggle to show a message for a specific setting.

        Available settings: edit, count

        `count` - Show the next number message when a user sends an incorrect number. Default is disabled
        `edit` - Shows a message when a user edits their message in the counting channel. Default is disabled
        """
        config = self.config.guild(ctx.guild)
        if setting.lower() == "edit":
            toggle = await config.toggle_edit_message()
            await config.toggle_edit_message.set(not toggle)
            await ctx.send(
                f"Message for when user edits in counting channel is now {'enabled' if not toggle else 'disabled'}"
            )
        elif setting.lower() == "count":
            toggle = await config.toggle_next_number_message()
            await config.toggle_next_number_message.set(not toggle)
            await ctx.send(
                f"Message for when user send incorrect number in counting channel is now {'enabled' if not toggle else 'disabled'}"
            )
        else:
            await ctx.send("Invalid setting. Available settings: edit, count")

    @countingset.command()
    async def togglesameuser(self, ctx):
        """
        Toggle whether the same user can count more than once consecutively.

        Users cannot count consecutively if this is enabled meaning they have to wait for someone else to count.
        """
        config = self.config.guild(ctx.guild)
        same_user_to_count = await config.same_user_to_count()
        await config.same_user_to_count.set(not same_user_to_count)
        await ctx.send(
            f"Same user counting consecutively is now {'allowed' if not same_user_to_count else 'disallowed'}"
        )

    @countingset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def show_settings(self, ctx: commands.Context) -> None:
        """Show the current counting settings in an embed."""
        guild_config = self.config.guild(ctx.guild)
        settings = await guild_config.all()

        channel_id = settings["channel"]
        channel = ctx.guild.get_channel(channel_id) if channel_id else None

        embed_fields = {
            "Counting Channel": channel.mention if channel else "Not set",
            "Counting Enabled": "Enabled" if settings["toggle"] else "Disabled",
            "Delete After": f"{settings['delete_after']} seconds",
            "Edit Message": "Enabled" if settings["toggle_edit_message"] else "Disabled",
            "Next Number Message": "Enabled" if settings["toggle_next_number_message"] else "Disabled",
            "Same User Count": "Enabled" if settings["same_user_to_count"] else "Disabled",
            "Reactions": "Enabled" if settings["toggle_reactions"] else "Disabled",
            "Reaction Emoji": settings["default_reaction"],
            "Silent Mode": "Enabled" if settings["use_silent"] else "Disabled",
            "Edit Message Content": settings["default_edit_message"],
            "Next Number Message Content": settings["default_next_number_message"],
            "Same User Count Message": settings["same_user_to_count_msg"],
        }

        embed = discord.Embed(title="Counting Settings", color=await ctx.embed_color())
        for name, value in embed_fields.items():
            inline = name not in ["Edit Message Content", "Next Number Message Content", "Same User Count Message"]
            embed.add_field(name=name, value=value, inline=inline)
        await ctx.send(embed=embed)
