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

from datetime import datetime, timedelta, timezone
from random import randint

import aiohttp
import discord
import orjson
from discord import File
from red_commons.logging import getLogger
from redbot.core import app_commands, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.views import SimpleMenu

from .converters import Generation
from .utils import API_URL, create_pokemon_embed, fetch_data, generate_image
from .views import HintView, PokemonView, WhosThatPokemonView

log = getLogger("red.maxcogs.whosthatpokemon")


class Pokemon(commands.Cog):
    """
    This is pokemon related stuff cog.

    - Can you guess Who's That Pokémon?
    - Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).
    - Get information about a Pokémon.
    """

    __author__ = ["@306810730055729152", "max", "flame442"]
    __version__ = "2.3.0"
    __docs__ = "https://cogs.maxapp.tv/"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {humanize_list(self.__author__)}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

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

        You can optionally specify generation from `gen1` to `gen9` only.

        **Example:**
        - `[p]whosthatpokemon` - This will start a new Generation.
        - `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.

        **Arguments:**
        - `[generation]` - Where you choose any generation from gen 1 to gen 9.
        """
        await ctx.typing()
        poke_id = generation or randint(1, 1010)

        temp = await generate_image(self, f"{poke_id:>03}", hide=True)
        if temp is None:
            log.error("Failed to generate image.")
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(seconds=30.0), "R"
        )
        species_data = await fetch_data(self.session, f"{API_URL}/pokemon-species/{poke_id}")
        if not species_data or species_data.get("http_code"):
            log.error(f"Failed to get species data from PokeAPI. {species_data}")
            return await ctx.send("Failed to get species data from PokeAPI.")
        pokemon_data = await fetch_data(self.session, f"{API_URL}/pokemon/{poke_id}")
        if not pokemon_data or pokemon_data.get("http_code"):
            log.error(f"Failed to get Pokémon data: {pokemon_data}")
            return await ctx.send("Failed to fetch Pokémon data.")
        names_data = species_data.get("names", [{}])
        eligible_names = [x["name"].lower() for x in names_data]
        english_name = [x["name"] for x in names_data if x["language"]["name"] == "en"][0]

        revealed = await generate_image(self, f"{poke_id:>03}", hide=False)
        revealed_img = File(revealed, "whosthatpokemon.png")

        view = WhosThatPokemonView(eligible_names)
        hint_view = HintView(
            {"species_data": species_data, "pokemon_data": pokemon_data}, view, english_name
        )
        view.add_item(hint_view.children[0])
        view.message = await ctx.send(
            f"**Who's that Pokémon?**\nI need a valid answer at most {img_timeout}.\nUse the hint button for help (one use only)!",
            file=File(temp, "guessthatpokemon.png"),
            view=view,
        )

        embed = discord.Embed(
            title=":tada: You got it right! :tada:",
            description=f"The Pokemon was... **{english_name}**.",
            color=0x76EE00,
        )
        embed.set_image(url="attachment://whosthatpokemon.png")
        embed.set_footer(text=f"Author: {ctx.author}", icon_url=ctx.author.display_avatar.url)
        timeout = await view.wait()
        if timeout:
            return await ctx.send(
                f"{ctx.author.mention} You took too long to answer.\nThe Pokemon was... **{english_name}**."
            )
        await ctx.send(file=revealed_img, embed=embed)

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
        select_fields = "id,name,supertype,subtypes,hp,types,evolvesFrom,evolvesTo,abilities,attacks,weaknesses,resistances,retreatCost,convertedRetreatCost,number,artist,rarity,flavorText,nationalPokedexNumbers,legalities,regulationMark,images,set"
        base_url = f"https://api.pokemontcg.io/v2/cards?q=name:{query}&select={select_fields}"
        try:
            async with self.session.get(base_url, headers=headers) as response:
                if response.status != 200:
                    log.error(f"Failed to fetch data. Status code: {response.status}.")
                    return await ctx.send(f"https://http.cat/{response.status}")
                output = orjson.loads(await response.read())
        except asyncio.TimeoutError:
            log.error("Operation timed out while fetching data.")
            return await ctx.send("Operation timed out.")

        if not output["data"]:
            log.info("There is no results for that search in the API.")
            return await ctx.send("There is no results for that search.")

        pages = []
        for i, data in enumerate(output["data"], 1):
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 215, 0))
            name = data["name"]
            hp = data.get("hp", "N/A")
            embed.title = f"{name} - HP: {hp}"
            basic_info = []
            supertype = data.get("supertype", "N/A")
            basic_info.append(f"{'Supertype:':<18}{supertype}")
            subtypes = data.get("subtypes", [])
            subtypes_str = ", ".join(subtypes) if subtypes else "N/A"
            basic_info.append(f"{'Subtypes:':<18}{subtypes_str}")
            types = data.get("types", [])
            types_str = ", ".join(types) if types else "N/A"
            basic_info.append(f"{'Types:':<18}{types_str}")
            basic_info.append(f"{'Evolves From:':<18}{data.get('evolvesFrom', 'None')}")
            evolves_to = data.get("evolvesTo", [])
            evolves_to_str = ", ".join(evolves_to) if evolves_to else "None"
            basic_info.append(f"{'Evolves To:':<18}{evolves_to_str}")
            basic_info.append(f"{'Rarity:':<18}{data.get('rarity', 'Common')}")
            basic_info.append(f"{'Artist:':<18}{data.get('artist', 'N/A')}")
            basic_info.append(f"{'Regulation Mark:':<18}{data.get('regulationMark', 'N/A')}")
            basic_info.append(f"{'Card Number:':<18}{data.get('number', 'N/A')}")
            basic_info.append(f"{'Set:':<18}{data['set']['name']}")
            national_pokedex = data.get("nationalPokedexNumbers", [])
            nat_dex_str = ", ".join(map(str, national_pokedex)) if national_pokedex else "N/A"
            basic_info.append(f"{'National Pokedex:':<18}{nat_dex_str}")
            legalities = data.get("legalities", {})
            legal_str = (
                ", ".join([k.capitalize() for k, v in legalities.items() if v == "Legal"])
                or "None"
            )
            basic_info.append(f"{'Legalities:':<18}{legal_str}")
            aligned_box = box("\n".join(basic_info), lang="yaml")
            embed.add_field(name="Card Info", value=aligned_box, inline=False)

            # Abilities
            abilities = data.get("abilities", [])
            if abilities:
                abilities_str = []
                for ability in abilities:
                    name = ability.get("name", "N/A")
                    type_ = ability.get("type", "N/A")
                    text = ability.get("text", "")
                    abilities_str.append(f"{'Name:':<18}{name}")
                    abilities_str.append(f"{'Type:':<18}{type_}")
                    if text:
                        abilities_str.append(f"{'Text:':<18}{text}")
                    abilities_str.append("")  # Spacer
                abilities_box = box(
                    "\n".join(abilities_str[:-1]), lang="yaml"
                )  # Remove last spacer
                embed.add_field(name="Abilities", value=abilities_box, inline=False)

            # Attacks
            attacks = data.get("attacks", [])
            if attacks:
                attacks_str = []
                for attack in attacks:
                    cost = attack.get("cost", [])
                    name = attack.get("name", "N/A")
                    damage = attack.get("damage", "N/A")
                    text = attack.get("text", "")
                    converted_cost = attack.get("convertedEnergyCost", 0)
                    cost_str = " ".join(cost)
                    attacks_str.append(f"{'Name:':<18}{name}")
                    attacks_str.append(f"{'Cost:':<18}{cost_str} ({converted_cost})")
                    attacks_str.append(f"{'Damage:':<18}{damage}")
                    if text:
                        attacks_str.append(f"{'Text:':<18}{text}")
                    attacks_str.append("")  # Spacer
                attacks_box = box("\n".join(attacks_str[:-1]), lang="yaml")  # Remove last spacer
                embed.add_field(name="Attacks", value=attacks_box, inline=False)

            # Weaknesses, Resistances, Retreat
            wr_info = []
            weaknesses = data.get("weaknesses", [])
            if weaknesses:
                w_type = weaknesses[0].get("type", "N/A")
                w_value = weaknesses[0].get("value", "N/A")
                wr_info.append(f"{'Weakness:':<18}{w_type} ({w_value})")
            resistances = data.get("resistances", [])
            if resistances:
                r_type = resistances[0].get("type", "N/A")
                r_value = resistances[0].get("value", "N/A")
                wr_info.append(f"{'Resistance:':<18}{r_type} ({r_value})")
            retreat_cost = data.get("retreatCost", [])
            retreat_symbols = "🌟" * len(retreat_cost) if retreat_cost else "None"
            converted_retreat = data.get("convertedRetreatCost", 0)
            wr_info.append(f"{'Retreat Cost:':<18}{retreat_symbols} ({converted_retreat})")
            if wr_info:
                wr_box = box("\n".join(wr_info), lang="yaml")
                embed.add_field(
                    name="Weaknesses / Resistances / Retreat", value=wr_box, inline=False
                )

            # Flavor Text
            flavor_text = data.get("flavorText", "")
            if flavor_text:
                flavor_box = box(flavor_text, lang="yaml")
                embed.add_field(name="Flavor Text", value=flavor_box, inline=False)

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
        await ctx.typing()
        pokemon_url = f"{API_URL}/pokemon/{pokemon.lower()}"
        pokemon_data = await fetch_data(self.session, pokemon_url)
        if not pokemon_data:
            return await ctx.send("Could not fetch Pokémon data.")

        view = PokemonView(ctx, self.session, pokemon_data)
        try:
            embed = await create_pokemon_embed(self.session, pokemon_data, "base")
            view.message = await ctx.send(embed=embed, view=view)
        except ValueError as e:
            log.error(f"Error creating initial embed: {e}", exc_info=True)
