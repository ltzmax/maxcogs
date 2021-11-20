import aiohttp
import discord
from redbot.core import commands
import nekosbest
import logging

try:
    from dislash.application_commands._modifications.old import send_with_components
    from dislash.interactions import ActionRow, Button, ButtonStyle
except Exception as e:
    raise CogLoadError(
        f"Can't load because: {e}\n"
        "Please install dislash by using "
        "`pip install dislash.py==1.4.9` "
        "in your console. "
        "Restart your bot if you still get this error."
    )

# CogLoadError handler from
# https://github.com/fixator10/Fixator10-Cogs/blob/9972aa58dea3a5a1a0758bca62cb8a08a7a51cc6/leveler/def_imgen_utils.py#L11-L30

log = logging.getLogger("red.maxcogs.nekos")

NEKOS_API = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845322551347.png?size=96"


class Nekos(commands.Cog):
    """Sending nekos images from nekos.best."""

    def __init__(self, bot):
        self.bot = bot
        self.session = nekosbest.Client()
        # monkeypatch dislash.py to not break slashtags by phen.
        if not hasattr(commands.Context, "sendi"):
            commands.Context.sendi = send_with_components

    __version__ = "0.1.5"
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
        row = ActionRow(
            Button(
                style=ButtonStyle.link,
                label="Author",
                url=neko.artist_href,
            ),
            Button(
                style=ButtonStyle.link,
                label="Source",
                url=neko.source_url,
            ),
        )
        try:
            await ctx.sendi(embed=emb, components=[row])
        except discord.HTTPException as e:
            await ctx.send(
                "Something went wrong while trying to post. Check console for details."
            )
            log.error(e)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def nekosversion(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)
