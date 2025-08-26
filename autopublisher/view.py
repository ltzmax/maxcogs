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


class IgnoredNewsChannelsView(discord.ui.LayoutView):
    def __init__(self, cog: commands.Cog) -> None:
        super().__init__(timeout=180)
        self.cog: commands.Cog = cog
        self.ctx: commands.Context = None
        self.message: discord.Message = None
        self.ignored_channels: typing.List[discord.ForumChannel] = []

        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(
            discord.ui.TextDisplay(
                "Select news channels to ignore/unignore.\n"
                "Use the Confirm button to save changes.\n"
                "Alternatively, use the command with #channel(s) to manage manually."
            )
        )
        self.container.add_item(discord.ui.Separator())
        self.select = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.news],
            placeholder="Select the news channels to ignore.",
            min_values=0,
        )
        self.select.callback = self.select_callback
        self.container.add_item(discord.ui.ActionRow(self.select))
        self.container.add_item(discord.ui.Separator())
        self.confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.success)
        self.confirm_button.callback = self.save_callback
        self.unignore_button = discord.ui.Button(
            label="Unignore", style=discord.ButtonStyle.danger
        )
        self.unignore_button.callback = self.unignore_callback
        self.container.add_item(discord.ui.ActionRow(self.confirm_button, self.unignore_button))
        self.add_item(self.container)

    async def start(self, ctx: commands.Context) -> None:
        self.ctx: commands.Context = ctx
        ignored_ids = await self.cog.config.guild(self.ctx.guild).ignored_channels()
        self.ignored_channels = [
            channel
            for channel_id in ignored_ids
            if (channel := self.ctx.guild.get_channel(channel_id))
        ]
        default_values = [
            discord.SelectDefaultValue(type="channel", id=channel.id)
            for channel in self.ignored_channels
        ]
        self.select.default_values = default_values

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.ctx.author.id] + list(self.ctx.bot.owner_ids):
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        self.select.disabled = True
        self.confirm_button.disabled = True
        self.unignore_button.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(e)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.ignored_channels = self.select.values
        await interaction.followup.send(
            "Click Confirm to save the selected news channels.",
            ephemeral=True,
        )

    async def save_callback(self, interaction: discord.Interaction) -> None:
        new_ignored_channels = [channel.id for channel in self.ignored_channels]
        current_ignored = await self.cog.config.guild(self.ctx.guild).ignored_channels()

        if sorted(new_ignored_channels) == sorted(current_ignored):
            return await interaction.response.send_message(
                "No changes were made.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set(new_ignored_channels)
        await interaction.response.send_message(
            ":white_check_mark: Ignored news channels saved!", ephemeral=True
        )

    async def unignore_callback(self, interaction: discord.Interaction) -> None:
        current_ignored = await self.cog.config.guild(self.ctx.guild).ignored_channels()
        if not current_ignored:
            return await interaction.response.send_message(
                "No news channels are currently ignored.",
                ephemeral=True,
            )

        await self.cog.config.guild(self.ctx.guild).ignored_channels.set([])
        await interaction.response.send_message(
            ":white_check_mark: Ignored news channels removed!", ephemeral=True
        )
        self.ignored_channels = []
        self.select.default_values = []
