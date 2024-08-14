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

import discord
from redbot.core.bot import Red
from redbot.core.config import Config


class ChannelView(discord.ui.View):
    def __init__(self, bot: Red, config: Config, guild_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.config = config
        self.guild_id = guild_id
        self.selected_channel = None
        # Initialize the select menu
        self.select = discord.ui.Select(placeholder="Select a news channel")
        self.select.callback = self.select_callback
        self.set_select_options()
        self.add_item(self.select)
        # Add buttons below the select menu
        self.confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
        self.confirm_button.callback = self.confirm_button_callback
        self.add_item(self.confirm_button)
        self.remove_button = discord.ui.Button(label="Remove", style=discord.ButtonStyle.red)
        self.remove_button.callback = self.remove_button_callback
        self.add_item(self.remove_button)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    def set_select_options(self):
        # This method sets the options for the select menu
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            channels = [channel for channel in guild.text_channels if channel.is_news()]
            self.select.options = [
                discord.SelectOption(label=channel.name, value=str(channel.id))
                for channel in channels
            ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_channel = self.bot.get_channel(int(interaction.data["values"][0]))
        await interaction.response.send_message(
            f"Selected channel: {self.selected_channel}.\n"
            "Click the `Confirm` button to confirm or the `Remove` button to remove from the ignored list.",
            ephemeral=True,
        )

    async def confirm_button_callback(self, interaction: discord.Interaction):
        if self.selected_channel:
            async with self.config.guild_from_id(
                self.guild_id
            ).ignored_channels() as ignored_channels:
                if self.selected_channel.id not in ignored_channels:
                    ignored_channels.append(self.selected_channel.id)
                    await interaction.response.send_message(
                        f"Confirmed and ignored channel: {self.selected_channel}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"Channel {self.selected_channel} is already ignored.",
                        ephemeral=True,
                    )
        else:
            await interaction.response.send_message("No channel selected.", ephemeral=True)

    async def remove_button_callback(self, interaction: discord.Interaction):
        if self.selected_channel:
            async with self.config.guild_from_id(
                self.guild_id
            ).ignored_channels() as ignored_channels:
                if self.selected_channel.id in ignored_channels:
                    ignored_channels.remove(self.selected_channel.id)
                    await interaction.response.send_message(
                        f"Removed channel from ignored list: {self.selected_channel}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"Channel {self.selected_channel} is not in the ignored list.",
                        ephemeral=True,
                    )
        else:
            await interaction.response.send_message("No channel selected.", ephemeral=True)
