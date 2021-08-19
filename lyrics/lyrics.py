import re
from asyncio import create_task
from asyncio.exceptions import TimeoutError as Te
from typing import Literal, Optional

import discord

# noinspection PyUnresolvedReferences
import ksoftapi
import lavalink
from redbot.core import commands
from redbot.core.utils.chat_formatting import bold, humanize_list, inline, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils.predicates import MessagePredicate

BASE_URL = "https://api.ksoft.si/lyrics/search"
BOT_SONG_RE = re.compile(
    (
        r"((\[)|(\()).*(of?ficial|feat\.?|"  # Thanks Wyn for the logic!
        r"ft\.?|audio|video|lyrics?|remix|HD).*(?(2)]|\))"
    ),
    flags=re.I,
)
# https://github.com/TheWyn/Wyn-RedV3Cogs/blob/fbd7ea3cfbd53dc27f50d43cf884041ab1b5bafc/lyrics/lyrics.py#L10


class Lyrics(commands.Cog):

    __author__ = ["Predeactor", "MAX"]
    __version__ = "v2.0.1"

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.client = None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        """
        Nothing to delete...
        """
        pass

    @commands.command(alias=["lyric"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user, wait=False)
    async def lyrics(self, ctx: commands.Context, *, song_name: Optional[str]):
        """Return the lyrics of a given music/song name or running music.

        This command can also find out the music you're actually listening to.
        Powered by KSoft.Si.
        """
        music = await self.determine_music_source(ctx, song_name)
        if not music and not song_name:
            await ctx.send_help()
            return
        try:
            client = await self.obtain_client()
        except AttributeError:
            await ctx.send("Not key for KSoft.Si has been set, ask owner to add a key.")
            return
        try:
            music_lyrics = await client.music.lyrics(music)
        except ksoftapi.NoResults:
            await ctx.send("No lyrics were found for your music.")
            return
        except ksoftapi.APIError as e:
            await ctx.send(
                "The API returned an unknown error: {error}".format(
                    error=inline(str(e))
                )
            )
            return
        except ksoftapi.Forbidden:
            await ctx.send("Request forbidden by the API.")
            return
        except KeyError:
            await ctx.send(
                "The set API key seem to be wrong. Please contact the bot owner."
            )
            return
        music = await self.get_song(ctx, music_lyrics, bool(song_name))
        if music is None:
            return
        embeds = await self.make_embed(music, ctx)
        if len(embeds) > 1:
            create_task(
                menu(ctx, embeds, DEFAULT_CONTROLS, timeout=600)
            )  # No await since max_concurrency is there
        else:
            await ctx.send(embed=embeds[0])

    async def get_song(self, ctx: commands.Context, music_lyrics, send_question: bool):
        message, available_musics = await self._title_choose(music_lyrics)
        if not send_question:
            return available_musics["0"]

        bot_message = await ctx.maybe_send_embed(message)
        predicator = MessagePredicate.less(10, ctx)
        try:
            user_message = await self.bot.wait_for(
                "message", check=predicator, timeout=60
            )
        except Te:
            await ctx.send("Rude.")
            return
        finally:
            await bot_message.delete()

        chosen_music = user_message.content
        if chosen_music not in available_musics:
            if chosen_music != "-1":
                await ctx.send(
                    "I was unable to find the corresponding music in the available music list."
                )
            return
        return available_musics[chosen_music]

    async def determine_music_source(
        self, ctx: commands.Context, song_str: Optional[str]
    ):
        if isinstance(ctx.channel, discord.DMChannel):
            return song_str
        try:
            player = lavalink.get_player(ctx.guild.id)
        except (KeyError, IndexError):
            player = None
        if not player and song_str:
            return BOT_SONG_RE.sub("", song_str)
        if not (player or song_str):
            return None
        if player and song_str:
            return BOT_SONG_RE.sub("", song_str)

        possible_music = player.current
        if not possible_music:
            return None
        return BOT_SONG_RE.sub("", possible_music.title)

    @staticmethod
    async def make_embed(music: ksoftapi.models.LyricResult, ctx: commands.Context):
        embeds = []
        for text in pagify(music.lyrics):
            embed = discord.Embed(
                color=await ctx.embed_color(), title=music.name, description=None
            )
            embed.set_thumbnail(
                url=music.album_art
                if str(music.album_art)
                != "https://cdn.ksoft.si/images/Logo1024%20-%20W.png"
                else discord.Embed.Empty
            )
            embed.set_footer(
                text="Powered by KSoft.Si.", icon_url=ctx.author.avatar_url
            )
            embed.description = text
            embeds.append(embed)
        return embeds

    @staticmethod
    async def _title_choose(list_of_music: list):
        """Function to return for requesting user's prompt, asking what music to choose.

        Parameters
        ----------
        list_of_music: list
            A list containing musics.

        Returns
        -------
        tuple:
            A tuple that contain a string with the message to send and a dict with methods
            available.
        """
        message = (
            "Please select the music you wish to get the lyrics by selecting the corresponding "
            "number (Say `-1` to abort):\n\n"
        )
        method = {}
        n = 0
        for music in list_of_music:
            # noinspection PyUnresolvedReferences
            if not isinstance(music, ksoftapi.models.LyricResult):
                continue  # Not a music
            year = music.album_year[0]
            message += "`{number}` - {title} by {author}{year}\n".format(
                number=n,
                title=music.name,
                author=music.artist,
                year=" (" + bold(str(year)) + ")" if year and int(year) > 1970 else "",
            )
            method[str(n)] = music
            n += 1
        return message, method

    async def obtain_client(self):
        """Get a client and put it in self.client (For caching).

        Returns
        -------
        ksoftapi.Client:
            Client to use, bound to self.client.

        Raises
        ------
        AttributeError:
            If the API key was not set.
        """
        if self.client:
            return self.client
        keys = await self.bot.get_shared_api_tokens("ksoftsi")
        if keys.get("api_key"):
            self.client = ksoftapi.Client(keys.get("api_key"))
            return self.client
        raise AttributeError("API key is not set.")

    @staticmethod
    async def __session_closer(client):
        await client.close()

    def cog_unload(self):
        if self.client:
            create_task(self.__session_closer(self.client))
