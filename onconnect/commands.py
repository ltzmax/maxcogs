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
from typing import Optional

import discord
from redbot.core import commands

from .abc import MixinMeta
from .converters import RealEmojiConverter
from .log import log


class Commands(MixinMeta):
    """The commands are stored here."""

    @commands.is_owner()
    @commands.guild_only()
    @commands.group(name="connectset")
    async def _connectset(self, ctx: commands.Context):
        """Settings for shard event logging."""

    @_connectset.command(name="channel", usage="[channel]")
    @commands.bot_has_permissions(manage_webhooks=True)
    async def _channel(self, ctx, *, channel: Optional[discord.TextChannel] = None):
        """Set the channel you want to send events.

        **Example:**
        - `[p]connectset channel #general`
        This will set the event channel to general.

        **Arguments:**
        - `[channel]` - Is where you set the event channel. Leave it blank to disable.
        """
        if channel:
            if not ctx.guild.me.permissions_in(channel).manage_webhooks:
                await ctx.send(f"I cannot manage webhooks in {channel.mention}!")
            else:
                await self.config.statuschannel.set(channel.id)
                await ctx.send(f"Event is now set to {channel.mention}")

        elif await self.config.statuschannel() is not None:
            await self.config.statuschannel.set(None)
            await ctx.send("Event is now disabled")
        else:
            await ctx.send(
                f"Events are already disabled.\nUse `{ctx.clean_prefix}connectset channel #channel` to enable."
            )

    @_connectset.group(name="emoji")
    async def _emoji(self, ctx: commands.Context):
        """Settings to change default emoji.

        Your bot need to share the same server as the emoji you want to set.
        """

    @_emoji.command(name="green", usage="[emoji]")
    async def emoji_green(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ):
        """Change the green emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.green.clear()
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Reset",
                    description=f"Successfully reset back to default.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send("Successfully reset back to default.")
        else:
            await self.config.green.set(str(emoji))
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Changed",
                    description=f"Successfully set your emoji to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send(f"Successfully set your emoji to {emoji}.")

    @_emoji.command(name="orange", usage="[emoji]")
    async def emoji_orange(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ):
        """Change the orange emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.orange.clear()
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Reset",
                    description=f"Successfully reset back to default.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send("Successfully reset back to default.")
        else:
            await self.config.orange.set(str(emoji))
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Changed",
                    description=f"Successfully set your emoji to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send(f"Successfully set your emoji to {emoji}.")

    @_emoji.command(name="red", usage="[emoji]")
    async def emoji_red(
        self, ctx: commands.Context, *, emoji: Optional[RealEmojiConverter] = None
    ):
        """Change the red emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.red.clear()
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Reset",
                    description=f"Successfully reset back to default.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send("Successfully reset back to default.")
        else:
            await self.config.red.set(str(emoji))
            if await ctx.embed_requested():
                em = discord.Embed(
                    title="Emoji Changed",
                    description=f"Successfully set your emoji to {emoji}.",
                    color=await ctx.embed_color(),
                )
                await ctx.reply(embed=em, mention_author=False)
            else:
                await ctx.send(f"Successfully set your emoji to {emoji}.")

    @_connectset.command(name="showsettings", aliases=["settings"])
    async def show_settings(self, ctx: commands.Context):
        """Shows the current settings for OnConnect."""
        config = await self.config.all()
        chan_config = config["statuschannel"]
        channel = f"<#{chan_config}>" if chan_config else "Not set."
        green_emoji = config["green"]
        orange_emoji = config["orange"]
        red_emoji = config["red"]

        em = discord.Embed(
            title="OnConnect Settings:",
            description=f"**Status channel:** {channel}",
            colour=await ctx.embed_colour(),
        )
        em.add_field(name="Green emoji:", value=green_emoji)
        em.add_field(name="Orange emoji:", value=orange_emoji)
        em.add_field(name="Red emoji:", value=red_emoji)
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException as e:
            await ctx.send(embed=em)
            log.info(e)

    @_connectset.command(name="version")
    async def connectset_version(self, ctx: commands.Context):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_colour(),
        )
        await ctx.send(embed=em)
