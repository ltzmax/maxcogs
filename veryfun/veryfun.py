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
import logging
from collections import Counter
from typing import Optional

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_number

from .core import ACTIONS, ICON, NEKOS

log = logging.getLogger("red.maxcogs.veryfun")


class VeryFun(commands.Cog):
    """Roleplay cog to interact with other users."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, 0x345628097929936899, force_registration=True
        )
        self.config.register_user(counter=Counter())

    async def cog_unload(self):
        await self.session.close()

    __version__ = "0.1.16"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def embedgen(self, ctx, user, action: str):
        async with self.session.get(NEKOS + action) as response:
            if response.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
            data = await response.json()

        async with self.config.user(user or ctx.author).all() as config:
            config["counter"][action] += 1

        action_fmt = ACTIONS.get(action, action)
        anime_name = data["results"][0]["anime_name"]
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=(
                f"**{ctx.author.mention}** {action_fmt} {f'**{user.mention}**' if user else 'themselves!'}\n"
                f"Received {action} count: {humanize_number(config['counter'][action])}"
            ),
        )
        emb.set_footer(
            text=f"Powered by nekos.best | Anime: {anime_name}", icon_url=ICON
        )
        emb.set_image(url=data["results"][0]["url"])
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException:
            await ctx.send(
                "Something went wrong while posting. Check your console for details."
            )
            log.exception(f"Command '{ctx.command.name}' failed to post:")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def baka(self, ctx, user: discord.Member):
        """Baka baka baka!"""
        await self.embedgen(ctx, user, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: discord.Member):
        """Cry!"""
        await self.embedgen(ctx, user, "cry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: discord.Member):
        """Cuddle a user!"""
        await self.embedgen(ctx, user, "cuddle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: discord.Member):
        """Dance!"""
        await self.embedgen(ctx, user, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: discord.Member):
        """Feeds a user!"""
        await self.embedgen(ctx, user, "feed")

    @commands.command()  # i want `hug` as alias. but i can't cause of core have their own hug command.
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hugs(self, ctx, user: discord.Member):
        """Hugs a user!"""
        await self.embedgen(ctx, user, "hug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: discord.Member):
        """Kiss a user!"""
        await self.embedgen(ctx, user, "kiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: discord.Member):
        """laugh!"""
        await self.embedgen(ctx, user, "laugh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: discord.Member):
        """Pats a user!"""
        await self.embedgen(ctx, user, "pat")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: discord.Member):
        """Poke a user!"""
        await self.embedgen(ctx, user, "poke")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member):
        """Slap a user!"""
        await self.embedgen(ctx, user, "slap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: discord.Member):
        """Smile!"""
        await self.embedgen(ctx, user, "smile")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: discord.Member):
        """Smugs at someone!"""
        await self.embedgen(ctx, user, "smug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: discord.Member):
        """Tickle a user!"""
        await self.embedgen(ctx, user, "tickle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: discord.Member):
        """Waves!"""
        await self.embedgen(ctx, user, "wave")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: discord.Member):
        """Bite a user!"""
        await self.embedgen(ctx, user, "bite")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: discord.Member):
        """blushs!"""
        await self.embedgen(ctx, user, "blush")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: discord.Member):
        """You're bored!"""
        await self.embedgen(ctx, user, "bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: discord.Member):
        """Facepalm a user!"""
        await self.embedgen(ctx, user, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: discord.Member):
        """happiness with a user!"""
        await self.embedgen(ctx, user, "happy")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: discord.Member):
        """highfive a user!"""
        await self.embedgen(ctx, user, "highfive")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: discord.Member):
        """Pout a user!"""
        await self.embedgen(ctx, user, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: discord.Member):
        """Shrugs a user!"""
        await self.embedgen(ctx, user, "shrug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: discord.Member):
        """Sleep zzzz!"""
        await self.embedgen(ctx, user, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: discord.Member):
        """Stares at a user!"""
        await self.embedgen(ctx, user, "stare")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: discord.Member):
        """Thinking!"""
        await self.embedgen(ctx, user, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: discord.Member):
        """thumbsup!"""
        await self.embedgen(ctx, user, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: discord.Member):
        """Winks at a user!"""
        await self.embedgen(ctx, user, "wink")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def handhold(self, ctx, user: discord.Member):
        """handhold a user!"""
        await self.embedgen(ctx, user, "handhold")

    @commands.command(aliases=["vkicks"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def vkick(self, ctx, user: discord.Member):
        """kick a user!"""
        await self.embedgen(ctx, user, "kick")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def punch(self, ctx, user: discord.Member):
        """punch a user!"""
        await self.embedgen(ctx, user, "punch")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shoot(self, ctx, user: discord.Member):
        """shoot a user!"""
        await self.embedgen(ctx, user, "shoot")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def yeet(self, ctx, user: discord.Member):
        """yeet a user far far away."""
        await self.embedgen(ctx, user, "yeet")
