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

import datetime
import logging
import random
import time

import discord
import pytz
from redbot.core import bank, commands
from redbot.core.errors import BalanceTooHigh
from redbot.core.utils.chat_formatting import humanize_number

log = logging.getLogger("red.maxcogs.chest.view")


class ChestView(discord.ui.View):
    def __init__(
        self,
        bot,
        config,
        channel,
    ):
        super().__init__(timeout=30)
        self.bot = bot
        self.config = config
        self.channel = channel
        self.message = None  # Add this line to store the message

    async def init_view(self):
        self.emoji = await self.config.emoji()  # Fetch the emoji from the config
        self.button = discord.ui.Button(
            label="Claim Here!",
            style=discord.ButtonStyle.green,
            emoji=self.emoji,
        )
        self.button.callback = self.button_callback
        self.add_item(self.button)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:  # Check if the message attribute is not None
            await self.message.edit(view=self)

    async def button_callback(self, interaction):
        embed = await self.get_embed()
        max_coins = await self.config.max_coins()
        fail_rate = await self.config.chance()
        toggle = await self.config.toggle()
        default_claim_image = await self.config.default_claim_image()
        default_fail_image = await self.config.default_fail_image()
        eco_name = await bank.get_currency_name(interaction.guild)
        bal = await bank.get_balance(interaction.user)
        chances = random.randint(1, 100)  # Generate a random chance
        if chances <= fail_rate:
            embed.add_field(
                name="Result:",
                value=f"Sorry {interaction.user.mention}, you didn't get any {eco_name} this time!",
                inline=False,
            )
        else:
            coins = random.randint(1, max_coins)
            try:
                await bank.deposit_credits(interaction.user, coins)
            except BalanceTooHigh as e:
                await bank.set_balance(interaction.user, e.max_balance)
                log.info(e)
            embed.add_field(
                name="Winner:",
                value=interaction.user.mention,
                inline=False,
            )
            embed.add_field(
                name=f"You Got:",
                value=f"{humanize_number(coins)} {eco_name}",
                inline=False,
            )
            if not chances <= fail_rate:
                embed.add_field(
                    name="Total Balance:",
                    value=f"Your new balance is now: {humanize_number(bal)}",
                    inline=False,
                )
        next_time = datetime.datetime.now(pytz.utc) + datetime.timedelta(hours=4)
        discord_timestamp = (
            f"<t:{int(next_time.timestamp())}:f> (<t:{int(next_time.timestamp())}:R>)"
        )
        embed.add_field(name="Next Spawn:", value=discord_timestamp, inline=False)
        if toggle:
            embed.set_image(url=default_claim_image if not chances <= fail_rate else default_fail_image)
        self.button.disabled = True
        # Remove the "Click the button to claim free..." text and footer after button click.
        embed.description = ""
        embed.set_footer(text="")
        await interaction.response.edit_message(embed=embed, view=self)

    async def get_embed(self):
        eco_name = await bank.get_currency_name(self.channel.guild)
        toggle = await self.config.toggle()
        default_spawn_image = await self.config.default_spawn_image()
        embed = discord.Embed(
            title="Chest Game",
            description=f"Click the button to claim free {eco_name}!",
            color=0xE91E63,
        )
        if toggle:
            embed.set_image(url=default_spawn_image)
        embed.set_footer(text="You have 30 seconds to Claim!")
        return embed
