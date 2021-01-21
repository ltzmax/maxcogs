# Credits: https://github.com/AlexFlipnote/discord_bot.py/blob/762ec7c741fb9380767adf7619601f259470ebe6/cogs/discord.py#L43
import discord

from redbot.core import commands


class ModCheck(commands.Cog):
    """Check which mod is online."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def mods(self, ctx):
        """Check which mods are online on current guild."""
        guild = ctx.message.guild
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "<:online:749221433552404581>Online:"},
            "idle": {"users": [], "emoji": "<:idle:749221433095356417>Idle:"},
            "dnd": {"users": [], "emoji": "<:do_not_disturb:749221432772395140>Dnd:"},
            "offline": {"users": [], "emoji": "<:offline:749221433049088082>Offline:"},
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
            color=0x30ba8f,
            description=(f"Mods online in guild **{ctx.guild.name}**\n\n{message}"),
        )
        embed.set_footer(text="Server ID: " + str(guild.id))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def admins(self, ctx):
        """Same as mods, but this only checks for admins online."""
        guild = ctx.message.guild
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "<:online:749221433552404581>Online:"},
            "idle": {"users": [], "emoji": "<:idle:749221433095356417>Idle:"},
            "dnd": {"users": [], "emoji": "<:do_not_disturb:749221432772395140>Dnd:"},
            "offline": {"users": [], "emoji": "<:offline:749221433049088082>Offline:"},
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
            color=0x30ba8f,
            description=(f"Admins online in guild **{ctx.guild.name}**\n\n{message}"),
        )
        embed.set_footer(text="Server ID: " + str(guild.id))
        await ctx.send(embed=embed)
