import discord
import datetime
import humanize
import time
import pkg_resources

from tabulate import tabulate
from lavalink import node
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import box



async def parse_llnode_stat(stats: node.NodeStats, stat_name: str):
    stat = getattr(stats, stat_name)
    if isinstance(stat, int) and stat_name.startswith("memory_"):
        stat = humanize.naturalsize(stat, binary=True)
    if stat_name == "uptime":
        stat = chat.humanize_timedelta(seconds=stat / 1000)
    if "load" in stat_name:
        stat = f"{round(stat*100, 2)} %"
    return stat


class Utility(commands.Cog):
    """Utility commands to use."""

    __version__ = "2.1.0"
    __author__ = ["MAX", "Fixator10", "AlexFlipnote"]

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """Shows some stats for [botname]."""
        total_members = 0
        total_unique = len(self.bot.users)

        text = 0
        voice = 0
        for guilds, guild in enumerate(self.bot.guilds):
            total_members += guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        version = pkg_resources.get_distribution("discord.py").version
        servers = str(len(self.bot.guilds))
        users = str(len(self.bot.users))
        emb = discord.Embed(
            title=f"Botstats for {self.bot.user.name}:", color=await ctx.embed_color()
        )
        emb.add_field(
            name="Users:",
            value=(
                f"{servers} servers\n{total_members} total members\n{total_unique} unique members"
            ),
            inline=True,
        )
        emb.add_field(
            name="Channels:",
            value=(f"{text + voice} total\n{text} text\n{voice} voice"),
            inline=True,
        )
        emb.set_footer(text=f"Discord.py v{version}")
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)

    @commands.command(aliases=["cmdstats"])
    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    async def cmdstat(self, ctx):
        """Shows how many commands available on [botname]
        
        This only shows from cogs loaded."""
        commands = len(set(self.bot.walk_commands()))

        emb = discord.Embed(
            title=f"cmdstat on {self.bot.user.name}", color=await ctx.embed_color()
        )
        emb.add_field(name="Commands available:", value=commands, inline=True)
        await ctx.send(embed=emb)

    @commands.command()
    @commands.is_owner()
    async def llnodestats(self, ctx):
        """Lavalink nodestats.
        
        This require audio loaded before you using this command."""
        nodes = node.get_nodes_stats()
        if not nodes:
            await ctx.send(chat.info("No nodes found. This require audio loaded and wait for lavalink to connect for this to work."))
            return
        stats = [stat for stat in dir(nodes[0]) if not stat.startswith("_")]
        tabs = [f"Node {i}/{len(nodes)}\n"
                + chat.box(
                    tabulate(
                        [
                            (
                                stat.replace("_", " ").title(),
                                await parse_llnode_stat(n, stat),
                            )
                            for stat in stats
                        ],
                    ),
                    "ml",
                ) for i, n in enumerate(nodes, start=1)]
        await menu(ctx, tabs, DEFAULT_CONTROLS)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def mods(self, ctx):
        """Check which mods are online in current guild.
        
        When users needs a mod for something they can check whos online currently."""
        # All credits to AlexFlipnote.
        guild = ctx.message.guild
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "\N{LARGE GREEN CIRCLE}Online:"},
            "idle": {"users": [], "emoji": "\N{LARGE YELLOW CIRCLE}Idle:"},
            "dnd": {"users": [], "emoji": "\N{LARGE RED CIRCLE}Dnd:"},
            "offline": {"users": [], "emoji": "\N{MEDIUM WHITE CIRCLE}Offline:"},
        }

        for user in ctx.guild.members:
            user_perm = ctx.channel.permissions_for(user)
            if user_perm.kick_members or user_perm.ban_members:
                if not user.bot:
                    all_status[str(user.status)]["users"].append(f"\n**{user}**")

        for g in all_status:
            if all_status[g]["users"]:
                message += (
                    f"{all_status[g]['emoji']} {', '.join(all_status[g]['users'])}\n\n"
                )

        embed = discord.Embed(
            description=(f"Mods in guild **{ctx.guild.name}**\n\n{message}"),
        )
        embed.colour = await ctx.embed_color()
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send(
                "Error: Seems like you have alot of mods. This has reached it's max length so this won't display your mods in this guild." # yee this could've been better messaged.
            ) # TODO: Add menus. when there is time for it.

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def admins(self, ctx):
        """Check which admins are online in current guild.
        
        This is same as mods but this only checks for admins."""
        # All credits to AlexFlipnote.
        guild = ctx.message.guild
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "\N{LARGE GREEN CIRCLE}Online:"},
            "idle": {"users": [], "emoji": "\N{LARGE YELLOW CIRCLE}Idle:"},
            "dnd": {"users": [], "emoji": "\N{LARGE RED CIRCLE}Dnd:"},
            "offline": {"users": [], "emoji": "\N{MEDIUM WHITE CIRCLE}Offline:"},
        }

        for user in ctx.guild.members:
            user_perm = ctx.channel.permissions_for(user)
            if user_perm.administrator:
                if not user.bot:
                    all_status[str(user.status)]["users"].append(f"\n**{user}**")

        for g in all_status:
            if all_status[g]["users"]:
                message += (
                    f"{all_status[g]['emoji']} {', '.join(all_status[g]['users'])}\n\n"
                )

        embed = discord.Embed(
            description=(f"Admins in guild **{ctx.guild.name}**\n\n{message}"),
        )
        embed.colour = await ctx.embed_color()
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send(
                "Error: Seems like you have alot of admins. This has reached it's max length so this won't display your admins in this guild." # yee this could've been better messaged.
            ) # TODO: Add menus. when there is time for it.

    @commands.command(hidden=True) # hidden to avoide being used for spam which it's not made for.
    @commands.guild_only()
    @commands.cooldown(1, 500, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def commands(self, ctx):
        """This will show where commands are for [botname]."""
        if ctx.channel.permissions_for(ctx.me).embed_links:
            embed = discord.Embed(
                description=f"Use `{ctx.clean_prefix}help` to see all my commands.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"> Use `{ctx.clean_prefix}help` to see all my commands.")
