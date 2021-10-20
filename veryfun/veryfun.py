import aiohttp
import discord
import logging

from redbot.core import commands

log = logging.getLogger("red.maxcogs.veryfun")

NEKOS = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845956415488.png?v=1"


async def api_call(self, ctx, action: str):
    async with self.session.get(NEKOS + action) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        if response.status == 502:
            return await ctx.send("Api is currently down, try again later.")
        url = await response.json()
        return url


async def embedgen(self, ctx, user, url, action: str):
    emb = discord.Embed(
        colour=await ctx.embed_color(),
        description=f"**{ctx.author.mention}** {action} {f'**{str(user.mention)}**' if user else 'themselves'}!",
    )
    emb.set_footer(
        text="Powered by nekos.best",
        icon_url=ICON,
    )
    try:
        emb.set_image(url=url["url"])
    except KeyError:
        return await ctx.send("I ran into an issue. please try again later.")
    try:
        await ctx.send(f"{str(user.mention)}", embed=emb)
    except discord.HTTPException as e:
        await ctx.send("Something went wrong while posting. Check console for more.")
        log.error(f"Command '{ctx.command.name}' failed to post: {e}")


class VeryFun(commands.Cog):
    """Roleplay commands."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.0.8"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def baka(self, ctx, user: discord.Member):
        """Baka baka baka!"""
        url = await api_call(self, ctx, "baka")
        await embedgen(self, ctx, user, url, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: discord.Member):
        """Cry!"""
        url = await api_call(self, ctx, "cry")
        await embedgen(self, ctx, user, url, "cried")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: discord.Member):
        """Cuddle a user!"""
        url = await api_call(self, ctx, "cuddle")
        await embedgen(self, ctx, user, url, "cuddles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: discord.Member):
        """Dance!"""
        url = await api_call(self, ctx, "dance")
        await embedgen(self, ctx, user, url, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: discord.Member):
        """Feeds a user!"""
        url = await api_call(self, ctx, "feed")
        await embedgen(self, ctx, user, url, "feeds")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hugs(self, ctx, user: discord.Member):
        """Hugs a user!"""
        url = await api_call(self, ctx, "hug")
        await embedgen(self, ctx, user, url, "hugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: discord.Member):
        """Kiss a user!"""
        url = await api_call(self, ctx, "kiss")
        await embedgen(self, ctx, user, url, "just kissed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: discord.Member):
        """laugh!"""
        url = await api_call(self, ctx, "laugh")
        await embedgen(self, ctx, user, url, "laughs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: discord.Member):
        """Pats a user!"""
        url = await api_call(self, ctx, "pat")
        await embedgen(self, ctx, user, url, "pats")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: discord.Member):
        """Poke a user!"""
        url = await api_call(self, ctx, "poke")
        await embedgen(self, ctx, user, url, "pokes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member):
        """Slap a user!"""
        url = await api_call(self, ctx, "slap")
        await embedgen(self, ctx, user, url, "just slapped")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: discord.Member):
        """Smile!"""
        url = await api_call(self, ctx, "smile")
        await embedgen(self, ctx, user, url, "smiles at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: discord.Member):
        """Smugs at someone!"""
        url = await api_call(self, ctx, "smug")
        await embedgen(self, ctx, user, url, "smugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: discord.Member):
        """Tickle a user!"""
        url = await api_call(self, ctx, "tickle")
        await embedgen(self, ctx, user, url, "tickles")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: discord.Member):
        """Waves!"""
        url = await api_call(self, ctx, "wave")
        await embedgen(self, ctx, user, url, "waves at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: discord.Member):
        """Bite a user!"""
        url = await api_call(self, ctx, "bite")
        await embedgen(self, ctx, user, url, "bites")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: discord.Member):
        """blushs!"""
        url = await api_call(self, ctx, "blush")
        await embedgen(self, ctx, user, url, "blushes")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: discord.Member):
        """You're bored!"""
        url = await api_call(self, ctx, "bored")
        await embedgen(self, ctx, user, url, "very bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: discord.Member):
        """Facepalm a user!"""
        url = await api_call(self, ctx, "facepalm")
        await embedgen(self, ctx, user, url, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: discord.Member):
        """happiness with a user!"""
        url = await api_call(self, ctx, "happy")
        await embedgen(self, ctx, user, url, "is happy for")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: discord.Member):
        """highfive a user!"""
        url = await api_call(self, ctx, "highfive")
        await embedgen(self, ctx, user, url, "highfives")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: discord.Member):
        """Pout a user!"""
        url = await api_call(self, ctx, "pout")
        await embedgen(self, ctx, user, url, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: discord.Member):
        """Shrugs a user!"""
        url = await api_call(self, ctx, "shrug")
        await embedgen(self, ctx, user, url, "shrugs")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: discord.Member):
        """Sleep zzzz!"""
        url = await api_call(self, ctx, "sleep")
        await embedgen(self, ctx, user, url, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: discord.Member):
        """Stares at a user!"""
        url = await api_call(self, ctx, "stare")
        await embedgen(self, ctx, user, url, "stares at")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: discord.Member):
        """Thinking!"""
        url = await api_call(self, ctx, "think")
        await embedgen(self, ctx, user, url, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: discord.Member):
        """thumbsup!"""
        url = await api_call(self, ctx, "thumbsup")
        await embedgen(self, ctx, user, url, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: discord.Member):
        """Winks at a user!"""
        url = await api_call(self, ctx, "wink")
        await embedgen(self, ctx, user, url, "winks")
