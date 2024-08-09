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

from typing import Any, Dict, Final, Optional

import aiohttp
import discord
import orjson
import logging
from redbot.core import commands, Config
from redbot.core.bot import Red
from .core import ACTIONS, ICON, NEKOS
from .view import ImageButtonView, CountButtonView

log = logging.getLogger("red.maxcogs.nekosbest")


async def api_call(self, ctx: commands.Context, endpoint: str) -> Optional[Dict[str, Any]]:
    await ctx.typing()
    async with self.session.get(NEKOS + endpoint) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
            log.error("Something went wrong while trying to contact API.")
        data = await response.read()
        url = orjson.loads(data)
        return url

    # ------- Image Commands Handler ------->


async def imgembedgen(ctx: commands.Context, url: Dict[str, Any], endpoint: str) -> None:
    result = url["results"][0]
    artist_name = result["artist_name"]
    source_url = result["source_url"]
    artist_href = result["artist_href"]
    image = result["url"]

    emb = discord.Embed(
        title=f"Here's a picture of a {endpoint}",
        description=f"**Artist:** [{artist_name}]({artist_href})\n**Source:** {source_url}",
    )
    emb.colour = await ctx.embed_color()
    emb.set_image(url=image)
    emb.set_footer(text="Powered by nekos.best", icon_url=ICON)
    view = ImageButtonView(artist_href, source_url, image)
    await ctx.send(embed=emb, view=view)


