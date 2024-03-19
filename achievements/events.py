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
from redbot.core.utils.chat_formatting import humanize_number
from .abc import MixinMeta, CompositeMetaClass

log = logging.getLogger("red.maxcogs.achievements.events")


class EventsMixin(MixinMeta, metaclass=CompositeMetaClass):
    async def check_message_count(self, member):
        """Add a message to the message count for a member."""
        count = await self.config.member(member).message_count()
        await self.config.member(member).message_count.set(count + 1)
        return count

    async def get_message_count(self, member):
        """Get the message count for a member."""
        return await self.config.member(member).message_count()

    async def check_achievements(self, member):
        count = await self.get_message_count(member)
        unlocked_achievements = await self.config.member(member).unlocked_achievements()

        # Check if we should use default achievements or custom ones
        use_default_achievements = await self.config.guild(
            member.guild
        ).use_default_achievements()

        if use_default_achievements:
            # Use default achievements
            achievements = self.achievements
        else:
            # Use custom achievements
            achievements = await self.config.guild(member.guild).custom_achievements()

        for achievement, value in sorted(achievements.items(), key=lambda x: x[1]):
            if count >= value and achievement not in unlocked_achievements:
                unlocked_achievements.append(achievement)
                await self.config.member(member).unlocked_achievements.set(
                    unlocked_achievements
                )
                return achievement
        return None

    async def notification(self, member, unlocked_achievement, default_channel):
        # Check if achievement notifications are enabled
        if not await self.config.guild(member.guild).toggle_achievement_notification():
            return

        # Get the notification channel
        channel_id = await self.config.guild(member.guild).channel_notify()
        channel = self.bot.get_channel(channel_id) if channel_id else default_channel

        # Determine whether to use default or custom achievements
        use_default_achievements = await self.config.guild(
            member.guild
        ).use_default_achievements()
        achievements = (
            self.achievements
            if use_default_achievements
            else await self.config.guild(member.guild).custom_achievements()
        )

        # Determine the next rank
        achievement_keys = list(achievements.keys())
        achievement_index = achievement_keys.index(unlocked_achievement)
        next_rank = (
            achievement_keys[achievement_index + 1]
            if achievement_index + 1 < len(achievement_keys)
            else "No more ranks"
        )

        if channel.permissions_for(member.guild.me).embed_links:
            if (
                not channel.permissions_for(member.guild.me).embed_links
                and not channel.permissions_for(member.guild.me).send_messages
            ):
                log.info(
                    "I don't have permissions to send messages and embed links in channel {channel}".format(
                        channel=channel
                    )
                )
                return
            embed = discord.Embed(
                title="Achievement Unlocked",
                description=f"{member.mention} have unlocked the `{unlocked_achievement}` achievement for sending {humanize_number(await self.get_message_count(member))} messages!",
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"Next rank: {next_rank}")
            await channel.send(embed=embed)
        else:
            await channel.send(
                f"{member.mention} have unlocked the `{unlocked_achievement}` achievement for sending {humanize_number(await self.get_message_count(member))} messages!",
                allowed_mentions=discord.AllowedMentions(users=False),
            )

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if (
            message.author.bot
            or await self.bot.cog_disabled_in_guild(self, message.guild)
            or not await self.config.guild(message.guild).toggle()
            or message.guild is None
        ):
            return

        blacklisted_channels = await self.config.guild(
            message.guild
        ).blacklisted_channels()
        if isinstance(
            message.channel,
            (
                discord.TextChannel,
                discord.ForumChannel,
                discord.Thread,
                discord.VoiceChannel,
            ),
        ):
            if message.channel.id in blacklisted_channels:
                return
        if (
            message.channel.id in blacklisted_channels
            or message.author.id in await self.config.member(message.author).ignore_me()
        ):
            return
        await self.check_message_count(message.author)
        unlocked_achievement = await self.check_achievements(message.author)

        # Only send the embed message if an achievement was unlocked
        if unlocked_achievement is not None:
            await self.notification(
                message.author, unlocked_achievement, message.channel
            )
