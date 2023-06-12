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
from datetime import datetime, timedelta, timezone
from io import BytesIO
from random import randint
from typing import List, Optional

import aiohttp
import discord
from discord import File
from PIL import Image
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.views import SimpleMenu

from .converter import Generation
from .view import WhosThatPokemonView

API_URL = "https://pokeapi.co/api/v2"


class WhosThatPokemon(commands.Cog):
    """Can you guess Who's That Pokémon?"""

    __author__ = "<@306810730055729152>, MAX#1000, Flame (Flame#2941)"
    __version__ = "1.2.6"
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

    # _____ ________  ______  ___  ___   _   _______  _____
    # /  __ \  _  |  \/  ||  \/  | / _ \ | \ | |  _  \/  ___|
    # | /  \/ | | | .  . || .  . |/ /_\ \|  \| | | | |\ `--.
    # | |   | | | | |\/| || |\/| ||  _  || . ` | | | | `--. \
    # | \__/\ \_/ / |  | || |  | || | | || |\  | |/ / /\__/ /
    # \____/\___/\_|  |_/\_|  |_/\_| |_/\_| \_/___/  \____/
    @commands.command(name="wtpversion", hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def whosthatpokemon_version(self, ctx: commands.Context):
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
        await ctx.send(embed=embed)

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
        await self.config.user(ctx.author).score.set(
            (await self.config.user(ctx.author).score()) + 1
        )
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
        description = "\n".join(
            f"**{i}**. {ctx.guild.get_member(user_id)} - Score: {user_data['score']}"
            for i, (user_id, user_data) in enumerate(data, start=1)
        )
        embed = discord.Embed(
            title="Leaderboard", description=description, color=0xE91E63
        )
        embed.set_footer(text=f"Page 1/{len(data)}")
        pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            use_select_menu=True,
            timeout=60,
        ).start(ctx)

    # ___ ___  __ __  _____ ______      ____     ___       ___   __    __  ____     ___  ____
    # |   |   ||  |  |/ ___/|      |    |    \   /  _]     /   \ |  |__|  ||    \   /  _]|    \
    # | _   _ ||  |  (   \_ |      |    |  o  ) /  [_     |     ||  |  |  ||  _  | /  [_ |  D  )
    # |  \_/  ||  |  |\__  ||_|  |_|    |     ||    _]    |  O  ||  |  |  ||  |  ||    _]|    /
    # |   |   ||  :  |/  \ |  |  |      |  O  ||   [_     |     ||  `  '  ||  |  ||   [_ |    \
    # |   |   ||     |\    |  |  |      |     ||     |    |     | \      / |  |  ||     ||  .  \
    # |___|___| \__,_| \___|  |__|      |_____||_____|     \___/   \_/\_/  |__|__||_____||__|\_|
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
