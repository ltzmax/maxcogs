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

from red_commons.logging import getLogger
from redbot.core import app_commands, commands

from ..api import API_URL, fetch_data
from ..formatters import create_pokemon_embed
from ..views import PokemonView


log = getLogger("red.maxcogs.whosthatpokemon.commands.pokeinfo")


class PokeinfoCommands:
    """pokeinfo command — mixed into the main Pokemon cog."""

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
        pokemon_data = await fetch_data(self.session, f"{API_URL}/pokemon/{pokemon.lower()}")
        if not pokemon_data or pokemon_data.get("http_code"):
            code = pokemon_data.get("http_code") if pokemon_data else None
            if code == 404:
                return await ctx.send(f"No Pokémon found for `{pokemon}`.")
            return await ctx.send("Could not fetch Pokémon data. Please try again later.")

        view = PokemonView(ctx, self.session, pokemon_data)
        try:
            embed = await create_pokemon_embed(self.session, pokemon_data, "base")
            view.message = await ctx.send(embed=embed, view=view)
        except ValueError as e:
            log.error("Error creating initial embed: %s", e, exc_info=True)
            await ctx.send("Something went wrong building the Pokémon embed.")
