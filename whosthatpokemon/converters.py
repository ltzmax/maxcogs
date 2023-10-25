"""
MIT License

Copyright (c) 2023-present ltzmax

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

import asyncio
from io import BytesIO
from typing import Any, Dict, Optional, List
from PIL import Image
from random import randint
from redbot.core import commands
from redbot.core.data_manager import bundled_data_path

# This is for my whosthatpokemon cog.
# https://github.com/ltzmax/maxcogs/tree/master/whosthatpokemon


class Generation(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        allowed_gens = [f"gen{x}" for x in range(1, 9)]
        if argument.lower() not in allowed_gens:
            ctx.command.reset_cooldown(ctx)
            raise commands.BadArgument("Only `gen1` to `gen8` values are allowed.")

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
            return randint(810, 898)


async def get_data(self, url: str) -> Dict[str, Any]:
    try:
        async with self.session.get(url) as response:
            if response.status != 200:
                self.log.error(
                    f"Failed to get data from {url} with status code {response.status}"
                )
                return {"http_code": response.status}
            return await response.json()
    except asyncio.TimeoutError:
        self.log.error(f"Request to {url} timed out.")
        return {"http_code": 408}


async def generate_image(self, poke_id: str, *, hide: bool) -> Optional[BytesIO]:
    base_image = Image.open(bundled_data_path(self) / "template.webp").convert("RGBA")
    bg_width, bg_height = base_image.size
    base_url = f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{poke_id}.png"
    try:
        async with self.session.get(base_url) as response:
            if response.status != 200:
                return None
            data = await response.read()
    except asyncio.TimeoutError:
        return None
    pbytes = BytesIO(data)
    poke_image = Image.open(pbytes)
    poke_width, poke_height = poke_image.size
    poke_image_resized = poke_image.resize(
        (int(poke_width * 1.6), int(poke_height * 1.6))
    )

    if hide:
        p_load = poke_image_resized.load()  # type: ignore
        for y in range(poke_image_resized.size[1]):
            for x in range(poke_image_resized.size[0]):
                if p_load[x, y] == (0, 0, 0, 0):  # type: ignore
                    continue
                p_load[x, y] = (1, 1, 1)  # type: ignore

    paste_w = int((bg_width - poke_width) / 10)
    paste_h = int((bg_height - poke_height) / 4)

    base_image.paste(poke_image_resized, (paste_w, paste_h), poke_image_resized)
    temp = BytesIO()
    base_image.save(temp, "png")
    temp.seek(0)
    pbytes.close()
    base_image.close()
    poke_image.close()
    return temp


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
        await interaction.response.send_message(
            f"You guessed: {self.poke.value}",
            ephemeral=True,
        )


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
    async def guess_the_pokemon(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = WhosThatPokemonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.poke.value.casefold() in self.eligible_names and self.winner is None:
            self.winner = interaction.user
            self.stop()

            # Disable the button after a correct response
            button.disabled = True
            button.label = "Correct Pokémon Guessed"
            button.style = discord.ButtonStyle.success
            await self.message.edit(view=self)
            # Send a message indicating who guessed the Pokémon
            await interaction.followup.send(
                f"{interaction.user.mention} guessed the Pokémon correctly!",
            )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await interaction.response.send_message(
            f"An error occured: {error}", ephemeral=True
        )
