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
from logging import LoggerAdapter
from typing import Any, Final

import aiohttp
import discord
import orjson
from red_commons.logging import RedTraceLogger, getLogger
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from .core import ACTIONS, ICON, NEKOS

log: RedTraceLogger = getLogger("red.maxcogs.roleplaycog")


class RolePlayCog(commands.Cog):
    """Roleplay cog to interact with other users."""

    __version__: Final[str] = "0.2.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://maxcogs.gitbook.io/maxcogs/cogs/roleplaycog"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

        self.log: LoggerAdapter[RedTraceLogger] = LoggerAdapter(
            log, {"version": self.__version__}
        )

    async def cog_unload(self):
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def embedgen(
        self, ctx: commands.Context, member: discord.Member, action: str
    ) -> None:
        async with self.session.get(NEKOS + action) as response:
            if response.status != 200:
                self.log.error(
                    f"Something went wrong while trying to contact API. Status Code: {response.status}"
                )
                await ctx.send("Something went wrong while trying to contact API.")
                return
            response_data = await response.read()
            data = orjson.loads(response_data)

        action_fmt = ACTIONS.get(action, action)
        anime_name = data["results"][0]["anime_name"]
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=(
                f"{ctx.author.mention} {action_fmt} {f'{member.mention}' if member else 'themselves!'}\n"
            ),
        )
        emb.set_footer(
            text=f"Powered by nekos.best\nAnime Name: {anime_name}", icon_url=ICON
        )
        emb.set_image(url=data["results"][0]["url"])
        await ctx.send(embed=emb)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="rpcversion", hidden=True)
    async def roleplaycog_version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
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
