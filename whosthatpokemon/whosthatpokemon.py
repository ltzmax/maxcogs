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
from datetime import datetime, timedelta, timezone
from random import randint
from typing import Any, Final, List, Optional
from io import BytesIO

import aiohttp
import discord
import logging
import asyncio
from PIL import Image
from discord import File
from perftracker import perf, get_stats
from redbot.core.data_manager import bundled_data_path
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu
from .converters import (
    WhosThatPokemonView,
    get_data,
    Generation,
)

log = logging.getLogger("red.maxcogs.whosthatpokemon")

API_URL: Final[str] = "https://pokeapi.co/api/v2"


class WhosThatPokemon(commands.Cog):
    """Can you guess Who's That Pokémon?"""

    __author__: Final[List[str]] = ["@306810730055729152", "max", "flame442"]
    __version__: Final[str] = "1.4.2"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/whosthatpokemon"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_user = {
            "total_correct_guesses": 0,
        }
        self.config.register_user(**default_user)

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {humanize_list(self.__author__)}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @perf(max_entries=1000)
    async def generate_image(self, poke_id: str, *, hide: bool) -> Optional[BytesIO]:
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
            log.error(f"Failed to get data from {base_url} due to timeout")
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

    @commands.command(name="wtpversion", hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def whosthatpokemon_version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog"""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(
        generation=("Optionally choose generation from gen1 to gen9.")
    )
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
        english_name = [x["name"] for x in names_data if x["language"]["name"] == "en"][
            0
        ]

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
        if await self.config.user(ctx.author).all():
            await self.config.user(ctx.author).total_correct_guesses.set(
                await self.config.user(ctx.author).total_correct_guesses() + 1
            )
            log.info(
                f"{ctx.author} guessed the pokemon correctly and got a point added to their total correct guesses."
            )
        await ctx.send(file=revealed_img, embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="wtpleaderboard", aliases=["wtplb"])
    async def whosthatpokemon_leaderboard(self, ctx: commands.Context):
        """Shows the leaderboard for whosthatpokemon.

        This is global leaderboard and not per server.
        This will show the top 10 users with most correct guesses.
        """
        pages = []
        users = await self.config.all_users()
        sorted_users = sorted(
            users.items(), key=lambda x: x[1]["total_correct_guesses"]
        )
        sorted_users.reverse()
        if not sorted_users:
            return await ctx.send(
                "No one has played whosthatpokemon yet. Use `[p]whosthatpokemon` to start!"
            )
            log.info("No one has played whosthatpokemon yet so nothing to show.")
        embed = discord.Embed(
            title="WhosThatPokemon Leaderboard",
            description="Top 10 users with most correct guesses.",
            color=await ctx.embed_color(),
        )
        for index, user in enumerate(sorted_users[:10], start=1):
            user_id = int(user[0])
            total_correct_guesses = await self.config.user_from_id(
                user_id
            ).total_correct_guesses()
            total = humanize_number(total_correct_guesses)
            user_obj = self.bot.get_user(user_id)
            if user_obj is None:
                continue
            embed.add_field(
                name=f"{index}. {user_obj}",
                value=f"Total correct guesses: **{total}**",
                inline=False,
            )
        pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=60,
        ).start(ctx)

    @commands.command(name="wtpstats")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def whosthatpokemon_stats(self, ctx: commands.Context):
        """Shows your stats for whosthatpokemon.

        This will show your total correct guesses.
        """
        total_correct_guesses = await self.config.user(
            ctx.author
        ).total_correct_guesses()
        if not total_correct_guesses:
            return await ctx.send(
                f"You have not played whosthatpokemon yet. Use `{ctx.clean_prefix}whosthatpokemon` to start!"
            )
            log.info(
                f"{ctx.author} tried to check their stats but they have not played whosthatpokemon yet."
            )
        human = humanize_number(total_correct_guesses)
        await ctx.send(
            f"{ctx.author.mention} you have **{human}** correct guesses in whosthatpokemon.",
            allowed_mentions=discord.AllowedMentions(users=False),
        )

    @commands.is_owner()
    @commands.command(name="wtpreset")
    @commands.cooldown(2, 43200, commands.BucketType.user)
    async def whosthatpokemon_preset(self, ctx: commands.Context):
        """Resets the whosthatpokemon leaderboard.

        This will reset the leaderboard globally.
        This can only be used by the bot owner and 2 times per 12 hours.
        """
        if not await self.config.all_users():
            return await ctx.send(
                "No one has played whosthatpokemon yet so nothing to reset."
            )
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset the leaderboard?\n**This will reset the leaderboard globally**.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.clear_all_users()
            await ctx.send("✅ WhosThatPokemon leaderboard has been reset.")
            log.info(f"{ctx.author} reset the whosthatpokemon leaderboard globally.")
        else:
            await ctx.send("❌ WhosThatPokemon leaderboard reset has been cancelled.")

    @commands.is_owner()
    @commands.command(name="wtpperformance", hidden=True)
    async def whosthatpokemon_performance(self, ctx):
        """Shows performance."""
        stats = get_stats()
        record = stats.get(self.generate_image)
        if record:
            avg_time = stats.avg_time(self.generate_image)
            cpm = stats.cpm(self.generate_image)
            await ctx.send(
                f"Average Time: {avg_time:.3f}s | Calls per minute: {cpm:.3f}"
            )
        else:
            await ctx.send("No performance found yet.")
