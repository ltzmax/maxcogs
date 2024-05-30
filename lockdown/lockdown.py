import discord
import logging

from typing import Optional, Union, Any, Final
from redbot.core import commands, Config, app_commands

log = logging.getLogger("red.maxcogs.lockdown")


class Lockdown(commands.Cog):
    """
    Let moderators lockdown a channel to prevent messages from being sent.
    """

    __version__: Final[str] = "1.0.5"
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
            description=reason,
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
    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command(aliases=["lockdown"])
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're locking this channel",
        channel="The channel to lockdown.",
        role="The role to lockdown.",
    )
    async def lock(
        self,
        ctx: commands.Context,
        reason: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        role: Optional[discord.Role] = None,
    ):
        """Lock a channel down.

        This will remove the permission `send_messages` from the provided role in the channel. If no role is provided, the default role will be used.

        __Parameters__
        --------------
        ``reason``: Optional[str]
            - The reason why you're locking this channel.
        ``channel``: Optional[discord.TextChannel]
            - The channel to lock down. If no channel is provided, the current channel will be locked down.
        ``role``: Optional[discord.Role]
            - The role to remove the `send_messages` permission from. If no role is provided, the default role will be used.
        """
        if role is None:
            role = ctx.guild.default_role

        # let's not lock the channel roles higher than the bot's top role
        # Since it doesn't have the permission to do so.
        bot_role = ctx.guild.get_member(ctx.me.id).top_role
        if role >= bot_role:
            return await ctx.send(
                "I can't lock a channel for a role higher than or equal to my top role."
            )
        # Check if the role is higher than the author's top role.
        top_role = ctx.guild.get_member(ctx.author.id).top_role
        if role >= top_role:
            return await ctx.send(
                "You can't lock a channel for a role higher than or equal to your top role."
            )

        if channel is None:
            channel = ctx.channel

        # It's currently not possible to do this.
        if isinstance(
            channel, Union[discord.VoiceChannel, discord.ForumChannel, discord.Thread]
        ):
            return await ctx.send("I can't lockdown a voice, forum or thread channels.")

        overwrites = channel.overwrites_for(role)
        if overwrites is None:
            overwrites = discord.PermissionOverwrite()
        if overwrites.send_messages is False:
            return await ctx.send(
                f"❌ {'Role' if role != ctx.guild.default_role else 'Channel'} is already locked."
            )

        overwrites.send_messages = False
        embed = discord.Embed(
            title="Channel Locked",
            description=f"🔒 Locked channel {channel.mention} for {role.mention if role != ctx.guild.default_role else 'everyone'}",
            color=0xFF0000,
        )
        if reason:
            embed.add_field(name="Reason:", value=reason or "No reason provided.")
        embed.set_footer(text=f"Locked by {ctx.author}")
        await ctx.send(embed=embed)
        await channel.set_permissions(role, overwrite=overwrites)
        await self.log_channel(
            guild=ctx.guild,
            event="Channel Locked",
            reason=f"{channel.mention} was locked by {ctx.author.mention}"
            + (f" for Reason: {reason}" if reason else ""),
        )

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.mod_or_can_manage_channel()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    @app_commands.describe(
        reason="The reason why you're unlocking this channel",
        channel="The channel to unlock.",
        role="The role to unlock.",
    )
    async def unlock(
        self,
        ctx: commands.Context,
        reason: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        role: Optional[discord.Role] = None,
    ):
        """Unlock a channel.

        This will unlock the provided role in the channel. If no role is provided, the default role will be used.

        __Parameters__
        --------------
        ``reason``: Optional[str]
            - The reason why you're unlocking this channel.
        ``channel``: Optional[discord.TextChannel]
            - The channel to unlock. If no channel is provided, the current channel will be unlocked.
        ``role``: Optional[discord.Role]
            - The role to remove the `send_messages` permission from. If no role is provided, the default role will be used.
        """
        if role is None:
            role = ctx.guild.default_role

        # let's not lock the channel roles higher than the bot's top role
        # Since it doesn't have the permission to do so.
        bot_role = ctx.guild.get_member(ctx.me.id).top_role
        if role >= bot_role:
            return await ctx.send(
                "I can't unlock a channel for a role higher than or equal to my top role."
            )
        # Check if the role is higher than the author's top role.
        top_role = ctx.guild.get_member(ctx.author.id).top_role
        if role >= top_role:
            return await ctx.send(
                "You can't unlock a channel for a role higher than or equal to your top role."
            )

        if channel is None:
            channel = ctx.channel

        # It's currently not possible to do this.
        if isinstance(
            channel, Union[discord.VoiceChannel, discord.ForumChannel, discord.Thread]
        ):
            return await ctx.send("I can't lockdown a voice, forum or thread channels.")

        overwrites = channel.overwrites_for(role)
        if overwrites is None:
            overwrites = discord.PermissionOverwrite()
        if overwrites.send_messages is None:
            return await ctx.send(
                f"❌ {'Role' if role != ctx.guild.default_role else 'Channel'} is already unlocked."
            )

        overwrites.send_messages = None
        embed = discord.Embed(
            title="Channel Unlocked",
            description=f"🔓 Unlocked channel {channel.mention} for {role.mention if role != ctx.guild.default_role else 'everyone'}",
            color=0x00FF00,
        )
        if reason:
            embed.add_field(name="Reason:", value=reason or "No reason provided.")
        embed.set_footer(text=f"Unlocked by {ctx.author}")
        await ctx.send(embed=embed)
        await channel.set_permissions(role, overwrite=overwrites)
        await self.log_channel(
            guild=ctx.guild,
            event="Channel Unlocked",
            reason=f"{channel.mention} was unlocked by {ctx.author.mention}"
            + (f" for Reason: {reason}" if reason else ""),
        )
