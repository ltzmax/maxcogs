import aiohttp
import discord
from redbot.core import commands

NEKOS = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845956415488.png?v=1"


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

    __version__ = "0.0.2"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def baka(self, ctx, user: discord.Member):
        """Baka baka baka!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "baka") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** baka {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cry(self, ctx, user: discord.Member):
        """Cry!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "cry") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** cried {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cuddle(self, ctx, user: discord.Member):
        """Cuddle a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "cuddle") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** cuddles {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def dance(self, ctx, user: discord.Member):
        """Dance!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "dance") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** dance {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def feed(self, ctx, user: discord.Member):
        """Feeds a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "feed") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** feeds {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def hug(self, ctx, user: discord.Member):
        """Hugs a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "hug") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** hugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.is_nsfw()  # because kissing can be really out of minds.
    @commands.bot_has_permissions(embed_links=True)
    async def kiss(self, ctx, user: discord.Member):
        """Kiss a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "kiss") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** just kissed {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def laugh(self, ctx, user: discord.Member):
        """laugh!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "laugh") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** laughs {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pat(self, ctx, user: discord.Member):
        """Pats a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "pat") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** pats {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def poke(self, ctx, user: discord.Member):
        """Poke a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "poke") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** pokes {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def slap(self, ctx, user: discord.Member):
        """Slap a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "slap") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** just slapped {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smile(self, ctx, user: discord.Member):
        """Smile!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "smile") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** smiles at {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smug(self, ctx, user: discord.Member):
        """Smugs at someone!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "smug") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** smugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def tickle(self, ctx, user: discord.Member):
        """Tickle a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "tickle") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** tickles {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wave(self, ctx, user: discord.Member):
        """Waves!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "wave") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** waves at {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bite(self, ctx, user: discord.Member):
        """Bite a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "bite") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** bites {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def blush(self, ctx, user: discord.Member):
        """blushs!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "blush") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** blushes {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bored(self, ctx, user: discord.Member):
        """You're bored!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "bored") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** very bored {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def facepalm(self, ctx, user: discord.Member):
        """Facepalm a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "facepalm") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** facepalm {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def happy(self, ctx, user: discord.Member):
        """happiness with a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "happy") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** is happy for {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def highfive(self, ctx, user: discord.Member):
        """highfive a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "highfive") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** highfives {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pout(self, ctx, user: discord.Member):
        """Pout a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "pout") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** pout {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shrug(self, ctx, user: discord.Member):
        """Shrugs a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "shrug") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** shrugs {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sleep(self, ctx, user: discord.Member):
        """Sleep zzzz!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "sleep") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** sleep {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def stare(self, ctx, user: discord.Member):
        """Stares at a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "stare") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** stares at {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def think(self, ctx, user: discord.Member):
        """Thinking!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "think") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** think {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def thumbsup(self, ctx, user: discord.Member):
        """thumbsup!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "thumbsup") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** thumbsup {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wink(self, ctx, user: discord.Member):
        """Winks at a user!"""
        async with aiohttp.ClientSession() as session:
            async with session.get(NEKOS + "wink") as response:
                if response.status != 200:
                    return await ctx.send(
                        "Something went wrong while trying to contact API."
                    )
                if response.status == 502:
                    return await ctx.send("Api is currently down, try again later.")
                url = await response.json()
                emb = discord.Embed(
                    colour=await ctx.embed_color(),
                    description=f"**{ctx.author.mention}** winks {f'**{str(user.mention)}**' if user else 'themselves'}!",
                )
            emb.colour = await ctx.embed_color()
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
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting.")
