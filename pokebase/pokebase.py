import asyncio
import base64
from contextlib import suppress
from io import BytesIO
from math import floor
from random import choice
from string import capwords

import aiohttp
import jmespath
from aiocache import SimpleMemoryCache, cached
from bs4 import BeautifulSoup as bsp
from discord import Colour, Embed, File
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import bold, humanize_number, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .utils import BADGES, STYLES, TRAINERS, get_generation

cache = SimpleMemoryCache()

API_URL = "https://pokeapi.co/api/v2"
BULBAPEDIA_URL = "https://bulbapedia.bulbagarden.net/wiki"


class Pokebase(commands.Cog):
    """Search for various info about a Pokémon and related data."""

    __authors__ = ["ow0x", "MAX#1000", "phalt"]
    __version__ = "1.2.0"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad."""
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  v{self.__version__}"
        )

    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_data(self, url: str):
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {"http_code": response.status}
                return await response.json()
        except asyncio.TimeoutError:
            return {"http_code": 408}

    @staticmethod
    def basic_embed(colour: Colour, data: dict) -> Embed:
        """Basic embed for the info command."""
        embed = Embed(colour=colour)
        base_pokemon_url = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/"
        embed.set_thumbnail(url=f"{base_pokemon_url}{data['id']:>03}.png")
        embed.add_field(name="Introduced In", value=get_generation(data["id"]))
        if height := data.get("height"):
            humanize_height = (
                f"{floor(height * 3.94 // 12)} ft. "
                f"{floor(height * 3.94 % 12)} in.\n({height / 10} m.)"
            )
            embed.add_field(name="Height", value=humanize_height)
        if weight := data.get("weight"):
            humanize_weight = f"{round(weight * 0.2205, 2)} lbs.\n({weight / 10} kgs.)"
            embed.add_field(name="Weight", value=humanize_weight)
        embed.add_field(
            name="Types",
            value="/".join(
                x["type"].get("name").title() for x in data.get("types", [{}])
            ),
        )
        return embed

    @staticmethod
    def species_embed(embed: Embed, data: dict) -> Embed:
        gender_rate = data.get("gender_rate", 0)
        male_ratio = 100 - ((gender_rate / 8) * 100)
        female_ratio = (gender_rate / 8) * 100
        genders = {
            "male": 0.0 if gender_rate == -1 else male_ratio,
            "female": 0.0 if gender_rate == -1 else female_ratio,
            "genderless": gender_rate == -1,
        }

        final_gender_rate = ""
        if genders["genderless"]:
            final_gender_rate += "Genderless"
        if genders["male"] != 0.0:
            final_gender_rate += f"\u2642 {genders['male']}%\n"
        if genders["female"] != 0.0:
            final_gender_rate += f"\u2640 {genders['female']}%"
        embed.add_field(name="Gender Rate", value=final_gender_rate)
        embed.add_field(
            name="Base Happiness", value=f"{data.get('base_happiness', 0)} / 255"
        )
        embed.add_field(
            name="Capture Rate", value=f"{data.get('capture_rate', 0)} / 255"
        )

        genus = [
            x.get("genus")
            for x in data.get("genera", [{}])
            if x.get("language").get("name") == "en"
        ]
        genus_text = f"The {genus[0]}"
        flavor_text = [
            x.get("flavor_text")
            for x in data.get("flavor_text_entries", [{}])
            if x.get("language").get("name") == "en"
        ]
        flavor_text = (
            choice(flavor_text).replace("\n", " ").replace("\f", " ").replace("\r", " ")
        )
        embed.description = f"**{genus_text}**\n\n{flavor_text}"
        return embed

    @staticmethod
    def base_stats_embed(embed: Embed, data: dict) -> Embed:
        if data.get("held_items"):
            held_items = "\n".join(
                f"{x['item'].get('name').replace('-', ' ').title()} "
                f"({x['version_details'][0]['rarity']}%)"
                for x in data.get("held_items", [{}])
            )
            embed.add_field(name="Held Items", value=held_items)
        else:
            embed.add_field(name="Held Items", value="None")

        abilities = "\n".join(
            f"[{aby['ability'].get('name').replace('-', ' ').title()}]({BULBAPEDIA_URL}/"
            f"{aby['ability'].get('name').title().replace('-', '_')}_%28Ability%29)"
            f"{' (Hidden Ability)' if aby.get('is_hidden') else ''}"
            for aby in data.get("abilities", [{}])
        )
        embed.add_field(name="Abilities", value=abilities)

        base_stats = {}
        for stat in data.get("stats", [{}]):
            base_stats[stat.get("stat").get("name")] = stat.get("base_stat")
        total_base_stats = sum(base_stats.values())

        def draw_bar(attribute: str) -> str:
            to_fill = round((base_stats[attribute] / 255) * 10) * 2
            fill, blank = ("█" * to_fill, " " * (20 - to_fill))
            return f"`|{fill}{blank}|`"

        sp_attack = base_stats["special-attack"]
        sp_defense = base_stats["special-defense"]
        pretty_base_stats = (
            f"**`{'HP':<12}:`**  {draw_bar('hp')} **{base_stats['hp']}**\n"
            f"**`{'Attack':<12}:`**  {draw_bar('attack')} **{base_stats['attack']}**\n"
            f"**`{'Defense':<12}:`**  {draw_bar('defense')} **{base_stats['defense']}**\n"
            f"**`{'Sp. Attack':<12}:`**  {draw_bar('special-attack')} **{sp_attack}**\n"
            f"**`{'Sp. Defense':<12}:`**  {draw_bar('special-defense')} **{sp_defense}**\n"
            f"**`{'Speed':<12}:`**  {draw_bar('speed')} **{base_stats['speed']}**\n"
            f"**`{'Total':<12}:`**  `|--------------------|` **{total_base_stats}**"
        )
        embed.add_field(
            name="Base Stats (Base Form)", value=pretty_base_stats, inline=False
        )
        return embed

    async def evolution_chain(self, evo_url: str) -> str:
        result = await self.get_data(evo_url)
        if result.get("http_code"):
            return ""
        evo_data = result.get("chain", [{}])
        base_evo = evo_data["species"].get("name").title()
        evolves_to = ""
        if evo_data.get("evolves_to"):
            evolves_to += " -> " + "/".join(
                x["species"].get("name").title() for x in evo_data["evolves_to"]
            )
        if evo_data.get("evolves_to") and evo_data["evolves_to"][0].get("evolves_to"):
            evolves_to += " -> " + "/".join(
                x["species"].get("name").title()
                for x in evo_data["evolves_to"][0].get("evolves_to")
            )
        return f"{base_evo} {evolves_to}" if evolves_to else ""

    @commands.group(aliases=["pokemon"], invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pokedex(self, ctx: Context, *, pokemon: str):
        """Command group to get various info about a Pokémon.

        You can search by name or ID of a Pokémon.

        Pokémon ID refers to: [National Pokédex](https://bulbapedia.bulbagarden.net/wiki/National_Pok%C3%A9dex) number.
        """
        pokemon = pokemon.replace(" ", "-")
        async with ctx.typing():
            data = await self.get_data(f"{API_URL}/pokemon/{pokemon.lower()}")
            if err := data.get("http_code"):
                if err == 404:
                    return await ctx.send(
                        "⚠ Could not find any Pokémon with that name."
                    )
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{data}"
                )

            embed = self.basic_embed(await ctx.embed_colour(), data)
            embed.set_footer(text="Powered by Poke API")
            pokemon_name = data.get("name", "none").title()
            species_data = await self.get_data(
                f'{API_URL}/pokemon-species/{data.get("id")}'
            )

            if not species_data.get("http_code"):
                with suppress(IndexError):
                    pokemon_name = [
                        x["name"]
                        for x in species_data["names"]
                        if x["language"]["name"] == "en"
                    ][0]
                embed = self.species_embed(embed, species_data)
            embed = self.base_stats_embed(embed, data)
            if species_data and species_data.get("evolution_chain"):
                evo_url = species_data["evolution_chain"].get("url")
                if_evolves = await self.evolution_chain(evo_url)
                if if_evolves:
                    embed.add_field(
                        name="Evolution Chain", value=if_evolves, inline=False
                    )

            type_effect_url = (
                f"{BULBAPEDIA_URL}/{pokemon_name.replace(' ', '_')}"
                "_%28Pokémon%29#Type_effectiveness"
            )
            embed.add_field(
                name="Weakness/Resistance",
                value=f"[See it on Bulbapedia]({type_effect_url})",
            )
            embed.set_author(
                name=f"#{data['id']:>03} - {pokemon_name}",
                url=f"https://www.pokemon.com/us/pokedex/{data.get('name')}",
            )
        await ctx.send(embed=embed)

    @pokedex.command()
    async def ability(self, ctx: Context, *, ability: str):
        """Get various info about a known Pokémon ability.

        You can search by ability's name or it's unique ID.

        Abilities provide passive effects for Pokémon in battle or in the overworld.
        Pokémon have multiple possible abilities but can have only one ability at a time.

        Check out Bulbapedia for greater detail:
        • http://bulbapedia.bulbagarden.net/wiki/Ability
        • https://bulbapedia.bulbagarden.net/wiki/Ability#List_of_Abilities
        """
        async with ctx.typing():
            data = await self.get_data(
                f'{API_URL}/ability/{ability.replace(" ", "-").lower()}'
            )
            if err := data.get("http_code"):
                if err == 404:
                    return await ctx.send(
                        "⚠ Could not find Pokémon abilities with that name."
                    )
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{data}"
                )
            if not data:
                return await ctx.send(
                    "Something went wrong while trying to query PokeAPI."
                )

            embed = Embed(colour=await ctx.embed_colour())
            embed.title = data.get("name").replace("-", " ").title()
            embed.url = f'{BULBAPEDIA_URL}/{data.get("name").title().replace("-", "_")}_%28Ability%29'
            effect_entries = data.get("effect_entries", [{}])
            embed.description = [
                x.get("effect")
                for x in effect_entries
                if x["language"].get("name") == "en"
            ][0]

            if data.get("generation"):
                embed.add_field(
                    name="Introduced In",
                    value=f'Gen. **{data["generation"].get("name").split("-")[1].upper()}**',
                )
            short_effect = [
                x.get("short_effect")
                for x in effect_entries
                if x["language"].get("name") == "en"
            ][0]
            embed.add_field(name="Ability's Effect", value=short_effect, inline=False)
            if data.get("pokemon"):
                pokemons = ", ".join(
                    x["pokemon"].get("name").title() for x in data["pokemon"]
                )
                embed.add_field(
                    name=f"Pokémons with {data.get('name').title()}",
                    value=pokemons,
                    inline=False,
                )
            embed.set_footer(text="Powered by Poke API")
        await ctx.send(embed=embed)

    @pokedex.command()
    async def moves(self, ctx: Context, pokemon: str):
        """Get the Pokémon's moves set."""
        pokemon = pokemon.replace(" ", "-")
        async with ctx.typing():
            data = await self.get_data(f"{API_URL}/pokemon/{pokemon.lower()}")
            if err := data.get("http_code"):
                if err == 404:
                    return await ctx.send("⚠ Could not find Pokémon moves.")
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{data}"
                )
            if not (data or data.get("moves")):
                return await ctx.send("No moves found for this Pokémon.")

            moves_list = "\n".join(
                f'`[{i:>2}]` **{move["move"]["name"].title().replace("-", " ")}**'
                for i, move in enumerate(data["moves"], start=1)
            )

            pages = []
            all_pages = list(pagify(moves_list, page_length=400))
            for i, page in enumerate(all_pages, start=1):
                embed = Embed(colour=await ctx.embed_colour(), description=page)
                embed.title = f"Moves for : {data['name'].title()} (#{data['id']:>03})"
                embed.set_thumbnail(
                    url=f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{data['id']:>03}.png",
                )
                embed.set_footer(text=f"Page {i} of {len(all_pages)}")
                pages.append(embed)
        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def moveinfo(self, ctx: Context, *, move: str):
        """Fetch info about a Pokémon's move.

        You can search by a move name or it's ID.

        Moves are the skills of Pokémon in battle.
        In battle, a Pokémon uses one move each turn.

        Some moves (including those learned by Hidden Machine) can be used outside of
        battle as well, usually for the purpose of removing obstacles or exploring new areas.

        You can find a list of known Pokémon moves here:
        https://bulbapedia.bulbagarden.net/wiki/List_of_moves
        """
        move_query = move.replace(",", " ").replace(" ", "-").replace("'", "").lower()
        async with ctx.typing():
            data = await self.get_data(f"{API_URL}/move/{move_query}")
            if err := data.get("http_code"):
                if err == 404:
                    return await ctx.send(
                        "⚠ Could not find Pokémon move with that name."
                    )
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{data}"
                )
            if not data:
                return await ctx.send(
                    "Something went wrong while trying to query PokeAPI."
                )

            embed = Embed(colour=await ctx.embed_colour())
            embed.title = data.get("name").replace("-", " ").title()
            embed.url = (
                f'{BULBAPEDIA_URL}/{capwords(move).replace(" ", "_")}_%28move%29'
            )
            if data.get("effect_entries"):
                effect = "\n".join(
                    [
                        f"{x.get('short_effect')}\n{x.get('effect')}"
                        for x in data.get("effect_entries", [{}])
                        if x.get("language").get("name") == "en"
                    ]
                )
                embed.description = f"**Move Effect:** \n\n{effect}"

            if data.get("generation"):
                embed.add_field(
                    name="Introduced In",
                    value=f'Gen. **{data["generation"].get("name").split("-")[1].upper()}**',
                )
            if data.get("accuracy"):
                embed.add_field(name="Accuracy", value=f"{data.get('accuracy')}%")
            embed.add_field(name="Base Power", value=str(data.get("power")))
            if data.get("effect_chance"):
                embed.add_field(
                    name="Effect Chance", value=f"{data.get('effect_chance')}%"
                )
            embed.add_field(name="Power Points (PP)", value=str(data.get("pp")))
            if data.get("type"):
                embed.add_field(
                    name="Move Type", value=data.get("type").get("name").title()
                )
            if data.get("contest_type"):
                embed.add_field(
                    name="Contest Type",
                    value=data.get("contest_type").get("name").title(),
                )
            if data.get("damage_class"):
                embed.add_field(
                    name="Damage Class",
                    value=data.get("damage_class").get("name").title(),
                )
            embed.add_field(name="\u200b", value="\u200b")
            if data.get("learned_by_pokemon"):
                learned_by = [
                    x.get("name").title() for x in data.get("learned_by_pokemon", [{}])
                ]
                embed.add_field(
                    name=f"Learned by {len(learned_by)} Pokémons",
                    value=f'{", ".join(learned_by)[:500]}... and more.',
                    inline=False,
                )

            embed.set_footer(text="Powered by Poke API")
        await ctx.send(embed=embed)

    @pokedex.command()
    async def item(self, ctx: Context, *, item: str):
        """Get various info about a Pokémon item.

        You can search by an item's name or unique ID.

        An item is an object in the games which the player can pick up,
        keep in their bag, and use in some manner.

        They have various uses, including healing, powering up,
        helping catch Pokémon, or to access a new area.

        For more info:
        • https://bulbapedia.bulbagarden.net/wiki/Item
        • https://bulbapedia.bulbagarden.net/wiki/Category:Items
        """
        item = item.replace(" ", "-").lower()
        async with ctx.typing():
            embed = Embed(colour=await ctx.embed_colour())
            item_data = await self.get_data(f"{API_URL}/item/{item}")
            if err := item_data.get("http_code"):
                if err == 404:
                    return await ctx.send(
                        "⚠ Could not find Pokémon item with that name."
                    )
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{item_data}"
                )
            if not item_data:
                return await ctx.send("No results.")

            embed.title = item_data.get("name").title().replace("-", " ")
            embed.url = f"{BULBAPEDIA_URL}/{item.title().replace('-', '_')}"
            effect_entries = item_data.get("effect_entries", [{}])
            item_effect = (
                "**Item effect:** "
                + [
                    x.get("effect")
                    for x in effect_entries
                    if x["language"].get("name") == "en"
                ][0]
            )
            item_summary = (
                "**Summary:** "
                + [
                    x.get("short_effect")
                    for x in item_data.get("effect_entries", [{}])
                    if x.get("language").get("name") == "en"
                ][0]
            )
            embed.description = f"{item_effect}\n\n{item_summary}"
            embed.add_field(name="Cost", value=humanize_number(item_data.get("cost")))
            embed.add_field(
                name="Category",
                value=str(
                    item_data.get("category")
                    .get("name", "unknown")
                    .title()
                    .replace("-", " ")
                ),
            )
            if item_data.get("attributes"):
                attributes = "\n".join(
                    x.get("name").title().replace("-", " ")
                    for x in item_data["attributes"]
                )
                embed.add_field(name="Attributes", value=attributes)
            if item_data.get("fling_power"):
                embed.add_field(
                    name="Fling Power", value=humanize_number(item_data["fling_power"])
                )
            if item_data.get("fling_effect"):
                fling_data = await self.get_data(item_data["fling_effect"]["url"])
                if not fling_data.get("http_code"):
                    fling_effect = [
                        x.get("effect")
                        for x in fling_data.get("effect_entries", [{}])
                        if x.get("language").get("name") == "en"
                    ][0]
                    embed.add_field(
                        name="Fling Effect", value=fling_effect, inline=False
                    )
            if item_data.get("held_by_pokemon"):
                held_by = ", ".join(
                    x.get("pokemon").get("name").title()
                    for x in item_data["held_by_pokemon"]
                )
                embed.add_field(name="Held by Pokémon(s)", value=held_by, inline=False)
            embed.set_footer(text="Powered by Poke API!")
        await ctx.send(embed=embed)

    @commands.command(name="itemcategory", aliases=["itemcat"])
    @commands.bot_has_permissions(embed_links=True)
    async def item_category(self, ctx: Context, *, category: str):
        """Fetch items in a given Pokémon item category."""
        category = category.replace(" ", "-").lower()
        async with ctx.typing():
            category_data = await self.get_data(f"{API_URL}/item-category/{category}")
            if err := category_data.get("http_code"):
                if err == 404:
                    return await ctx.send(
                        "⚠ Could not find Pokémon item category with that name."
                    )
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{category_data}"
                )
            if not category_data:
                return await ctx.send("No results.")
            embed = Embed(colour=await ctx.embed_colour())
            embed.title = f"{category_data['name'].title().replace('-', ' ')}"
            items_list = "\n".join(
                f'**{i}.** {item.get("name").title().replace("-", " ")}'
                for i, item in enumerate(category_data.get("items"), 1)
            )
            embed.description = (
                "__**List of items in this category:**__\n\n" + items_list
            )
            embed.set_footer(text="Powered by Poke API!")
        await ctx.send(embed=embed)

    @pokedex.command()
    async def location(self, ctx: Context, pokemon: str):
        """Responds with the location data for a Pokémon."""
        pokemon = pokemon.replace(" ", "-")
        async with ctx.typing():
            data = await self.get_data(f"{API_URL}/pokemon/{pokemon.lower()}")
            if err := data.get("http_code"):
                if err == 404:
                    return await ctx.send("⚠ Could not find a location with that name.")
                return await ctx.send(
                    f"⚠ API sent response code: https://http.cat/{data}"
                )
            if not data or not data.get("location_area_encounters"):
                return await ctx.send("No location data found for said Pokémon.")

            get_encounters = await self.get_data(data["location_area_encounters"])
            if get_encounters.get("http_code"):
                return await ctx.send("No location data found for this Pokémon.")

            jquery = jmespath.compile(
                "[*].{url: location_area.url, name: version_details[*].version.name}"
            )
            new_dict = jquery.search(get_encounters)

            pretty_data = ""
            for i, loc in enumerate(new_dict, 1):
                area_data = await self.get_data(loc["url"])
                if area_data.get("http_code"):
                    continue
                location_data = await self.get_data(area_data["location"]["url"])
                if location_data.get("http_code"):
                    continue
                location_names = ", ".join(
                    x["name"]
                    for x in location_data["names"]
                    if x["language"]["name"] == "en"
                )
                generations = "/".join(x.title().replace("-", " ") for x in loc["name"])
                pretty_data += f"`[{i:>2}]` {bold(location_names)} ({generations})\n"

            embed = Embed(colour=await ctx.embed_colour(), description=pretty_data)
            embed.title = f"#{data['id']:>03} - {data['name'].title()}"
            embed.url = f"{BULBAPEDIA_URL}/{data['name'].title()}_%28Pok%C3%A9mon%29#Game_locations"
            embed.set_thumbnail(
                url=f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{data['id']:>03}.png",
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def tcgcard(self, ctx: Context, *, query: str):
        """Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG)."""
        api_key = (await ctx.bot.get_shared_api_tokens("pokemontcg")).get("api_key")
        headers = {"X-Api-Key": api_key} if api_key else None
        async with ctx.typing():
            base_url = f"https://api.pokemontcg.io/v2/cards?q=name:{query}"
            try:
                async with self.session.get(base_url, headers=headers) as response:
                    if response.status != 200:
                        await ctx.send(f"https://http.cat/{response.status}")
                        return
                    output = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if not output["data"]:
                return await ctx.send("No results.")

            pages = []
            for i, data in enumerate(output["data"], 1):
                embed = Embed(colour=await ctx.embed_colour())
                embed.title = data["name"]
                embed.description = "**Rarity:** " + str(data.get("rarity"))
                embed.add_field(name="Artist:", value=str(data.get("artist")))
                embed.add_field(
                    name="Belongs to Set:", value=str(data["set"]["name"]), inline=False
                )
                embed.add_field(
                    name="Set Release Date:", value=str(data["set"]["releaseDate"])
                )
                embed.set_thumbnail(url=str(data["set"]["images"]["logo"]))
                embed.set_image(url=str(data["images"]["large"]))
                embed.set_footer(
                    text=f"Page {i} of {len(output['data'])} • Powered by Pokémon TCG API!"
                )
                pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])

        await menu(ctx, pages, DEFAULT_CONTROLS, timeout=60.0)

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def trainercard(
        self,
        ctx: Context,
        name: str,
        style: str,
        trainer: str,
        badge: str,
        *,
        pokemons: str,
    ):
        """Generate a trainer card for a Pokémon trainer in different styles.

        This command requires you to pass values for multiple parameters.

        Supported values for these parameters are explained briefly as follows:
        ```apache
        name    : Provide any personalised name of your choice.
        style   : default, black, collector, dp, purple
        trainer : ash, red, ethan, lyra, brendan, may, lucas, dawn
        badge   : kanto, johto, hoenn, sinnoh, unova and kalos
        pokemons: You can provide maximum up to 6 Pokémon's names or #IDs
        ```

        ℹ Pokémons from #891 to #898 are not supported yet for trainer card
        """
        base_url = "https://pokecharms.com/index.php?trainer-card-maker/render"
        if style.lower() not in ["default", "black", "collector", "dp", "purple"]:
            return await ctx.send(
                f"style value `{style}` is unsupported. See command help!"
            )
        if trainer.lower() not in [
            "ash",
            "red",
            "ethan",
            "lyra",
            "brendan",
            "may",
            "lucas",
            "dawn",
        ]:
            return await ctx.send(
                f"trainer value `{trainer}` is unsupported. See command help!"
            )
        if badge.lower() not in ["kanto", "johto", "hoenn", "sinnoh", "unova", "kalos"]:
            return await ctx.send(
                f"badge value `{badge}` is unsupported. See command help!"
            )
        if len(pokemons.split()) > 6:
            return await ctx.send("You cannot provide more than 6 Pokémons.")

        async with ctx.typing():
            pkmn_ids = []
            for pokemon in pokemons.split():
                get_ids = await self.get_data(f"{API_URL}/pokemon/{pokemon.lower()}")
                if get_ids.get("http_code"):
                    continue
                if get_ids.get("id"):
                    pkmn_ids.append(get_ids["id"])

            panel_ids = []
            panel_url = "https://pokecharms.com/trainer-card-maker/pokemon-panels"
            for npn in pkmn_ids:
                payload = aiohttp.FormData()
                payload.add_field("number", npn)
                payload.add_field("_xfResponseType", "json")
                async with self.session.post(panel_url, data=payload) as resp:
                    if resp.status != 200:
                        panel_ids.append("1")
                    soup = bsp((await resp.json()).get("templateHtml"), "html.parser")
                    try:
                        panel_ids.append(soup.find_all("li")[0].get("data-id"))
                    except IndexError:
                        panel_ids.append("1")

            form = aiohttp.FormData()
            form.add_field("trainername", name[:12])
            form.add_field("background", str(STYLES[style.lower()]))
            form.add_field("character", str(TRAINERS[trainer.lower()]))
            form.add_field("badges", "8")
            form.add_field(
                "badgesUsed", ",".join(str(x) for x in BADGES[badge.lower()])
            )
            form.add_field("pokemon", str(len(pokemons.split())))
            form.add_field("pokemonUsed", ",".join(panel_ids))
            form.add_field("_xfResponseType", "json")
            try:
                async with self.session.post(base_url, data=form) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    output = (await response.json()).get("trainerCard")
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

        if output:
            base64_img_bytes = output.encode("utf-8")
            decoded_image_data = BytesIO(base64.decodebytes(base64_img_bytes))
            decoded_image_data.seek(0)
            await ctx.send(file=File(decoded_image_data, "trainer-card.png"))
            return
        else:
            await ctx.send("No trainer card was generated. :(")
