from logging import LoggerAdapter
from typing import Any, List

import discord
from red_commons.logging import RedTraceLogger, getLogger

log: RedTraceLogger = getLogger("red.maxcogs.whosthatpokemon.view")


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
            f"You entered: {self.poke.value}", ephemeral=True
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
                f"{self.winner.display_name} guessed the Pokémon correctly!"
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
        log.error("Error in WhosThatPokemonView: %s", error, exc_info=True)
