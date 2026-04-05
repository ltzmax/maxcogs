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
from datetime import datetime, timedelta, timezone
from random import randint

import discord
from discord import File
from red_commons.logging import getLogger
from redbot.core import app_commands, commands

from ..api import API_URL, fetch_data
from ..converters import Generation
from ..image import generate_image
from ..views import HintView, WhosThatPokemonView


log = getLogger("red.maxcogs.whosthatpokemon.commands.whosthatpokemon")


class WhosThatPokemonCommands:
    """whosthatpokemon command — mixed into the main Pokemon cog."""

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(generation="Optionally choose generation from gen1 to gen9.")
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
        poke_id_str = f"{poke_id:>03}"
        (species_data, pokemon_data), (hidden_temp, revealed_temp) = await asyncio.gather(
            asyncio.gather(
                fetch_data(self.session, f"{API_URL}/pokemon-species/{poke_id}"),
                fetch_data(self.session, f"{API_URL}/pokemon/{poke_id}"),
            ),
            asyncio.gather(
                generate_image(self, poke_id_str, hide=True),
                generate_image(self, poke_id_str, hide=False),
            ),
        )

        if not species_data or species_data.get("http_code"):
            log.error("Failed to get species data: %s", species_data)
            return await ctx.send("Failed to get species data from PokéAPI.")
        if not pokemon_data or pokemon_data.get("http_code"):
            log.error("Failed to get Pokémon data: %s", pokemon_data)
            return await ctx.send("Failed to fetch Pokémon data.")
        if hidden_temp is None or revealed_temp is None:
            log.error("Failed to generate image for poke_id %s", poke_id)
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        names_data = species_data.get("names", [{}])
        eligible_names = [x["name"].lower() for x in names_data]
        english_name = next(
            (x["name"] for x in names_data if x["language"]["name"] == "en"),
            "Unknown",
        )

        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(seconds=30.0), "R"
        )

        view = WhosThatPokemonView(eligible_names)
        hint_view = HintView(
            {"species_data": species_data, "pokemon_data": pokemon_data},
            english_name,
        )
        view.add_item(hint_view.hint_button)

        view.message = await ctx.send(
            f"**Who's that Pokémon?**\nI need a valid answer at most {img_timeout}.\n"
            "Use the hint button for help (one use only)!",
            file=File(hidden_temp, "guessthatpokemon.png"),
            view=view,
        )

        embed = discord.Embed(
            title=":tada: You got it right! :tada:",
            description=f"The Pokemon was... **{english_name}**.",
            color=0x76EE00,
        )
        embed.set_image(url="attachment://whosthatpokemon.png")
        embed.set_footer(text=f"Author: {ctx.author}", icon_url=ctx.author.display_avatar.url)

        timed_out = await view.wait()
        if timed_out:
            return await ctx.send(
                f"{ctx.author.mention} You took too long to answer.\n"
                f"The Pokemon was... **{english_name}**."
            )
        await ctx.send(file=File(revealed_temp, "whosthatpokemon.png"), embed=embed)
