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
from datetime import datetime

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import SetApiView, SimpleMenu

from .utils import apicheck, get_media_data, search_media

log = logging.getLogger("red.maxcogs.themoviedb")


class TheMovieDB(commands.Cog):
    """Search for informations of movies and TV shows from themoviedb.org."""

    __author__ = "MAX"
    __version__ = "1.0.0"
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
        # This is to prevent people from searching for the movie "Utøya: July 22", "Utoya: July 22 or "22 July"
        blocked_search = ("utoya: july 22", "utøya: july 22", "22 july")
        if query.lower() in blocked_search:
            await ctx.send(f"The term '{query}' is blocked from search.")
            return

        await ctx.typing()
        data = await search_media(ctx, query, "movie")
        if data is None:
            await ctx.send("Something went wrong with TMDB. Please try again later.")
            return

        if not data["results"]:
            await ctx.send(f"No results found for {query}")
            log.info(f"{ctx.author} searched for {query} but no results were found.")
            return

        pages = []
        results = data["results"]
        for i in range(len(results)):
            data = await get_media_data(ctx, results[i]["id"], "movie")
            movie_id = results[i]["id"]

            embed = discord.Embed(
                title=data["title"][:256] if data["title"] else "No title available.",
                url=f"https://www.themoviedb.org/movie/{movie_id}",
                description=data["overview"][:1048]
                if data["overview"]
                else "No description available.",
                colour=await ctx.embed_colour(),
            )
            if data["poster_path"]:
                embed.set_thumbnail(
                    url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
                )
            if data["backdrop_path"]:
                embed.set_image(
                    url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
                )
            if data["original_title"]:
                embed.add_field(
                    name="Original Title:", value=data["original_title"], inline=False
                )
            if data["release_date"]:
                embed.add_field(
                    name="Release Date:",
                    value=f"<t:{int(datetime.strptime(data['release_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["runtime"]:
                embed.add_field(name="Runtime:", value=humanize_number(data["runtime"]))
            if data["status"]:
                embed.add_field(name="Status:", value=data["status"])
            if data["belongs_to_collection"]:
                embed.add_field(
                    name="Belongs to Collection:",
                    value=data["belongs_to_collection"]["name"],
                )
            if data["genres"]:
                embed.add_field(
                    name="Genres:",
                    value=humanize_list([i["name"] for i in data["genres"]]),
                    inline=False,
                )
            if data["production_companies"]:
                embed.add_field(
                    name="Production Companies:",
                    value=humanize_list(
                        [i["name"] for i in data["production_companies"]]
                    ),
                    inline=False,
                )
            if data["production_countries"]:
                embed.add_field(
                    name="Production Countries:",
                    value=humanize_list(
                        [i["name"] for i in data["production_countries"]]
                    ),
                    inline=False,
                )
            if data["spoken_languages"]:
                embed.add_field(
                    name="Spoken Languages:",
                    value=humanize_list(
                        [i["english_name"] for i in data["spoken_languages"]]
                    ),
                )
            if data["original_language"]:
                embed.add_field(
                    name="Original Language:", value=data["original_language"]
                )
            if data["revenue"]:
                embed.add_field(
                    name="Revenue:", value=f"${humanize_number(data['revenue'])}"
                )
            if data["budget"]:
                embed.add_field(
                    name="Budget:", value=f"${humanize_number(data['budget'])}"
                )
            if data["popularity"]:
                embed.add_field(
                    name="Popularity:", value=humanize_number(data["popularity"])
                )
            if data["vote_average"]:
                embed.add_field(name="Vote Average:", value=data["vote_average"])
            if data["vote_count"]:
                embed.add_field(
                    name="Vote Count:", value=humanize_number(data["vote_count"])
                )
            embed.add_field(
                name="Adult:", value="Yes" if data["adult"] is True else "No"
            )
            if data["homepage"]:
                embed.add_field(name="Homepage:", value=data["homepage"])
            if data["tagline"]:
                embed.add_field(name="Tagline:", value=data["tagline"], inline=False)
            embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
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
        # This is to prevent people from searching for the mini serie of "22 July"
        blocked_search = ("22 juli", "22 july")
        if query.lower() in blocked_search:
            await ctx.send(f"The term '{query}' is blocked from search.")
            return

        await ctx.typing()
        data = await search_media(ctx, query, "tv")
        if data is None:
            await ctx.send("Something went wrong with TMDB. Please try again later.")
            return

        if not data["results"]:
            await ctx.send(f"No results found for {query}")
            log.info(f"{ctx.author} searched for {query} but no results were found.")
            return

        pages = []
        results = data["results"]
        for i in range(len(results)):
            data = await get_media_data(ctx, results[i]["id"], "tv")
            tv_id = results[i]["id"]

            embed = discord.Embed(
                title=data["name"][:256] if data["name"] else "No title available.",
                url=f"https://www.themoviedb.org/tv/{tv_id}",
                description=data["overview"][:1048]
                if data["overview"]
                else "No description available.",
                colour=await ctx.embed_colour(),
            )
            if data["poster_path"]:
                embed.set_thumbnail(
                    url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
                )
            if data["backdrop_path"]:
                embed.set_image(
                    url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
                )
            if data["original_name"]:
                embed.add_field(
                    name="Original Name:", value=data["original_name"], inline=False
                )
            if data["first_air_date"]:
                embed.add_field(
                    name="First Air Date:",
                    value=f"<t:{int(datetime.strptime(data['first_air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["last_episode_to_air"]:
                embed.add_field(
                    name="Last Episode Air Date:",  # When the last episode aired.
                    value=f"<t:{int(datetime.strptime(data['last_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["next_episode_to_air"]:
                embed.add_field(
                    name="Next Episode Air Date:",  # When the next episode will air.
                    value=f"<t:{int(datetime.strptime(data['next_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["last_air_date"]:
                embed.add_field(
                    name="Last Air Date:",  # When the show ended.
                    value=f"<t:{int(datetime.strptime(data['last_air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["episode_run_time"]:
                embed.add_field(
                    name="Episode Run Time:",
                    value=f"{data['episode_run_time'][0]} minutes",
                )
            if data["number_of_episodes"]:
                embed.add_field(
                    name="Number of Episodes:",
                    value=humanize_number(data["number_of_episodes"]),
                )
            if data["number_of_seasons"]:
                embed.add_field(
                    name="Number of Seasons:", value=data["number_of_seasons"]
                )
            if data["status"]:
                embed.add_field(name="Status:", value=data["status"])
            if data["in_production"]:
                embed.add_field(
                    name="In Production:",
                    value="Yes" if data["in_production"] else "No",
                )
            if data["type"]:
                embed.add_field(name="Type:", value=data["type"])
            if data["networks"]:
                embed.add_field(
                    name="Networks:",
                    value=humanize_list([i["name"] for i in data["networks"]]),
                )
            if data["spoken_languages"]:
                embed.add_field(
                    name="Spoken Languages:",
                    value=humanize_list(
                        [i["english_name"] for i in data["spoken_languages"]]
                    ),
                )
            if data["genres"]:
                embed.add_field(
                    name="Genres:",
                    value=humanize_list([i["name"] for i in data["genres"]]),
                    inline=False,
                )
            if data["production_companies"]:
                embed.add_field(
                    name="Production Companies:",
                    value=humanize_list(
                        [i["name"] for i in data["production_companies"]]
                    ),
                    inline=False,
                )
            if data["production_countries"]:
                embed.add_field(
                    name="Production Countries:",
                    value=humanize_list(
                        [i["name"] for i in data["production_countries"]]
                    ),
                    inline=False,
                )
            if data["created_by"]:
                embed.add_field(
                    name="Created By:",
                    value=", ".join([i["name"] for i in data["created_by"]]),
                )
            if data["popularity"]:
                embed.add_field(
                    name="Popularity:", value=humanize_number(data["popularity"])
                )
            if data["vote_average"]:
                embed.add_field(name="Vote Average:", value=data["vote_average"])
            if data["vote_count"]:
                embed.add_field(
                    name="Vote Count:", value=humanize_number(data["vote_count"])
                )
            embed.add_field(
                name="Adult:", value="Yes" if data["adult"] is True else "No"
            )
            if data["homepage"]:
                embed.add_field(name="Homepage:", value=data["homepage"])
            if data["tagline"]:
                embed.add_field(name="Tagline:", value=data["tagline"], inline=False)
            embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
            pages.append(embed)
        await SimpleMenu(
            pages,
            use_select_menu=True,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)
