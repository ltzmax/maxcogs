from datetime import datetime

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.views import SetApiView, SimpleMenu


# Taken from flare's Dank memer cog.
# https://github.com/flaree/flare-cogs/blob/1cc1ef9734f40daf2878f2c9dfe68a61e8767eab/dankmemer/dankmemer.py#L16-L19
async def apicheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    return bool(token.get("api_key"))


class TheMovieDB(commands.Cog):
    """Search for informations of movies and TV shows from themoviedb.org."""

    __author__ = "MAX"
    __version__ = "1.0.1"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/themoviedb/README.md"

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
            "3. Once you have your API key, copy your API Key then run the following command:\n"
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
        await ctx.send(embed=embed)

    @commands.check(apicheck)
    @commands.hybrid_command(aliases=["movies"])
    @app_commands.describe(query="The movie you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Search for a movie.

        You can write the full name of the movie to get more accurate results.

        **Examples:**
        - `[p]movie The Matrix`
        - `[p]movie The Matrix 1999`

        **Arguments:**
        - `<query>` - The movie you want to search for.
        """
        await ctx.typing()
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        base_url = (
            f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
        )
        params = {"api_key": api_key}
        async with self.session.get(base_url, params=params) as resp:
            if resp.status != 200:
                await ctx.send(
                    "Something went wrong with TMDB. Please try again later."
                )
                return
            data = await resp.json()
        if not data["results"]:
            await ctx.send("No results found.")
            return

        pages = []
        results = data["results"]
        for i in range(len(results)):
            movie_id = results[i]["id"]
            base_url = (
                f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
            )
            async with self.session.get(base_url) as resp:
                data = await resp.json()

            if len(data["title"]) > 256:
                data["title"] = data["title"][:256] + "..."

            embed = discord.Embed(
                title=data["title"],
                url=f"https://www.themoviedb.org/movie/{movie_id}",
                description=data["overview"][:1048] or "No description available.",
                colour=await ctx.embed_colour(),
            )
            embed.set_thumbnail(
                url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
            )
            if data["original_title"]:
                embed.add_field(name="Original Title:", value=data["original_title"])
            if data["release_date"]:
                embed.add_field(
                    name="Release Date:",
                    value=f"<t:{int(datetime.strptime(data['release_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["runtime"]:
                embed.add_field(name="Runtime:", value=f"{data['runtime']} minutes")
            if data["status"]:
                embed.add_field(name="Status:", value=data["status"])
            if data["genres"]:
                embed.add_field(
                    name="Genres:", value=", ".join([i["name"] for i in data["genres"]])
                )
            if data["production_companies"]:
                embed.add_field(
                    name="Production Companies:",
                    value=", ".join([i["name"] for i in data["production_companies"]]),
                )
            if data["production_countries"]:
                embed.add_field(
                    name="Production Countries:",
                    value=", ".join([i["name"] for i in data["production_countries"]]),
                )
            if data["spoken_languages"]:
                embed.add_field(
                    name="Spoken Languages:",
                    value=", ".join([i["name"] for i in data["spoken_languages"]]),
                )
            if data["original_language"]:
                embed.add_field(
                    name="Original Language:", value=data["original_language"]
                )
            embed.add_field(name="Adult content:", value=data["adult"])
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
            if data["homepage"]:
                embed.add_field(name="Homepage:", value=data["homepage"])
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
        - `[p]tvshow The Simpsons`

        **Arguments:**
        - `<query>` - The serie you want to search for.
        """
        await ctx.typing()
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
        base_url = (
            f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={query}"
        )
        params = {"api_key": api_key}
        async with self.session.get(base_url, params=params) as resp:
            if resp.status != 200:
                await ctx.send(
                    "Something went wrong with TMDB. Please try again later."
                )
                return
            data = await resp.json()
        if not data["results"]:
            await ctx.send("No results found.")
            return

        pages = []
        results = data["results"]
        for i in range(len(results)):
            tv_id = results[i]["id"]
            base_url = f"https://api.themoviedb.org/3/tv/{tv_id}?api_key={api_key}"
            async with self.session.get(base_url) as resp:
                data = await resp.json()

            if len(data["name"]) > 256:
                data["name"] = data["name"][:256] + "..."

            embed = discord.Embed(
                title=data["name"],
                url=f"https://www.themoviedb.org/tv/{tv_id}",
                description=data["overview"][:1048] or "No description available.",
                colour=await ctx.embed_colour(),
            )
            embed.set_thumbnail(
                url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
            )
            if data["original_name"]:
                embed.add_field(name="Original Name:", value=data["original_name"])
            if data["first_air_date"]:
                embed.add_field(
                    name="First Air Date:",
                    value=f"<t:{int(datetime.strptime(data['first_air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["last_episode_to_air"]:
                embed.add_field(
                    name="Last Episode Air Date:",
                    value=f"<t:{int(datetime.strptime(data['last_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["next_episode_to_air"]:
                embed.add_field(
                    name="Next Episode Air Date:",
                    value=f"<t:{int(datetime.strptime(data['next_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
                )
            if data["number_of_episodes"]:
                embed.add_field(
                    name="Number of Episodes:", value=data["number_of_episodes"]
                )
            if data["number_of_seasons"]:
                embed.add_field(
                    name="Number of Seasons:", value=data["number_of_seasons"]
                )
            if data["status"]:
                embed.add_field(name="Status:", value=data["status"])
            if data["type"]:
                embed.add_field(name="Type:", value=data["type"])
            if data["genres"]:
                embed.add_field(
                    name="Genres:", value=", ".join([i["name"] for i in data["genres"]])
                )
            if data["networks"]:
                embed.add_field(
                    name="Networks:",
                    value=", ".join([i["name"] for i in data["networks"]]),
                )
            embed.add_field(name="Adult content:", value=data["adult"])
            if data["spoken_languages"]:
                embed.add_field(
                    name="Spoken Languages:",
                    value=", ".join([i["name"] for i in data["spoken_languages"]]),
                )
            if data["production_companies"]:
                embed.add_field(
                    name="Production Companies:",
                    value=", ".join([i["name"] for i in data["production_companies"]]),
                )
            if data["production_countries"]:
                embed.add_field(
                    name="Production Countries:",
                    value=", ".join([i["name"] for i in data["production_countries"]]),
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
            if data["homepage"]:
                embed.add_field(name="Homepage:", value=data["homepage"])
            embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
            pages.append(embed)
        await SimpleMenu(
            pages,
            use_select_menu=True,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)
