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

from typing import Final

import aiohttp
from red_commons.logging import getLogger
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

from .commands.tcgcard import TcgcardCommands
from .commands.whosthatpokemon import WhosThatPokemonCommands
from .commands.pokeinfo import PokeinfoCommands

log = getLogger("red.maxcogs.whosthatpokemon")


class Pokemon(WhosThatPokemonCommands, TcgcardCommands, PokeinfoCommands, commands.Cog):
    """
    This is pokemon related stuff cog.

    - Can you guess Who's That Pokémon?
    - Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).
    - Get information about a Pokémon.
    """

    __author__: Final[tuple[str, ...]] = ("@306810730055729152", "max", "flame442")
    __version__: Final[str] = "2.4.0"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return (
            f"{pre_processed}\n\nAuthor: {humanize_list(list(self.__author__))}"
            f"\nCog Version: {self.__version__}\nDocs: {self.__docs__}"
        )

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Nothing to delete."""
        return
