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

from typing import Dict

import aiohttp
import discord
from red_commons.logging import getLogger

from .api import API_URL, fetch_data

log = getLogger("red.maxcogs.whosthatpokemon.formatters")

MAX_DESCRIPTION_LENGTH = 4000


def _format_list(items: list[str], separator: str = ", ") -> str:
    """Format a list of items into a human-readable string."""
    return separator.join(items) if items else "None"


def _get_official_artwork(sprites: dict) -> str | None:
    """Get the official artwork URL from sprites, falling back to front_default."""
    return sprites.get("other", {}).get("official-artwork", {}).get(
        "front_default"
    ) or sprites.get("front_default")


def _format_stats(stats: list[dict]) -> str:
    """Format base stats into a readable string with total."""
    if not stats:
        return "No stats available."
    stat_lines = [f"{s['stat']['name'].capitalize()}: {s['base_stat']}" for s in stats]
    total = sum(s["base_stat"] for s in stats)
    return "\n".join(stat_lines) + f"\nTotal: {total}"


def _format_height_weight(height: int, weight: int) -> tuple[str, str]:
    """Format height and weight in metric and imperial units."""
    return (
        f"{height/10:.1f}m ({height*3.28084/10:.2f}ft)",
        f"{weight/10:.1f}kg ({weight*2.20462/10:.2f}lbs)",
    )


def _format_abilities(abilities: list[dict]) -> str:
    """Format abilities, including hidden ones."""
    if not abilities:
        return "No abilities available."
    ability_names = [a["ability"]["name"].capitalize() for a in abilities]
    hidden = [a["ability"]["name"].capitalize() for a in abilities if a.get("is_hidden", False)]
    hidden_str = f" (Hidden: {_format_list(hidden or ['None'])})"
    return _format_list(ability_names) + hidden_str


def _format_game_indices(game_indices: list[dict]) -> str:
    """Format game indices into a readable string."""
    if not game_indices:
        return "No game indices available."
    return _format_list(
        [f"{g['game_index']} ({g['version']['name'].capitalize()})" for g in game_indices]
    )


def _format_types(types: list[dict]) -> str:
    """Format Pokémon types into a readable string."""
    return _format_list([t["type"]["name"].capitalize() for t in types])


def _truncate_description(text: str) -> str:
    """Truncate text if it exceeds the maximum description length."""
    return text[:MAX_DESCRIPTION_LENGTH] + "..." if len(text) > MAX_DESCRIPTION_LENGTH else text


async def create_pokemon_embed(
    session: aiohttp.ClientSession, pokemon_data: Dict, section: str = "base"
) -> discord.Embed:
    """
    Create a Discord embed for Pokémon data based on the specified section.

    Args:
        session: The aiohttp ClientSession.
        pokemon_data: The Pokémon data from PokéAPI.
        section: The section to display (base, held_items, moves, locations).

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
        color=0xFF0000,
        url=f"https://www.pokemon.com/us/pokedex/{pokemon_data['name']}",
    )

    thumbnail_url = sprites.get("front_default")
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    image_url = _get_official_artwork(sprites)
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

        embed.add_field(name="Base Stats:", value=_format_stats(stats), inline=False)
        height_str, weight_str = _format_height_weight(height, weight)
        embed.add_field(name="Height:", value=height_str, inline=True)
        embed.add_field(name="Weight:", value=weight_str, inline=True)
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Base Experience:", value=base_experience, inline=True)
        embed.add_field(name="Types:", value=_format_types(types), inline=True)
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Abilities:", value=_format_abilities(abilities), inline=False)
        embed.add_field(
            name="Game Indices:", value=_format_game_indices(game_indices), inline=False
        )

    elif section == "held_items":
        held_items = pokemon_data.get("held_items", [])
        if not held_items:
            embed.description = "No held items data available."
        else:
            items_info = _format_list(
                [
                    f"{h['item']['name'].capitalize()} ({h['version_details'][0]['rarity'] if h['version_details'] else 'Unknown'})"
                    for h in held_items
                    if "item" in h
                ]
            )
            embed.description = _truncate_description(items_info)

    elif section == "moves":
        moves = pokemon_data.get("moves", [])
        if not moves:
            embed.description = "No moves data available."
        else:
            moves_info = _format_list(
                [
                    f"{m['move']['name'].capitalize()} ({m['version_group_details'][0]['level_learned_at'] if m['version_group_details'] else 'Unknown'})"
                    for m in moves
                    if m.get("move") and m["move"].get("name")
                ]
            )
            embed.description = _truncate_description(moves_info)

    elif section == "locations":
        location_url = f"{API_URL}/pokemon/{pokemon_data['id']}/encounters"
        location_areas = await fetch_data(session, location_url)
        if not location_areas:
            embed.description = "No location data available."
        else:
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
                    chance = detail.get("encounter_details", [{}])[0].get("chance", "Unknown")
                    versions.append(f"{version_name}: {chance}%")
                versions_str = "\n".join(versions) if versions else "No version details"
                locations.append(f"**{location_name}**:\n{versions_str}")
            embed.description = _truncate_description("\n\n".join(locations))

    else:
        raise ValueError(f"Unsupported section: {section}")

    embed.set_footer(text=f"Powered by PokéAPI | Pokémon ID: {pokemon_data.get('id', 'Unknown')}")
    return embed
