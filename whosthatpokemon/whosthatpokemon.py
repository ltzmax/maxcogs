# This cog did not have a license.
# This cog was created by owocado and is now continued by ltzmax.
# This cog was transfered via a pr from the author of the code https://github.com/ltzmax/maxcogs/pull/46
import asyncio
from io import BytesIO
from random import randint
from typing import List, Optional
from datetime import datetime, timezone, timedelta

import aiohttp
import discord
from discord import File
from PIL import Image
from redbot.core import commands, app_commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.views import SimpleMenu
from redbot.core.utils.predicates import MessagePredicate

from .view import WhosThatPokemonView
from .converter import Generation

API_URL = "https://pokeapi.co/api/v2"


class WhosThatPokemon(commands.Cog):
    """Can you guess Who's That Pokémon?"""

    __author__ = "<@306810730055729152>", "MAX#1000, Flame (Flame#2941)"
    __version__ = "1.2.5"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/whosthatpokemon/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_user = {
            "score": 0,
        }
        self.config.register_user(**default_user)

    async def cog_unload(self) -> None:
        await self.session.close()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    async def get_data(self, url: str):
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {"http_code": response.status}
                return await response.json()
        except asyncio.TimeoutError:
            return {"http_code": 408}

    async def generate_image(self, poke_id: str, *, hide: bool):
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
    async def whosthatpokemon_version(self, ctx: commands.Context):
        """Shows the version of the cog"""
        version = self.__version__
        author = self.__author__
        await ctx.send(
            box(f"{'Author':<10}: {author}\n{'Version':<10}: {version}", lang="yaml")
        )

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(
        generation=("Optionally choose generation from gen1 to gen8.")
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
        ]
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    async def whosthatpokemon(
        self, ctx: commands.Context, generation: Optional[Generation] = None
    ):
        """Guess Who's that Pokémon in 30 seconds!

        You can optionally specify generation from `gen1` to `gen8` only,
        to restrict this guessing game to specific Pokemon generation.

        Otherwise, it will default to pulling random pokemon from gen 1 to gen 8.

        **Example:**
        - `[p]whosthatpokemon` - This will start a new Generation.
        - `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.

        **Arguments:**
        - `[generation]` - Where you choose any generation from gen 1 to gen 8.
        """
        await ctx.typing()
        poke_id = generation or randint(1, 898)
        if_guessed_right = False

        temp = await self.generate_image(f"{poke_id:>03}", hide=True)
        if temp is None:
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        # Took this from Core's event file.
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/41d89c7b54a1f231a01f79655c20d4acf1799633/redbot/core/_events.py#L424-L426
        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(seconds=30.0), "R"
        )
        species_data = await self.get_data(f"{API_URL}/pokemon-species/{poke_id}")
        if species_data.get("http_code"):
            return await ctx.send("Failed to get species data from PokeAPI.")
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
            color=await ctx.embed_color(),
        )
        embed.set_image(url="attachment://whosthatpokemon.png")
        embed.set_footer(text=f"Author: {ctx.author}", icon_url=ctx.author.avatar.url)
        # because we want it to timeout and not tell the user that they got it right.
        # This is probably not the best way to do it, but it works perfectly fine.
        timeout = await view.wait()
        if timeout:
            return await ctx.send(
                f"{ctx.author.mention} Time's up! You could not guess the pokemon in right time.",
            )
        data = await self.config.user(ctx.author).all()
        if data:
            data["score"] += 1
            await self.config.user(ctx.author).set(data)
        await ctx.send(file=revealed_img, embed=embed)

    @commands.command(name="wtplb")
    @commands.bot_has_permissions(embed_links=True)
    async def whosthatpokemon_leaderboard(self, ctx: commands.Context):
        """Shows the leaderboard for whosthatpokemon game.

        This leaderboard is based on the score of the user who guessed the pokemon correctly.
        Your score will show on all servers that you have played whosthatpokemon on current bot.
        """
        data = await self.config.all_users()
        if not data:
            return await ctx.send("No one has played whosthatpokemon yet.")
        pages = []
        data = sorted(data.items(), key=lambda x: x[1]["score"], reverse=True)
        for i, (user_id, user_data) in enumerate(data, start=1):
            user = ctx.guild.get_member(user_id)
            if user is None:
                continue
        embed = discord.Embed(
            title="Leaderboard",
            description=f"{i}. {user}  -  Score: {user_data['score']}",
            color=0xE91E63,
        )
        pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=60,
        ).start(ctx)

    @commands.is_owner()
    @commands.command(name="wtpreset", hidden=True)
    async def whosthatpokemon_reset(self, ctx: commands.Context):
        """Resets the whosthatpokemon game.

        **WARNING**
            - This will reset the score of all users who have played whosthatpokemon game.
        """
        data = await self.config.all_users()
        if not data:
            return await ctx.send("No one has played whosthatpokemon yet.")
        msg = (
            "⚠️**WARNING**⚠️\n"
            "This will reset the score of all users who have played whosthatpokemon game.\n"
            "Are you sure you want to continue?\n"
            "Type `yes` to continue or `no` to cancel. - You have 30 seconds to respond."
        )
        message = await ctx.send(msg)
        try:
            pred = MessagePredicate.yes_or_no(ctx)
            await ctx.bot.wait_for("message", check=pred, timeout=30)
        except asyncio.TimeoutError:
            await message.edit(content="You took too long to respond.")
            return
        if pred.result is True:
            await self.config.clear_all_users()
            await message.edit(content="All users score has been reset.")
        else:
            await message.edit(content="Reset cancelled.")
