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
from typing import Final, Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

from .converter import EmojiConverter

log = logging.getLogger("red.maxcogs.suggestion")


class Suggestion(commands.Cog):
    """Suggest something to the server or something else?"""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.0.4"
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
            "next_suggestion_id": 0,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

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
        next_id = data["next_suggestion_id"]
        await self.config.guild(ctx.guild).next_suggestion_id.set(next_id + 1)
        embed = discord.Embed(
            title="New Suggestion",
            description=message,
            color=await ctx.embed_color(),
        )
        embed.set_author(
            name=f"{ctx.author} ({ctx.author.id})",
            icon_url=ctx.author.avatar.url,
        )
        # need to set the footer to something so we can check if the suggestion is pending
        # This allows us to approve/deny suggestions only from the cog and not from other embed messages.
        embed.set_footer(text="Suggestion Pending.")
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
        await ctx.reply(
            "Suggestion sent!",
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def suggest(self, ctx, *, message: str):
        """Send a suggestion to the suggestion channel."""
        await self.suggest_embed(ctx, message=message)

    @commands.admin()
    @commands.guild_only()
    @commands.command(aliases=["accept"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def approve(self, ctx, message_id: int):
        """Approve a suggestion.

        This will also clear the reactions on the suggestion if the suggestion voting is enabled.

        __Parameters__
        - message_id - The ID of the suggestion message.

        **Example:**
        - `[p]approve 1167805683668889711`
            - Approves the suggestion with the message ID of `1167805683668889711`.
        """
        if not message_id:
            return await ctx.send("You need to provide a message ID")
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        if toggle is False:
            return await ctx.send("Suggestion system is disabled")
        if channel is None:
            return await ctx.send("Suggestion channel is not set")
        try:
            message = await self.bot.get_channel(channel).fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("That message ID is invalid")
        if message.author != self.bot.user:
            return await ctx.send("That message is not a suggestion")
        if not message.embeds:
            return await ctx.send("That message is not a suggestion")
        embed = message.embeds[0]
        # Check if the suggestion is pending to be approved
        if embed.footer.text != "Suggestion Pending.":
            return await ctx.send("That suggestion has already been processed")
        new_embed = discord.Embed.from_dict(embed.to_dict())
        new_embed.color = discord.Color.green()
        new_embed.set_footer(text="Suggestion have been Approved.")
        try:
            await message.edit(embed=new_embed)
        except discord.Forbidden as e:
            return await ctx.send(
                "Unfortunatly I don't have permissions to edit that message due to it being too old.\nDiscord only allows bots to edit messages that are less than 2 weeks old."
            )
            log.info(e)
        if data["suggest_vote"]:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                log.info("I don't have permissions to clear reactions")
                pass
        await ctx.send("Suggestion approved")

    @commands.admin()
    @commands.guild_only()
    @commands.command(aliases=["deny"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def reject(self, ctx, message_id: int):
        """Reject a suggestion.

        This will also clear the reactions on the suggestion if the suggestion voting is enabled.

        __Parameters__
        - message_id - The ID of the suggestion message.

        **Example:**
        - `[p]reject 1167805683668889711`
            - Rejects the suggestion with the message ID of `1167805683668889711`.
        """
        if not message_id:
            return await ctx.send("You need to provide a message ID")
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channel = data["channel"]
        if toggle is False:
            return await ctx.send("Suggestion system is disabled")
        if channel is None:
            return await ctx.send("Suggestion channel is not set")
        try:
            message = await self.bot.get_channel(channel).fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("That message ID is invalid")
            log.info("Message ID is invalid")
        if message.author != self.bot.user:
            return await ctx.send("That message is not a suggestion")
        embed = message.embeds[0]
        # Check if the suggestion is pending to be denied
        if embed.footer.text != "Suggestion Pending.":
            return await ctx.send("That suggestion has already been processed")
        new_embed = discord.Embed.from_dict(embed.to_dict())
        new_embed.color = 0x8B0000
        new_embed.set_footer(text="Suggestion have been Rejected.")
        try:
            await message.edit(embed=new_embed)
        except discord.Forbidden as e:
            return await ctx.send(
                "Unfortunatly I don't have permissions to edit that message due to it being too old.\nDiscord only allows bots to edit messages that are less than 2 weeks old."
            )
            log.info(e)
        if data["suggest_vote"]:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                log.info("I don't have permissions to clear reactions")
                pass
        await ctx.send("Suggestion denied")

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

    @suggestion.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set or reset the suggestion channel."""
        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            or not channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                "I don't have permissions to send messages or embed links in {channel}".format(
                    channel=channel.mention
                )
            )
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Suggestion channel set to {channel.mention}")

    @suggestion.command()
    async def resetchannel(self, ctx):
        """Reset the suggestion channel."""
        await self.config.guild(ctx.guild).channel.set(None)
        await ctx.send("Suggestion channel reset")

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
        embed = discord.Embed(
            title="Suggestion settings",
            description="""
            **Toggle:** {toggle}
            **Channel:** {channel}
            **Suggest vote:** {suggest_vote}
            **Default upvote emoji:** {upvote}
            **Default downvote emoji:** {downvote}
            """.format(
                toggle=toggle,
                channel=channel.mention if channel else "Not set",
                suggest_vote=suggest_vote,
                upvote=suggest_default_upvote,
                downvote=suggest_default_downvote,
            ),
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
