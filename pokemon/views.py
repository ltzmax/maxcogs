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

import contextlib
import random

import aiohttp
import discord
from red_commons.logging import getLogger
from redbot.core import commands

from .formatters import (
    PokemonSection,
    _get_official_artwork,
    build_locations_text,
    build_section_text,
)


log = getLogger("red.maxcogs.whosthatpokemon.views")

POKEAPI_FOOTER = "Powered by PokéAPI"


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
    def __init__(self, eligible_names: list[str]) -> None:
        self.eligible_names = eligible_names
        self.winner = None
        self.message = None
        super().__init__(timeout=30.0)

    async def on_timeout(self) -> None:
        if self.winner is not None:
            return
        for item in self.children:
            item.disabled = True
        if self.message:
            with contextlib.suppress(discord.HTTPException):
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
            button.disabled = True
            button.label = "Correct Pokémon Guessed"
            button.style = discord.ButtonStyle.success
            if self.message:
                await self.message.edit(view=self)
            with contextlib.suppress(discord.HTTPException):
                await interaction.followup.send(
                    f"{interaction.user.mention} Guessed the Pokémon correctly!",
                )
        else:
            with contextlib.suppress(discord.HTTPException):
                await interaction.followup.send(
                    f"{interaction.user.mention}, Wrong Pokémon name!",
                )


class HintButton(discord.ui.Button):
    """One-time hint button, used directly inside WhosThatPokemonView."""

    def __init__(self, pokemon_data: dict, pokemon_name: str):
        super().__init__(label="Get Hint", style=discord.ButtonStyle.primary, emoji="💡")
        self.pokemon_data = pokemon_data
        self.pokemon_name = pokemon_name.lower()
        self.hint_used = False

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.hint_used:
            return await interaction.response.send_message(
                "The hint has already been used!", ephemeral=True
            )

        self.hint_used = True
        self.disabled = True
        if self.view and self.view.message:
            with contextlib.suppress(discord.HTTPException):
                await self.view.message.edit(view=self.view)

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
            characteristics.append(f"Height: {height / 10:.1f}m")
        if weight := pokemon_data.get("weight"):
            characteristics.append(f"Weight: {weight / 10:.1f}kg")
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


def _build_pokemon_container(
    pokemon_data: dict,
    section: PokemonSection,
    section_text: str,
    accent_colour: discord.Colour,
) -> discord.ui.Container:
    """Build a Components v2 Container for a Pokémon section."""
    name = pokemon_data["name"].capitalize()
    sprites = pokemon_data.get("sprites", {})
    thumbnail_url = sprites.get("front_default")
    poke_id = pokemon_data.get("id", "Unknown")

    header_text = f"## {name} - {section.capitalize()}"
    footer_text = f"-# {POKEAPI_FOOTER} | Pokémon ID: {poke_id}"

    components = []

    if thumbnail_url:
        components.append(
            discord.ui.Section(
                discord.ui.TextDisplay(header_text),
                accessory=discord.ui.Thumbnail(thumbnail_url),
            )
        )
    else:
        components.append(discord.ui.TextDisplay(header_text))

    components.append(discord.ui.Separator())
    components.append(discord.ui.TextDisplay(section_text))
    components.append(discord.ui.Separator())
    components.append(discord.ui.TextDisplay(footer_text))

    return discord.ui.Container(*components, accent_colour=accent_colour)


class _PokemonCloseBtn(discord.ui.Button):
    def __init__(self, pokemon_view: "PokemonView", disabled: bool = False):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, disabled=disabled)
        self.pokemon_view = pokemon_view

    async def callback(self, interaction: discord.Interaction):
        self.pokemon_view._build_content(disabled=True)
        await interaction.response.edit_message(view=self.pokemon_view)
        self.pokemon_view.stop()


class PokemonSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Base", value=PokemonSection.BASE),
            discord.SelectOption(label="Held Items", value=PokemonSection.HELD_ITEMS),
            discord.SelectOption(label="Moves", value=PokemonSection.MOVES),
            discord.SelectOption(label="Locations", value=PokemonSection.LOCATIONS),
        ]
        super().__init__(
            placeholder="Choose a section...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.current_section = PokemonSection(self.values[0])
        await self.view.update_view(interaction)


class PokemonView(discord.ui.LayoutView):
    def __init__(
        self,
        ctx: commands.Context,
        session: aiohttp.ClientSession,
        pokemon_data: dict,
        accent_colour: discord.Colour,
        timeout: int = 120,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.session = session
        self.pokemon_data = pokemon_data
        self.accent_colour = accent_colour
        self.current_section = PokemonSection.BASE
        self.message = None
        self._last_section_text = ""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You are not the owner of this interaction.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message:
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.message.edit(view=self._build_disabled_view())

    def _build_disabled_view(self) -> "PokemonView":
        """Return a copy of this view with all interactive items disabled."""
        disabled = PokemonView(
            self.ctx, self.session, self.pokemon_data, self.accent_colour, timeout=0
        )
        disabled._build_content(disabled=True)
        return disabled

    def _build_content(self, section_text: str = "", disabled: bool = False):
        """Rebuild the view's container and controls."""
        self.clear_items()

        select = PokemonSelect()
        select.disabled = disabled
        for opt in select.options:
            opt.default = opt.value == self.current_section

        close_btn = _PokemonCloseBtn(self, disabled=disabled)

        if section_text:
            self._last_section_text = section_text

        container = _build_pokemon_container(
            self.pokemon_data,
            self.current_section,
            self._last_section_text or "No content available.",
            self.accent_colour,
        )
        container.add_item(discord.ui.ActionRow(select))
        container.add_item(discord.ui.ActionRow(close_btn))
        self.add_item(container)

    async def update_view(self, interaction: discord.Interaction) -> None:
        """Fetch section content and edit the message."""
        try:
            match self.current_section:
                case PokemonSection.LOCATIONS:
                    section_text = await build_locations_text(self.session, self.pokemon_data)
                case _:
                    section_text = build_section_text(self.pokemon_data, self.current_section)
        except ValueError as e:
            log.error("Error loading %s section: %s", self.current_section, e)
            return await interaction.response.send_message(
                f"Error loading {self.current_section} section.", ephemeral=True
            )

        self._build_content(section_text)
        await interaction.response.edit_message(view=self)

    async def send_initial(self, ctx: commands.Context) -> None:
        """Build the initial base section and send the message."""
        section_text = build_section_text(self.pokemon_data, PokemonSection.BASE)
        self._build_content(section_text)
        self.message = await ctx.send(view=self)


# ── TCG Card Views ────────────────────────────────────────────────────────────

class _GoToPageModal(discord.ui.Modal, title="Go to Page"):
    page: discord.ui.TextInput = discord.ui.TextInput(
        label="Page Number",
        placeholder="Enter a page number...",
        max_length=4,
        required=True,
    )

    def __init__(self, card_view: "TcgCardView"):
        super().__init__()
        self.card_view = card_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        total = len(self.card_view.cards)
        try:
            page = int(self.page.value)
        except ValueError:
            return await interaction.response.send_message(
                "Please enter a valid number.", ephemeral=True
            )
        if not 1 <= page <= total:
            return await interaction.response.send_message(
                f"Page must be between 1 and {total}.", ephemeral=True
            )
        self.card_view.current = page - 1
        self.card_view._build_content()
        await interaction.response.edit_message(view=self.card_view)


class _GoToPageBtn(discord.ui.Button):
    def __init__(self, card_view: "TcgCardView", disabled: bool = False):
        super().__init__(
            label="Go to Page",
            style=discord.ButtonStyle.secondary,
            emoji="🔢",
            disabled=disabled,
        )
        self.card_view = card_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(_GoToPageModal(self.card_view))


class _NavBtn(discord.ui.Button):
    def __init__(self, direction: str, card_view: "TcgCardView", disabled: bool = False):
        match direction:
            case "prev":
                label, emoji = "Previous", "◀️"
            case "next":
                label, emoji = "Next", "▶️"
        super().__init__(
            label=label, emoji=emoji,
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.direction = direction
        self.card_view = card_view

    async def callback(self, interaction: discord.Interaction):
        match self.direction:
            case "prev" if self.card_view.current > 0:
                self.card_view.current -= 1
            case "next" if self.card_view.current < len(self.card_view.cards) - 1:
                self.card_view.current += 1
        self.card_view._build_content()
        await interaction.response.edit_message(view=self.card_view)


class _CloseBtn(discord.ui.Button):
    def __init__(self, card_view: "TcgCardView", disabled: bool = False):
        super().__init__(label="Close", style=discord.ButtonStyle.danger, disabled=disabled)
        self.card_view = card_view

    async def callback(self, interaction: discord.Interaction):
        self.card_view._build_content(disabled=True)
        await interaction.response.edit_message(view=self.card_view)
        self.card_view.stop()


class TcgCardView(discord.ui.LayoutView):
    """Components v2 paginated view for TCG cards."""

    def __init__(
        self,
        ctx: commands.Context,
        cards: list[dict],
        card_text_builder,
        accent_colour: discord.Colour,
        timeout: int = 120,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.cards = cards
        self.card_text_builder = card_text_builder
        self.accent_colour = accent_colour
        self.current = 0
        self.message = None
        self._build_content()

    def _build_content(self, disabled: bool = False):
        """Rebuild the container with current card and nav buttons."""
        self.clear_items()
        data = self.cards[self.current]
        card_name = data["name"]
        hp = data.get("hp", "N/A")
        card_image = str(data["images"]["large"])
        set_logo = str(data["set"]["images"]["logo"])
        total = len(self.cards)

        header_text = f"## {card_name} - HP: {hp}"
        footer_text = f"-# Card {self.current + 1} of {total} · Powered by Pokémon TCG API"
        card_text = self.card_text_builder(data)

        nav_row = discord.ui.ActionRow()
        if self.current > 0:
            nav_row.add_item(_NavBtn("prev", self, disabled=disabled))
        if self.current < total - 1:
            nav_row.add_item(_NavBtn("next", self, disabled=disabled))
        if total > 1:
            nav_row.add_item(_GoToPageBtn(self, disabled=disabled))

        close_btn = _CloseBtn(self, disabled=disabled)

        components = [
            discord.ui.Section(
                discord.ui.TextDisplay(header_text),
                accessory=discord.ui.Thumbnail(set_logo),
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(card_text),
            discord.ui.Separator(),
            discord.ui.MediaGallery(
                discord.MediaGalleryItem(card_image, description=f"{card_name} card"),
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(footer_text),
            discord.ui.ActionRow(close_btn),
        ]
        if nav_row.children:
            components.append(nav_row)

        self.add_item(discord.ui.Container(*components, accent_colour=self.accent_colour))

    async def on_timeout(self):
        self._build_content(disabled=True)
        if self.message:
            with contextlib.suppress(discord.NotFound, discord.HTTPException):
                await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You are not the owner of this interaction.", ephemeral=True
            )
            return False
        return True
