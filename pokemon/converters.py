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

import asyncio
import logging
import random
from random import randint
from typing import Any, Dict, List, Optional

import discord
from redbot.core import commands

log = logging.getLogger("red.maxcogs.whosthatpokemon.converters")


class Generation(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        allowed_gens = [f"gen{x}" for x in range(1, 10)]
        if argument.lower() not in allowed_gens:
            ctx.command.reset_cooldown(ctx)
            raise commands.BadArgument("Only `gen1` to `gen9` values are allowed.")

        if argument.lower() == "gen1":
            return randint(1, 151)
        elif argument.lower() == "gen2":
            return randint(152, 251)
        elif argument.lower() == "gen3":
            return randint(252, 386)
        elif argument.lower() == "gen4":
            return randint(387, 493)
        elif argument.lower() == "gen5":
            return randint(494, 649)
        elif argument.lower() == "gen6":
            return randint(650, 721)
        elif argument.lower() == "gen7":
            return randint(722, 809)
        elif argument.lower() == "gen8":
            return randint(810, 905)
        elif argument.lower() == "gen9":
            return randint(906, 1010)


async def get_data(self, url: str) -> Dict[str, Any]:
    try:
        async with self.session.get(url) as response:
            if response.status != 200:
                return {"http_code": response.status}
                log.error(f"Failed to get data from {url} with status code {response.status}")
            return await response.json()
    except asyncio.TimeoutError:
        log.error(f"Failed to get data from {url} due to timeout")
        return {"http_code": 408}


# Mainly flame who build this view and modal. All credits goes to flame for that work.
# https://discord.com/channels/133049272517001216/133251234164375552/1104515319604723762
class WhosThatPokemonModal(discord.ui.Modal, title="Whos That Pokémon?"):
    poke: discord.ui.TextInput = discord.ui.TextInput(
        label="Pokémon",
        placeholder="Enter the pokémon here...",
        max_length=14,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class WhosThatPokemonView(discord.ui.View):
    def __init__(self, eligible_names: List[Any]) -> None:
        self.eligible_names = eligible_names
        self.winner = None
        super().__init__(timeout=30.0)

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label="Guess The Pokémon", style=discord.ButtonStyle.blurple)
    async def guess_the_pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = WhosThatPokemonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.poke.value.casefold() in self.eligible_names and self.winner is None:
            self.winner = interaction.user
            self.stop()

            button.disabled = True
            button.label = "Correct Pokémon Guessed"
            button.style = discord.ButtonStyle.success
            await self.message.edit(view=self)
            await interaction.followup.send(
                f"{interaction.user.mention} Guessed the Pokémon correctly!",
            )
        else:
            await interaction.followup.send(
                f"{interaction.user.mention}, Wrong Pokémon name!",
            )


class HintView(discord.ui.View):
    """A view that provides a one-time hint for Who's That Pokémon game."""

    def __init__(self, pokemon_data: dict, parent_view: "WhosThatPokemonView", pokemon_name: str):
        super().__init__(timeout=None)
        self.pokemon_data = pokemon_data
        self.parent_view = parent_view
        self.pokemon_name = pokemon_name.lower()
        self.hint_used = False

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.id == self.user.id:
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Get Hint", style=discord.ButtonStyle.primary, emoji="💡")
    async def hint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the hint button click."""
        if self.hint_used:
            return await interaction.response.send_message(
                "The hint has already been used!", ephemeral=True
            )

        self.hint_used = True
        button.disabled = True
        species_data = self.pokemon_data.get("species_data", {})
        pokemon_data = self.pokemon_data.get("pokemon_data", {})

        hints = []

        if types := pokemon_data.get("types", []):
            type_names = [t["type"]["name"].capitalize() for t in types]
            hints.append(f"Type: {', '.join(type_names)}")

        if generation := species_data.get("generation", {}).get("name"):
            gen_number = generation.replace("generation-", "").upper()
            hints.append(f"Generation: {gen_number}")

        characteristics = []
        if height := pokemon_data.get("height"):
            characteristics.append(f"Height: {height/10:.1f}m")
        if weight := pokemon_data.get("weight"):
            characteristics.append(f"Weight: {weight/10:.1f}kg")
        if characteristics:
            hints.append(random.choice(characteristics))

        name_length = len(self.pokemon_name)
        if name_length <= 5:
            reveal_count = 2
        elif name_length <= 8:
            reveal_count = 3
        else:
            reveal_count = 4

        reveal_count = min(reveal_count, name_length)
        reveal_indices = random.sample(range(name_length), reveal_count)

        masked_name = ""
        for i in range(name_length):
            if i in reveal_indices:
                masked_name += self.pokemon_name[i]
            else:
                masked_name += "_"
        hints.append(f"Name: {masked_name}")
        hint_text = "\n".join(hints) if hints else "No hints available!"

        embed = discord.Embed(
            title="Pokémon Hint",
            description=hint_text,
            color=0x3F0071,
        )
        embed.set_footer(text="This hint can only be used once per game!")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.message.edit(view=self.parent_view)
