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

import orjson
from red_commons.logging import getLogger
from redbot.core import app_commands, commands

from ..views import TcgCardView


log = getLogger("red.maxcogs.whosthatpokemon.commands.tcgcard")

_TCG_FIELDS = (
    "id,name,supertype,subtypes,hp,types,evolvesFrom,evolvesTo,abilities,attacks,"
    "weaknesses,resistances,retreatCost,convertedRetreatCost,number,artist,rarity,"
    "flavorText,nationalPokedexNumbers,legalities,regulationMark,images,set"
)


def _build_card_text(data: dict) -> str:
    """Build a plain-text summary of a TCG card's details."""
    lines = []

    lines.append(f"**Supertype:** {data.get('supertype', 'N/A')}")
    subtypes = ", ".join(data.get("subtypes", [])) or "N/A"
    lines.append(f"**Subtypes:** {subtypes}")
    types = ", ".join(data.get("types", [])) or "N/A"
    lines.append(f"**Types:** {types}")
    lines.append(f"**Evolves From:** {data.get('evolvesFrom', 'None')}")
    evolves_to = ", ".join(data.get("evolvesTo", [])) or "None"
    lines.append(f"**Evolves To:** {evolves_to}")
    lines.append(f"**Rarity:** {data.get('rarity', 'Common')}")
    lines.append(f"**Artist:** {data.get('artist', 'N/A')}")
    lines.append(f"**Regulation Mark:** {data.get('regulationMark', 'N/A')}")
    lines.append(f"**Card Number:** {data.get('number', 'N/A')}")
    lines.append(f"**Set:** {data['set']['name']}")
    nat_dex = ", ".join(map(str, data.get("nationalPokedexNumbers", []))) or "N/A"
    lines.append(f"**National Pokédex:** {nat_dex}")
    legalities = data.get("legalities", {})
    legal_str = (
        ", ".join(k.capitalize() for k, v in legalities.items() if v == "Legal") or "None"
    )
    lines.append(f"**Legalities:** {legal_str}")

    abilities = data.get("abilities", [])
    if abilities:
        lines.append("")
        lines.append("**Abilities:**")
        for ability in abilities:
            lines.append(f"• {ability.get('name', 'N/A')} ({ability.get('type', 'N/A')})")
            if text := ability.get("text"):
                lines.append(f"  {text}")

    attacks = data.get("attacks", [])
    if attacks:
        lines.append("")
        lines.append("**Attacks:**")
        for attack in attacks:
            cost = " ".join(attack.get("cost", []))
            converted = attack.get("convertedEnergyCost", 0)
            damage = attack.get("damage", "N/A")
            lines.append(
                f"• {attack.get('name', 'N/A')} - Cost: {cost} ({converted}) - Damage: {damage}"
            )
            if text := attack.get("text"):
                lines.append(f"  {text}")

    weaknesses = data.get("weaknesses", [])
    resistances = data.get("resistances", [])
    retreat_cost = data.get("retreatCost", [])
    converted_retreat = data.get("convertedRetreatCost", 0)

    wr_lines = []
    if weaknesses:
        wr_lines.append(
            f"**Weakness:** {weaknesses[0].get('type', 'N/A')} ({weaknesses[0].get('value', 'N/A')})"
        )
    if resistances:
        wr_lines.append(
            f"**Resistance:** {resistances[0].get('type', 'N/A')} ({resistances[0].get('value', 'N/A')})"
        )
    retreat_symbols = "🌟" * len(retreat_cost) if retreat_cost else "None"
    wr_lines.append(f"**Retreat Cost:** {retreat_symbols} ({converted_retreat})")
    if wr_lines:
        lines.append("")
        lines.extend(wr_lines)

    if flavor := data.get("flavorText"):
        lines.append("")
        lines.append(f"**Flavor Text:** *{flavor}*")

    return "\n".join(lines)


class TcgcardCommands:
    """tcgcard command mixed into the main Pokemon cog."""

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
                match response.status:
                    case 200:
                        output = orjson.loads(await response.read())
                    case _:
                        log.error("Failed to fetch TCG data status %s", response.status)
                        return await ctx.send(f"https://http.cat/{response.status}")
        except asyncio.TimeoutError:
            log.error("Timed out fetching TCG data.")
            return await ctx.send("Operation timed out.")

        if not output["data"]:
            return await ctx.send("There are no results for that search.")

        accent = await ctx.embed_color()
        view = TcgCardView(ctx, output["data"], _build_card_text, accent)
        view.message = await ctx.send(view=view)
