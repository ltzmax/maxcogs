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
import asyncio
import re
from typing import Final, Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

from .converter import EmojiConverter

SUGGESTION_ID = re.compile(r"(?:Suggestion #)(\d+)")

log = logging.getLogger("red.maxcogs.suggestion")


class Suggestion(commands.Cog):
    """Suggest something to the server or something else?"""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.0.7"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/suggestion"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=78631113035100160)
        default_guild = {
            "toggle": False,
            "channel": None,
            "suggest_vote": False,
            "suggest_default_upvote": "👍",
            "suggest_default_downvote": "👎",
            "suggestion_id": 0,
            "allouw_without_command": False,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        """
        Send a suggestion to the suggestion channel without using a command.
        You can just type your suggestion in the suggestion channel and the bot will delete your message and build the embed with your message.
        """
        if message.guild is None:
            return
        # check if its enabled or not
        if not await self.config.guild(message.guild).allouw_without_command():
            return
        # Ignore bots
        if message.author.bot:
            return
        # check for the channel
        channel = await self.config.guild(message.guild).channel()
        if channel is None:
            return
        # check for the channel
        if message.channel.id != channel:
            return
        # check if the cog is disabled
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        if not message.content:
            return

        # check for the length
        if len(message.content) > 2024 or len(message.content) < 3:
            await asyncio.sleep(0.3)
            await message.delete()
            await message.channel.send(
                "Your suggestion must be between 3 and 2024 characters long",
                delete_after=10,
            )
            log.info(
                f"Suggestion is too long or too short in {message.channel} by {message.author} ({message.author.id})"
            )
            return

        # check for the permissions of the bot in the channel
        if (
            not message.guild.me.guild_permissions.manage_messages
            or not message.guild.me.guild_permissions.embed_links
            or not message.guild.me.guild_permissions.send_messages
        ):
            await self.config.guild(message.guild).withoutcmd.set(False)
            return
            log.info(
                "I don't have permissions to send messages, manage messages or embed links in {channel}".format(
                    channel=message.channel
                )
            )
        next_id = await self.config.guild(message.guild).suggestion_id() + 1
        await self.config.guild(message.guild).suggestion_id.set(next_id)
        # Create an embed from the message
        embed = discord.Embed(
            title="New Suggestion",
            description=f"**Description**:\n> {message.content}",
            color=await self.bot.get_embed_color(message.channel),
        )
        embed.set_author(
            name=f"{message.author} ({message.author.id})",
            icon_url=message.author.avatar.url,
        )
        # Delete the original message
        await asyncio.sleep(0.3)
        await message.delete()
        # Send the embed
        message = await message.channel.send(f"Suggestion #{next_id}", embed=embed)
        if await self.config.guild(message.guild).suggest_vote():
            if not message.channel.permissions_for(message.guild.me).add_reactions:
                await self.config.guild(message.guild).suggest_vote.set(False)
                return
                log.info(
                    "I don't have permissions to add reactions in {channel}".format(
                        channel=message.channel
                    )
                )
            await asyncio.sleep(0.5)
            await message.add_reaction(
                await self.config.guild(message.guild).suggest_default_upvote()
            )
            await message.add_reaction(
                await self.config.guild(message.guild).suggest_default_downvote()
            )

    async def suggest_embed(self, ctx, *, message: str):
        """Send a suggestion to the suggestion channel."""
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        if toggle is False:
            return await ctx.send("Suggestion system is disabled")
        if channel is None:
            return await ctx.send("Suggestion channel is not set")
        channel = self.bot.get_channel(channel)
        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            or not channel.permissions_for(ctx.guild.me).embed_links
        ):
            await self.config.guild(ctx.guild).channel.set(None)
            return
            log.info(
                "I don't have permissions to send messages or embed links in {channel}".format(
                    channel=channel
                )
            )
        if len(message) > 2024 or len(message) < 3:
            return await ctx.send(
                "Your suggestion must be between 3 and 2024 characters long"
            )
            log.info("Suggestion is too long or too short")
        next_id = data["suggestion_id"] + 1
        await self.config.guild(ctx.guild).suggestion_id.set(next_id)
        embed = discord.Embed(
            title="New Suggestion",
            description=f"**Description**:\n> {message}",
            color=await ctx.embed_color(),
        )
        embed.set_author(
            name=f"{ctx.author} ({ctx.author.id})",
            icon_url=ctx.author.avatar.url,
        )
        msg = await channel.send(
            f"Suggestion #{next_id}",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )
        if data["suggest_vote"]:
            if not channel.permissions_for(ctx.guild.me).add_reactions:
                await data["suggest_vote"].set(False)
                return
                log.info(
                    "I don't have permissions to add reactions in {channel}".format(
                        channel=channel
                    )
                )
            await msg.add_reaction(data["suggest_default_upvote"])
            await msg.add_reaction(data["suggest_default_downvote"])
        await ctx.send(
            "Suggestion sent!",
            allowed_mentions=discord.AllowedMentions(replied_user=False),
            reference=ctx.message.to_reference(fail_if_not_exists=False),
        )

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def suggest(self, ctx, *, message: str):
        """Send a suggestion to the suggestion channel."""
        if await self.config.guild(ctx.guild).allouw_without_command():
            return await ctx.send(
                "You can't use this command while allow_without_command is enabled",
                allowed_mentions=discord.AllowedMentions(replied_user=False),
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        await self.suggest_embed(ctx, message=message)

    @commands.command()
    @commands.guild_only()
    @commands.admin()
    async def approve(self, ctx, message_id: int, *, reason: Optional[str] = None):
        """
        Approve a suggestion.

        Must be a message id of a suggestion in the suggestion channel.
        If the suggestion is approved, the bot will edit the embed and add a footer with the approver.

        Parameters
        ----------
        - message_id : int
            - The message id of the suggestion.
        """
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        if toggle is False:
            return await ctx.send("Suggestion system is disabled")
        if channel is None:
            return await ctx.send("Suggestion channel is not set")
        channel = self.bot.get_channel(channel)
        try:
            msg = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            return await ctx.send("Something went wrong while approving the suggestion")
            log.info(f"Some error occured while approving a suggestion: {e}")
        if reason is not None and len(reason) > 1024:
            return await ctx.send(
                "Your reason must be between 0 and 1024 characters long"
            )
        if msg.embeds:
            try:
                embed = msg.embeds[0]
            except IndexError:
                return await ctx.send("Message not found")
                log.info(
                    f"{ctx.author} tried to approve a message that is not a suggestion"
                )
            if embed.title != "New Suggestion":
                return await ctx.send("This message is not a suggestion")
            embed.color = 0x00FF00
            if reason is not None:
                embed.add_field(name="Reason:", value=f"> {reason}")
            embed.set_footer(text="Approved by {author}".format(author=ctx.author))
            await msg.edit(embed=embed)
            await ctx.send(
                "Approved suggestion #{id}".format(
                    id=SUGGESTION_ID.search(msg.content).group(1)
                ),
                allowed_mentions=discord.AllowedMentions(replied_user=False),
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        else:
            await ctx.send("This message is not a suggestion")

    @commands.command()
    @commands.guild_only()
    @commands.admin()
    async def reject(self, ctx, message_id: int, *, reason: Optional[str] = None):
        """
        Reject a suggestion.

        Must be a message id of a suggestion in the suggestion channel.
        If the suggestion is rejected, the bot will edit the embed and add a footer with the rejecter.

        Parameters
        ----------
        - message_id : int
            - The message id of the suggestion.
        """
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        if toggle is False:
            return await ctx.send("Suggestion system is disabled")
        if channel is None:
            return await ctx.send("Suggestion channel is not set")
        channel = self.bot.get_channel(channel)
        try:
            msg = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            return await ctx.send("Something went wrong while rejecting the suggestion")
            log.info(f"Some error occured while rejecting a suggestion: {e}")
        if reason is not None and len(reason) > 1024:
            return await ctx.send(
                "Your reason must be between 0 and 1024 characters long"
            )
        if msg.embeds:
            try:
                embed = msg.embeds[0]
            except IndexError:
                return await ctx.send("Message not found")
                log.info(
                    f"{ctx.author} tried to reject a message that is not a suggestion"
                )
            if embed.title != "New Suggestion":
                return await ctx.send("This message is not a suggestion")
            embed.color = 0xFF0000
            if reason is not None:
                embed.add_field(name="Reason:", value=f"> {reason}")
            embed.set_footer(text="Rejected by {author}".format(author=ctx.author))
            await msg.edit(embed=embed)
            await ctx.send(
                "Rejected suggestion #{id}".format(
                    id=SUGGESTION_ID.search(msg.content).group(1)
                ),
                allowed_mentions=discord.AllowedMentions(replied_user=False),
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        else:
            await ctx.send("This message is not a suggestion")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def suggestion(self, ctx):
        """Manage the suggestion system."""

    @suggestion.command()
    async def toggle(self, ctx):
        """Toggle the suggestion system"""
        toggle = await self.config.guild(ctx.guild).toggle()
        await self.config.guild(ctx.guild).toggle.set(not toggle)
        await ctx.send(
            f"Suggestion system is now {'enabled' if not toggle else 'disabled'}"
        )

    @suggestion.command(name="withoutcmd")
    async def allouw_without_command(self, ctx):
        """
        Toggle whether suggestions can be sent without using a command.

        This means that you can just type your suggestion in the suggestion channel and the bot will build the embed with your message.

        Note: This will disable the `[p]suggest` command from being used.
        """
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("You need to enable the suggestion system first")
        if not await self.config.guild(ctx.guild).channel():
            return await ctx.send("You need to set the suggestion channel first")
        if not ctx.guild.me.guild_permissions.manage_messages:
            return await ctx.send("I don't have permissions to manage messages")
        toggle = await self.config.guild(ctx.guild).allouw_without_command()
        await self.config.guild(ctx.guild).allouw_without_command.set(not toggle)
        await ctx.send(
            f"Suggestion system is now {'enabled' if not toggle else 'disabled'}"
        )

    @suggestion.command()
    async def channel(self, ctx, channel: Optional[discord.TextChannel]):
        """Set or reset the suggestion channel."""
        if channel is None:
            await self.config.guild(ctx.guild).channel.set(None)
            return await ctx.send("Suggestion channel reset")
        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            or not channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                "I don't have permissions to send messages or embed links in {channel}".format(
                    channel=channel.mention
                )
            )
        if await self.config.guild(ctx.guild).channel() == channel.id:
            return await ctx.send("This channel is already the suggestion channel")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Suggestion channel set to {channel.mention}")

    @suggestion.command()
    async def vote(self, ctx):
        """Toggle upvote/downvote on suggestions."""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("You need to enable the suggestion system first")
        suggest_vote = await self.config.guild(ctx.guild).suggest_vote()
        await self.config.guild(ctx.guild).suggest_vote.set(not suggest_vote)
        await ctx.send(
            f"Suggestion voting is now {'enabled' if not suggest_vote else 'disabled'}"
        )

    @suggestion.group()
    async def emoji(self, ctx):
        """Set a new default upvote/downvote emoji."""

    @emoji.command()
    async def upvote(self, ctx, emoji: Optional[EmojiConverter]):
        """Set a new default upvote emoji."""
        data = await self.config.guild(ctx.guild).all()
        if emoji is None:
            await self.config.guild(ctx.guild).suggest_default_upvote.set("👍")
            return await ctx.send("Default upvote emoji reset")
        await self.config.guild(ctx.guild).suggest_default_upvote.set(str(emoji))
        await ctx.send(f"Default upvote emoji set to {emoji}")

    @emoji.command()
    async def downvote(self, ctx, emoji: Optional[EmojiConverter]):
        """Set a new default downvote emoji."""
        data = await self.config.guild(ctx.guild).all()
        if emoji is None:
            await self.config.guild(ctx.guild).suggest_default_downvote.set("👎")
            return await ctx.send("Default downvote emoji reset")
        await self.config.guild(ctx.guild).suggest_default_downvote.set(str(emoji))
        await ctx.send(f"Default downvote emoji set to {emoji}")

    @suggestion.command()
    async def reset(self, ctx):
        """Reset the suggestion settings."""
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        suggest_vote = data["suggest_vote"]
        if toggle is False and channel is None and suggest_vote is False:
            return await ctx.send("Suggestion settings are already reset")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset the suggestion settings?", view=view
        )
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            await ctx.send("Suggestion settings reset")
        else:
            await ctx.send("Cancelled")

    @suggestion.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx):
        """Show the suggestion settings."""
        toggle = await self.config.guild(ctx.guild).toggle()
        channel = self.bot.get_channel(await self.config.guild(ctx.guild).channel())
        suggest_vote = await self.config.guild(ctx.guild).suggest_vote()
        suggest_default_upvote = await self.config.guild(
            ctx.guild
        ).suggest_default_upvote()
        suggest_default_downvote = await self.config.guild(
            ctx.guild
        ).suggest_default_downvote()
        withoutcmd = await self.config.guild(ctx.guild).allouw_without_command()
        msg = (
            "Suggestion system: {toggle}\n"
            "Without command: {withoutcmd}\n"
            "Suggestion channel: {channel}\n"
            "Suggestion voting: {suggest_vote}\n"
            "Default upvote emoji: {suggest_default_upvote}\n"
            "Default downvote emoji: {suggest_default_downvote}"
        ).format(
            toggle=toggle,
            withoutcmd=withoutcmd,
            channel=channel.mention if channel is not None else None,
            suggest_vote=suggest_vote,
            suggest_default_upvote=suggest_default_upvote,
            suggest_default_downvote=suggest_default_downvote,
        )
        embed = discord.Embed(
            title="Suggestion settings",
            description=msg,
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @suggestion.command()
    @commands.bot_has_permissions(embed_links=True)
    async def version(self, ctx):
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)
