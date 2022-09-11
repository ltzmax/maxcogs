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

import aiohttp
import discord
from redbot.core import Config, commands

from .embed import api_call, embedgen


class VeryFun(commands.Cog):
    """Roleplay cog to interact with other users."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=0x345628097929936898)
        default_guild = {
            "replies": False,
            "mentions": False,
        }
        self.config.register_guild(**default_guild)

    async def cog_unload(self):
        await self.session.close()

    __version__ = "0.1.16"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.group(aliases=["vfset"])
    @commands.admin_or_permissions(manage_server=True)
    async def veryfunset(self, ctx):
        """Settings to toggle replies."""

    @veryfunset.command(name="reply", aliases=["replies"])
    async def veryfunset_reply(self, ctx: commands.Context, *, replies: bool):
        """Toggle to use replies on each roleplay.

        This is not global setting, this will only enable for this guild.

        **Example**:
        - `[p]verfynset reply true` - This will enable replies.
        - `[p]veryfunset reply false` - This will disable replies.

        **Arguments**:
        - `<replies>` - Where you set either true or false.
        """
        mentions = await self.config.guild(ctx.guild).mentions()
        if mentions is True:
            return await ctx.send(
                "You need to disable mentions before you can disable replies."
            )
        await self.config.guild(ctx.guild).replies.set(replies)
        if not replies:
            await ctx.send("Replies has been disabled")
        else:
            await ctx.send("Replies has been enabled")

    @veryfunset.command(name="mention", aliases=["mentions"])
    async def veryfunset_mention(self, ctx: commands.Context, *, mentions: bool):
        """Toggle to use mentions on replies.

        This is not global setting, this will only enable for this guild.

        **Example**:
        - `[p]verfynset mention true` - This will enable replies.
        - `[p]veryfunset mention false` - This will disable replies.

        **Arguments**:
        - `<mentions>` - Where you set either true or false.
        """
        replies = await self.config.guild(ctx.guild).replies()
        if replies is False:
            return await ctx.send("You need to enable replies to use mentions.")
        await self.config.guild(ctx.guild).mentions.set(mentions)
        if not mentions:
            await ctx.send("mentions has been disabled")
        else:
            await ctx.send("mentions has been enabled")

    @commands.bot_has_permissions(embed_links=True)
    @veryfunset.command(name="settings", aliases=["showsettings"])
    async def veryfunset_settings(self, ctx):
        """Shows current settings.

        - `False` = Disabled.
        - `True` = Enabled.
        """
        replies = await self.config.guild(ctx.guild).replies()
        mentions = await self.config.guild(ctx.guild).mentions()
        embed = discord.Embed(
            title="VeryFun settings",
            description=f"Replies is set to {replies}\nMentions is set to {mentions}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @veryfunset.command(name="version", hidden=True)
    async def veryfunset_version(self, ctx):
        """Shows the cog version."""
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Cog Version:",
                description=f"Author: {self.__author__}\nVersion: {self.__version__}",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(
                f"Cog Version: {self.__version__}\nAuthor: {self.__author__}"
            )

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def baka(self, ctx, user: discord.Member):
        """Baka baka baka!"""
        url = await api_call(self, ctx, "baka")
        await embedgen(self, ctx, user, url, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: discord.Member):
        """Cry at someone or yourself."""
        url = await api_call(self, ctx, "cry")
        await embedgen(self, ctx, user, url, "cries at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: discord.Member):
        """Cuddle a user or yourself."""
        url = await api_call(self, ctx, "cuddle")
        await embedgen(self, ctx, user, url, "cuddles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: discord.Member):
        """Dance!"""
        url = await api_call(self, ctx, "dance")
        await embedgen(self, ctx, user, url, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: discord.Member):
        """Feeds a user!"""
        url = await api_call(self, ctx, "feed")
        await embedgen(self, ctx, user, url, "feeds")

    @commands.command()  # i want `hug` as alias. but i can't cause of core have their own hug command.
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hugs(self, ctx, user: discord.Member):
        """Hugs a user!"""
        url = await api_call(self, ctx, "hug")
        await embedgen(self, ctx, user, url, "hugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: discord.Member):
        """Kiss a user!"""
        url = await api_call(self, ctx, "kiss")
        await embedgen(self, ctx, user, url, "just kissed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: discord.Member):
        """laugh!"""
        url = await api_call(self, ctx, "laugh")
        await embedgen(self, ctx, user, url, "laughs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: discord.Member):
        """Pats a user!"""
        url = await api_call(self, ctx, "pat")
        await embedgen(self, ctx, user, url, "pats")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: discord.Member):
        """Poke a user!"""
        url = await api_call(self, ctx, "poke")
        await embedgen(self, ctx, user, url, "pokes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member):
        """Slap a user!"""
        url = await api_call(self, ctx, "slap")
        await embedgen(self, ctx, user, url, "just slapped")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: discord.Member):
        """Smile!"""
        url = await api_call(self, ctx, "smile")
        await embedgen(self, ctx, user, url, "smiles at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: discord.Member):
        """Smugs at someone!"""
        url = await api_call(self, ctx, "smug")
        await embedgen(self, ctx, user, url, "smugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: discord.Member):
        """Tickle a user!"""
        url = await api_call(self, ctx, "tickle")
        await embedgen(self, ctx, user, url, "tickles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: discord.Member):
        """Waves!"""
        url = await api_call(self, ctx, "wave")
        await embedgen(self, ctx, user, url, "waves at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: discord.Member):
        """Bite a user!"""
        url = await api_call(self, ctx, "bite")
        await embedgen(self, ctx, user, url, "bites")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: discord.Member):
        """blushs!"""
        url = await api_call(self, ctx, "blush")
        await embedgen(self, ctx, user, url, "blushes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: discord.Member):
        """You're bored!"""
        url = await api_call(self, ctx, "bored")
        await embedgen(self, ctx, user, url, "very bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: discord.Member):
        """Facepalm a user!"""
        url = await api_call(self, ctx, "facepalm")
        await embedgen(self, ctx, user, url, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: discord.Member):
        """happiness with a user!"""
        url = await api_call(self, ctx, "happy")
        await embedgen(self, ctx, user, url, "is happy for")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: discord.Member):
        """highfive a user!"""
        url = await api_call(self, ctx, "highfive")
        await embedgen(self, ctx, user, url, "highfives")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: discord.Member):
        """Pout a user!"""
        url = await api_call(self, ctx, "pout")
        await embedgen(self, ctx, user, url, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: discord.Member):
        """Shrugs a user!"""
        url = await api_call(self, ctx, "shrug")
        await embedgen(self, ctx, user, url, "shrugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: discord.Member):
        """Sleep zzzz!"""
        url = await api_call(self, ctx, "sleep")
        await embedgen(self, ctx, user, url, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: discord.Member):
        """Stares at a user!"""
        url = await api_call(self, ctx, "stare")
        await embedgen(self, ctx, user, url, "stares at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: discord.Member):
        """Thinking!"""
        url = await api_call(self, ctx, "think")
        await embedgen(self, ctx, user, url, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: discord.Member):
        """thumbsup!"""
        url = await api_call(self, ctx, "thumbsup")
        await embedgen(self, ctx, user, url, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: discord.Member):
        """Winks at a user!"""
        url = await api_call(self, ctx, "wink")
        await embedgen(self, ctx, user, url, "winks")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def handhold(self, ctx, user: discord.Member):
        """handhold a user!"""
        url = await api_call(self, ctx, "handhold")
        await embedgen(self, ctx, user, url, "handholds")

    @commands.command(aliases=["vkicks"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def vkick(self, ctx, user: discord.Member):
        """kick a user!

        This is `vkick` because kick is taken by the mod cog.
        If you do not use mod cog, you can use alias cog to make it `kick`.
        """
        url = await api_call(self, ctx, "kick")
        await embedgen(self, ctx, user, url, "kicks")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def punch(self, ctx, user: discord.Member):
        """punch a user!"""
        url = await api_call(self, ctx, "punch")
        await embedgen(self, ctx, user, url, "punches")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shoot(self, ctx, user: discord.Member):
        """shoot a user!"""
        url = await api_call(self, ctx, "shoot")
        await embedgen(self, ctx, user, url, "shoots")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def yeet(self, ctx, user: discord.Member):
        """yeet a user far far away."""
        url = await api_call(self, ctx, "yeet")
        await embedgen(self, ctx, user, url, "yeets")
