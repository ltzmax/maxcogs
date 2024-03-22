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
import logging

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list, humanize_number
from typing import Union, Literal, Optional

from .converters import EmojiConverter
from .abc import MixinMeta, CompositeMetaClass
from redbot.core.utils.views import SimpleMenu, ConfirmView

log = logging.getLogger("red.maxcogs.achievements.admin_commands")

DEFAULT_EMOJI_CHECK = "✅"
DEFAULT_EMOJI_X = "❌"

class AdminCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.group(aliases=["achieveset"])
    @commands.guild_only()
    @commands.admin()
    async def achievementset(self, ctx):
        """Achievement settings."""

    @achievementset.command()
    async def toggle(self, ctx):
        """Toggle achievements."""
        toggle = await self.config.guild(ctx.guild).toggle()
        await self.config.guild(ctx.guild).toggle.set(not toggle)
        await ctx.send(
            f"Achievements are now {'enabled' if not toggle else 'disabled'}."
        )

    @achievementset.command(usage="<add|remove> <channel>", aliases=["bl"])
    async def blacklist(
        self,
        ctx: commands.Context,
        add_or_remove: Literal["add", "remove"],
        channels: Union[
            discord.TextChannel,
            discord.ForumChannel,
            discord.Thread,
            discord.VoiceChannel,
        ],
    ):
        """Add or remove a channel from the blacklisted channels list.

        This will prevent the bot from counting messages in the blacklisted channels.

        **Examples:**
        - `[p]achievement blacklist add #general`
        - `[p]achievement blacklist remove #general`

        **Arguments:**
        - `<add_or_remove>`: Whether to add or remove the channel from the blacklisted channels list.
        - `<channels>`: The channels to add or remove from the blacklisted channels list.
        """
        blacklisted = await self.config.guild(ctx.guild).blacklisted_channels()
        if add_or_remove == "add":
            if channels.id in blacklisted:
                return await ctx.send("That channel is already blacklisted.")
            blacklisted.append(channels.id)
            await self.config.guild(ctx.guild).blacklisted_channels.set(blacklisted)
            await ctx.send(f"{channels.mention} has been blacklist.")
        else:
            if channels.id not in blacklisted:
                return await ctx.send("That channel is not blacklisted.")
            blacklisted.remove(channels.id)
            await self.config.guild(ctx.guild).blacklisted_channels.set(blacklisted)
            await ctx.send(f"Removed {channels.mention} from the blacklist.")

    @achievementset.command(aliases=["listbl"])
    @commands.bot_has_permissions(embed_links=True)
    async def listblacklisted(self, ctx):
        """List all blacklisted channels."""
        blacklisted_channels = await self.config.guild(ctx.guild).blacklisted_channels()
        # Fetch all channel IDs in the guild
        guild_channel_ids = {channel.id for channel in ctx.guild.channels}
        # Remove deleted channels from the blacklisted channels
        blacklisted_channels = [
            channel_id
            for channel_id in blacklisted_channels
            if channel_id in guild_channel_ids
        ]
        # Update the blacklisted channels in the config
        await self.config.guild(ctx.guild).blacklisted_channels.set(
            blacklisted_channels
        )
        if not blacklisted_channels:
            return await ctx.send("No blacklisted channels in this server.")
        pages = []
        channels = humanize_list([f"<#{channel}>" for channel in blacklisted_channels])
        for page in range(0, len(channels), 1024):
            embed = discord.Embed(
                title="Blacklisted Channels",
                description=channels[page : page + 1024],
                color=await ctx.embed_color(),
            )
            embed.set_footer(text=f"Page: {page//1024 + 1}/{len(channels)//1024 + 1}")
            pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @achievementset.command()
    async def notify(self, ctx):
        """Toggle achievement notifications.

        If channel is not set, it will use channels where they unlocked the achievement.
        """
        toggle = await self.config.guild(ctx.guild).toggle_achievement_notification()
        await self.config.guild(ctx.guild).toggle_achievement_notification.set(
            not toggle
        )
        if toggle:
            await ctx.send("Achievement notifications are now disabled.")
        else:
            await ctx.send("Achievement notifications are now enabled.")

    @achievementset.command()
    async def channel(self, ctx, channel: Optional[discord.TextChannel]):
        """Set the channel to notify about achievements."""
        if channel is None:
            await self.config.guild(ctx.guild).channel_notify.set(None)
            await ctx.send("Channel removed.")
        else:
            await self.config.guild(ctx.guild).channel_notify.set(channel.id)
            await ctx.send(f"Channel set to {channel.mention}.")

    @achievementset.command()
    async def settings(self, ctx):
        """Check the current settings."""
        toggle = await self.config.guild(ctx.guild).toggle()
        channel = await self.config.guild(ctx.guild).channel_notify()
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()
        toggle_achievement_notification = await self.config.guild(
            ctx.guild
        ).toggle_achievement_notification()
        await ctx.send(
            "## Achievement Settings\n"
            f"**Toggle**: {'Enabled' if toggle else 'Disabled'}\n"
            f"**Channel**: {ctx.guild.get_channel(channel).mention if channel else 'None'}\n"
            f"**Use Custom Achievements**: {'Enabled' if use_default_achievements else 'Disabled'}\n"
            f"**Achievement Notifications**: {'Enabled' if toggle_achievement_notification else 'Disabled'}"
            f"**Default Check Emoji**: {await self.config.guild(ctx.guild).default_emoji_check()}\n"
            f"**Default Cross Emoji**: {await self.config.guild(ctx.guild).default_emoji_x()}"
        )

    @achievementset.group()
    async def emoji(self, ctx):
        """Emoji settings."""

    @emoji.command()
    async def check(self, ctx, emoji: Optional[EmojiConverter]):
        """Set the check emoji.

        This only shows in `[p]achievements list` and `[p]achievements unlocked` commands.

        **Examples:**
        - `[p]achievements emoji check :white_check_mark:`
        - `[p]achievements emoji check :heavy_check_mark:`

        **Arguments:**
        - `<emoji>`: The emoji to set as the check emoji.
        """
        if emoji is None:
            await self.config.guild(ctx.guild).default_emoji_check.set(
                DEFAULT_EMOJI_CHECK
            )
            await ctx.send("I've reset the check emoji to the default.")
        else:
            await self.config.guild(ctx.guild).default_emoji_check.set(str(emoji))
            await ctx.send(f"Check emoji set to {str(emoji)}.")

    @emoji.command()
    async def cross(self, ctx, emoji: Optional[EmojiConverter]):
        """Set the cross emoji.

        This only shows in `[p]achievements list` and `[p]achievements unlocked` commands.

        **Examples:**
        - `[p]achievements emoji cross :x:`
        - `[p]achievements emoji cross :heavy_multiplication_x:`

        **Arguments:**
        - `<emoji>`: The emoji to set as the cross emoji.
        """
        if emoji is None:
            await self.config.guild(ctx.guild).default_emoji_x.set(DEFAULT_EMOJI_X)
            await ctx.send("I've reset the cross emoji to the default.")
        else:
            await self.config.guild(ctx.guild).default_emoji_x.set(str(emoji))
            await ctx.send(f"Cross emoji set to {str(emoji)}.")

    ## OWNRER COMMANDS

    @commands.is_owner()
    @achievementset.command()
    async def reset(self, ctx, member: discord.Member):
        """Reset a member's profile.

        This will reset the message count and unlocked achievements and cannot be undone without a backup.
        """
        if (
            not await self.config.member(member).unlocked_achievements()
            and not await self.config.member(member).message_count()
        ):
            return await ctx.send(f"{member} has no profile to reset.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            f"## [WARNING] You are about to reset {member}'s profile. Are you sure you want to continue?",
            view=view,
        )
        await view.wait()
        if view.result:
            await ctx.typing()
            await self.config.member(member).clear()
            await ctx.send("Profile reset.")
            log.info(f"{ctx.author} reset {member}'s profile in {ctx.guild}.")
        else:
            await ctx.send("Not resetting.")

    @commands.is_owner()
    @achievementset.command(hidden=True)
    async def resetall(self, ctx):
        """Reset all profiles.

        This will reset all message counts and unlocked achievements and cannot be undone without a backup.
        """
        if not await self.config.all_members() and not await self.config.all_guilds():
            return await ctx.send("Nothing to reset really.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "## [WARNING] You are about to reset all profiles. Are you sure you want to continue?",
            view=view,
        )
        await view.wait()
        if view.result:
            await ctx.typing()
            await self.config.clear_all_members()
            await self.config.guild(ctx.guild).clear()
            await ctx.send("All profiles reset.")
            log.info(f"{ctx.author} reset all profiles in {ctx.guild}.")
        else:
            await ctx.send("Not resetting.")
