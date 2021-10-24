import logging
from abc import ABC
from datetime import datetime, timezone
from typing import Union

import discord
import psutil
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as chat

from .commands import Commands


log = logging.getLogger("red.maxcogs.onconnect")


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class OnConnect(Commands, commands.Cog, metaclass=CompositeMetaClass):
    """This cog is used to send shard events."""

    __version__ = "0.0.4"
    __author__ = "MAX"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=0x345628097929936898, force_registration=True
        )
        default_global = {
            "statuschannel": None,
            "green": "\N{LARGE GREEN CIRCLE}",
            "orange": "\N{LARGE ORANGE CIRCLE}",
            "red": "\N{LARGE RED CIRCLE}",
        }
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_get_data_for_user(self, *, user_id: int) -> dict:
        """This cog does not story any end user data."""
        return {}

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    async def get_or_fetch_channel(self, channel_id: int):
        # This is based on https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/bot.py#L957
        """Retrieves a channel based on its ID.

        Parameters
        -----------
        channel_id: int
            The id of the channel to retrieve.
        """
        if (channel := self.bot.get_channel(channel_id)) is not None:
            return channel

        return await self.bot.fetch_channel(channel_id)

    async def _send_event_message(
        self, message: str, colour: Union[discord.Colour, int]
    ) -> None:
        """Send an embed message to the set statuschannel.

        Parameters
        -----------
        message: str
            The message to send to the statuschannel.

        colour: Union[discord.Colour, int]
            The colour to set in the embed message.
        """
        channel_config = await self.config.statuschannel()
        if channel_config is None:
            return

        event_embed = discord.Embed(description=message, colour=colour)
        channel = await self.get_or_fetch_channel(channel_id=channel_config)
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name="OnConnect")
        if webhook is None:
            webhook = await channel.create_webhook(name="OnConnect")

        await webhook.send(
            username=self.bot.user.name,
            avatar_url=self.bot.user.avatar_url,
            embed=event_embed,
        )

    @commands.Cog.listener()
    async def on_shard_connect(self, shard_id: int):
        emoji = await self.config.orange()
        message = f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) connected!"
        await self.bot.wait_until_red_ready()
        await self._send_event_message(message=message, colour=discord.Colour.orange())

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int):
        emoji = await self.config.green()
        message = f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) ready!"
        await self.bot.wait_until_red_ready()
        await self._send_event_message(message=message, colour=discord.Colour.green())

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id: int):
        emoji = await self.config.red()
        message = f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) disconnected!"
        await self._send_event_message(message=message, colour=discord.Colour.red())

    @commands.Cog.listener()
    async def on_shard_resumed(self, shard_id: int):
        emoji = await self.config.orange()
        message = f"{emoji} {self.bot.user.name} (Shard ID {shard_id}) resumed!"
        await self.bot.wait_until_red_ready()
        await self._send_event_message(message=message, colour=discord.Colour.orange())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_red_ready()
        process_start = datetime.fromtimestamp(
            psutil.Process().create_time(), tz=timezone.utc
        )
        launch_time = chat.humanize_timedelta(
            timedelta=datetime.now(tz=timezone.utc) - process_start
        )
        message = (
            f"> Launch time: {launch_time}\n\n{self.bot.user.name} is ready to use!"
        )
        await self._send_event_message(message=message, colour=discord.Colour.green())
