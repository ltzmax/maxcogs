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

    __version__: Final[str] = "1.3.3"
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        guild = message.guild
        if guild is None:
            return

        config = self.config.guild(guild)
        user_config = self.config.user(message.author)
        toggle = await config.toggle()
        if not toggle:
            return

        channel_id = await config.channel()
        if channel_id is None or message.channel.id != channel_id:
            return

        if (
            not message.channel.permissions_for(message.guild.me).manage_messages
            or not message.channel.permissions_for(message.guild.me).send_messages
        ):
            log.warning(
                "I don't have permission to manage messages or send messages in {channel} ({channel_id})".format(
                    channel=message.channel.name, channel_id=message.channel.id
                )
            )
            return

        use_silent = await config.use_silent()
        default_reaction = await config.default_reaction()
        delete_after = await config.delete_after()
        default_next_number_message = await config.default_next_number_message()
        count = await config.count()
        next_count = count + 1

        # Check if the same user is allowed to count more than once
        same_user_to_count = await config.same_user_to_count()
        last_user_id = await config.last_user_id()
        if same_user_to_count and last_user_id == message.author.id:
            await message.delete()
            return await message.channel.send(
                "You cannot count consecutively. Please wait for someone else to count.",
                delete_after=delete_after,
                silent=use_silent,
            )

        if message.content.isdigit() and int(message.content) == next_count:
            await config.count.set(next_count)
            await config.last_user_id.set(message.author.id)  # Update the last user who counted
            user_count = await user_config.count()
            await user_config.count.set(user_count + 1)
            await user_config.last_count_timestamp.set(datetime.now().isoformat())
            if await config.toggle_reactions():
                await asyncio.sleep(0.3)  # Sleep for a bit.
                if message.channel.permissions_for(message.guild.me).add_reactions:
                    try:
                        await message.add_reaction(default_reaction)
                    except discord.HTTPException:
                        log.warning(
                            "I don't have permission to add reactions in {channel}".format(
                                channel=message.channel.name
                            )
                        )
        else:
            await message.delete()
            if await config.toggle_next_number_message():
                await message.channel.send(
                    default_next_number_message.format(next_count=next_count),
                    delete_after=delete_after,
                    silent=use_silent,
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Delete the message if it's edited in the counting channel.
        """
        if after.author.bot:
            return

        guild = after.guild
        if guild is None:
            return

        config = self.config.guild(guild)
        toggle = await config.toggle()
        if not toggle:
            return

        channel_id = await config.channel()
        if channel_id is None or after.channel.id != channel_id:
            return

        if (
            not after.channel.permissions_for(after.guild.me).manage_messages
            or not after.channel.permissions_for(after.guild.me).send_messages
        ):
            log.warning(
                "I don't have permission to manage messages or send messages in {channel} ({channel_id})".format(
                    channel=after.channel.name, channel_id=after.channel.id
                )
            )
            return

        use_silent = await config.use_silent()
        delete_after = await config.delete_after()
        default_edit_message = await config.default_edit_message()

        await after.delete()
        if await config.toggle_edit_message():
            await after.channel.send(
                default_edit_message, delete_after=delete_after, silent=use_silent
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

        # Check if the user is a bot
        if user.bot:
            return await ctx.send("Bots do not count.")

        # Check if the user is in the guild
        member = ctx.guild.get_member(user.id)
        if not member:
            return await ctx.send("User is not in this server.")

        user_config = self.config.user(user)
        user_count = await user_config.count()
        last_count_timestamp = await user_config.last_count_timestamp()

        # Check if the user has counted yet
        if not user_count:
            return await ctx.send(f"{user.display_name} has not counted yet.")

        table_data = [
            ["Your Count:", humanize_number(user_count)],
        ]
        table = tabulate(table_data, headers=["Title", "Count"], tablefmt="simple")
        msg_box = f"{user.display_name}'s Counting Stats\n" + box(table, lang="prolog")
        if last_count_timestamp:
            last_count_time = datetime.fromisoformat(last_count_timestamp)
            time = discord.utils.format_dt(last_count_time, style="R")

        await ctx.send(
            f"{msg_box}\nYou Last Counted: {time}",
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

    @countingset.command()
    async def toggle(self, ctx):
        """Toggle counting in the channel"""
        config = self.config.guild(ctx.guild)
        toggle = await config.toggle()
        await config.toggle.set(not toggle)
        await ctx.send(
            f"Counting is now {'enabled' if not toggle else 'disabled'}\n"
            f"{'Please set the counting channel using `{prefix}countingset channel #channel` to enable counting.' if not toggle else ''}".format(
                prefix=ctx.clean_prefix
            )
        )

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

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(
            "Counting channel has been set to {channel}\nPlease enable counting using `{prefix}countingset toggle`".format(
                channel=channel.mention, prefix=ctx.clean_prefix
            )
        )

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

    @countingset.command()
    async def setmessage(self, ctx, message_type: str, *, message: str):
        """
        Set the default message for a specific type.

        Available message types: edit, count

        `edit` - The message to show when a user edits their message in the counting channel.
        `count` - The message to show when a user sends an incorrect number in the counting channel.

        **Examples:**
        - `[p]countingset setmessage edit You can't edit your messages here.`
        - `[p]countingset setmessage count Next number should be {next_count}`

        **Arguments:**
        - `<message_type>` The type of message to set (edit or count).
        - `<message>` The message to set.
        """
        config = self.config.guild(ctx.guild)

        if message_type.lower() == "edit":
            await config.default_edit_message.set(message)
            await ctx.send("Default message for edit in counting channel set")
        elif message_type.lower() == "count":
            await config.default_next_number_message.set(message)
            await ctx.send("Default message for wrong number set")
        else:
            await ctx.send("Invalid message type. Available types: edit, count")

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

    @countingset.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """Show the current counting settings."""
        config = self.config.guild(ctx.guild)
        channel_id = await config.channel()
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        toggle = await config.toggle()
        delete_after = await config.delete_after()
        default_edit_message = await config.default_edit_message()
        default_next_number_message = await config.default_next_number_message()
        toggle_edit_message = await config.toggle_edit_message()
        toggle_next_number_message = await config.toggle_next_number_message()
        same_user_to_count = await config.same_user_to_count()
        default_reaction = await config.default_reaction()
        toggle_reactions = await config.toggle_reactions()
        silent = await config.use_silent()

        embed = discord.Embed(
            title="Counting Settings",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Counting Channel:", value=channel.mention if channel else "Not set")
        embed.add_field(name="Toggle:", value="Enabled" if toggle else "Disabled")
        embed.add_field(name="Delete After:", value=f"{delete_after} seconds")
        embed.add_field(
            name="Toggle Edit Message:",
            value="Enabled" if toggle_edit_message else "Disabled",
        )
        embed.add_field(
            name="Toggle Next Number Message:",
            value="Enabled" if toggle_next_number_message else "Disabled",
        )
        embed.add_field(
            name="Same User To Count:",
            value="Enabled" if same_user_to_count else "Disabled",
        )
        embed.add_field(
            name="Toggle Reactions:",
            value="Enabled" if toggle_reactions else "Disabled",
        )
        embed.add_field(name="Default Reaction:", value=default_reaction)
        embed.add_field(name="Silent Messages:", value="Enabled" if silent else "Disabled")
        embed.add_field(name="Default Edit Message:", value=default_edit_message, inline=False)
        embed.add_field(
            name="Default Next Number Message:",
            value=default_next_number_message,
            inline=False,
        )
        await ctx.send(embed=embed)
