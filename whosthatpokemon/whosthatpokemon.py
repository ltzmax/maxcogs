# This cog did not have a license.
# This cog was created by owocado and is now continued by ltzmax.
# This cog was transfered via a pr from the author of the code https://github.com/ltzmax/maxcogs/pull/46
import asyncio
from contextlib import suppress
from io import BytesIO
from random import randint
from typing import List, Optional
from datetime import datetime, timezone, timedelta

import aiohttp
import discord
from discord import File
from PIL import Image
from redbot.core import commands, app_commands
from redbot.core.bot import Red
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import box
from redbot.core.data_manager import bundled_data_path

from .converter import Generation

API_URL = "https://pokeapi.co/api/v2"

# All credited to flame for doing the view and modal.
# https://discord.com/channels/133049272517001216/133251234164375552/1104515319604723762
class WhosPokemonModal(discord.ui.Modal, title='Whos That Pokemon?'):
    poke = discord.ui.TextInput(
        label='Pokemon',
        placeholder='Enter the pokemon here...',
        max_length="30",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"You guessed {self.poke.value}!",
            ephemeral=True,
        )

class GuessButton(discord.ui.View):
    def __init__(self, eligible_names, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.eligible_names = eligible_names
        self.winner = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def disable_items(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Guess The Pokémon", style=discord.ButtonStyle.blurple)
    async def guess(self, interaction, button):
        modal = WhosPokemonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.poke.value.casefold() in self.eligible_names and self.winner is None:
            self.winner = interaction.user
            self.stop()
            button.disabled = True
            await interaction.response.edit_message(view=self)

    async def on_error(self, interaction, error, item):
        await ctx.send(error)

class WhosThatPokemon(commands.Cog):
    """Can you guess Who's That Pokémon?"""

    __author__ = "<@306810730055729152>", "MAX#1000"
    __version__ = "1.2.1"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/whosthatpokemon/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    async def get_data(self, url: str):
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {"http_code": response.status}
                return await response.json()
        except asyncio.TimeoutError:
            return {"http_code": 408}

    async def generate_image(self, poke_id: str, *, hide: bool):
        base_image = Image.open(bundled_data_path(self) / "template.webp").convert(
            "RGBA"
        )
        bg_width, bg_height = base_image.size
        base_url = (
            f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{poke_id}.png"
        )
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

    @commands.command(name="wtpversion", hidden=True)
    async def whosthatpokemon_version(self, ctx: commands.Context):
        """Shows the version of the cog"""
        version = self.__version__
        author = self.__author__
        await ctx.send(
            box(f"{'Author':<10}: {author}\n{'Version':<10}: {version}", lang="yaml")
        )

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(
        generation=("Optionally choose generation from gen1 to gen8.")
    )
    @app_commands.choices(
        generation=[
            app_commands.Choice(name="Generation 1", value="gen1"),
            app_commands.Choice(name="Generation 2", value="gen2"),
            app_commands.Choice(name="Generation 3", value="gen3"),
            app_commands.Choice(name="Generation 4", value="gen4"),
            app_commands.Choice(name="Generation 5", value="gen5"),
            app_commands.Choice(name="Generation 6", value="gen6"),
            app_commands.Choice(name="Generation 7", value="gen7"),
            app_commands.Choice(name="Generation 8", value="gen8"),
        ]
    )
    @commands.cooldown(1, 40, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def whosthatpokemon(
        self, ctx: Context, generation: Optional[Generation] = None
    ):
        """Guess Who's that Pokémon in 30 seconds!

        You can optionally specify generation from `gen1` to `gen8` only,
        to restrict this guessing game to specific Pokemon generation.

        Otherwise, it will default to pulling random pokemon from gen 1 to gen 8.

        **Example:**
        - `[p]whosthatpokemon` - This will start a new Generation.
        - `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.

        **Arguments:**
        - `[generation]` - Where you choose any generation from gen 1 to gen 8.
        """
        await ctx.typing()
        poke_id = generation or randint(1, 898)

        temp = await self.generate_image(f"{poke_id:>03}", hide=True)
        if temp is None:
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        # Took this from Core's event file.
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/41d89c7b54a1f231a01f79655c20d4acf1799633/redbot/core/_events.py#L424-L426
        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(seconds=30.0), "R"
        )
        species_data = await self.get_data(f"{API_URL}/pokemon-species/{poke_id}")
        if species_data.get("http_code"):
            return await ctx.send("Failed to get species data from PokeAPI.")
        names_data = species_data.get("names", [{}])
        eligible_names = [x["name"].lower() for x in names_data]
        english_name = [x["name"] for x in names_data if x["language"]["name"] == "en"][
            0
        ]

        revealed = await self.generate_image(f"{poke_id:>03}", hide=False)
        revealed_img = File(revealed, "whosthatpokemon.png")

        view = GuessButton(eligible_names)

        view.message = await ctx.send(
            f"**Who's that Pokémon?**\nThis will timeout {img_timeout}.",
            file=File(temp, "guessthatpokemon.png"), view=view,
        )

        emb = discord.Embed(description=f"It was ... **{english_name}**")
        emb.title = "🎉 You guessed it right!! 🎉"
        emb.colour = 0x00FF00
        emb.set_image(url="attachment://whosthatpokemon.png")
        emb.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        timeout = await view.wait()
        if timeout:
            return await ctx.send(f"This has timedout, it was... **{english_name}**", file=revealed_img, view=None)
        await ctx.send(embed=emb, file=revealed_img)
