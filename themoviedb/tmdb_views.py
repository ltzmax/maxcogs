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

from datetime import datetime

import aiohttp
import discord
from red_commons.logging import getLogger
from redbot.core.utils.chat_formatting import humanize_list, humanize_number

from .tmdb_utils import get_media_data

log = getLogger("red.maxcogs.themoviedb.views")

TMDB_BASE_IMAGE = "https://image.tmdb.org/t/p"


def _parse_date(date_str: str) -> str | None:
    """Convert a YYYY-MM-DD string to a Discord timestamp, or return None."""
    if not date_str:
        return None
    try:
        ts = int(datetime.strptime(date_str[:10], "%Y-%m-%d").timestamp())
        return f"<t:{ts}:D>"
    except (ValueError, TypeError):
        return None


def _build_detail_fields(data: dict, item_type: str) -> dict:
    """Build the fields dict for a movie or TV detail view."""
    is_movie = item_type == "movie"

    # Dates
    if is_movie:
        release = _parse_date(data.get("release_date", ""))
        dates = {"Release Date": release} if release else {}
    else:
        first = _parse_date(data.get("first_air_date", ""))
        last = _parse_date(data.get("last_air_date", ""))
        next_ep = _parse_date((data.get("next_episode_to_air") or {}).get("air_date", ""))
        dates = {}
        if first:
            dates["First Air Date"] = first
        if last:
            dates["Last Air Date"] = last
        if next_ep:
            dates["Next Episode Air Date"] = next_ep

    # Episode/season info (TV only)
    episode_info = {}
    if not is_movie:
        n_seasons = data.get("number_of_seasons")
        n_episodes = data.get("number_of_episodes")
        if n_seasons:
            episode_info[f"Number of {'Season' if n_seasons == 1 else 'Seasons'}"] = n_seasons
        if n_episodes:
            episode_info["Number of Episodes"] = n_episodes

    # Runtime (movie only)
    runtime = {}
    if is_movie and data.get("runtime"):
        runtime["Runtime"] = f"{data['runtime']} minutes"

    # Status
    status = {"Status": data.get("status")} if data.get("status") else {}

    # Genres
    genres = [g["name"] for g in data.get("genres", [])]
    genre_field = {}
    if genres:
        genre_field[f"{'Genre' if len(genres) == 1 else 'Genres'}"] = humanize_list(genres)

    # Production
    companies = [c["name"] for c in data.get("production_companies", [])]
    countries = [c["name"] for c in data.get("production_countries", [])]
    languages = [la["name"] for la in data.get("spoken_languages", [])]
    production = {}
    if companies:
        production[f"Production {'Company' if len(companies) == 1 else 'Companies'}"] = (
            humanize_list(companies)
        )
    if countries:
        production[f"Production {'Country' if len(countries) == 1 else 'Countries'}"] = (
            humanize_list(countries)
        )
    if languages:
        production[f"{'Spoken Language' if len(languages) == 1 else 'Spoken Languages'}"] = (
            humanize_list(languages)
        )

    # Ratings
    ratings = {
        "Popularity": humanize_number(data.get("popularity", 0)),
        "Vote Average": data.get("vote_average"),
        "Vote Count": humanize_number(data.get("vote_count", 0)),
    }

    # Movie specific extras
    movie_extras = {}
    if is_movie:
        if data.get("budget"):
            movie_extras["Budget"] = f"${humanize_number(data['budget'])}"
        if data.get("revenue"):
            movie_extras["Revenue"] = f"${humanize_number(data['revenue'])}"
        collection = (data.get("belongs_to_collection") or {}).get("name")
        if collection:
            movie_extras["Belongs to Collection"] = collection
        movie_extras["Adult"] = "Yes" if data.get("adult") else "No"

    # Original titles
    originals = {}
    if is_movie and data.get("original_title") and data["original_title"] != data.get("title"):
        originals["Original Title"] = data["original_title"]
    if not is_movie and data.get("original_name") and data["original_name"] != data.get("name"):
        originals["Original Name"] = data["original_name"]

    # Misc
    misc = {}
    if data.get("tagline"):
        misc["Tagline"] = data["tagline"]
    if data.get("homepage"):
        misc["Homepage"] = data["homepage"]

    fields = (
        dates
        | status
        | episode_info
        | runtime
        | genre_field
        | production
        | ratings
        | movie_extras
        | originals
        | misc
    )
    return {k: v for k, v in fields.items() if v}


