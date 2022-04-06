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
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .abc import MixinMeta
from .converters import RealEmojiConverter

log = logging.getLogger("red.maxcogs.onconnect")


class Commands(MixinMeta):
    """Commands for managing the cog's settings are found here."""

    @commands.is_owner()
    @commands.guild_only()
    @commands.group(name="connectset")
    async def _connectset(self, ctx: commands.Context) -> None:
        """Manage settings for onconnect."""
  
    @commands.bot_can_react()
    @_connectset.command(name="channel")
    async def _channel(
        self, ctx, *, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Set the channel to log shard events to.

        Note: Events are not able to be set in threads.

        **Example:**
        - `[p]connectset channel #general`
        This will set the event channel to general.

        **Arguments:**
        - `[channel]` - Is where you set the event channel. Leave it blank to disable.
        """
        # i have no idea where to add this, but works for now.
        # just doesn't work outside of a thread, it will clear the channel instead.
        if isinstance(ctx.channel, discord.Thread):
            return await self.maybe_reply(
                ctx=ctx, message="You can't set events in thread."
            )
        guild = ctx.guild
        embed_requested = await ctx.embed_requested()
        if channel:
            if not channel.permissions_for(guild.me).embed_links:
                return await self.maybe_reply(
                    ctx=ctx,
                    message="I do not have the `embed_links` permission in {}.".format(
                        channel.mention
                    ),
                )
            await self.config.statuschannel.set(channel.id)
            log.info(f"Status Channel set to {channel} ({channel.id})")
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"Events will now be sent to {channel.mention}.",
                    colour=await ctx.embed_colour(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message=f"Events will now be sent to {channel.mention}."
                )

        elif await self.config.statuschannel() is not None:
            if embed_requested:
                embed = discord.Embed(
                    title="Are you sure you want to disable events?",
                    colour=await ctx.embed_colour(),
                )
                msg = await ctx.send(embed=embed)
            else:
                msg = await ctx.send("Are you sure you want to disable events?")

            # Switch Reaction Predicate to use buttons whenever i have read enough docs for it.
            # Right now i don't know 100% how to do it correctly.
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            try:
                await self.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await self.maybe_reply(
                    ctx=ctx,
                    message="You took too long to respond, cancelling.",
                    mention_author=True,
                )
                await msg.clear_reactions()
            else:
                if pred.result is True:
                    await self.config.statuschannel.set(None)
                    log.info("Status Channel has been disabled.")
                    if embed_requested:
                        embed = discord.Embed(
                            title="Setting Changed",
                            description="Events have been disabled.",
                            colour=await ctx.embed_colour(),
                        )
                        await self.maybe_reply(ctx=ctx, embed=embed)
                    else:
                        await self.maybe_reply(
                            ctx=ctx, message="Events have been disabled."
                        )
                else:
                    await self.maybe_reply(ctx=ctx, message="Cancelled.")
        else:
            await self.maybe_reply(
                ctx=ctx,
                message=(
                    f"Events are already disabled. Use `{ctx.clean_prefix}connectset "
                    "channel #channel` to enable."
                    "\n**Note** You cannot set events in threads."
                ),
                mention_author=True,
            )

    @_connectset.group(name="emoji", aliases=["emojis"])
    async def _emoji(self, ctx: commands.Context):
        """Settings to change default emoji.

        NOTE: If you want to set custom emojis, your bot needs to share the same server
        as the custom emoji. Make sure shard event channel has external emoji permission enabled.
        """

    @_emoji.command(name="green")
    async def _emoji_green(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ) -> None:
        """Change the green emoji to your own.

        **Example:**
        - `[p]connectset emoji green :green_heart:`
        This will change the green emoji to :green_heart:.

        **Arguments:**
        - `[emoji]` - Is where you set the emoji. Leave it blank to reset.
        """
        embed_requested = await ctx.embed_requested()
        if not emoji:
            await self.config.green.clear()
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The green emoji has been reset.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message="The green emoji has been reset."
                )
        else:
            await self.config.green.set(str(emoji))
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The green emoji has been set to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message=f"The green emoji has been set to {emoji}."
                )

    @_emoji.command(name="orange")
    async def _emoji_orange(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ) -> None:
        """Change the orange emoji to your own.

        **Example:**
        - `[p]connectset emoji orange :orange_heart:`
        This will change the orange emoji to :orange_heart:.

        **Arguments:**
        - `[emoji]` - Is where you set the emoji. Leave it blank to reset.
        """
        embed_requested = await ctx.embed_requested()
        if not emoji:
            await self.config.orange.clear()
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The orange emoji has been reset.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message="The orange emoji has been reset."
                )
        else:
            await self.config.orange.set(str(emoji))
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The orange emoji has been set to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message=f"The orange emoji has been set to {emoji}."
                )

    @_emoji.command(name="red")
    async def _emoji_red(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ) -> None:
        """Change the red emoji to your own.

        **Example:**
        - `[p]connectset emoji red :heart:`
        This will change the red emoji to :heart:.

        **Arguments:**
        - `[emoji]` - Is where you set the emoji. Leave it blank to reset.
        """
        embed_requested = await ctx.embed_requested()
        if not emoji:
            await self.config.red.clear()
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The red emoji has been reset.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(ctx=ctx, message="The red emoji has been reset.")
        else:
            await self.config.red.set(str(emoji))
            if embed_requested:
                embed = discord.Embed(
                    title="Setting Changed",
                    description=f"The red emoji has been set to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await self.maybe_reply(ctx=ctx, embed=embed)
            else:
                await self.maybe_reply(
                    ctx=ctx, message=f"The red emoji has been set to {emoji}."
                )

    @_connectset.command(name="showsettings", aliases=["settings"])
    async def _show_settings(self, ctx: commands.Context) -> None:
        """Shows the current settings for OnConnect."""
        config = await self.config.all()
        chan_config = config["statuschannel"]
        status_channel = f"<#{chan_config}>" if chan_config else "Not set."
        green_emoji = config["green"]
        orange_emoji = config["orange"]
        red_emoji = config["red"]
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="OnConnect Settings",
                description=f"**Status Channel:** {status_channel}",
                colour=await ctx.embed_colour(),
            )
            embed.add_field(name="Green Emoji:", value=green_emoji)
            embed.add_field(name="Orange Emoji:", value=orange_emoji)
            embed.add_field(name="Red Emoji:", value=red_emoji)
            embed.set_thumbnail(url=str(self.bot.user.display_avatar))
            await self.maybe_reply(ctx=ctx, embed=embed)
        else:
            message = (
                f"**`{'Status Channel':<15}:`** {status_channel}\n"
                f"**`{'Green Emoji':<15}:`** {green_emoji}\n"
                f"**`{'Orange Emoji':<15}:`** {orange_emoji}\n"
                f"**`{'Red Emoji':<15}:`** {red_emoji}"
            )
            await self.maybe_reply(ctx=ctx, message=message)

    @_connectset.command(name="version")
    async def _version(self, ctx: commands.Context) -> None:
        """Shows the cog version."""
        message = f"Author: {self.__author__}\nVersion: {self.__version__}"
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Cog Version:",
                description=message,
                colour=await ctx.embed_colour(),
            )
            await self.maybe_reply(ctx=ctx, embed=embed)
        else:
            await self.maybe_reply(ctx=ctx, message=f"**Cog Version:**\n{message}")
