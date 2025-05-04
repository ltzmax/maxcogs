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
from typing import Any, Dict, Final, List, Optional

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
MAX_DESCRIPTION_LENGTH = 4000


class Pokemon(commands.Cog):
    """
    This is pokemon related stuff cog.
    - Can you guess Who's That Pokémon?
    - Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).
    - Get information about a Pokémon.
    """

    __author__: Final[List[str]] = ["@306810730055729152", "max", "flame442"]
    __version__: Final[str] = "1.10.0"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/pokemon.html"

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

    async def fetch_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from a URL asynchronously.

        Args:
            url: The URL to fetch data from.

        Returns:
            The JSON response or None if the request fails.
        """
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except (aiohttp.ClientError, ValueError):
            return None

    def _format_list(self, items: List[str], separator: str = ", ") -> str:
        """Format a list of items into a human-readable string."""
        return separator.join(items) if items else "None"

    def _get_official_artwork(self, sprites: Dict[str, Any]) -> Optional[str]:
        """Get the official artwork URL from sprites, falling back to front_default."""
        return sprites.get("other", {}).get("official-artwork", {}).get(
            "front_default"
        ) or sprites.get("front_default")

    def _format_stats(self, stats: List[Dict[str, Any]]) -> str:
        """Format base stats into a readable string with total."""
        if not stats:
            return "No stats available."
        stat_lines = [f"{s['stat']['name'].capitalize()}: {s['base_stat']}" for s in stats]
        total = sum(s["base_stat"] for s in stats)
        return "\n".join(stat_lines) + f"\nTotal: {total}"

    def _format_height_weight(self, height: int, weight: int) -> tuple[str, str]:
        """Format height and weight in metric and imperial units."""
        return (
            f"{height/10:.1f}m ({height*3.28084/10:.2f}ft)",
            f"{weight/10:.1f}kg ({weight*2.20462/10:.2f}lbs)",
        )

    def _format_abilities(self, abilities: List[Dict[str, Any]]) -> str:
        """Format abilities, including hidden ones."""
        if not abilities:
            return "No abilities available."
        ability_names = [a["ability"]["name"].capitalize() for a in abilities]
        hidden = [
            a["ability"]["name"].capitalize() for a in abilities if a.get("is_hidden", False)
        ]
        hidden_str = f" (Hidden: {self._format_list(hidden or ['None'])})"
        return self._format_list(ability_names) + hidden_str

    def _format_game_indices(self, game_indices: List[Dict[str, Any]]) -> str:
        """Format game indices into a readable string."""
        if not game_indices:
            return "No game indices available."
        return self._format_list(
            [f"{g['game_index']} ({g['version']['name'].capitalize()})" for g in game_indices]
        )

    def _format_types(self, types: List[Dict[str, Any]]) -> str:
        """Format Pokémon types into a readable string."""
        return self._format_list([t["type"]["name"].capitalize() for t in types])

    def _truncate_description(self, text: str) -> str:
        """Truncate text if it exceeds the maximum description length."""
        return (
            text[:MAX_DESCRIPTION_LENGTH] + "..." if len(text) > MAX_DESCRIPTION_LENGTH else text
        )

    async def create_pokemon_embed(
        self, pokemon_data: Dict[str, Any], section: str = "base"
    ) -> discord.Embed:
        """
        Create a Discord embed for Pokémon data based on the specified section.

        Args:
            pokemon_data: The Pokémon data from PokéAPI.
            section: The section to display (e.g., "base", "held_items", "moves", "locations").

        Returns:
            A Discord embed with the requested Pokémon information.

        Raises:
            ValueError: If the data is invalid or the section is unsupported.
        """
        if not pokemon_data or "name" not in pokemon_data:
            raise ValueError("Invalid Pokémon data provided.")

        name = pokemon_data["name"].capitalize()
        sprites = pokemon_data.get("sprites", {})
        embed = discord.Embed(
            title=f"{name} {section.capitalize()}",
            description=f"Information about {name}'s {section}",
            color=discord.Color.blue(),
            url=f"https://www.pokemon.com/us/pokedex/{pokemon_data['name']}",
        )

        thumbnail_url = sprites.get("front_default")
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        image_url = self._get_official_artwork(sprites)
        if image_url:
            embed.set_image(url=image_url)

        if section == "base":
            stats = pokemon_data.get("stats", [])
            types = pokemon_data.get("types", [])
            abilities = pokemon_data.get("abilities", [])
            game_indices = pokemon_data.get("game_indices", [])
            height = pokemon_data.get("height", 0)
            weight = pokemon_data.get("weight", 0)
            base_experience = pokemon_data.get("base_experience", "Unknown")

            embed.add_field(
                name="Base Stats:",
                value=self._format_stats(stats),
                inline=False,
            )
            height_str, weight_str = self._format_height_weight(height, weight)
            embed.add_field(name="Height:", value=height_str, inline=True)
            embed.add_field(name="Weight:", value=weight_str, inline=True)
            embed.add_field(name=" ", value=" ", inline=False)
            embed.add_field(name="Base Experience:", value=base_experience, inline=True)
            embed.add_field(name="Types:", value=self._format_types(types), inline=True)
            embed.add_field(name=" ", value=" ", inline=False)
            embed.add_field(
                name="Abilities:",
                value=self._format_abilities(abilities),
                inline=False,
            )
            embed.add_field(
                name="Game Indices:",
                value=self._format_game_indices(game_indices),
                inline=False,
            )

        elif section == "held_items":
            held_items = pokemon_data.get("held_items", [])
            if not held_items:
                raise ValueError("No held items data available.")
            items_info = self._format_list(
                [
                    f"{h['item']['name'].capitalize()} ({h['version_details'][0]['rarity']})"
                    for h in held_items
                    if "item" in h and "version_details" in h and h["version_details"]
                ]
            )
            embed.description = self._truncate_description(items_info)

        elif section == "moves":
            moves = pokemon_data.get("moves", [])
            if not moves:
                raise ValueError("No moves data available.")
            moves_info = self._format_list(
                [
                    f"{m['move']['name'].capitalize()} ({m['version_group_details'][0]['level_learned_at']})"
                    for m in moves
                    if m.get("move") and m["move"].get("name") and m.get("version_group_details")
                ]
            )
            embed.description = self._truncate_description(moves_info)

        elif section == "locations":
            location_url = f"{API_URL}/pokemon/{pokemon_data['name']}/encounters"
            location_areas = await self.fetch_data(location_url)
            if not location_areas:
                raise ValueError("No location data available.")
            locations = []
            for location in location_areas:
                location_name = (
                    location.get("location_area", {})
                    .get("name", "Unknown Location")
                    .replace("-", " ")
                    .title()
                )
                versions = []
                for detail in location.get("version_details", []):
                    version_name = (
                        detail.get("version", {})
                        .get("name", "Unknown Version")
                        .replace("-", " ")
                        .title()
                    )
                    chance = detail.get("encounter_details", [{}])[0].get(
                        "chance", "Unknown Chance"
                    )
                    if chance is not None:
                        versions.append(f"{version_name}: {chance}%")
                versions_str = "\n".join(versions) if versions else "No version details"
                locations.append(f"**{location_name}**:\n{versions_str}")
            locations_str = "\n".join(locations)
            embed.description = self._truncate_description(locations_str)

        else:
            raise ValueError(f"Unsupported section: {section}")

        embed.set_footer(
            text=f"Powered by PokéAPI | Pokémon ID: {pokemon_data.get('id', 'Unknown')}"
        )
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
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 215, 0))
            embed.title = (
                f"Stage {data.get('stage', 'Basic')} {data['name']} - HP{data.get('hp', 'N/A')}"
            )
            description = data.get("flavorText", "No description available.")
            embed.description = f"**Description:** {description}"

            embed.add_field(name="Rarity:", value=data.get("rarity", "Common"), inline=True)
            embed.add_field(name="Hp:", value=data.get("hp", "N/A"), inline=True)
            embed.add_field(name="EvolveFrom:", value=data.get("evolvesFrom", "None"), inline=True)
            embed.add_field(
                name="RegulationMark:", value=data.get("regulationMark", "N/A"), inline=True
            )

            tcgdex_id = data.get("id", "N/A")
            card_number = data.get("number", "N/A")
            embed.add_field(name="TCGdex ID:", value=f"sush-138", inline=False)
            embed.add_field(name="Card number:", value=card_number, inline=False)

            retreat_cost = data.get("retreatCost", [])
            retreat_symbols = "🌟" * len(retreat_cost) if retreat_cost else "None"
            embed.add_field(name="Retreat Cost:", value=retreat_symbols, inline=False)

            attacks = data.get("attacks", [])
            if attacks:
                for attack in attacks:
                    name = attack.get("name", "N/A")
                    cost = attack.get("cost", [])
                    damage = attack.get("damage", "N/A")
                    text = attack.get("text", "No effect.")
                    attack_str = f"**{name}** - {' '.join(cost)} - {damage}\n{text}"
                    embed.add_field(name=f"Attack:", value=attack_str, inline=False)
            else:
                embed.add_field(name="Attacks:", value="No attacks available.", inline=False)

            weaknesses = data.get("weaknesses", [])
            if weaknesses:
                weakness_type = weaknesses[0].get("type", "N/A")
                embed.add_field(name="Weakness:", value=weakness_type, inline=False)
            resistances = data.get("resistances", [])
            if resistances:
                resistance_type = resistances[0].get("type", "N/A")
                embed.add_field(name="Resistance:", value=resistance_type, inline=False)

            embed.add_field(name="Set:", value=data["set"]["name"], inline=False)

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
    @app_commands.describe(pokemon="The Pokémon to search for")
    async def pokeinfo(self, ctx: commands.Context, *, pokemon: str) -> None:
        """Get information about a Pokémon.

        **Example:**
        - `[p]pokeinfo pikachu` - returns information about Pikachu.

        **Arguments:**
        - `<pokemon>` - The Pokémon to search for.
        """
        pokemon_url = f"{API_URL}/pokemon/{pokemon.lower()}"
        pokemon_data = await self.fetch_data(pokemon_url)
        if not pokemon_data:
            return await ctx.send("Could not fetch Pokémon data.")

        # Was gonna move it to seperate file but i got so damn tired at 10AM in the morning.
        # I'll move it later if i feel like it unless i decide to make something with components V2.
        class PokemonView(discord.ui.View):
            def __init__(self, ctx, pokemon_data, timeout=120):
                super().__init__(timeout=timeout)
                self.ctx = ctx
                self.pokemon_data = pokemon_data
                self.current_section = "base"
                self.message = None

            async def on_timeout(self):
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                if self.message:
                    try:
                        await self.message.edit(view=self)
                    except discord.NotFound as e:
                        log.error(f"Message not found: {e}", exc_info=True)

            async def interaction_check(self, interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message(
                        "You are not the owner of this interaction.", ephemeral=True
                    )
                    return False
                return True

            async def update_embed(self, interaction: discord.Interaction):
                try:
                    embed = await self.ctx.cog.create_pokemon_embed(
                        self.pokemon_data, self.current_section
                    )
                    await interaction.response.edit_message(embed=embed, view=self)
                except ValueError as e:
                    await interaction.response.send_message(
                        f"Error for {self.current_section}", ephemeral=True
                    )
                    log.error(f"Error for {self.current_section}: {e}", exc_info=True)

            @discord.ui.button(label="Base", style=discord.ButtonStyle.primary, custom_id="base")
            async def base_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.current_section = "base"
                await self.update_embed(interaction)

            @discord.ui.button(
                label="Held Items", style=discord.ButtonStyle.primary, custom_id="held_items"
            )
            async def held_items_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.current_section = "held_items"
                await self.update_embed(interaction)

            @discord.ui.button(label="Moves", style=discord.ButtonStyle.primary, custom_id="moves")
            async def moves_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.current_section = "moves"
                await self.update_embed(interaction)

            @discord.ui.button(
                label="Locations", style=discord.ButtonStyle.primary, custom_id="locations"
            )
            async def locations_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.current_section = "locations"
                await self.update_embed(interaction)

        view = PokemonView(ctx, pokemon_data)
        try:
            embed = await self.create_pokemon_embed(pokemon_data, "base")
            message = await ctx.send(embed=embed, view=view)
            view.message = message
        except ValueError as e:
            await ctx.send(f"Error creating embed")
            log.error(f"Error creating embed: {e}", exc_info=True)
