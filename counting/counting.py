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

import logging
from datetime import datetime
from typing import Any, Final, Literal, Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.views import ConfirmView

log = logging.getLogger("red.maxcogs.counting")


class Counting(commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "1.0.0"
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
            await self.config.channel.clear()
            log.info(
                "I don't have permission to manage messages in the counting channel, clearing it."
            )
            return

        delete_after = await config.delete_after()
        default_next_number_message = await config.default_next_number_message()
        count = await config.count()
        next_count = count + 1

        # Check if the same user is allowed to count more than once
        same_user_to_count = await config.same_user_to_count()
        last_user_id = await config.last_user_id()
        if not same_user_to_count and last_user_id == message.author.id:
            await message.delete()
            return await message.channel.send(
                "You cannot count consecutively. Please wait for someone else to count.",
                delete_after=delete_after,
            )

        if message.content.isdigit() and int(message.content) == next_count:
            await config.count.set(next_count)
            await config.last_user_id.set(message.author.id)  # Update the last user who counted
            user_count = await user_config.count()
            await user_config.count.set(user_count + 1)
            await user_config.last_count_timestamp.set(datetime.now().isoformat())
        else:
            await message.delete()
            await message.channel.send(
                default_next_number_message.format(next_count=next_count),
                delete_after=delete_after,
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

        delete_after = await config.delete_after()
        default_edit_message = await config.default_edit_message()

        await after.delete()
        if await config.toggle_edit_message():
            await after.channel.send(default_edit_message, delete_after=delete_after)

    async def countingstats(self, ctx):
        config = self.config.guild(ctx.guild)
        user_config = self.config.user(ctx.author)
        count = await config.count()
        user_count = await user_config.count()
        last_count_timestamp = await user_config.last_count_timestamp()

        embed = discord.Embed(
            title="Counting Stats",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Server Count:", value=humanize_number(count))
        embed.add_field(name="Your Count:", value=humanize_number(user_count), inline=False)
        if last_count_timestamp:
            last_count_time = datetime.fromisoformat(last_count_timestamp)
            embed.add_field(
                name="You last counted:",
                value=discord.utils.format_dt(last_count_time, style="R"),
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.group()
    @commands.guild_only()
    async def counting(self, ctx):
        """Counting commands"""

    @counting.command(name="countstats", aliases=["stats"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def count_stats(self, ctx: commands.Context):
        """Get your current counting statistics."""
        await self.countingstats(ctx)

    @counting.command(name="resetme")
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
            await ctx.send("Your counting stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def countingset(self, ctx):
        """Counting settings commands."""

    @countingset.command()
    async def toggle(self, ctx):
        """Toggle counting in the channel"""
        if not await self.config.guild(ctx.guild).channel():
            return await ctx.send(
                "Counting channel is not set. Please set it first using `{prefix}countingset channel`".format(
                    prefix=ctx.clean_prefix
                )
            )
        config = self.config.guild(ctx.guild)
        toggle = await config.toggle()
        await config.toggle.set(not toggle)
        await ctx.send(f"Counting is now {'enabled' if not toggle else 'disabled'}")

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
                "I don't have permission to send or manage messages in that channel."
            )

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(
            "Counting channel has been set to {channel}\n-# Now toggle counting using `{prefix}countingset toggle`".format(
                prefix=ctx.clean_prefix, channel=channel.mention
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
        """Reset the counting channel"""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset the counting channel? This will reset the count to 0.",
            view=view,
        )
        await view.wait()
        if view.result:
            config = self.config.guild(ctx.guild)
            await config.count.set(0)
            await ctx.send("Counting channel has been reset to 0")
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
    async def enable(self, ctx, setting: str):
        """
        Toggle to show the edit message or next number message.

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
        """Toggle whether the same user can count more than once consecutively."""
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

        embed = discord.Embed(
            title="Counting Settings",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Counting Channel", value=channel.mention if channel else "Not set")
        embed.add_field(name="Toggle", value="Enabled" if toggle else "Disabled")
        embed.add_field(name="Delete After", value=f"{delete_after} seconds")
        embed.add_field(
            name="Toggle Edit Message", value="Enabled" if toggle_edit_message else "Disabled"
        )
        embed.add_field(
            name="Toggle Next Number Message",
            value="Enabled" if toggle_next_number_message else "Disabled",
        )
        embed.add_field(
            name="Same User To Count", value="Allowed" if same_user_to_count else "Disallowed"
        )
        embed.add_field(name="Default Edit Message", value=default_edit_message, inline=False)
        embed.add_field(
            name="Default Next Number Message", value=default_next_number_message, inline=False
        )
        await ctx.send(embed=embed)