def build_detail_view(
    data: dict,
    item_id: int,
    item_type: str,
    accent_colour: discord.Colour,
) -> "DetailView":
    """Build a Components v2 detail view for a movie or TV show."""
    url = f"https://www.themoviedb.org/{item_type}/{item_id}"
    title = data.get("title" if item_type == "movie" else "name", "No title available.")[:256]
    description = data.get("overview", "No description available.")[:1048]
    poster_path = data.get("poster_path")
    thumbnail_url = f"{TMDB_BASE_IMAGE}/w500{poster_path}" if poster_path else None
    fields = _build_detail_fields(data, item_type)

    field_lines = [f"**{name}:** {value}" for name, value in fields.items()]
    mid = len(field_lines) // 2
    fields_text_1 = "\n".join(field_lines[:mid])
    fields_text_2 = "\n".join(field_lines[mid:])

    header_text = f"## {title}\n{description}"
    components = []

    if thumbnail_url:
        components.append(
            discord.ui.Section(
                discord.ui.TextDisplay(header_text),
                accessory=discord.ui.Thumbnail(thumbnail_url),
            )
        )
    else:
        components.append(discord.ui.TextDisplay(header_text))

    if fields_text_1:
        components.append(discord.ui.Separator())
        components.append(discord.ui.TextDisplay(fields_text_1))
    if fields_text_2:
        components.append(discord.ui.Separator())
        components.append(discord.ui.TextDisplay(fields_text_2))

    components.append(discord.ui.Separator())
    components.append(
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label=title[:80],
                url=url,
                emoji="📺" if item_type == "tv" else "🎥",
            ),
        )
    )

    view = DetailView()
    view.add_item(discord.ui.Container(*components, accent_colour=accent_colour))
    return view


class DetailView(discord.ui.LayoutView):
    """Components v2 view for the movie/TV detail display."""

    pass


class MediaPaginator(discord.ui.View):
    """Paginated search results view using a standard embed."""

    def __init__(
        self,
        ctx,
        filtered_results: list,
        media_type: str,
        api_key: str,
        session: aiohttp.ClientSession,
        accent_colour: discord.Colour,
        items_per_page: int = 10,
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.filtered_results = self._sort_results(filtered_results, media_type)
        self.media_type = media_type
        self.api_key = api_key
        self.session = session
        self.accent_colour = accent_colour
        self.current_page = 0
        self.items_per_page = items_per_page
        self.message = None
        self._add_buttons()

    def _sort_results(self, results: list, media_type: str) -> list:
        date_key = "release_date" if media_type == "movie" else "first_air_date"

        def get_date(item):
            date_str = item.get(date_key, "0000-00-00")
            try:
                return datetime.strptime(date_str[:10], "%Y-%m-%d").timestamp()
            except (ValueError, TypeError):
                return float("-inf")

        return sorted(results, key=get_date, reverse=True)

    def _get_label(self, result: dict, index: int) -> str:
        key_map = {
            "movie": {"title": "title", "date": "release_date"},
            "tv": {"title": "name", "date": "first_air_date"},
        }
        keys = key_map[self.media_type]
        title = result.get(keys["title"], "Unknown")
        date = result.get(keys["date"], "N/A")[:4]
        popularity = round(result.get("popularity", 0), 1)
        return f"{index + 1}. {title} ({date}) ★ {popularity}"

    def _add_buttons(self):
        """Add select and nav buttons for the current page."""
        self.clear_items()
        start_idx = self.current_page * self.items_per_page
        end_idx = min((self.current_page + 1) * self.items_per_page, len(self.filtered_results))
        for i in range(start_idx, end_idx):
            self.add_item(MediaButton(paginator=self, index=i))

        if self.current_page > 0:
            self.add_item(NavButton(paginator=self, direction="prev"))
        if end_idx < len(self.filtered_results):
            self.add_item(NavButton(paginator=self, direction="next"))

    def build_embed(self) -> discord.Embed:
        """Build the search results embed for the current page."""
        start_idx = self.current_page * self.items_per_page
        end_idx = min((self.current_page + 1) * self.items_per_page, len(self.filtered_results))
        total_pages = -(-len(self.filtered_results) // self.items_per_page)

        embed = discord.Embed(
            title="Search Results",
            description="\n".join(
                self._get_label(self.filtered_results[i], i) for i in range(start_idx, end_idx)
            ),
            colour=self.accent_colour,
        )
        embed.set_footer(
            text=(
                f"Page {self.current_page + 1}/{total_pages} · "
                f"{len(self.filtered_results)} results · "
                f"Click a number button to view details · "
                f"Powered by TMDB"
            ),
            icon_url="http://i.maxapp.tv/uploads/3c9c.png",
        )
        return embed

    async def _cleanup(self):
        """Disable all buttons and update the message."""
        for item in self.children:
            item.disabled = True
        if not self.session.closed:
            await self.session.close()
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.HTTPException) as e:
                log.error("Failed to edit message during cleanup: %s", e)

    async def on_timeout(self):
        await self._cleanup()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "Only %s can use this menu." % self.ctx.author.mention, ephemeral=True
            )
            return False
        return True


