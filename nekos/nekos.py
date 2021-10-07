import aiohttp
import discord
from redbot.core import commands
import nekosbest

NEKOS_API = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845322551347.png?size=96"


class Nekos(commands.Cog):
    """Sending nekos images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = nekosbest.Client()

    __version__ = "0.1.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command(aliases=["nekos"])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def neko(self, ctx):
        """Send a random neko image."""
        neko = await self.session.get_image("nekos")
        emb = discord.Embed(
            title="Here's a pic of neko",
            description=f"Artist: [{neko.artist_name}]({neko.artist_href})\nSource: {neko.source_url}",
        )
        emb.colour = await ctx.embed_color()
        emb.set_footer(
            text="Powered by nekos.best",
            icon_url=ICON,
        )
        if neko.url:
            emb.set_image(url=neko.url)
        else:
            emb.description = "I was unable to get image, can you try again?"
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException:
            await ctx.send("Something went wrong while posting an image.")
