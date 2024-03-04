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

import logging

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import SetApiView, SimpleMenu

from .utils import (
    apicheck,
    get_media_data,
    search_media,
    check_results,
    build_tvshow_embed,
    build_movie_embed,
)

log = logging.getLogger("red.maxcogs.themoviedb")


# This is to prevent the cog from being used to search for movies and TV shows related to the 2011 Norway attacks.
# TheMovieDB has a lot of movies and TV shows related to this event, and it's not appropriate to use this cog to search for them.
# As a norwegian, I don't want to see movies and TV shows related to this event, and I don't want to see this cog being used to search for them,
# the attack was very tragic and it hurts me to see movies and TV shows related to this event, those should never have been made in the first place.
BLOCKED_SEARCH = {"utoya: july 22", "utøya: july 22", "22 july", "22 juli"}

class TheMovieDB(commands.Cog):
    """Search for informations of movies and TV shows from themoviedb.org."""

    __author__ = "MAX"
    __version__ = "1.0.4"
    __docs__ = "https://maxcogs.gitbook.io/maxcogs/cogs/themoviedb"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    @commands.group()
    @commands.is_owner()
    async def tmdbset(self, ctx: commands.Context):
        """Setup TheMovieDB."""

    @tmdbset.command(name="creds")
    @commands.bot_has_permissions(embed_links=True)
    async def tmdbset_creds(self, ctx: commands.Context):
        """Set your TMDB API key"""
        msg = (
            "You will need to create an API key to use this cog.\n"
            "1. If you don't have an account, you will need to create one first from here <https://www.themoviedb.org/signup>\n"
            "2. To get your API key, go to <https://www.themoviedb.org/settings/api> "
            "and select the Developer option and fill out the form.\n"
            "3. Once they approve your request, you will get your API key, copy it and use the command:\n"
            f"`{ctx.clean_prefix}set api tmdb api_key <your api key>`"
        )
        default_keys = {"api_key": ""}
        view = SetApiView("tmdb", default_keys)
        embed = discord.Embed(
            title="TMDB API Key",
            description=msg,
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="You can also set your API key by using the button.")
        await ctx.send(embed=embed, view=view)

    @tmdbset.command(name="version")
    @commands.bot_has_permissions(embed_links=True)
    async def tmdbset_version(self, ctx: commands.Context):
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

    @commands.check(apicheck)
    @commands.hybrid_command(aliases=["movies"])
    @app_commands.describe(query="The movie you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Search for a movie.

        You can write the full name of the movie to get more accurate results.

        **Examples:**
        - `[p]movie the matrix`
        - `[p]movie the hunger games the ballad of songbirds and snakes`

        **Arguments:**
        - `<query>` - The movie you want to search for.
        """
        if query.lower() in BLOCKED_SEARCH:
            return await ctx.send(f"The term '{query}' is blocked from search.")
            
        await ctx.typing()
        data = await search_media(ctx, query, "movie")
        if not data:
            return await ctx.send(
                "Something went wrong with TMDB. Please try again later."
            )
        if not await check_results(ctx, data, query):
            return
        pages = []
        results = data["results"]
        for i in range(len(results)):
            data = await get_media_data(ctx, results[i]["id"], "movie")
            movie_id = results[i]["id"]
            embed = await build_movie_embed(ctx, data, movie_id, i, results)
            pages.append(embed)
        await SimpleMenu(
            pages,
            use_select_menu=True,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @commands.check(apicheck)
    @commands.hybrid_command(aliases=["tv"])
    @app_commands.describe(query="The serie you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Search for a TV show.

        You can write the full name of the tv show to get more accurate results.

        **Examples:**
        - `[p]tvshow the simpsons`
        - `[p]tvshow family guy`

        **Arguments:**
        - `<query>` - The serie you want to search for.
        """
        if query.lower() in BLOCKED_SEARCH:
            return await ctx.send(f"The term '{query}' is blocked from search.")
            
        await ctx.typing()
        data = await search_media(ctx, query, "tv")
        if not data:
            return await ctx.send(
                "Something went wrong with TMDB. Please try again later."
            )
        if not await check_results(ctx, data, query):
            return
        pages = []
        results = data["results"]
        for i in range(len(results)):
            data = await get_media_data(ctx, results[i]["id"], "tv")
            tv_id = results[i]["id"]
            embed = await build_tvshow_embed(ctx, data, tv_id, i, results)
            pages.append(embed)
        await SimpleMenu(
            pages,
            use_select_menu=True,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)
