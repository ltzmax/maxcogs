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


class HoneycombView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=120)
        self.game = game

    async def on_timeout(self):
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(e)

    @discord.ui.button(
        custom_id="join_honeycombs",
        label="Enter The Game (0/456)",
        style=discord.ButtonStyle.blurple,
    )
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        credit_name = await bank.get_currency_name(interaction.guild)
        winning_price = await self.game.config.winning_price()
        losing_price = await self.game.config.losing_price()
        user_balance = await bank.get_balance(interaction.user)
        if user_balance < winning_price + losing_price:
            return await interaction.response.send_message(
                f"You do not have enough {credit_name} to enter the game.", ephemeral=True
            )

        player_data = await self.game.config.guild(interaction.guild).players()
        player_ids = {player["user_id"] for player in player_data.values()}
        if interaction.user.id in player_ids:
            return await interaction.response.send_message(
                "You have already joined the game. You cannot leave.", ephemeral=True
            )

        if len(player_data) >= 456:
            return await interaction.response.send_message(
                "The game is already full. Please wait for the next game to start.", ephemeral=True
            )

        available_numbers = [i for i in range(1, 457) if i not in player_data]
        player_number = random.choice(available_numbers)

        shapes = await self.game.config.guild(interaction.guild).shapes()
        shape = random.choice(shapes)
        player_data[player_number] = {
            "user_id": interaction.user.id,
            "shape": shape,
            "passed": None,
            "player_number": player_number,
        }
        await self.game.config.guild(interaction.guild).players.set(player_data)
        await interaction.response.send_message(
            f"You have joined the game as `Player {player_number}`.\nYou have been assigned the shape {shape}",
            ephemeral=True,
        )
        button.label = f"Enter The Game ({len(player_data)}/{456})"
        await interaction.message.edit(view=self)
