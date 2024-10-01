# This cog did not have a license but is now licensed under the MIT License.
# This cog was created by owocado and is now continued by ltzmax.
# This cog was transfered via a pr from the author of the code https://github.com/ltzmax/maxcogs/pull/46
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
from datetime import datetime, timedelta, timezone
from io import BytesIO
from random import randint
from typing import Any, Final, List, Optional

import aiohttp
import discord
import orjson
from discord import File
from PIL import Image
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import SimpleMenu

from .converters import Generation, WhosThatPokemonView, get_data

log = logging.getLogger("red.maxcogs.whosthatpokemon")

API_URL: Final[str] = "https://pokeapi.co/api/v2"


class Pokemon(commands.Cog):
    """
    This is pokemon related stuff cog.
    - Can you guess Who's That Pokémon?
    - Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).
    - Get information about a Pokémon.
    """

    __author__: Final[List[str]] = ["@306810730055729152", "max", "flame442"]
    __version__: Final[str] = "1.7.2"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Pokemon.md"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {humanize_list(self.__author__)}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

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
            log.error(f"Failed to get data from {base_url} due to timeout")
            return None
        pbytes = BytesIO(data)
        poke_image = Image.open(pbytes)
        poke_width, poke_height = poke_image.size
        poke_image_resized = poke_image.resize((int(poke_width * 1.6), int(poke_height * 1.6)))

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

    # --------- POKEMON INFO -----------

    def create_base_info_embed(self, data):
        embed = discord.Embed(
            title=data["name"].capitalize(),
            description=f"Information about {data['name'].capitalize()}",
            color=discord.Color.blue(),
            url=f"https://www.pokemon.com/us/pokedex/{data['name']}",
        )
        embed.set_thumbnail(url=data["sprites"]["front_default"])
        embed.add_field(
            name="Base Stats:",
            value="\n".join(
                [f"{s['stat']['name'].capitalize()}: {s['base_stat']}" for s in data["stats"]]
            )
            + f"\nTotal: {sum([s['base_stat'] for s in data['stats']])}",
            inline=False,
        )
        embed.add_field(
            name="Height:",
            value=f"{data['height']/10:.1f}m ({data['height']*3.28084/10:.2f}ft)",
        )
        embed.add_field(
            name="Weight:",
            value=f"{data['weight']/10:.1f}kg ({data['weight']*2.20462/10:.2f}lbs)",
        )
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Base Experience:", value=data["base_experience"])
        embed.add_field(
            name="Types:",
            value=humanize_list([t["type"]["name"].capitalize() for t in data["types"]]),
        )
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(
            name="Abilities:",
            value=humanize_list([a["ability"]["name"].capitalize() for a in data["abilities"]])
            + f" (Hidden: {humanize_list([a['ability']['name'].capitalize() for a in data['abilities'] if a['is_hidden']] or ['None'])})",
        )
        if data["game_indices"]:
            embed.add_field(
                name="Game Indices:",
                value=humanize_list(
                    [
                        f"{g['game_index']} ({g['version']['name'].capitalize()})"
                        for g in data["game_indices"]
                    ]
                ),
                inline=False,
            )
        embed.set_image(url=data["sprites"]["other"]["official-artwork"]["front_default"])
        embed.set_footer(text="Powered by PokéAPI | Pokemon ID: " + str(data["id"]))
        return embed

    def create_held_items_embed(self, data):
        items_held_info = humanize_list(
            [
                f"{h['item']['name'].capitalize()} ({h['version_details'][0]['rarity']})"
                for h in data["held_items"]
            ]
        )
        embed = discord.Embed(
            title=data["name"].capitalize() + " Held Items",
            description=f"{items_held_info if len(items_held_info) < 4000 else 'Too many items to display.'}",
            color=discord.Color.blue(),
            url=f"https://www.pokemon.com/us/pokedex/{data['name']}",
        )
        embed.set_footer(text="Powered by PokéAPI | Pokemon ID: " + str(data["id"]))
        return embed

    def create_moves_embed(self, data):
        moves_info = humanize_list(
            [
                "\n".join(
                    [
                        f"{m['move']['name'].capitalize()} ({m['version_group_details'][0]['level_learned_at']})"
                        for m in data["moves"]
                    ]
                )
            ]
        )
        embed = discord.Embed(
            title=data["name"].capitalize() + " Moves",
            description=f"{moves_info if len(moves_info) < 4000 else 'Too many moves to display.'}",
            color=discord.Color.blue(),
            url=f"https://www.pokemon.com/us/pokedex/{data['name']}",
        )
        embed.set_footer(text="Powered by PokéAPI | Pokemon ID: " + str(data["id"]))
        return embed

    async def fetch_location_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.json()

    async def create_locations_embed(self, data, location_areas):
        # Ensure location_areas is a list
        if not isinstance(location_areas, list):
            return None

        # Format the location information
        locations = []
        for location in location_areas:
            if not isinstance(location, dict):
                continue
            location_area = location.get("location_area", {})
            location_name = location_area.get("name", "Unknown Location").replace("-", " ").title()
            version_details = location.get("version_details", [])

            # Format version details
            versions = []
            for detail in version_details:
                version_name = (
                    detail.get("version", {})
                    .get("name", "Unknown Version")
                    .replace("-", " ")
                    .title()
                )
                encounter_details = detail.get("encounter_details", [])
                if encounter_details:
                    chance = encounter_details[0].get("chance", "Unknown Chance")
                    versions.append(f"{version_name}: {chance}%")

            versions_str = "\n".join(versions)
            locations.append(f"**{location_name}**:\n{versions_str}")

        # Join all locations into a single string
        locations_str = "\n\n".join(locations)

        # Ensure the description does not exceed the character limit
        if len(locations_str) > 4000:
            locations_str = locations_str[:4000] + "..."

        embed = discord.Embed(
            title=data["name"].capitalize() + " Locations",
            description=locations_str,
            color=discord.Color.blue(),
            url=f"https://www.pokemon.com/us/pokedex/{data['name']}",
        )
        embed.set_footer(text="Powered by PokéAPI | Pokemon ID: " + str(data["id"]))
        return embed

    # --------- WHOSTHATPOKEMON -----------

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(generation=("Optionally choose generation from gen1 to gen9."))
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
            app_commands.Choice(name="Generation 9", value="gen9"),
        ]
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def whosthatpokemon(
        self,
        ctx: commands.Context,
        generation: Generation = None,
    ) -> None:
        """Guess Who's that Pokémon in 30 seconds!

        You can optionally specify generation from `gen1` to `gen8` only.

        **Example:**
        - `[p]whosthatpokemon` - This will start a new Generation.
        - `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.

        **Arguments:**
        - `[generation]` - Where you choose any generation from gen 1 to gen 9.
        """
        await ctx.typing()
        poke_id = generation or randint(1, 1010)
        if_guessed_right = False

        temp = await self.generate_image(f"{poke_id:>03}", hide=True)
        if temp is None:
            self.log.error(f"Failed to generate image.")
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        # Took this from Core's event file.
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/41d89c7b54a1f231a01f79655c20d4acf1799633/redbot/core/_events.py#L424-L426
        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(seconds=30.0), "R"
        )
        species_data = await get_data(self, f"{API_URL}/pokemon-species/{poke_id}")
        if species_data.get("http_code"):
            return await ctx.send("Failed to get species data from PokeAPI.")
            log.error(f"Failed to get species data from PokeAPI. {species_data}")
        names_data = species_data.get("names", [{}])
        eligible_names = [x["name"].lower() for x in names_data]
        english_name = [x["name"] for x in names_data if x["language"]["name"] == "en"][0]

        revealed = await self.generate_image(f"{poke_id:>03}", hide=False)
        revealed_img = File(revealed, "whosthatpokemon.png")

        view = WhosThatPokemonView(eligible_names)
        view.message = await ctx.send(
            f"**Who's that Pokémon?**\nI need a valid answer at most {img_timeout}.",
            file=File(temp, "guessthatpokemon.png"),
            view=view,
        )

        embed = discord.Embed(
            title=":tada: You got it right! :tada:",
            description=f"The Pokemon was... **{english_name}**.",
            color=0x76EE00,
        )
        embed.set_image(url="attachment://whosthatpokemon.png")
        embed.set_footer(text=f"Author: {ctx.author}", icon_url=ctx.author.avatar.url)
        # because we want it to timeout and not tell the user that they got it right.
        # This is probably not the best way to do it, but it works perfectly fine.
        timeout = await view.wait()
        if timeout:
            return await ctx.send(
                f"{ctx.author.mention} You took too long to answer.\nThe Pokemon was... **{english_name}**."
            )
            log.info(f"{ctx.author} ran out of time to guess the pokemon.")
        await ctx.send(file=revealed_img, embed=embed)

    # --------- TCGCARD -----------

    @commands.hybrid_command()
    @app_commands.describe(query=("The Pokémon you want to search a card for."))
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def tcgcard(self, ctx: commands.Context, *, query: str) -> None:
        """Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).

        **Example:**
        - `[p]tcgcard pikachu` - returns information about pikachu's cards.

        **Arguments:**
        - `<query>` - The pokemon you want to search for.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("pokemontcg")).get("api_key")
        headers = {"X-Api-Key": api_key} if api_key else None
        await ctx.typing()
        base_url = f"https://api.pokemontcg.io/v2/cards?q=name:{query}"
        try:
            async with self.session.get(base_url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send(f"https://http.cat/{response.status}")
                    log.error(f"Failed to fetch data. Status code: {response.status}.")
                    return
                output = orjson.loads(await response.read())
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out.")
            log.error("Operation timed out while fetching data.")
            return

        if not output["data"]:
            await ctx.send("There is no results for that search.")
            log.info("There is no results for that search in the API.")
            return

        pages = []
        for i, data in enumerate(output["data"], 1):
            dt = datetime.utcnow()
            release = datetime.strptime(data["set"]["releaseDate"], "%Y/%m/%d")
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.title = data["name"]
            rarity = data.get("rarity")
            if rarity == "Promo":
                rarity = "Uncommon"
            embed.description = "**Rarity:** " + str(rarity)
            embed.add_field(name="Artist:", value=str(data.get("artist")))
            embed.add_field(name="Belongs to Set:", value=str(data["set"]["name"]), inline=False)
            embed.add_field(
                name="Set Release Date:",
                value=discord.utils.format_dt(release, style="D"),
                inline=False,
            )
            embed.add_field(
                name="Weakness:",
                value=str(data.get("weaknesses", [{}])[0].get("type")),
            )
            embed.set_thumbnail(url=str(data["set"]["images"]["logo"]))
            embed.set_image(url=str(data["images"]["large"]))
            embed.set_footer(
                text=f"Page {i} of {len(output['data'])} • Powered by Pokémon TCG API!"
            )
            pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    @app_commands.describe(pokemon=("The Pokémon you want to search for."))
    async def pokeinfo(self, ctx: commands.Context, *, pokemon: str):
        """Get information about a Pokémon.

        **Example:**
        - `[p]pokeinfo pikachu` - returns information about Pikachu.

        **Arguments:**
        - `<pokemon>` - The Pokémon you want to search for.
            - If you dont know names, you can check the list from the [national pokedex](https://pokemondb.net/pokedex/national).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}"
            ) as response:
                if response.status != 200:
                    return await ctx.send("Could not fetch data from the PokéAPI.")
                    log.error(
                        f"Failed to fetch data from the PokéAPI. Status code: {response.status}."
                    )
                data = await response.json()

        pages = []
        pages.append(self.create_base_info_embed(data))
        if data["held_items"]:
            pages.append(self.create_held_items_embed(data))
        if data["moves"]:
            pages.append(self.create_moves_embed(data))
        if data["location_area_encounters"]:
            location_areas = await self.fetch_location_data(data["location_area_encounters"])
            if location_areas:
                embed = await self.create_locations_embed(data, location_areas)
                if embed:
                    pages.append(embed)
        await SimpleMenu(
            pages,
            use_select_menu=True,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)
