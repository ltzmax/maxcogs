import discord

from .log import log
from typing import Union
from .abc import MixinMeta
from redbot.core import Config


class Events(MixinMeta):
    """Events."""

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

        try:
            channel = await self.get_or_fetch_channel(channel_id=channel_config)
        except discord.NotFound as e:
            if await self.config.statuschannel() is not None:
                await self.config.statuschannel.clear()
                log.error(f"Statuschannel not found, deleting ID from config. {e}")

            return

        event_embed = discord.Embed(description=message, colour=colour)
        webhooks = await channel.webhooks()
        if not webhooks:
            webhook = await channel.create_webhook(name="OnConnect")
        else:
            usable_webhooks = [
                w for w in webhooks if w.token
            ]  # Based on https://github.com/TheDiscordHistorian/historian-cogs/blob/main/on_connect/cog.py#L45
            if not usable_webhooks:
                webhook = await channel.create_webhook(name="OnConnect")
            else:
                webhook = usable_webhooks[0]

        await webhook.send(
            username=self.bot.user.name,
            avatar_url=self.bot.user.avatar_url,
            embed=event_embed,
        )
