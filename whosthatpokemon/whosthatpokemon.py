import asyncio
from contextlib import suppress
from io import BytesIO
from random import randint
from typing import Optional

import aiohttp
import discord
from discord import Colour, Embed, File
from PIL import Image
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import Context
from redbot.core.data_manager import bundled_data_path

from .converter import Generation

API_URL = "https://pokeapi.co/api/v2"


class WhosThatPokemon(commands.Cog):
    """Can you guess Who's That Pokémon?"""

    __authors__ = ["ow0x", "MAX#1000"]
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

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

    @commands.hybrid_command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def whosthatpokemon(
        self, ctx: Context, generation: Optional[Generation] = None
    ):
        """Guess Who's that Pokémon in 30 seconds!

        You can optionally specify generation from `gen1` to `gen8` only,
        to restrict this guessing game to specific Pokemon generation.

        Otherwise, it will default to pulling random pokemon from all 8 Gens.
        """
        async with ctx.typing():
            poke_id = generation or randint(1, 898)
            if_guessed_right = False

            temp = await self.generate_image(f"{poke_id:>03}", hide=True)
            if temp is None:
                return await ctx.send("Failed to generate whosthatpokemon card image.")

            inital_img = await ctx.send(
                "You have **30 seconds** to answer. Who's that Pokémon?",
                file=File(temp, "guessthatpokemon.png"),
            )
            message = await ctx.send(
                "You have **3**/3 attempts left to guess it right."
            )
            species_data = await self.get_data(f"{API_URL}/pokemon-species/{poke_id}")
            if species_data.get("http_code"):
                return await ctx.send("Failed to get species data from PokeAPI.")
            names_data = species_data.get("names", [{}])
            eligible_names = [x["name"].lower() for x in names_data]
            english_name = [
                x["name"] for x in names_data if x["language"]["name"] == "en"
            ][0]

            def check(msg: discord.Message) -> bool:
                return (
                    msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
                )

            revealed = await self.generate_image(f"{poke_id:>03}", hide=False)
            revealed_img = File(revealed, "whosthatpokemon.png")

        attempts = 0
        while attempts != 3:
            try:
                guess = await ctx.bot.wait_for("message", timeout=30.0, check=check)
            except asyncio.TimeoutError:
                attempts = 3
                with suppress(discord.NotFound, discord.HTTPException):
                    await inital_img.delete()
                    await message.delete()
                return await ctx.send(
                    f"Time over, **{ctx.author}**! You could not guess the Pokémon in 30 seconds."
                )

            if guess.content.lower() in eligible_names:
                attempts = 3
                if_guessed_right = True
                with suppress(discord.NotFound, discord.HTTPException):
                    await inital_img.delete()
                    await message.delete()
            else:
                attempts += 1
                if_guessed_right = False
                to_send = (
                    f"❌ Your guess is wrong! **{3 - attempts}**/3 attempts remaining."
                )
                try:
                    await message.edit(content=to_send)
                except (discord.NotFound, discord.HTTPException):
                    await ctx.send(to_send)

            if attempts == 3:
                with suppress(discord.NotFound, discord.HTTPException):
                    await inital_img.delete()
                    await message.delete()
                emb = Embed(description=f"It was ... **{english_name}**")
                if if_guessed_right:
                    emb.title = "🎉 POGGERS!! You guessed it right! 🎉"
                    emb.colour = Colour(0x00FF00)
                else:
                    emb.title = "You took too many attempts! 😔 😮\u200d💨"
                    emb.colour = Colour(0xFF0000)
                emb.set_image(url=f"attachment://whosthatpokemon.png")
                emb.set_footer(
                    text=f"Requested by {ctx.author}",
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=emb, file=revealed_img)
