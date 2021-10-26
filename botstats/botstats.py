import datetime

import discord
import pkg_resources
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_number
from tabulate import tabulate


class BotStats(commands.Cog):
    """Shows some stats for [botname]."""

    __author__ = "MAX"
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """Statistics for [botname]."""
        total_members = 0
        total_unique = len(self.bot.users)
        text = 0
        voice = 0
        stage_channels = 0
        category_channel = 0
        store_channel = 0
        for guilds, guild in enumerate(self.bot.guilds):
            total_members += guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1
                elif isinstance(channel, discord.StageChannel):
                    stage_channels += 1
                elif isinstance(channel, discord.CategoryChannel):
                    category_channel += 1
                elif isinstance(channel, discord.StoreChannel):
                    store_channel += 1

        # The stuff above here is from here
        # https://github.com/Rapptz/RoboDanny/blob/1fb95d76d1b7685e2e2ff950e11cddfc96efbfec/cogs/stats.py#L236

        version = pkg_resources.get_distribution("discord.py").version
        servers = str(len(self.bot.guilds))
        emb = discord.Embed(
            title=f"botstats for {self.bot.user.name}:", color=await ctx.embed_color()
        )
        emb.add_field(
            name="Users:",
            value=box(
                tabulate(
                    [
                        ["Servers", servers],
                        ["Total Users", total_members],
                        ["Unique Users", total_unique],
                    ],
                    tablefmt="plain",
                ),
                "ARM",
            ),
        )
        emb.add_field(
            name="Channels:",
            value=box(
                tabulate(
                    [
                        ["Text Channels", text],
                        ["Voice Channels", voice],
                        ["Stage Channels", stage_channels],
                    ],
                    tablefmt="plain",
                ),
                "ARM",
            ),
        )
        emb.add_field(
            name="\N{ZERO WIDTH SPACE}", value="\N{ZERO WIDTH SPACE}", inline=False
        )
        emb.add_field(
            name="Total channels:",
            value=box(
                tabulate(
                    [
                        ["Total Channels", text + voice + stage_channels],
                        ["Total Categories", category_channel],
                        ["Total Store Channels", store_channel],
                    ],
                    tablefmt="plain",
                ),
                "ARM",
            ),
        )

        emb.set_footer(text=f"Discord.py v{version}")
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)

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
