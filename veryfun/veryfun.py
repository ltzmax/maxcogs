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
            return await ctx.send(
                "Something went wrong while trying to contact API."
            )
        if response.status == 502:
            return await ctx.send("Api is currently down, try again later.")
        url = await response.json()
        return url

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

    __version__ = "0.0.7"
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
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** baka {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'baka' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: discord.Member):
        """Cry!"""
        url = await api_call(self, ctx, "cry")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** cried {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'cry' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: discord.Member):
        """Cuddle a user!"""
        url = await api_call(self, ctx, "cuddle")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** cuddles {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'cuddle' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: discord.Member):
        """Dance!"""
        url = await api_call(self, ctx, "dance")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** dance {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'dance' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: discord.Member):
        """Feeds a user!"""
        url = await api_call(self, ctx, "feed")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** feeds {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'feed' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hugs(self, ctx, user: discord.Member):
        """Hugs a user!"""
        url = await api_call(self, ctx, "baka")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** hugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'hugs' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: discord.Member):
        """Kiss a user!"""
        url = await api_call(self, ctx, "kiss")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** just kissed {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'kiss' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: discord.Member):
        """laugh!"""
        url = await api_call(self, ctx, "laugh")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** laughs {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'laugh' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: discord.Member):
        """Pats a user!"""
        url = await api_call(self, ctx, "pat")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** pats {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'pat' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: discord.Member):
        """Poke a user!"""
        url = await api_call(self, ctx, "poke")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** pokes {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'poke' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member):
        """Slap a user!"""
        url = await api_call(self, ctx, "slap")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** just slapped {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'slap' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: discord.Member):
        """Smile!"""
        url = await api_call(self, ctx, "smile")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** smiles at {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'smile' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: discord.Member):
        """Smugs at someone!"""
        url = await api_call(self, ctx, "smug")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** smugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'smug' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: discord.Member):
        """Tickle a user!"""
        url = await api_call(self, ctx, "tickle")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** tickles {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'tickle' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: discord.Member):
        """Waves!"""
        url = await api_call(self, ctx, "wave")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** waves at {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'wave' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: discord.Member):
        """Bite a user!"""
        url = await api_call(self, ctx, "bite")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** bites {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'bite' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: discord.Member):
        """blushs!"""
        url = await api_call(self, ctx, "blush")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** blushes {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'blush' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: discord.Member):
        """You're bored!"""
        url = await api_call(self, ctx, "bored")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** very bored {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'bored' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: discord.Member):
        """Facepalm a user!"""
        url = await api_call(self, ctx, "facepalm")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** facepalm {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'facepalm' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: discord.Member):
        """happiness with a user!"""
        url = await api_call(self, ctx, "happy")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** is happy for {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'happy' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: discord.Member):
        """highfive a user!"""
        url = await api_call(self, ctx, "highfive")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** highfives {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'highfive' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: discord.Member):
        """Pout a user!"""
        url = await api_call(self, ctx, "pout")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** pout {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'pout' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: discord.Member):
        """Shrugs a user!"""
        url = await api_call(self, ctx, "shrug")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** shrugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'shrug' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: discord.Member):
        """Sleep zzzz!"""
        url = await api_call(self, ctx, "sleep")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** sleep {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'sleep' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: discord.Member):
        """Stares at a user!"""
        url = await api_call(self, ctx, "stare")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** stares at {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'stare' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: discord.Member):
        """Thinking!"""
        url = await api_call(self, ctx, "think")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** think {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'think' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: discord.Member):
        """thumbsup!"""
        url = await api_call(self, ctx, "thimbsup")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** thumbsup {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'thumbsup' failed to post: {e}")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: discord.Member):
        """Winks at a user!"""
        url = await api_call(self, ctx, "wink")
        emb = discord.Embed(
            colour=await ctx.embed_color(),
            description=f"**{ctx.author.mention}** winks {f'**{str(user.mention)}**' if user else 'themselves'}!",
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
            await ctx.send(
                "Something went wrong while posting. Check console for more."
            )
            log.error(f"Command 'wink' failed to post: {e}")
