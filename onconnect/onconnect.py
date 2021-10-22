from datetime import datetime, timezone

import logging
import aiohttp
import discord
import psutil
from abc import ABC
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as chat

from .commands import Commands

log = logging.getLogger("red.maxcogs.onconnect")

GREEN = "\N{LARGE GREEN CIRCLE}"
YELLOW = "\N{LARGE YELLOW CIRCLE}"
RED = "\N{LARGE RED CIRCLE}"

STATUSCHANNEL = "None"


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class OnConnect(
    Commands,
    commands.Cog,
    metaclass=CompositeMetaClass,
):
    """This cog is used to send shard events."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=0x345628097929936898, force_registration=True
        )
        self.config.register_global(
            statuschannel=STATUSCHANNEL,
            green=GREEN,
            yellow=YELLOW,
            red=RED,
        )
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.0.3"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    # -------- EVENTS ----------

    # Still missing on_shard_connect and on_connect. but they fail to send.
    # They will need webhook support as they use that 99% of time.
    # PR's are welcome to add that since i won't have time in a while for this.

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        config = await self.config.statuschannel()
        emoji = await self.config.green()
        if config is None:
            return
        embed = discord.Embed(
            color=0x008800,
            description=f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) ready!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        config = await self.config.statuschannel()
        emoji = await self.config.red()
        if config is None:
            return
        embed = discord.Embed(
            color=discord.Color.red(),
            description=f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) disconnected!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)

    @commands.Cog.listener()
    async def on_shard_resumed(self, shard_id: int):
        config = await self.config.statuschannel()
        emoji = await self.config.yellow()
        if config is None:
            return
        embed = discord.Embed(
            color=0x008800,
            description=f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) resumed!",
        )
        channel = self.bot.get_channel(config)
        try:
            await channel.send(embed=embed)
        except AttributeError as e:
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("Something went wrong, Check console for details.")
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
            log.error(e)
        except discord.Forbidden as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)
        except discord.HTTPException as e:
            await channel.send("Something went wrong, Check console for details.")
            log.error(e)
