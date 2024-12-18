"""
MIT License

Copyright (c) 2024-present AAA3A
Copyright (c) 2022-2024 ltzmax

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
import typing

import discord
from redbot.core import commands

log = logging.getLogger("red.maxcogs.autopublisher.view")


# Credit: AAA3A for the original code and idea of this view.py file.
# https://discord.com/channels/133049272517001216/133251234164375552/1280854205497737216
class IgnoredNewsChannelsView(discord.ui.View):
    def __init__(self, cog: commands.Cog) -> None:
        super().__init__(timeout=180)
        self.cog: commands.Cog = cog
        self.ctx: commands.Context = None
        self.message: discord.Message = None
        self.ignored_channels: typing.List[discord.ForumChannel] = []

    async def start(self, ctx: commands.Context) -> None:
        self.ctx: commands.Context = ctx
        self.ignored_channels: typing.List[discord.ForumChannel] = [
            channel
            for channel_id in await self.cog.config.guild(self.ctx.guild).ignored_channels()
            if (channel := self.ctx.guild.get_channel(channel_id))
        ]
        self.select.default_values = self.ignored_channels

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id] + list(self.ctx.bot.owner_ids):
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(e)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.news],
        min_values=0,
        placeholder="Select the news channels to ignore.",
    )
    async def select(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ) -> None:
        await interaction.response.defer()
        selected_channels = select.values
        current_ignored_channels = await self.cog.config.guild(self.ctx.guild).ignored_channels()

        for channel in selected_channels:
            if channel.id in current_ignored_channels:
                current_ignored_channels.remove(channel.id)
            else:
                current_ignored_channels.append(channel.id)
        self.ignored_channels = [
            self.ctx.guild.get_channel(channel_id) for channel_id in current_ignored_channels
        ]

        await interaction.followup.send(
            f"Click on the button to Confirm the selected news channels.",
            ephemeral=True,
        )

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        new_ignored_channels = [channel.id for channel in self.ignored_channels]

        # Check if the channel is already ignored
        if new_ignored_channels == await self.cog.config.guild(self.ctx.guild).ignored_channels():
            return await interaction.response.send_message(
                "No changes were made because the selected news channel is already ignored.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set(new_ignored_channels)
        await interaction.response.send_message(
            ":white_check_mark: Ignored news channels saved!", ephemeral=True
        )

    @discord.ui.button(label="Unignore", style=discord.ButtonStyle.danger)
    async def unignore(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.ignored_channels not in self.cog.config.guild(self.ctx.guild).ignored_channels():
            return await interaction.response.send_message(
                "No changes were made because the selected news channel is not ignored.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set([])
        await interaction.response.send_message(
            ":white_check_mark: Ignored news channels removed!", ephemeral=True
        )
