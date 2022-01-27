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
from typing import Union

import discord
from redbot.core import Config

from .abc import MixinMeta
from .log import log


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
            webhook = await channel.create_webhook(
                name=f"{self.bot.user.name}'s OnConnect"
            )
        else:
            # Based on https://github.com/TheDiscordHistorian/historian-cogs/blob/main/on_connect/cog.py#L45
            usable_webhooks = [webhook for webhook in webhooks if webhook.token]
        if not usable_webhooks:
            webhook = await channel.create_webhook(
                name=f"{self.bot.user.name}'s OnConnect"
            )
        else:
            webhook = usable_webhooks[0]

        await webhook.send(
            username=self.bot.user.name,
            avatar_url=self.bot.user.avatar.url,  # Dpy 2.0.
            embed=event_embed,
        )
