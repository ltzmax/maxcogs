# This cog was orginially made by epic guy#0715.
# He gave me permissions to use his code to turn it into watchlists.
# https://github.com/npc203/npc-cogs/tree/main/todo

import asyncio
import random
from typing import Literal

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.vendored.discord.ext import menus

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class WatchList(commands.Cog):
    """
    A simple watchlists for your movies and series.
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=6732102719277,
            force_registration=True,
        )
        self.config.register_user(serie=[])
        self.config.register_user(anime=[])
        self.config.register_user(movie=[])
        self.config.register_global(menus=True)

    __version__ = "0.0.1"
    __author__ = "MAX, npc-cogs(epic guy#0715)"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.group()
    async def watchlist(self, ctx):
        """Manage your watchlists."""

    @watchlist.group(name="movie", invoke_without_command=True)
    async def watchlist_movie(self, ctx, id_: int):
        """Manage your movie(s) watchlist

        Use <id> to get a specific watchlist."""
        movie = await self.config.user(ctx.author).movie()
        try:
            if isinstance(movie[id_], list):
                await ctx.send(movie[id_][1])
            else:
                await ctx.send(movie[id_])
        except IndexError:
            await ctx.send(f"Invalid ID: {id_}")

    @watchlist_movie.command(name="add")
    async def watchlist_movie_add(self, ctx, *, task: str):
        """Add a new task to your watchlist."""
        async with self.config.user(ctx.author).movie() as movie:
            movie_id = len(movie)
            movie.append(
                [ctx.message.jump_url, task]
            )  # using a list to support future watchlist edit
        await ctx.send(f"Your watchlist for movie has been added to id: **{movie_id}**")

    @watchlist_movie.command(name="edit")
    async def watchlist_movie_edit(self, ctx, index: int, *, task: str):
        """Edit a watchlist quickly"""
        async with self.config.user(ctx.author).movie() as movie:
            try:
                old = (
                    movie[index][1] if isinstance(movie[index], list) else movie[index]
                )
                movie[index] = [ctx.message.jump_url, task]
                await ctx.send_interactive(
                    pagify(
                        f"Sucessfully edited ID: {index}\n**from:**\n{old}\n**to:**\n{task}"
                    )
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {index}")

    @watchlist_movie.command(name="list")
    async def watchlist_movie_list(self, ctx):
        """List all your watchlists"""
        movie = await self.config.user(ctx.author).movie()
        if not movie:
            await ctx.send("There's no movie(s) in your watchlist.")
        else:
            movie_text = ""
            if await ctx.embed_requested():
                for i, x in enumerate(movie):
                    if isinstance(x, list):
                        movie_text += f"{i}. {x[1]}\n"
                    else:
                        movie_text += f"{i}. {x}\n"
                pagified = tuple(pagify(movie_text, page_length=2048, shorten_by=0))
                # embeds and menus
                if await self.config.menus():
                    emb_pages = [
                        discord.Embed(
                            title="Your movie WatchList:",
                            description=page,
                            color=await ctx.embed_color(),
                        ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        for num, page in enumerate(pagified, 1)
                    ]
                    await ResultMenu(source=Source(emb_pages, per_page=1)).start(ctx)
                # embeds and not menus
                else:
                    for num, page in enumerate(pagified, 1):
                        await ctx.send(
                            embed=discord.Embed(
                                title="Your movie WatchList:",
                                description=page,
                                color=await ctx.embed_color(),
                            ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        )
            else:
                for i, x in enumerate(movie):
                    movie_text += (
                        f"{i}. {x[1]}\n" if isinstance(x, list) else f"{i}. {x}\n"
                    )
                pagified = tuple(pagify(movie_text))
                # not embeds and menus
                if await self.config.menus():
                    await ResultMenu(source=Source(pagified, per_page=1)).start(ctx)
                # not embeds and not menus
                else:
                    for page in pagified:
                        await ctx.send(page)

    @watchlist_movie.command(name="search")
    async def watchlist_movie_search(self, ctx, *, text):
        """Quick search in your watchlist to find stuff fast."""
        no_case = text.lower()
        movie = await self.config.user(ctx.author).movie()
        async with ctx.typing():
            results = []
            for ind in range(len(movie)):
                x = movie[ind][1] if isinstance(movie[ind], list) else movie[ind]
                if no_case in x.lower():
                    results.append(f"**{ind}**. {x}")
            if results:
                await ctx.send_interactive(
                    pagify(f"Search results for {text}:\n" + "\n".join(results))
                )
            else:
                await ctx.send(f"No results found for {text}")

    @watchlist_movie.command(name="remove", aliases=["delete"])
    async def watchlist_movie_remove(self, ctx, *indices: int):
        """Remove your watchlist tasks,

        supports multiple id removals as well.

        **Example:**
        - `[p]watchlist movie remove 1 2 3`."""
        movie = await self.config.user(ctx.author).movie()
        if len(indices) == 1:
            try:
                x = movie.pop(indices[0])
                await self.config.user(ctx.author).movie.set(movie)
                await ctx.send_interactive(
                    pagify(f"Succesfully removed: {x[1] if isinstance(x,list) else x}")
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {indices[0]}")
        else:
            removed = []
            temp = []
            removed_inds = []
            for j, i in enumerate(movie):
                if j not in indices:
                    temp.append(i)
                else:
                    removed.append(i)
                    removed_inds.append(j)
            await self.config.user(ctx.author).movie.set(temp)
            if removed:
                await ctx.send_interactive(
                    pagify(
                        (
                            f"Invalid IDs:{', '.join(str(i) for i in indices if i not in removed_inds)} \n"
                            if len(removed) != len(indices)
                            else ""
                        )
                        + "Succesfully removed:\n"
                        + "\n".join(
                            f"{i}. {x[1] if isinstance(x,list) else x}"
                            for i, x in enumerate(removed, 1)
                        ),
                    )
                )
            else:
                await ctx.send(f"Invalid IDs: {', '.join(map(str,indices))}")

            # ---- series -----

    @watchlist.group(name="serie", invoke_without_command=True)
    async def watchlist_serie(self, ctx, id_: int):
        """Manage your serie(s) watchlist

        Use <id> to get a specific watchlist."""
        serie = await self.config.user(ctx.author).serie()
        try:
            if isinstance(serie[id_], list):
                await ctx.send(serie[id_][1])
            else:
                await ctx.send(serie[id_])
        except IndexError:
            await ctx.send(f"Invalid ID: {id_}")

    @watchlist_serie.command(name="add")
    async def watchlist_serie_add(self, ctx, *, task: str):
        """Add a new task to your watchlist."""
        async with self.config.user(ctx.author).serie() as serie:
            serie_id = len(serie)
            serie.append(
                [ctx.message.jump_url, task]
            )  # using a list to support future watchlist edit
        await ctx.send(f"Your watchlist has been added to id: **{serie_id}**")

    @watchlist_serie.command(name="edit")
    async def watchlist_serie_edit(self, ctx, index: int, *, task: str):
        """Edit a watchlist quickly"""
        async with self.config.user(ctx.author).serie() as serie:
            try:
                old = (
                    serie[index][1] if isinstance(serie[index], list) else serie[index]
                )
                serie[index] = [ctx.message.jump_url, task]
                await ctx.send_interactive(
                    pagify(
                        f"Sucessfully edited ID: {index}\n**from:**\n{old}\n**to:**\n{task}"
                    )
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {index}")

    @watchlist_serie.command(name="list")
    async def watchlist_serie_list(self, ctx):
        """List all your watchlists"""
        serie = await self.config.user(ctx.author).serie()
        if not serie:
            await ctx.send("There's no serie(s) in your watchlist.")
        else:
            serie_text = ""
            if await ctx.embed_requested():
                for i, x in enumerate(serie):
                    if isinstance(x, list):
                        serie_text += f"{i}. {x[1]}\n"
                    else:
                        serie_text += f"{i}. {x}\n"
                pagified = tuple(pagify(serie_text, page_length=2048, shorten_by=0))
                # embeds and menus
                if await self.config.menus():
                    emb_pages = [
                        discord.Embed(
                            title="Your serie WatchList:",
                            description=page,
                            color=await ctx.embed_color(),
                        ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        for num, page in enumerate(pagified, 1)
                    ]
                    await ResultMenu(source=Source(emb_pages, per_page=1)).start(ctx)
                # embeds and not menus
                else:
                    for num, page in enumerate(pagified, 1):
                        await ctx.send(
                            embed=discord.Embed(
                                title="Your serie WatchList:",
                                description=page,
                                color=await ctx.embed_color(),
                            ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        )
            else:
                for i, x in enumerate(serie):
                    serie_text += (
                        f"{i}. {x[1]}\n" if isinstance(x, list) else f"{i}. {x}\n"
                    )
                pagified = tuple(pagify(serie_text))
                # not embeds and menus
                if await self.config.menus():
                    await ResultMenu(source=Source(pagified, per_page=1)).start(ctx)
                # not embeds and not menus
                else:
                    for page in pagified:
                        await ctx.send(page)

    @watchlist_serie.command(name="search")
    async def watchlist_serie_search(self, ctx, *, text):
        """Quick search in your watchlist to find stuff fast."""
        no_case = text.lower()
        serie = await self.config.user(ctx.author).serie()
        async with ctx.typing():
            results = []
            for ind in range(len(serie)):
                x = serie[ind][1] if isinstance(serie[ind], list) else serie[ind]
                if no_case in x.lower():
                    results.append(f"**{ind}**. {x}")
            if results:
                await ctx.send_interactive(
                    pagify(f"Search results for {text}:\n" + "\n".join(results))
                )
            else:
                await ctx.send(f"No results found for {text}")

    @watchlist_serie.command(name="remove", aliases=["delete"])
    async def watchlist_serie_remove(self, ctx, *indices: int):
        """Remove your watchlist tasks,

        supports multiple id removals as well.

        **Example:**
        - `[p]watchlist serie remove 1 2 3`."""
        serie = await self.config.user(ctx.author).serie()
        if len(indices) == 1:
            try:
                x = serie.pop(indices[0])
                await self.config.user(ctx.author).serie.set(serie)
                await ctx.send_interactive(
                    pagify(f"Succesfully removed: {x[1] if isinstance(x,list) else x}")
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {indices[0]}")
        else:
            removed = []
            temp = []
            removed_inds = []
            for j, i in enumerate(serie):
                if j not in indices:
                    temp.append(i)
                else:
                    removed.append(i)
                    removed_inds.append(j)
            await self.config.user(ctx.author).serie.set(temp)
            if removed:
                await ctx.send_interactive(
                    pagify(
                        (
                            f"Invalid IDs:{', '.join(str(i) for i in indices if i not in removed_inds)} \n"
                            if len(removed) != len(indices)
                            else ""
                        )
                        + "Succesfully removed:\n"
                        + "\n".join(
                            f"{i}. {x[1] if isinstance(x,list) else x}"
                            for i, x in enumerate(removed, 1)
                        ),
                    )
                )
            else:
                await ctx.send(f"Invalid IDs: {', '.join(map(str,indices))}")

    # ---- anime -----

    @watchlist.group(name="anime", invoke_without_command=True)
    async def watchlist_anime(self, ctx, id_: int):
        """Manage your anime(s) watchlist

        Use <id> to get a specific watchlist."""
        anime = await self.config.user(ctx.author).anime()
        try:
            if isinstance(anime[id_], list):
                await ctx.send(anime[id_][1])
            else:
                await ctx.send(anime[id_])
        except IndexError:
            await ctx.send(f"Invalid ID: {id_}")

    @watchlist_anime.command(name="add")
    async def watchlist_anime_add(self, ctx, *, task: str):
        """Add a new task to your watchlist."""
        async with self.config.user(ctx.author).anime() as anime:
            anime_id = len(anime)
            anime.append(
                [ctx.message.jump_url, task]
            )  # using a list to support future watchlist edit
        await ctx.send(f"Your watchlist for anime has been added to id: **{anime_id}**")

    @watchlist_anime.command(name="edit")
    async def watchlist_anime_edit(self, ctx, index: int, *, task: str):
        """Edit a watchlist quickly"""
        async with self.config.user(ctx.author).anime() as anime:
            try:
                old = (
                    anime[index][1] if isinstance(anime[index], list) else anime[index]
                )
                anime[index] = [ctx.message.jump_url, task]
                await ctx.send_interactive(
                    pagify(
                        f"Sucessfully edited ID: {index}\n**from:**\n{old}\n**to:**\n{task}"
                    )
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {index}")

    @watchlist_anime.command(name="list")
    async def watchlist_anime_list(self, ctx):
        """List all your watchlists"""
        anime = await self.config.user(ctx.author).anime()
        if not anime:
            await ctx.send("There's no anime(s) in your watchlist.")
        else:
            anime_text = ""
            if await ctx.embed_requested():
                for i, x in enumerate(anime):
                    if isinstance(x, list):
                        anime_text += f"{i}. {x[1]}\n"
                    else:
                        anime_text += f"{i}. {x}\n"
                pagified = tuple(pagify(anime_text, page_length=2048, shorten_by=0))
                # embeds and menus
                if await self.config.menus():
                    emb_pages = [
                        discord.Embed(
                            title="Your anime WatchList:",
                            description=page,
                            color=await ctx.embed_color(),
                        ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        for num, page in enumerate(pagified, 1)
                    ]
                    await ResultMenu(source=Source(emb_pages, per_page=1)).start(ctx)
                # embeds and not menus
                else:
                    for num, page in enumerate(pagified, 1):
                        await ctx.send(
                            embed=discord.Embed(
                                title="Your anime WatchList:",
                                description=page,
                                color=await ctx.embed_color(),
                            ).set_footer(text=f"Page: {num}/{len(pagified)}")
                        )
            else:
                for i, x in enumerate(anime):
                    anime_text += (
                        f"{i}. {x[1]}\n" if isinstance(x, list) else f"{i}. {x}\n"
                    )
                pagified = tuple(pagify(anime_text))
                # not embeds and menus
                if await self.config.menus():
                    await ResultMenu(source=Source(pagified, per_page=1)).start(ctx)
                # not embeds and not menus
                else:
                    for page in pagified:
                        await ctx.send(page)

    @watchlist_anime.command(name="search")
    async def watchlist_anime_search(self, ctx, *, text):
        """Quick search in your watchlist to find stuff fast."""
        no_case = text.lower()
        anime = await self.config.user(ctx.author).anime()
        async with ctx.typing():
            results = []
            for ind in range(len(anime)):
                x = anime[ind][1] if isinstance(anime[ind], list) else anime[ind]
                if no_case in x.lower():
                    results.append(f"**{ind}**. {x}")
            if results:
                await ctx.send_interactive(
                    pagify(f"Search results for {text}:\n" + "\n".join(results))
                )
            else:
                await ctx.send(f"No results found for {text}")

    @watchlist_anime.command(name="remove", aliases=["delete"])
    async def watchlist_anime_remove(self, ctx, *indices: int):
        """Remove your watchlist tasks,

        supports multiple id removals as well.

        **Example:**
        - `[p]watchlist anime remove 1 2 3`."""
        anime = await self.config.user(ctx.author).anime()
        if len(indices) == 1:
            try:
                x = anime.pop(indices[0])
                await self.config.user(ctx.author).anime.set(anime)
                await ctx.send_interactive(
                    pagify(f"Succesfully removed: {x[1] if isinstance(x,list) else x}")
                )
            except IndexError:
                await ctx.send(f"Invalid ID: {indices[0]}")
        else:
            removed = []
            temp = []
            removed_inds = []
            for j, i in enumerate(anime):
                if j not in indices:
                    temp.append(i)
                else:
                    removed.append(i)
                    removed_inds.append(j)
            await self.config.user(ctx.author).anime.set(temp)
            if removed:
                await ctx.send_interactive(
                    pagify(
                        (
                            f"Invalid IDs:{', '.join(str(i) for i in indices if i not in removed_inds)} \n"
                            if len(removed) != len(indices)
                            else ""
                        )
                        + "Succesfully removed:\n"
                        + "\n".join(
                            f"{i}. {x[1] if isinstance(x,list) else x}"
                            for i, x in enumerate(removed, 1)
                        ),
                    )
                )
            else:
                await ctx.send(f"Invalid IDs: {', '.join(map(str,indices))}")

    @watchlist.command(aliases=["clear"])
    async def removeall(self, ctx, *indices: int):
        """Removes all your watchlists from all lists."""
        msg = await ctx.send("Are you sure do you want to remove all your watchlists?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await ctx.bot.wait_for("reaction_add", check=pred)
        except asyncio.TimeoutError:
            pass
        if pred.result is True:
            await self.config.user_from_id(ctx.author.id).clear()
            await ctx.send("Successfully removed all your watchlists")
        else:
            await ctx.send("Cancelled.")

    @watchlist.command(name="version")
    @commands.bot_has_permissions(embed_links=True)
    async def watchlist_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}.",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # should I add anything more here?
        await self.config.user_from_id(user_id).clear()


# ---- MENUS ------


class Source(menus.ListPageSource):
    async def format_page(self, menu, embeds):
        return embeds


# Thanks fixator https://github.com/fixator10/Fixator10-Cogs/blob/V3.leveler_abc/leveler/menus/top.py
class ResultMenu(menus.MenuPages, inherit_buttons=False):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            timeout=60,
            clear_reactions_after=True,
            delete_message_after=True,
        )

    def _skip_double_triangle_buttons(self):
        return super()._skip_double_triangle_buttons()

    async def finalize(self, timed_out):
        """|coro|
        A coroutine that is called when the menu loop has completed
        its run. This is useful if some asynchronous clean-up is
        required after the fact.
        Parameters
        --------------
        timed_out: :class:`bool`
            Whether the menu completed due to timing out.
        """
        if timed_out and self.delete_message_after:
            self.delete_message_after = False

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @menus.button("\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f", position=menus.First(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        if self.current_page == 0:
            await self.show_page(self._source.get_max_pages() - 1)
        else:
            await self.show_checked_page(self.current_page - 1)

    @menus.button("\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f", position=menus.Last(0))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        if self.current_page == self._source.get_max_pages() - 1:
            await self.show_page(0)
        else:
            await self.show_checked_page(self.current_page + 1)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)

    @menus.button("\N{CROSS MARK}", position=menus.First(2))
    async def stop_pages(self, payload) -> None:
        self.stop()
