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

import random
from typing import Any, List

import aiohttp
import discord
from red_commons.logging import getLogger
from redbot.core import commands

from .formatters import create_pokemon_embed

log = getLogger("red.maxcogs.whosthatpokemon.views")


# Credits to flame for the original WhosThatPokemon modal/view design.
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
        self.message = None
        super().__init__(timeout=30.0)

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

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
            if self.message:
                await self.message.edit(view=self)
            try:
                await interaction.followup.send(
                    f"{interaction.user.mention} Guessed the Pokémon correctly!",
                )
            except discord.HTTPException:
                pass
        else:
            try:
                await interaction.followup.send(
                    f"{interaction.user.mention}, Wrong Pokémon name!",
                )
            except discord.HTTPException:
                pass


class HintView(discord.ui.View):
    """Provides a one-time hint button — intended to be added directly to WhosThatPokemonView."""

    def __init__(self, pokemon_data: dict, pokemon_name: str):
        super().__init__(timeout=None)
        self.pokemon_data = pokemon_data
        self.pokemon_name = pokemon_name.lower()
        self.hint_used = False

    @discord.ui.button(label="Get Hint", style=discord.ButtonStyle.primary, emoji="💡")
    async def hint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        reveal_count = min(
            2 if name_length <= 5 else 3 if name_length <= 8 else 4,
            name_length,
        )
        reveal_indices = set(random.sample(range(name_length), reveal_count))
        masked_name = "".join(
            c if i in reveal_indices else "_" for i, c in enumerate(self.pokemon_name)
        )
        hints.append(f"Name: {masked_name}")

        embed = discord.Embed(
            title="Pokémon Hint",
            description="\n".join(hints) if hints else "No hints available!",
            color=0x3F0071,
        )
        embed.set_footer(text="This hint can only be used once per game!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PokemonSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="Base", value="base"),
            discord.SelectOption(label="Held Items", value="held_items"),
            discord.SelectOption(label="Moves", value="moves"),
            discord.SelectOption(label="Locations", value="locations"),
        ]
        super().__init__(
            placeholder="Choose a section...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.current_section = self.values[0]
        await self.parent_view.update_embed(interaction)


class PokemonView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context,
        session: aiohttp.ClientSession,
        pokemon_data: dict,
        timeout=120,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.session = session
        self.pokemon_data = pokemon_data
        self.current_section = "base"
        self.message = None
        self.add_item(PokemonSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You are not the owner of this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    async def update_embed(self, interaction: discord.Interaction) -> None:
        try:
            embed = await create_pokemon_embed(
                self.session, self.pokemon_data, self.current_section
            )
            await interaction.response.edit_message(embed=embed, view=self)
        except ValueError as e:
            await interaction.response.send_message(
                f"Error loading {self.current_section} section.", ephemeral=True
            )
            log.error("Error loading %s section: %s", self.current_section, e)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
        self.stop()
