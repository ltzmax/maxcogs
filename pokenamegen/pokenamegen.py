import discord
import logging
from random import choice
from redbot.core import commands, Config

from .constants import POKEMON

log = logging.getLogger("red.maxcogs.pokenamegen")


class PokeNameGen(commands.Cog):
    """Get random pokémon names."""

    __author__ = "MAX"
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            mentions=True,
        )

    # I cannot tell you how bored i was when i made this cog...
    # It's mostly just meant for people who like pokémon for the most.
    # Pokémon names are from the global national dex: https://pokemondb.net/pokedex/national.

    @commands.is_owner()
    @commands.group()
    async def pset(self, ctx):
        """Settings to change mentions to true or false."""

    @pset.command(name="set", usage="<true_or_false>")
    async def pset_set(self, ctx: commands.Context, mentions: bool):
        """Change the mention to true or false.

        Default is true.

        **Example:**
        - `[p]qset set false` this will disable the mentions on replies.

        **Arguments:**
        - `<true_or_false>` is where you set `true` or `false`."""

        await self.config.mentions.set(mentions)
        mentions = "true" if mentions else "false"
        await ctx.send("Mentions is now {}.".format(mentions))

    @commands.command(aliases=["pokeng"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pokenamegen(self, ctx):
        """Get random pokémon names."""
        emb = discord.Embed(
            title="Here's a random pokémon name:",
            description=choice(POKEMON),
            colour=await ctx.embed_color(),
        )
        try:
            await ctx.reply(embed=emb, mention_author=await self.config.mentions())
        except discord.HTTPException:
            await ctx.send(embed=emb)
            log.info(
                "Command 'pokenamegen' failed to use reply due to message was unknown."
            )
