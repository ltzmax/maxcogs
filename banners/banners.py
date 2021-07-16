import discord
from redbot.core import commands


class Banners(commands.Cog):
    """Show's guild's server banner."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.2.0"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.guild_only()
    @commands.command(aliases=["banners"])
    @commands.bot_has_permissions(embed_links=True)
    async def banner(self, ctx: commands.Context):
        """Shows guilds banner image.

        - It's called `splash` but for most it's known as `server banner`."""
        guild = ctx.guild
        if not guild.splash:
            return await ctx.send("No banner image found in this guild.")
        em = discord.Embed(title=f"{ctx.guild.name}'s banner image:")
        em.colour = await ctx.embed_color()
        if guild.splash:
            em.set_image(url=guild.splash_url_as(format="png"))
        await ctx.send(embed=em)
