from redbot.core import commands, Config
import aiohttp
import json
import discord
import logging

log = logging.getLogger("red.maxcogs.inspirational")


class Inspirational(commands.Cog):
    """Inspirational Quotes.

    Powered by zenquotes API."""

    __author__ = "MAX"
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            mentions=True,
        )
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.is_owner()
    @commands.group()
    async def qset(self, ctx):
        """Settings to change mentions to true or false."""

    @qset.command(name="set", usage="<true_or_false>")
    async def qset_set(self, ctx: commands.Context, mentions: bool):
        """Change the mention to true or false.

        **Example:**
        - `[p]qset set false` this will disable the mentions on replies.

        **Arguments:**
        - `<true_or_false>` is where you add false or true."""

        await self.config.mentions.set(mentions)
        mentions = "true" if mentions else "false"
        await ctx.send("Mentions is now {}.".format(mentions))

    @commands.command(aliases=["quote"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def quotes(self, ctx):
        """Get inspirational quotes."""
        async with self.session.get("https://zenquotes.io/api/random") as resp:
            if resp.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
            json = await resp.json(content_type=None)
            quotes = json[0]["q"] + "\n- " + json[0]["a"]
            emb = discord.Embed(
                description=f"{quotes}",
                colour=await ctx.embed_color(),
            )
            emb.set_footer(text="Powered by Zenquotes API.")
            try:
                await ctx.reply(embed=emb, mention_author=await self.config.mentions())
            except discord.HTTPException:
                await ctx.send(embed=emb)
                log.info(
                    "Command 'quote' failed to use reply due to message was unknown."
                )
                # use info because this is not really error. :P
