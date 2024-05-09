import discord
import logging

from typing import Optional, Union, Any, Final
from redbot.core import commands, Config, app_commands

log = logging.getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    This only works with the default role.
    """

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Lockdown.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "log_channel": None,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return


    async def log_channel(
        self,
        guild: discord.Guild,
        event: str,
        reason: Optional[str] = None,
    ) -> None:
        log_channel = await self.config.guild(guild).log_channel()
        if not log_channel:
            return
        log_channel = guild.get_channel(log_channel)
        if not log_channel:
            return
        if (
            not log_channel.permissions_for(guild.me).send_messages
            or not log_channel.permissions_for(guild.me).embed_links
        ):
            log.warning(
                f"I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            return
        embed = discord.Embed(
            title=f"{event}",
            description=f"{reason or 'No reason provided.'}",
            color=0xFF0000,
        )
        await log_channel.send(embed=embed)

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lockdownset(self, ctx: commands.Context):
        """Lockdown settings commands."""

    @lockdownset.command()
    async def logchannel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ):
        """Set the channel for logging lockdowns."""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel.clear()
            return await ctx.send("Log channel cleared.")
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}.")

    @lockdownset.command()
    async def settings(self, ctx: commands.Context):
        """Get the current log channel."""
        all = await self.config.guild(ctx.guild).all()
        log_channel = all["log_channel"]
        await ctx.send(
            f"Log channel: {ctx.guild.get_channel(log_channel).mention if log_channel else 'None'}"
        )

    @commands.guild_only()
    @commands.bot_can_manage_channel()
    @commands.hybrid_command(aliases=["lockdown"])
    @app_commands.describe(channel="The channel to lockdown.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Lock a channel down.

        This will remove the permission `send_messages` from the default role in the channel.

        __Parameters__
        --------------
        channel: Optional[discord.TextChannel]
            The channel to lock down. If no channel is provided, the current channel will be locked down.
        """
        if ctx.channel.overwrites_for(ctx.guild.default_role).send_messages is False:
            return await ctx.send("❌ Channel is already locked.")
        channel = ctx.channel
        overwrite = discord.PermissionOverwrite(send_messages=False)
        if channel is None:
            await ctx.send("🔒 Channel locked.")
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await self.log_channel(
                guild=ctx.guild,
                event="Channel Locked",
                reason=f"{channel.mention} was locked down by {ctx.author.mention}.",
            )
        else:
            await ctx.send(f"🔒 {channel.mention} locked.")
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await self.log_channel(
                guild=ctx.guild,
                event="Channel Locked",
                reason=f"{channel.mention} was locked down by {ctx.author.mention}.",
            )

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.bot_can_manage_channel()
    @app_commands.describe(channel="The channel to unlock.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ):
        """Unlock a channel.

        This will allow the default role to send messages in the channel.

        __Parameters__
        --------------
        channel: Optional[discord.TextChannel]
            The channel to unlock. If no channel is provided, the current channel will be unlocked.
        """
        if ctx.channel.overwrites_for(ctx.guild.default_role).send_messages is None:
            return await ctx.send("❌ Channel is not locked.")
        channel = ctx.channel
        overwrites = discord.PermissionOverwrite(send_messages=None)
        if channel is None:
            await ctx.send("🔓 Channel unlocked.")
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await self.log_channel(
                guild=ctx.guild,
                event="Channel Unlocked",
                reason=f"{channel.mention} was unlocked by {ctx.author.mention}.",
            )
        else:
            await ctx.send(f"🔓 {channel.mention} unlocked.")
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await self.log_channel(
                guild=ctx.guild,
                event="Channel Unlocked",
                reason=f"{channel.mention} was unlocked by {ctx.author.mention}.",
            )
