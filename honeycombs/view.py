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

import logging
import random

import discord
from redbot.core import bank

log = logging.getLogger("red.maxcogs.honeycombs.view")


class JoinButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(
            custom_id="join_honeycombs", label=label, style=discord.ButtonStyle.blurple
        )

    async def callback(self, interaction: discord.Interaction):
        view: HoneycombView = self.view
        game_state = view.cog.get_game_state(view.guild)
        guild_config = view.cog.get_guild_config(view.guild)
        currency_name = await bank.get_currency_name(interaction.guild)
        winning_price = view.cog.cache["global"]["winning_price"]
        losing_price = view.cog.cache["global"]["losing_price"]
        user_balance = await bank.get_balance(interaction.user)

        if user_balance < winning_price + losing_price:
            return await interaction.response.send_message(
                f"You do not have enough {currency_name} to enter the game.", ephemeral=True
            )

        player_ids = {data["user_id"] for data in game_state.players.values()}
        if interaction.user.id in player_ids:
            for number, data in game_state.players.items():
                if data["user_id"] == interaction.user.id:
                    return await interaction.response.send_message(
                        f"You are already in the game as `Player {number}` with shape {data['shape']}. You cannot leave.",
                        ephemeral=True,
                    )

        if len(game_state.players) >= 456:
            return await interaction.response.send_message(
                "The game is already full. Please wait for the next game to start.", ephemeral=True
            )

        available_numbers = [i for i in range(1, 457) if i not in game_state.players]
        player_number = random.choice(available_numbers)
        shapes = guild_config["shapes"]
        shape = random.choice(shapes)

        game_state.players[player_number] = {
            "user_id": interaction.user.id,
            "shape": shape,
            "passed": None,
            "player_number": player_number,
        }

        view.player_count += 1
        self.label = f"Enter The Game ({view.player_count}/456)"
        try:
            await interaction.response.send_message(
                f"You have joined the game as `Player {player_number}`.\nYour shape is {shape}\nThis message will disappear, but your number and shape are recorded!",
                ephemeral=True,
            )
            await interaction.message.edit(view=view)
        except discord.HTTPException as e:
            log.error(f"Failed to edit message: {e}")


class HoneycombView(discord.ui.LayoutView):
    def __init__(self, cog, guild):
        super().__init__(timeout=120)
        self.cog = cog
        self.guild = guild
        self.player_count = 0

        self.container = discord.ui.Container(accent_color=discord.Color.blurple())
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(
            discord.ui.TextDisplay(
                "Sugar Honeycombs Challenge!"
            )
        )
        self.container.add_item(discord.ui.Separator())
        self.game_details = discord.ui.TextDisplay("")
        self.container.add_item(self.game_details)
        self.container.add_item(discord.ui.Separator())
        self.join_button = JoinButton(label="Enter The Game (0/456)")
        self.container.add_item(discord.ui.ActionRow(self.join_button))
        self.container.add_item(discord.ui.Separator())
        self.add_item(self.container)

    async def setup(self, total_price, currency_name, minimum_players, end_time):
        """Initialize the player count and game details."""
        game_state = self.cog.get_game_state(self.guild)
        self.player_count = len(game_state.players)
        self.join_button.label = f"Enter The Game ({self.player_count}/456)"
        self.game_details.content = (
            f"Price to Enter: {total_price} {currency_name}\n"
            f"Minimum Players: {minimum_players}\n"
            f"Game starts <t:{end_time}:R>"
        )

    async def on_timeout(self):
        """Disable the button on timeout and update the message."""
        for child in self.walk_children():
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(f"Failed to edit message on timeout: {e}")

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item
    ):
        """Handle interaction errors."""
        log.error(
            f"Interaction error for custom_id={interaction.data.get('custom_id')}: {error}",
            exc_info=True,
        )
        await interaction.response.send_message(
            "An error occurred. Please try again.", ephemeral=True
        )
