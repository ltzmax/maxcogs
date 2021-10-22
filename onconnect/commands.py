import discord
import logging

from .abc import MixinMeta
from redbot.core import commands, Config

log = logging.getLogger("red.maxcogs.onconnect")


class Commands(MixinMeta):
    """The commands are stored here."""

    @commands.is_owner()
    @commands.group(name="connectset")
    async def _connectset(self, ctx):
        """Settings to set channel to send events."""

    @_connectset.command(name="channel", usage="[channel]")
    async def _channel(self, ctx, *, channel: discord.TextChannel = None):
        """Set the channel you want to send events.

        Leave it blank to disable.

        **Example:**
        - `[p]connectset channel #general` - This will set the event channel to general.

        **Arguments:**
        - `[channel]` is where you set the event channel.
        """
        config = await self.config.statuschannel()
        if config is None:
            await self.config.statuschannel.set(channel.id)
            await ctx.send(f"Event is now set to {channel.mention}")
            log.info("Events is successfully set.")
        else:
            await self.config.statuschannel.set(None)
            await ctx.send("Event is now disabled")
            log.info("Events is successfully disabled.")

    @_connectset.group(name="emoji")
    async def emoji(self, ctx):
        """Settings to change default emoji.

        Your bot need to share the same server as the emoji you want to set."""

    @emoji.command(name="green", usage="[emoji]")
    async def emoji_green(self, ctx: commands.Context, *, emoji: str = None):
        """Change the green emoji to your own.

        Leave it blank to reset back to default."""
        if not emoji:
            await self.config.green.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.green.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

    @emoji.command(name="yellow", usage="[emoji]")
    async def emoji_yellow(self, ctx: commands.Context, *, emoji: str = None):
        """Change the yellow emoji to your own.

        Leave it blank to reset back to default."""
        if not emoji:
            await self.config.yellow.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.yellow.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

    @emoji.command(name="red", usage="[emoji]")
    async def emoji_red(self, ctx: commands.Context, *, emoji: str = None):
        """Change the red emoji to your own.

        Leave it blank to reset back to default."""
        if not emoji:
            await self.config.red.clear()
            await ctx.send("Successfully reset back to default.")
        else:
            await self.config.red.set(emoji)
            await ctx.send(f"Successfully set your emoji to {emoji}.")
            await ctx.tick()

    @_connectset.command(aliases=["settings"])
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def showsettings(self, ctx: commands.Context):
        """Shows the current settings."""
        config = await self.config.statuschannel()
        green = await self.config.green()
        yellow = await self.config.yellow()
        red = await self.config.red()

        em = discord.Embed(
            title="Settings:",
            color=await ctx.embed_colour(),
        )
        em.add_field(name="Channel set:", value=config, inline=False)
        em.add_field(name="Green emoji:", value=green)
        em.add_field(name="Yellow emoji:", value=yellow)
        em.add_field(name="Red emoji:", value=red)
        try:
            await ctx.reply(embed=em, mention_author=False)
        except discord.HTTPException as e:
            await ctx.send(embed=em)
            log.info(e)