class MediaButton(discord.ui.Button["MediaPaginator"]):
    """Button to select a search result by its list number."""

    def __init__(self, paginator: "MediaPaginator", index: int):
        super().__init__(
            label=str(index + 1),
            style=discord.ButtonStyle.primary,
        )
        self.paginator = paginator
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            data = await get_media_data(
                self.paginator.ctx,
                self.paginator.session,
                self.paginator.filtered_results[self.index]["id"],
                self.paginator.media_type,
                api_key=self.paginator.api_key,
            )
        except aiohttp.ClientConnectionError as e:
            log.error(
                "Network error fetching media ID %s: %s",
                self.paginator.filtered_results[self.index]["id"],
                e,
                exc_info=True,
            )
            return await interaction.response.send_message(
                "Network error, please try again.", ephemeral=True
            )
        except Exception as e:
            log.error(
                "Error fetching media ID %s: %s",
                self.paginator.filtered_results[self.index]["id"],
                e,
                exc_info=True,
            )
            return await interaction.response.send_message(
                "Error fetching media details.", ephemeral=True
            )

        if not data:
            return await interaction.response.send_message(
                "Failed to fetch media details.", ephemeral=True
            )

        detail_view = build_detail_view(
            data=data,
            item_id=self.paginator.filtered_results[self.index]["id"],
            item_type=self.paginator.media_type,
            accent_colour=self.paginator.accent_colour,
        )
        await interaction.response.send_message(view=detail_view)
        await self.paginator._cleanup()


class NavButton(discord.ui.Button["MediaPaginator"]):
    """Previous/Next page navigation button."""

    def __init__(self, paginator: "MediaPaginator", direction: str):
        super().__init__(
            label="Previous" if direction == "prev" else "Next",
            emoji="◀️" if direction == "prev" else "▶️",
            style=discord.ButtonStyle.secondary,
        )
        self.paginator = paginator
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            start_idx = self.paginator.current_page * self.paginator.items_per_page
            end_idx = start_idx + self.paginator.items_per_page
            if self.direction == "prev" and self.paginator.current_page > 0:
                self.paginator.current_page -= 1
            elif self.direction == "next" and end_idx < len(self.paginator.filtered_results):
                self.paginator.current_page += 1
            self.paginator._add_buttons()
            await interaction.response.edit_message(
                embed=self.paginator.build_embed(), view=self.paginator
            )
        except discord.HTTPException as e:
            log.error("Error navigating page: %s", e, exc_info=True)
            await interaction.response.send_message(
                "Error navigating, please try again.", ephemeral=True
            )
