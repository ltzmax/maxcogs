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
import asyncio
from typing import Optional

import aiohttp
import discord
from redbot.core import Config, commands

from .core import api_call, embedgen


class VeryFun(commands.Cog):
    """Roleplay commands."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    __version__ = "0.1.13"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(name="vrfversion", hidden=True)
    async def veryfun_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def baka(self, ctx, user: Optional[discord.Member] = None):
        """Baka baka baka!"""
        url = await api_call(self, ctx, "baka")
        await embedgen(self, ctx, user, url, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: Optional[discord.Member] = None):
        """Cry!"""
        url = await api_call(self, ctx, "cry")
        await embedgen(self, ctx, user, url, "cries at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: Optional[discord.Member] = None):
        """Cuddle a user!"""
        url = await api_call(self, ctx, "cuddle")
        await embedgen(self, ctx, user, url, "cuddles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: Optional[discord.Member] = None):
        """Dance!"""
        url = await api_call(self, ctx, "dance")
        await embedgen(self, ctx, user, url, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: Optional[discord.Member] = None):
        """Feeds a user!"""
        url = await api_call(self, ctx, "feed")
        await embedgen(self, ctx, user, url, "feeds")

    @commands.command()  # i want `hug` as alias. but i can't cause of core have their own hug command.
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hugs(self, ctx, user: Optional[discord.Member] = None):
        """Hugs a user!"""
        url = await api_call(self, ctx, "hug")
        await embedgen(self, ctx, user, url, "hugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: Optional[discord.Member] = None):
        """Kiss a user!"""
        url = await api_call(self, ctx, "kiss")
        await embedgen(self, ctx, user, url, "just kissed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: Optional[discord.Member] = None):
        """laugh!"""
        url = await api_call(self, ctx, "laugh")
        await embedgen(self, ctx, user, url, "laughs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: Optional[discord.Member] = None):
        """Pats a user!"""
        url = await api_call(self, ctx, "pat")
        await embedgen(self, ctx, user, url, "pats")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: Optional[discord.Member] = None):
        """Poke a user!"""
        url = await api_call(self, ctx, "poke")
        await embedgen(self, ctx, user, url, "pokes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: Optional[discord.Member] = None):
        """Slap a user!"""
        url = await api_call(self, ctx, "slap")
        await embedgen(self, ctx, user, url, "just slapped")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: Optional[discord.Member] = None):
        """Smile!"""
        url = await api_call(self, ctx, "smile")
        await embedgen(self, ctx, user, url, "smiles at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: Optional[discord.Member] = None):
        """Smugs at someone!"""
        url = await api_call(self, ctx, "smug")
        await embedgen(self, ctx, user, url, "smugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: Optional[discord.Member] = None):
        """Tickle a user!"""
        url = await api_call(self, ctx, "tickle")
        await embedgen(self, ctx, user, url, "tickles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: Optional[discord.Member] = None):
        """Waves!"""
        url = await api_call(self, ctx, "wave")
        await embedgen(self, ctx, user, url, "waves at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: Optional[discord.Member] = None):
        """Bite a user!"""
        url = await api_call(self, ctx, "bite")
        await embedgen(self, ctx, user, url, "bites")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: Optional[discord.Member] = None):
        """blushs!"""
        url = await api_call(self, ctx, "blush")
        await embedgen(self, ctx, user, url, "blushes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: Optional[discord.Member] = None):
        """You're bored!"""
        url = await api_call(self, ctx, "bored")
        await embedgen(self, ctx, user, url, "very bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: Optional[discord.Member] = None):
        """Facepalm a user!"""
        url = await api_call(self, ctx, "facepalm")
        await embedgen(self, ctx, user, url, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: Optional[discord.Member] = None):
        """happiness with a user!"""
        url = await api_call(self, ctx, "happy")
        await embedgen(self, ctx, user, url, "is happy for")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: Optional[discord.Member] = None):
        """highfive a user!"""
        url = await api_call(self, ctx, "highfive")
        await embedgen(self, ctx, user, url, "highfives")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: Optional[discord.Member] = None):
        """Pout a user!"""
        url = await api_call(self, ctx, "pout")
        await embedgen(self, ctx, user, url, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: Optional[discord.Member] = None):
        """Shrugs a user!"""
        url = await api_call(self, ctx, "shrug")
        await embedgen(self, ctx, user, url, "shrugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: Optional[discord.Member] = None):
        """Sleep zzzz!"""
        url = await api_call(self, ctx, "sleep")
        await embedgen(self, ctx, user, url, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: Optional[discord.Member] = None):
        """Stares at a user!"""
        url = await api_call(self, ctx, "stare")
        await embedgen(self, ctx, user, url, "stares at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: Optional[discord.Member] = None):
        """Thinking!"""
        url = await api_call(self, ctx, "think")
        await embedgen(self, ctx, user, url, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: Optional[discord.Member] = None):
        """thumbsup!"""
        url = await api_call(self, ctx, "thumbsup")
        await embedgen(self, ctx, user, url, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: Optional[discord.Member] = None):
        """Winks at a user!"""
        url = await api_call(self, ctx, "wink")
        await embedgen(self, ctx, user, url, "winks")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def handhold(self, ctx, user: Optional[discord.Member] = None):
        """handhold a user!"""
        url = await api_call(self, ctx, "handhold")
        await embedgen(self, ctx, user, url, "handholds")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kicks(self, ctx, user: Optional[discord.Member] = None):
        """kick a user!"""
        url = await api_call(self, ctx, "kick")
        await embedgen(self, ctx, user, url, "kicks")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def punch(self, ctx, user: Optional[discord.Member] = None):
        """punch a user!"""
        url = await api_call(self, ctx, "punch")
        await embedgen(self, ctx, user, url, "punches")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shoot(self, ctx, user: Optional[discord.Member] = None):
        """shoot a user!"""
        url = await api_call(self, ctx, "shoot")
        await embedgen(self, ctx, user, url, "shoots")
