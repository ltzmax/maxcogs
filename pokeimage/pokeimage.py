import discord
import aiohttp
import logging
from io import BytesIO
from redbot.core import commands

log = logging.getLogger("red.maxcogs.pokeimage")

ICON = "https://cdn.discordapp.com/emojis/725574447029026887.png?size=96"


class PokeImage(commands.Cog):
    """Get random pokémon images.

    From https://api.itzmax.me"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    __version__ = "0.0.3"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def pokeimg(self, ctx):
        """Get random pokémon image."""
        await ctx.trigger_typing()
        async with self.session.get("https://api.itzmax.me/api/pokemon") as resp:
            data = await resp.read()
            if resp.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
        file = BytesIO(data)
        file.name = "thumbnail.png"
        embed = discord.Embed(title="Here's a random pokémon image:")
        if file:
            embed.set_image(url="attachment://thumbnail.png")
        else:
            embed.description = "I was unable to get image."
        embed.set_footer(text="Powered by api.itzmax.me", icon_url=ICON)
        embed.colour = await ctx.embed_color()
        try:
            await ctx.send(embed=embed, file=discord.File(file))
        except discord.HTTPException as e:
            await ctx.send(
                "Something went wrong while trying to post. Check console for more info."
            )
            log.error(f"Command 'pokeimg' failed: {e}")