class NekosBest(commands.Cog):
    """Sends random images from nekos.best + RolePlay Commands."""

    __version__: Final[str] = "2.3.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/NekosBest.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {"command_counts": {}}
        self.config.register_user(**default_user)

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    # ------- RolePlay Commands Handler ------>

    async def embedgen(self, ctx: commands.Context, member: discord.Member, action: str) -> None:
        url = await api_call(self, ctx, action)
        if url is None:
            return

        action_fmt = ACTIONS.get(action, action)
        anime_name = url["results"][0]["anime_name"]
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=(
                f"{ctx.author.mention} {action_fmt} {f'{member.mention}' if member and member != ctx.author else 'themselves!'}"
            ),
        )
        emb.set_footer(text=f"Powered by nekos.best\nAnime Name: {anime_name}", icon_url=ICON)
        emb.set_image(url=url["results"][0]["url"])

        # Count the command usage
        user_config = self.config.user(ctx.author)
        command_counts = await user_config.command_counts()
        if action not in command_counts:
            command_counts[action] = 0
        command_counts[action] += 1
        await user_config.command_counts.set(command_counts)
        count = command_counts[action]

        view = CountButtonView(ctx, action, count)
        await ctx.send(embed=emb, view=view)

    # -------- image Commands ------->

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def waifu(self, ctx: commands.Context) -> None:
        """Send a random waifu image."""
        url = await api_call(self, ctx, "waifu")
        await imgembedgen(ctx, url, "waifu")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def nekos(self, ctx: commands.Context) -> None:
        """Send a random neko image."""
        url = await api_call(self, ctx, "neko")
        await imgembedgen(ctx, url, "neko")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def kitsune(self, ctx: commands.Context) -> None:
        """Send a random kitsune image."""
        url = await api_call(self, ctx, "kitsune")
        await imgembedgen(ctx, url, "kitsune")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def husbando(self, ctx: commands.Context) -> None:
        """Send a random husbando image."""
        url = await api_call(self, ctx, "husbando")
        await imgembedgen(ctx, url, "husbando")

    # --------- ROLEPLAY COMMANDS ------------>

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def yawn(self, ctx: commands.Context, member: discord.Member) -> None:
        """yawn!"""
        await self.embedgen(ctx, member, "yawn")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def handshake(self, ctx: commands.Context, member: discord.Member) -> None:
        """handshake!"""
        await self.embedgen(ctx, member, "handshake")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def lurk(self, ctx: commands.Context, member: discord.Member) -> None:
        """Lurks!"""
        await self.embedgen(ctx, member, "lurk")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def peck(self, ctx: commands.Context, member: discord.Member) -> None:
        """peck!"""
        await self.embedgen(ctx, member, "peck")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def baka(self, ctx: commands.Context, member: discord.Member) -> None:
        """Baka baka baka!"""
        await self.embedgen(ctx, member, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cry(self, ctx: commands.Context, member: discord.Member) -> None:
        """Cry!"""
        await self.embedgen(ctx, member, "cry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cuddle(self, ctx: commands.Context, member: discord.Member) -> None:
        """Cuddle a user!"""
        await self.embedgen(ctx, member, "cuddle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def dance(self, ctx: commands.Context, member: discord.Member) -> None:
        """Dance!"""
        await self.embedgen(ctx, member, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def feed(self, ctx: commands.Context, member: discord.Member) -> None:
        """Feeds a user!"""
        await self.embedgen(ctx, member, "feed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def hugs(self, ctx: commands.Context, member: discord.Member) -> None:
        """Hugs a user!"""
        await self.embedgen(ctx, member, "hug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def kiss(self, ctx: commands.Context, member: discord.Member) -> None:
        """Kiss a user!"""
        await self.embedgen(ctx, member, "kiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def laugh(self, ctx: commands.Context, member: discord.Member) -> None:
        """laugh!"""
        await self.embedgen(ctx, member, "laugh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pat(self, ctx: commands.Context, member: discord.Member) -> None:
        """Pats a user!"""
        await self.embedgen(ctx, member, "pat")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokes(self, ctx: commands.Context, member: discord.Member) -> None:
        # Due to conflict with pokecord cog, it has to be pokes.
        # Feel free to use alias cog if you want poke only.
        """Pokes at a user!"""
        await self.embedgen(ctx, member, "poke")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def slap(self, ctx: commands.Context, member: discord.Member) -> None:
        """Slap a user!"""
        await self.embedgen(ctx, member, "slap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smile(self, ctx: commands.Context, member: discord.Member) -> None:
        """Smile!"""
        await self.embedgen(ctx, member, "smile")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smug(self, ctx: commands.Context, member: discord.Member) -> None:
        """Smugs at someone!"""
        await self.embedgen(ctx, member, "smug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def tickle(self, ctx: commands.Context, member: discord.Member) -> None:
        """Tickle a user!"""
        await self.embedgen(ctx, member, "tickle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wave(self, ctx: commands.Context, member: discord.Member) -> None:
        """Waves!"""
        await self.embedgen(ctx, member, "wave")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bite(self, ctx: commands.Context, member: discord.Member) -> None:
        """Bite a user!"""
        await self.embedgen(ctx, member, "bite")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def blush(self, ctx: commands.Context, member: discord.Member) -> None:
        """blushes!"""
        await self.embedgen(ctx, member, "blush")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bored(self, ctx: commands.Context, member: discord.Member) -> None:
        """You're bored!"""
        await self.embedgen(ctx, member, "bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def facepalm(self, ctx: commands.Context, member: discord.Member) -> None:
        """Facepalm at a user!"""
        await self.embedgen(ctx, member, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def happy(self, ctx: commands.Context, member: discord.Member) -> None:
        """happiness with a user!"""
        await self.embedgen(ctx, member, "happy")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def highfive(self, ctx: commands.Context, member: discord.Member) -> None:
        """highfive a user!"""
        await self.embedgen(ctx, member, "highfive")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pout(self, ctx: commands.Context, member: discord.Member) -> None:
        """Pout a user!"""
        await self.embedgen(ctx, member, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shrug(self, ctx: commands.Context, member: discord.Member) -> None:
        """Shrugs a user!"""
        await self.embedgen(ctx, member, "shrug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sleep(self, ctx: commands.Context, member: discord.Member) -> None:
        """Sleep zzzz!"""
        await self.embedgen(ctx, member, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def stare(self, ctx: commands.Context, member: discord.Member) -> None:
        """Stares at a user!"""
        await self.embedgen(ctx, member, "stare")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def think(self, ctx: commands.Context, member: discord.Member) -> None:
        """Thinking!"""
        await self.embedgen(ctx, member, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def thumbsup(self, ctx: commands.Context, member: discord.Member) -> None:
        """thumbsup!"""
        await self.embedgen(ctx, member, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wink(self, ctx: commands.Context, member: discord.Member) -> None:
        """Winks at a user!"""
        await self.embedgen(ctx, member, "wink")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    async def handhold(self, ctx: commands.Context, member: discord.Member) -> None:
        """handhold a user!"""
        await self.embedgen(ctx, member, "handhold")

    @commands.command(aliases=["vkicks"])
    @commands.bot_has_permissions(embed_links=True)
    async def vkick(self, ctx: commands.Context, member: discord.Member) -> None:
        """kick a user!"""
        await self.embedgen(ctx, member, "kick")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def punch(self, ctx: commands.Context, member: discord.Member) -> None:
        """punch a user!"""
        await self.embedgen(ctx, member, "punch")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shoot(self, ctx: commands.Context, member: discord.Member) -> None:
        """shoot a user!"""
        await self.embedgen(ctx, member, "shoot")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def yeet(self, ctx: commands.Context, member: discord.Member) -> None:
        """yeet a user far far away."""
        await self.embedgen(ctx, member, "yeet")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nod(self, ctx: commands.Context, member: discord.Member) -> None:
        """nods a user far far away."""
        await self.embedgen(ctx, member, "nod")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nope(self, ctx: commands.Context, member: discord.Member) -> None:
        """nope a user far far away."""
        await self.embedgen(ctx, member, "nope")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nom(self, ctx: commands.Context, member: discord.Member) -> None:
        """nom nom a user far far away."""
        await self.embedgen(ctx, member, "nom")
