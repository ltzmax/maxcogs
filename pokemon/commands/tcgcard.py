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

import discord
import orjson
from red_commons.logging import getLogger
from redbot.core import app_commands, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import SimpleMenu


log = getLogger("red.maxcogs.whosthatpokemon.commands.tcgcard")

_TCG_FIELDS = (
    "id,name,supertype,subtypes,hp,types,evolvesFrom,evolvesTo,abilities,attacks,"
    "weaknesses,resistances,retreatCost,convertedRetreatCost,number,artist,rarity,"
    "flavorText,nationalPokedexNumbers,legalities,regulationMark,images,set"
)


class TcgcardCommands:
    """tcgcard command — mixed into the main Pokemon cog."""

    @commands.hybrid_command()
    @app_commands.describe(query="The Pokémon you want to search a card for.")
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
        base_url = f"https://api.pokemontcg.io/v2/cards?q=name:{query}&select={_TCG_FIELDS}"
        try:
            async with self.session.get(base_url, headers=headers) as response:
                if response.status != 200:
                    log.error("Failed to fetch TCG data — status %s", response.status)
                    return await ctx.send(f"https://http.cat/{response.status}")
                output = orjson.loads(await response.read())
        except asyncio.TimeoutError:
            log.error("Timed out fetching TCG data.")
            return await ctx.send("Operation timed out.")

        if not output["data"]:
            return await ctx.send("There are no results for that search.")

        pages = []
        for i, data in enumerate(output["data"], 1):
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 215, 0))
            card_name = data["name"]
            hp = data.get("hp", "N/A")
            embed.title = f"{card_name} - HP: {hp}"

            basic_info = []
            basic_info.append(f"{'Supertype:':<18}{data.get('supertype', 'N/A')}")
            subtypes_str = ", ".join(data.get("subtypes", [])) or "N/A"
            basic_info.append(f"{'Subtypes:':<18}{subtypes_str}")
            types_str = ", ".join(data.get("types", [])) or "N/A"
            basic_info.append(f"{'Types:':<18}{types_str}")
            basic_info.append(f"{'Evolves From:':<18}{data.get('evolvesFrom', 'None')}")
            evolves_to_str = ", ".join(data.get("evolvesTo", [])) or "None"
            basic_info.append(f"{'Evolves To:':<18}{evolves_to_str}")
            basic_info.append(f"{'Rarity:':<18}{data.get('rarity', 'Common')}")
            basic_info.append(f"{'Artist:':<18}{data.get('artist', 'N/A')}")
            basic_info.append(f"{'Regulation Mark:':<18}{data.get('regulationMark', 'N/A')}")
            basic_info.append(f"{'Card Number:':<18}{data.get('number', 'N/A')}")
            basic_info.append(f"{'Set:':<18}{data['set']['name']}")
            nat_dex_str = ", ".join(map(str, data.get("nationalPokedexNumbers", []))) or "N/A"
            basic_info.append(f"{'National Pokedex:':<18}{nat_dex_str}")
            legalities = data.get("legalities", {})
            legal_str = (
                ", ".join(k.capitalize() for k, v in legalities.items() if v == "Legal") or "None"
            )
            basic_info.append(f"{'Legalities:':<18}{legal_str}")
            embed.add_field(
                name="Card Info", value=box("\n".join(basic_info), lang="yaml"), inline=False
            )
            abilities = data.get("abilities", [])
            if abilities:
                abilities_str = []
                for ability in abilities:
                    ability_name = ability.get("name", "N/A")
                    ability_type = ability.get("type", "N/A")
                    ability_text = ability.get("text", "")
                    abilities_str.append(f"{'Name:':<18}{ability_name}")
                    abilities_str.append(f"{'Type:':<18}{ability_type}")
                    if ability_text:
                        abilities_str.append(f"{'Text:':<18}{ability_text}")
                    abilities_str.append("")
                embed.add_field(
                    name="Abilities",
                    value=box("\n".join(abilities_str[:-1]), lang="yaml"),
                    inline=False,
                )

            attacks = data.get("attacks", [])
            if attacks:
                attacks_str = []
                for attack in attacks:
                    attack_name = attack.get("name", "N/A")
                    cost = attack.get("cost", [])
                    damage = attack.get("damage", "N/A")
                    attack_text = attack.get("text", "")
                    converted_cost = attack.get("convertedEnergyCost", 0)
                    attacks_str.append(f"{'Name:':<18}{attack_name}")
                    attacks_str.append(f"{'Cost:':<18}{' '.join(cost)} ({converted_cost})")
                    attacks_str.append(f"{'Damage:':<18}{damage}")
                    if attack_text:
                        attacks_str.append(f"{'Text:':<18}{attack_text}")
                    attacks_str.append("")
                embed.add_field(
                    name="Attacks",
                    value=box("\n".join(attacks_str[:-1]), lang="yaml"),
                    inline=False,
                )

            # Weaknesses / Resistances / Retreat
            wr_info = []
            weaknesses = data.get("weaknesses", [])
            if weaknesses:
                wr_info.append(
                    f"{'Weakness:':<18}{weaknesses[0].get('type', 'N/A')} ({weaknesses[0].get('value', 'N/A')})"
                )
            resistances = data.get("resistances", [])
            if resistances:
                wr_info.append(
                    f"{'Resistance:':<18}{resistances[0].get('type', 'N/A')} ({resistances[0].get('value', 'N/A')})"
                )
            retreat_cost = data.get("retreatCost", [])
            converted_retreat = data.get("convertedRetreatCost", 0)
            retreat_symbols = "🌟" * len(retreat_cost) if retreat_cost else "None"
            wr_info.append(f"{'Retreat Cost:':<18}{retreat_symbols} ({converted_retreat})")
            if wr_info:
                embed.add_field(
                    name="Weaknesses / Resistances / Retreat",
                    value=box("\n".join(wr_info), lang="yaml"),
                    inline=False,
                )

            flavor_text = data.get("flavorText", "")
            if flavor_text:
                embed.add_field(
                    name="Flavor Text", value=box(flavor_text, lang="yaml"), inline=False
                )

            embed.set_thumbnail(url=str(data["set"]["images"]["logo"]))
            embed.set_image(url=str(data["images"]["large"]))
            embed.set_footer(
                text=f"Page {i} of {len(output['data'])} • Powered by Pokémon TCG API!"
            )
            pages.append(embed)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
