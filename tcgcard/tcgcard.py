# This cog did not have a license.
# This cog was created by owocado and is now continued by ltzmax.
# This cog was transfered via a pr from the author of the code https://github.com/ltzmax/maxcogs/pull/46
import asyncio
from datetime import datetime

import aiohttp
import discord
from redbot.core.utils.chat_formatting import box
from redbot.core import commands, app_commands
from redbot.core.utils.views import SimpleMenu


class Tcgcard(commands.Cog):
    """Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG)."""

    __author__ = ["<@306810730055729152>", "MAX#1000"]
    __version__ = "1.3.0"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/tcgcard/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="tcgversion", hidden=True)
    async def tcgcard_version(self, ctx: commands.Context):
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

    @commands.hybrid_command()
    @app_commands.describe(query=("The Pokémon you want to search a card for."))
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def tcgcard(self, ctx: commands.Context, *, query: str):
        """Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).

        **Example:**
        - `[p]tcgcard pikachu` - returns information about pikachu's cards.

        **Arguments:**
        - `<query>` - The pokemon you want to search for.
        """
        api_key = (await ctx.bot.get_shared_api_tokens("pokemontcg")).get("api_key")
        headers = {"X-Api-Key": api_key} if api_key else None
        await ctx.typing()
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
            return await ctx.send("There is no results for that search.")

        pages = []
        for i, data in enumerate(output["data"], 1):
            dt = datetime.utcnow()
            release = datetime.strptime(data["set"]["releaseDate"], "%Y/%m/%d")
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.title = data["name"]
            embed.description = "**Rarity:** " + str(data.get("rarity"))
            embed.add_field(name="Artist:", value=str(data.get("artist")))
            embed.add_field(
                name="Belongs to Set:", value=str(data["set"]["name"]), inline=False
            )
            embed.add_field(
                name="Set Release Date:",
                value=discord.utils.format_dt(release, style="D"),
            )
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
