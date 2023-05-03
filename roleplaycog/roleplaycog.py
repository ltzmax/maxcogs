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
#from collections import Counter

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number, box

from .core import ACTIONS, ICON, NEKOS

log = logging.getLogger("red.maxcogs.veryfun")


class RolePlayCog(commands.Cog):
    """Roleplay cog to interact with other users."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        #self.config = Config.get_conf(
        #    self, 0x345628097929936899, force_registration=True
        #)
        #self.config.register_user(counter=Counter())

    async def cog_unload(self):
        await self.session.close()

    __version__ = "0.1.17"
    __author__ = "MAX"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/roleplaycog/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def embedgen(self, ctx, member, action: str):
        async with self.session.get(NEKOS + action) as response:
            if response.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
            data = await response.json()

        # Removing "#" will cause KeyError so enjoy if you do that.
        # If you want this to work, feel free to pr. i have absolutely no idea how to fix this.
        # if have tried everything i can think of and it still wont work. so i just leave it like this.
        #    .______      ___       __  .__   __. 
        #    |   _  \    /   \     |  | |  \ |  | 
        #    |  |_)  |  /  ^  \    |  | |   \|  | 
        #    |   ___/  /  /_\  \   |  | |  . `  | 
        #    |  |     /  _____  \  |  | |  |\   | 
        #    | _|    /__/     \__\ |__| |__| \__|
        #async with self.config.member(member or ctx.author).all() as config:
        #    config["counter"][action] += 1

        action_fmt = ACTIONS.get(action, action)
        anime_name = data["results"][0]["anime_name"]
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=(
                f"{ctx.author.mention} {action_fmt} {f'{member.mention}' if member else 'themselves!'}\n"
        #        f"Received {action} count: {humanize_number(config['counter'][action])}"
            ),
        )
        emb.set_footer(
            text=f"Powered by nekos.best\nAnime Name: {anime_name}", icon_url=ICON
        )
        emb.set_image(url=data["results"][0]["url"])
        await ctx.send(embed=emb)

    @commands.command(hidden=True)
    async def rpcversion(self, ctx):
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        await ctx.send(
            box(f"{'Author':<10}: {author}\n{'Version':<10}: {version}", lang="yaml")
        )

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def baka(self, ctx, member: discord.Member):
        """Baka baka baka!"""
        await self.embedgen(ctx, member, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cry(self, ctx, member: discord.Member):
        """Cry!"""
        await self.embedgen(ctx, member, "cry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cuddle(self, ctx, member: discord.Member):
        """Cuddle a user!"""
        await self.embedgen(ctx, member, "cuddle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def dance(self, ctx, member: discord.Member):
        """Dance!"""
        await self.embedgen(ctx, member, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def feed(self, ctx, member: discord.Member):
        """Feeds a user!"""
        await self.embedgen(ctx, member, "feed")

    @commands.command()  # i want `hug` as alias. but i can't cause of core have their own hug command.
    @commands.bot_has_permissions(embed_links=True)
    async def hugs(self, ctx, member: discord.Member):
        """Hugs a user!"""
        await self.embedgen(ctx, member, "hug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def kiss(self, ctx, member: discord.Member):
        """Kiss a user!"""
        await self.embedgen(ctx, member, "kiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def laugh(self, ctx, member: discord.Member):
        """laugh!"""
        await self.embedgen(ctx, member, "laugh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pat(self, ctx, member: discord.Member):
        """Pats a user!"""
        await self.embedgen(ctx, member, "pat")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def poke(self, ctx, member: discord.Member):
        """Poke a user!"""
        await self.embedgen(ctx, member, "poke")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def slap(self, ctx, member: discord.Member):
        """Slap a user!"""
        await self.embedgen(ctx, member, "slap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smile(self, ctx, member: discord.Member):
        """Smile!"""
        await self.embedgen(ctx, member, "smile")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smug(self, ctx, member: discord.Member):
        """Smugs at someone!"""
        await self.embedgen(ctx, member, "smug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def tickle(self, ctx, member: discord.Member):
        """Tickle a user!"""
        await self.embedgen(ctx, member, "tickle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wave(self, ctx, member: discord.Member):
        """Waves!"""
        await self.embedgen(ctx, member, "wave")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bite(self, ctx, member: discord.Member):
        """Bite a user!"""
        await self.embedgen(ctx, member, "bite")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def blush(self, ctx, member: discord.Member):
        """blushs!"""
        await self.embedgen(ctx, member, "blush")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bored(self, ctx, member: discord.Member):
        """You're bored!"""
        await self.embedgen(ctx, member, "bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def facepalm(self, ctx, member: discord.Member):
        """Facepalm a user!"""
        await self.embedgen(ctx, member, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def happy(self, ctx, member: discord.Member):
        """happiness with a user!"""
        await self.embedgen(ctx, member, "happy")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def highfive(self, ctx, member: discord.Member):
        """highfive a user!"""
        await self.embedgen(ctx, member, "highfive")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pout(self, ctx, member: discord.Member):
        """Pout a user!"""
        await self.embedgen(ctx, member, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shrug(self, ctx, member: discord.Member):
        """Shrugs a user!"""
        await self.embedgen(ctx, member, "shrug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sleep(self, ctx, member: discord.Member):
        """Sleep zzzz!"""
        await self.embedgen(ctx, member, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def stare(self, ctx, member: discord.Member):
        """Stares at a user!"""
        await self.embedgen(ctx, member, "stare")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def think(self, ctx, member: discord.Member):
        """Thinking!"""
        await self.embedgen(ctx, member, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def thumbsup(self, ctx, member: discord.Member):
        """thumbsup!"""
        await self.embedgen(ctx, member, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wink(self, ctx, member: discord.Member):
        """Winks at a user!"""
        await self.embedgen(ctx, member, "wink")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    async def handhold(self, ctx, member: discord.Member):
        """handhold a user!"""
        await self.embedgen(ctx, member, "handhold")

    @commands.command(aliases=["vkicks"])
    @commands.bot_has_permissions(embed_links=True)
    async def vkick(self, ctx, member: discord.Member):
        """kick a user!"""
        await self.embedgen(ctx, member, "kick")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def punch(self, ctx, member: discord.Member):
        """punch a user!"""
        await self.embedgen(ctx, member, "punch")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shoot(self, ctx, member: discord.Member):
        """shoot a user!"""
        await self.embedgen(ctx, member, "shoot")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def yeet(self, ctx, member: discord.Member):
        """yeet a user far far away."""
        await self.embedgen(ctx, member, "yeet")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nod(self, ctx, member: discord.Member):
        """nods a user far far away."""
        await self.embedgen(ctx, member, "nod")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nope(self, ctx, member: discord.Member):
        """nope a user far far away."""
        await self.embedgen(ctx, member, "nope")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nom(self, ctx, member: discord.Member):
        """nom nom a user far far away."""
        await self.embedgen(ctx, member, "nom")
