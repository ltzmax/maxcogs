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

from typing import Dict, Optional, Union

import aiohttp
import discord
from redbot.core import Config, app_commands, commands
from redbot.core.utils.views import SetApiView

from .everything_stuff import build_embed, get_media_data, search_and_display

# TODO:
# - Add upcoming movies (https://developer.themoviedb.org/reference/movie-upcoming-list) (Subject to change)
# - Add Airing today tv shows (https://developer.themoviedb.org/reference/tv-series-airing-today-list) (Subject to change)
# - Add person (https://developer.themoviedb.org/reference/search-person) (In progress)
# - Add Recommnedations (https://developer.themoviedb.org/reference/movie-recommendations) (Will be added in future update)


class TheMovieDB(commands.Cog):
    """
    Search for informations of movies and TV shows from themoviedb.org.
    """

    __author__ = "MAX"
    __version__ = "1.4.0"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/docs/TheMovieDB.md"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config: Config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_global: Dict[str, Union[bool, Optional[int]]] = {
            "use_box": False,
        }
        self.config.register_global(**default_global)

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
        """
        Configure TheMovieDB cog settings.
        """

    @tmdbset.command(name="usebox")
    async def tmdbset_usebox(self, ctx: commands.Context, value: bool):
        """
        Set if you want to use the box in the choose of movie/tv show.

        Disabled by default.

        - `True` to use the box art in the embeds.
        - `False` to not use the box art in the embeds.
        """
        await self.config.use_box.set(value)
        await ctx.send(f"Use box art set to `{value}`.")

    @tmdbset.command(name="creds")
    @commands.bot_has_permissions(embed_links=True)
    async def tmdbset_creds(self, ctx: commands.Context):
        """
        Guide to setting up the TMDB API key.

        This command will give you information on how to set up the API key.
        """
        msg = (
            "To use this cog, you need to get an API key from TheMovieDB.org.\n"
            "Here's how to do it:\n"
            "1. **Create an account**: Go to <https://www.themoviedb.org/signup> and sign up for an account.\n"
            "2. **Request a Developer API key**: Go to <https://www.themoviedb.org/settings/api> "
            "and select the Developer option. Fill out the form and wait for them to approve your request.\n"
            "3. **Get your API key**: Once approved, you will get your API key. Copy it and use the command:\n"
            f"`{ctx.clean_prefix}set api tmdb api_key <your api key>`\n"
            "The API key is used to fetch information about movies and TV shows from TheMovieDB.org."
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

    @commands.hybrid_command(aliases=["movies"])
    @app_commands.describe(query="The movie you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Search for a movie.

        You can write the full name of the movie to get more accurate results.

        **Examples:**
        - `[p]movie the dark knight`
        - `[p]movie the lord of the rings`

        **Arguments:**
        - `<query>` - The movie you want to search for.
        """
        token = await ctx.bot.get_shared_api_tokens("tmdb")
        if token.get("api_key") is None:
            return await ctx.send(
                "The bot owner has not set up the API key for TheMovieDB. "
                "Please ask them to set it up."
            )
        await search_and_display(ctx, query, "movie", get_media_data, build_embed, self.config)

    @commands.hybrid_command(aliases=["tv"])
    @app_commands.describe(query="The series you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Search for a TV show.

        You can write the full name of the TV show to get more accurate results.

        **Examples:**
        - `[p]tv the office`
        - `[p]tv game of thrones`

        **Arguments:**
        - `<query>` - The TV show you want to search for.
        """
        token = await ctx.bot.get_shared_api_tokens("tmdb")
        if token.get("api_key") is None:
            return await ctx.send(
                "The bot owner has not set up the API key for TheMovieDB. "
                "Please ask them to set it up."
            )
        await search_and_display(ctx, query, "tv", get_media_data, build_embed, self.config)
