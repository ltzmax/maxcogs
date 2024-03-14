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

from typing import Optional, Any, Final, Literal, Union
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import humanize_number, humanize_list
from redbot.core.utils.views import ConfirmView, SimpleMenu
from .unlock import achievements

DEFAULT_EMOJI_CHECK = "✅"
DEFAULT_EMOJI_X = "❌"

log = logging.getLogger("red.maxcogs.achievements")


class Achievements(commands.Cog):
    """Earn achievements by chatting in channels."""

    __version__: Final[str] = "1.3.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/achievements"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channel_notify": None,
            "use_default_achievements": True,
            "custom_achievements": {},
            "toggle": False,
            "toggle_achievements_notifications": False,
            "blacklisted_channels": [],
            "default_emoji_check": DEFAULT_EMOJI_CHECK,
            "default_emoji_x": DEFAULT_EMOJI_X,
        }
        default_member = {
            "message_count": 0,
            "unlocked_achievements": [],
            "ignore_me": [],
        }
        self.config.register_member(**default_member)
        self.config.register_guild(**default_guild)
        self.achievements = achievements

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: Any, user_id: int) -> None:
        await self.config.member_from_ids(user_id).clear()

    async def check_message_count(self, member):
        """Add a message to the message count for a member."""
        count = await self.config.member(member).message_count()
        count += 1
        await self.config.member(member).message_count.set(count)
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

    async def achievement_fuction(
        self,
        member: discord.Member,
        get_message_count,
        check_message_count,
        check_achievements,
    ):
        """Allow other cogs to use the achievement functions.

         This is useful for example giveaways, leveling, and other cogs that want to use the achievements.

        Example:
             - `await self.bot.get_cog("Achievements").achievement_fuction(member, get_message_count, check_message_count, check_achievements)`

         Arguments:
             - `member`: The discord.Member object to check.
             - `get_message_count`: The get_message_count function to get the message count for a member.
             - `check_message_count`: The check_message_count function to check the message count for a member.
             - `check_achievements`: The check_achievements function to check the achievements for a member.
        """
        return (
            await check_achievements(member),
            await get_message_count(member),
            await check_message_count(member),
        )

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
        # Check if the message is from a bot, or if the cog is disabled in the guild, or if the guild toggle is off, or if the guild is None
        if (
            message.author.bot
            or await self.bot.cog_disabled_in_guild(self, message.guild)
            or not await self.config.guild(message.guild).toggle()
            or message.guild is None
        ):
            return

        # Check if the message's channel is blacklisted or if the author is ignored
        blacklisted_channels = await self.config.guild(
            message.guild
        ).blacklisted_channels()

        if isinstance(
            message.channel,
            discord.Thread,
            discord.ForumChannel,
            discord.VoiceChannel,
            discord.TextChannel,
        ):
            if message.channel.parent_id in blacklisted_channels:
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

    @commands.group(aliases=["achieve"])
    async def achievements(self, ctx):
        """Achievements commands."""

    @commands.admin()
    @commands.guild_only()
    @achievements.command()
    async def toggle(self, ctx):
        """Toggle achievements."""
        toggle = await self.config.guild(ctx.guild).toggle()
        await self.config.guild(ctx.guild).toggle.set(not toggle)
        await ctx.send(
            f"Achievements are now {'enabled' if not toggle else 'disabled'}."
        )

    @commands.admin()
    @commands.guild_only()
    @achievements.command(usage="<add|remove> <channel>", aliases=["bl"])
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

    @commands.admin()
    @commands.guild_only()
    @achievements.command(aliases=["listbl"])
    @commands.bot_has_permissions(embed_links=True)
    async def listblacklisted(self, ctx):
        """List all blacklisted channels."""
        blacklisted_channels = await self.config.guild(ctx.guild).blacklisted_channels()
        if not blacklisted_channels:
            return await ctx.send("No blacklisted channels.")
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

    @achievements.command()
    @commands.guild_only()
    async def ignoreme(self, ctx):
        """Ignore yourself from earning achievements.

        This will prevent you from earning achievements until you run the command again.
        It will stop from counting your messages and unlocking achievements.
        """
        ignore_me = await self.config.member(ctx.author).ignore_me()
        if ctx.author.id in ignore_me:
            ignore_me.remove(ctx.author.id)
            await self.config.member(ctx.author).ignore_me.set(ignore_me)
            await ctx.send("You will now earn achievements.")
        else:
            ignore_me.append(ctx.author.id)
            await self.config.member(ctx.author).ignore_me.set(ignore_me)
            await ctx.send("You will no longer earn achievements.")

    @achievements.command()
    @commands.guild_only()
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

    @commands.admin()
    @commands.guild_only()
    @achievements.command()
    async def channel(self, ctx, channel: Optional[discord.TextChannel]):
        """Set the channel to notify about achievements."""
        if channel is None:
            await self.config.guild(ctx.guild).channel_notify.set(None)
            await ctx.send("Channel removed.")
        else:
            await self.config.guild(ctx.guild).channel_notify.set(channel.id)
            await ctx.send(f"Channel set to {channel.mention}.")

    @commands.admin()
    @commands.guild_only()
    @achievements.group()
    async def emoji(self, ctx):
        """Emoji settings."""

    @emoji.command()
    async def check(self, ctx, emoji: Optional[discord.Emoji]):
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
    async def cross(self, ctx, emoji: Optional[discord.Emoji]):
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

    @commands.guild_only()
    @achievements.command(name="list")
    @commands.bot_has_permissions(embed_links=True)
    async def list_achievements(self, ctx):
        """List all available achievements."""

        # Check if we should use default achievements or custom ones
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()

        if use_default_achievements:
            # Use default achievements
            achievements = self.achievements
        else:
            # Use custom achievements
            achievements = await self.config.guild(ctx.guild).custom_achievements()

        # Fetch the author's unlocked achievements
        unlocked_achievements = await self.config.member(
            ctx.author
        ).unlocked_achievements()
        if unlocked_achievements is None:
            unlocked_achievements = []

        default_emoji_check = await self.config.guild(ctx.guild).default_emoji_check()
        default_emoji_x = await self.config.guild(ctx.guild).default_emoji_x()

        achievements_list = [
            f"{default_emoji_check if key in unlocked_achievements else default_emoji_x} `{key}`: {humanize_number(value)} messages"
            for key, value in achievements.items()
        ]
        if not achievements_list:
            return await ctx.send("No achievements available.")
        pages = []
        page = ""
        for achievement in achievements_list:
            if len(page + achievement + "\n") > 1024:
                pages.append(page)
                page = achievement + "\n"
            else:
                page += achievement + "\n"
        if page:
            pages.append(page)
        embeds = [
            discord.Embed(
                title="Achievements", description=page, color=await ctx.embed_color()
            ).set_footer(text=f"Page: {i+1}/{len(pages)}")
            for i, page in enumerate(pages)
        ]
        await SimpleMenu(
            embeds,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @achievements.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def profile(self, ctx, member: discord.Member = None):
        """Check your profile or someone else's."""
        if member is None:
            member = ctx.author

        if member.bot:
            return await ctx.send("Bots don't have profiles.")

        count = await self.get_message_count(member)
        # Calculate next rank

        # Check if we should use default achievements or custom ones
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()

        if use_default_achievements:
            # Use default achievements
            achievements = self.achievements
        else:
            # Use custom achievements
            achievements = await self.config.guild(ctx.guild).custom_achievements()

        sorted_ranks = sorted(achievements.items(), key=lambda x: x[1])
        next_rank = None
        for rank, rank_count in sorted_ranks:
            if count < rank_count:
                next_rank = rank
                break

        embed = discord.Embed(
            title=f"{member}'s Profile", color=await ctx.embed_color()
        )
        embed.add_field(name="Messages:", value=humanize_number(count), inline=False)
        if next_rank:
            embed.add_field(
                name="Next Rank:",
                value=f"`{next_rank}`: {rank_count - count} Messages Left\n`Required`: {rank_count} Messages",
                inline=False,
            )
        embed.set_thumbnail(
            url=member.default_avatar.url if not member.avatar else member.avatar.url
        )
        ignored = member.id in await self.config.member(member).ignore_me()
        if ignored:
            embed.set_footer(text="This member is ignoring from earning achievements.")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @achievements.command(aliases=["lb"])
    @commands.bot_has_permissions(embed_links=True)
    async def leaderboard(self, ctx):
        """Check the leaderboard."""
        members = await self.config.all_members(ctx.guild)
        pages = []
        sorted_members = sorted(
            members.items(), key=lambda x: x[1]["message_count"], reverse=True
        )
        leaderboard = ""
        for member_id, data in sorted_members[:20]:
            member = ctx.guild.get_member(member_id)
            if member is not None:
                leaderboard += f"{sorted_members.index((member_id, data)) + 1}. {member.mention}: {humanize_number(data['message_count'])} {'messages' if data['message_count'] != 1 else 'message'}\n"

        if not leaderboard:
            return await ctx.send("No leaderboard available.")

        for page in range(0, len(leaderboard), 1024):
            embed = discord.Embed(
                title="Leaderboard",
                description=leaderboard[page : page + 1024],
                color=await ctx.embed_color(),
            )
            embed.set_footer(
                text=f"Page: {page//1024 + 1}/{len(leaderboard)//1024 + 1}"
            )
            pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @achievements.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def unlocked(self, ctx, member: discord.Member = None):
        """Check your unlocked achievements or someone else's."""
        if member is None:
            member = ctx.author
        pages = []
        unlocked_achievements = await self.config.member(member).unlocked_achievements()
        if unlocked_achievements is None:
            unlocked_achievements = []
        unlocked = ""
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()
        default_emoji_check = await self.config.guild(ctx.guild).default_emoji_check()
        for achievement in unlocked_achievements:
            if (
                use_default_achievements
                and not self.achievements
                or (not use_default_achievements and self.achievements)
            ):
                unlocked += f"{default_emoji_check} `{achievement}`\n"
        if unlocked:
            for page in range(0, len(unlocked), 1024):
                embed = discord.Embed(
                    title=f"{member}'s Unlocked Achievements",
                    description=unlocked[page : page + 1024],
                    color=await ctx.embed_color(),
                )
                embed.set_footer(
                    text=f"Page: {page//1024 + 1}/{len(unlocked)//1024 + 1}"
                )
                pages.append(embed)
            await SimpleMenu(
                pages,
                disable_after_timeout=True,
                timeout=120,
            ).start(ctx)
        else:
            await ctx.send("No unlocked achievements.")

    @commands.is_owner()
    @commands.guild_only()
    @achievements.command()
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
    @commands.guild_only()
    @achievements.command(hidden=True)
    async def resetall(self, ctx):
        """Reset all profiles.

        This will reset all message counts and unlocked achievements and cannot be undone without a backup.
        """
        if not await self.config.all_members():
            return await ctx.send("There are no profiles to reset.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "## [WARNING] You are about to reset all profiles. Are you sure you want to continue?",
            view=view,
        )
        await view.wait()
        if view.result:
            await ctx.typing()
            await self.config.clear_all_members()
            await ctx.send("All profiles reset.")
            log.info(f"{ctx.author} reset all profiles in {ctx.guild}.")
        else:
            await ctx.send("Not resetting.")

    @achievements.group()
    @commands.guild_only()
    @commands.guildowner()
    async def custom(self, ctx):
        """Custom achievements commands.

        Only guild owners can use these commands.

        Custom achievements are disabled by default. Enable them with `[p]achievement custom enable`.
        This will allow you to add, remove, and list custom achievements for your server.
        """

    @custom.command()
    async def enable(self, ctx):
        """Toggle custom achievements."""
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()
        await self.config.guild(ctx.guild).use_default_achievements.set(
            not use_default_achievements
        )
        if use_default_achievements:
            await ctx.send("Custom achievements are now enabled.")
        else:
            await ctx.send("Custom achievements are now disabled.")

    @custom.command()
    async def add(self, ctx, name: str, value: str):
        """Add a custom achievement.

        You must have custom achievements enabled to use this command.

        Example:
        - `[p]achievement custom add Epic 1000`
        - `[p]achievement custom add Legendary 10000`

        Arguments:
        - `<name>`: The name of the achievement. (must be between 1 and 256 characters)
        - `<value>`: The message count required to unlock the achievement. (must be an integer)
        """
        if await self.config.guild(ctx.guild).use_default_achievements():
            return await ctx.send(
                "Custom achievements are disabled.\nEnable them with `{prefix}achievement custom toggle`".format(
                    prefix=ctx.clean_prefix
                )
            )
        if len(name) > 256 or len(name) < 1:
            return await ctx.send("Name must be between 1 and 256 characters.")
        try:
            value = int(value)
        except ValueError as e:
            return await ctx.send("The value must be a number (integer).")
            log.error(e)
        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        if value in custom_achievements.values():
            return await ctx.send("That value is already an achievement.")
        if value < 5:
            return await ctx.send("The value must be at least 5.")
        if name in await self.config.guild(ctx.guild).custom_achievements():
            return await ctx.send("That achievement already exists.")
        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        custom_achievements[name] = value
        await self.config.guild(ctx.guild).custom_achievements.set(custom_achievements)
        await ctx.send(f"Added `{name}` achievement for `{value}` messages.")

    @custom.command()
    async def remove(self, ctx, name: str):
        """Remove a custom achievement.

        Example:
        - `[p]achievement custom remove Epic`
        - `[p]achievement custom remove Legendary`

        Arguments:
        - `<name>`: The name of the achievement. You can get the name from `[p]achievement list`.
        """

        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        if name in custom_achievements:
            del custom_achievements[name]
            await self.config.guild(ctx.guild).custom_achievements.set(
                custom_achievements
            )
            await ctx.send(f"Removed `{name}` achievement.")
        else:
            await ctx.send("That achievement does not exist.")

    @custom.command()
    async def clear(self, ctx):
        """Clear all custom achievements."""
        if not await self.config.guild(ctx.guild).custom_achievements():
            return await ctx.send("There are no custom achievements to clear.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "## [WARNING] You are about to clear all custom achievements. Are you sure you want to continue?",
            view=view,
        )
        await view.wait()
        if view.result:
            await ctx.typing()
            await self.config.guild(ctx.guild).custom_achievements.set({})
            await ctx.send("Custom achievements cleared.")
            log.info(f"{ctx.author} cleared all custom achievements in {ctx.guild}.")
        else:
            await ctx.send("Not clearing.")

    @commands.guild_only()
    @achievements.command()
    @commands.admin_or_permissions(manage_guild=True)
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
        )
