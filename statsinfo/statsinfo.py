import discord
import logging
import pkg_resources

from redbot.core import commands

from redbot.core.utils.chat_formatting import box

try:
    from tabulate import tabulate
except Exception as e:
    raise CogLoadError(
        f"Can't load because: {e}\n"
        "Please install tabulate by using "
        "`pip install tabulate` "
        "in your console. "
        "Restart your bot if you still get this error."
    )

# CogLoadError handler from
# https://github.com/fixator10/Fixator10-Cogs/blob/9972aa58dea3a5a1a0758bca62cb8a08a7a51cc6/leveler/def_imgen_utils.py#L11-L30

log = logging.getLogger("red.maxcogs.statsinfo")


class Statsinfo(commands.Cog):
    """This will show all current stats total from all guilds your bot is in."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.0.2"
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
    async def statsinfo(self, ctx: commands.Context):
        """Shows botstats for [botname].

        This will show all current stats total from all guilds your bot is in."""
        total_users = len(set(self.bot.get_all_members()))
        total_bots = len([m for m in self.bot.get_all_members() if m.bot])
        total_guilds = len(ctx.bot.guilds)
        total_channels = sum(len(s.channels) for s in ctx.bot.guilds)
        total_voice_channels = sum(len(s.voice_channels) for s in ctx.bot.guilds)
        total_stage_channels = sum(len(s.stage_channels) for s in ctx.bot.guilds)
        total_text_channels = sum(len(s.text_channels) for s in ctx.bot.guilds)
        total_categories = sum(len(s.categories) for s in ctx.bot.guilds)
        total_emojis = sum(len(s.emojis) for s in ctx.bot.guilds)
        total_roles = sum(len(s.roles) for s in ctx.bot.guilds)
        total_boosters = sum(len(s.premium_subscribers) for s in ctx.bot.guilds)
        total_shards = ctx.bot.shard_count

        shards = ("Shards") if self.bot.shard_count > 1 else ("Shard")
        # based on https://github.com/PredaaA/predacogs/blob/b02363b9123e3c55b9577c2192b550a8489ebca8/martools/marttools.py#L499

        latency = round(self.bot.latency * 1000)

        version = pkg_resources.get_distribution("discord.py").version

        # So had to do it in this way for store channels since the above was not possible.
        # and thanks to copilot for helping of this part below xD
        store_channel = 0
        for guilds, guild in enumerate(self.bot.guilds):
            for channel in guild.channels:
                if isinstance(channel, discord.StoreChannel):
                    store_channel += 1

        em = discord.Embed(
            title="Bot Stats",
            colour=await ctx.embed_color(),
        )
        em.add_field(
            name=f"{self.bot.user.name}'s total stats:",
            value=box(
                tabulate(
                    [
                        ["Ping:", latency],
                        [f"{shards}", total_shards],
                        ["Servers:", total_guilds],
                        ["Users:", total_users],
                        ["Bots:", total_bots],
                        ["Channels:", total_channels],
                        ["Voice Channels:", total_voice_channels],
                        ["Stage Channels:", total_stage_channels],
                        ["Text Channels:", total_text_channels],
                        ["Store Channels:", store_channel],
                        ["Categories:", total_categories],
                        ["Emojis:", total_emojis],
                        ["Roles:", total_roles],
                        ["Boosters:", total_boosters],
                    ]
                ),
                lang="yml",
            ),
        )
        em.set_footer(text=f"Discord.py v{version}")
        em.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        try:
            await ctx.send(embed=em)
        except discord.HTTPException as e:
            await ctx.send(
                "Something went wrong while trying to post. Check console for details."
            )
            log.error(e)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def statsversion(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)
