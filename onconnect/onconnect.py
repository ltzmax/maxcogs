from datetime import datetime, timezone

import logging
import aiohttp
import discord
import psutil
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as chat

log = logging.getLogger("red.maxcogs.onconnect")


class OnConnect(commands.Cog):
    """This cog is used to send shard events."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=0x345628097929936898, force_registration=True
        )
        default_global = {
            "statuschannel": None,
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.0.2"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        config = await self.config.statuschannel()
        if config is None:
            return
        embed = discord.Embed(
            color=0x008800,
            description=f"\N{LARGE GREEN CIRCLE} {self.bot.user.name} (Shard ID {shard_id}) ready!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        config = await self.config.statuschannel()
        if config is None:
            return
        embed = discord.Embed(
            color=discord.Color.red(),
            description=f"\N{LARGE RED CIRCLE} {self.bot.user.name} (Shard ID {shard_id}) disconnected!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)

    @commands.Cog.listener()
    async def on_shard_resumed(self, shard_id: int):
        config = await self.config.statuschannel()
        if config is None:
            return
        embed = discord.Embed(
            color=0x008800,
            description=f"\N{LARGE YELLOW CIRCLE} {self.bot.user.name} (Shard ID {shard_id}) resumed!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)

    @commands.Cog.listener()
    async def on_ready(self):
        config = await self.config.statuschannel()
        if config is None:
            return
        await self.bot.wait_until_red_ready()
        process_start = datetime.fromtimestamp(
            psutil.Process().create_time(), tz=timezone.utc
        )
        embed = discord.Embed(color=0x008800)
        embed.description = f"> Launch time: {chat.humanize_timedelta(timedelta=datetime.now(tz=timezone.utc) - process_start)}\n\n{self.bot.user.name} is ready to use!"
        embed.timestamp = datetime.utcnow()
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("I ran into an issue, check console for details.")
            log.error(e)

    @commands.is_owner()
    @commands.group(name="connectset")
    async def _connectset(self, ctx):
        """Settings to set channel to send events."""

    @_connectset.command(name="channel", usage="[channel]")
    async def _channel(self, ctx, *, channel: discord.TextChannel = None):
        """Set the channel you want to send events.

        Leave it blank to reset.

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

    @_connectset.command(aliases=["settings"])
    async def showsettings(self, ctx: commands.Context):
        """Shows settings for current channel set."""
        config = await self.config.statuschannel()
        await ctx.send("Setting:\n" f"Channel: <#{config}>")
