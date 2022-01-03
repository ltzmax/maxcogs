import logging
import discord

from .log import log
from .abc import MixinMeta
from typing import Optional
from redbot.core import commands


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
                await ctx.tick()

        elif await self.config.statuschannel() is not None:
            await self.config.statuschannel.set(None)
            await ctx.send("Event is now disabled")
        else:
            await ctx.send("Events are already disabled.")

    @_connectset.group(name="emoji")
    async def _emoji(self, ctx: commands.Context):
        """Settings to change default emoji.

        Your bot need to share the same server as the emoji you want to set.
        """

    @_emoji.command(name="green", usage="[emoji]")
    async def emoji_green(self, ctx: commands.Context, *, emoji: Optional[str] = None):
        """Change the green emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.green.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.green.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

    @_emoji.command(name="orange", usage="[emoji]")
    async def emoji_orange(self, ctx: commands.Context, *, emoji: Optional[str] = None):
        """Change the orange emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.orange.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.orange.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

    @_emoji.command(name="red", usage="[emoji]")
    async def emoji_red(self, ctx: commands.Context, *, emoji: Optional[str] = None):
        """Change the red emoji to your own.

        Leave it blank to reset back to default.
        """
        if not emoji:
            await self.config.red.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.red.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

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
