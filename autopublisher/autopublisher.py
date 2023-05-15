import discord
import logging
import asyncio

from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box

log = logging.getLogger("red.maxcogs.autopublisher")


class AutoPublisher(commands.Cog):
    """Automatically push news channel messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=15786223, force_registration=True
        )
        default_guild = {
            "toggle": False,
        }
        self.config.register_guild(**default_guild)

    __version__ = "0.1.0"
    __author__ = "MAX"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/autopublisher/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.guild is None:
            return
        if not await self.config.guild(message.guild).toggle():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if not message.guild.me.guild_permissions.manage_messages:
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                log.error(
                    f"AutoPublisher has been disabled in {message.guild.name} ({message.guild.id}) due to missing permissions."
                )
            return
        if getattr(message.channel, "is_news", None) is None:
            return
        if message.channel.is_news():
            try:
                # let's not publish right away.
                # wait for 4 seconds to prevent rate limit?
                await asyncio.sleep(4)
                await message.publish()
            except (discord.HTTPException, discord.Forbidden):
                log.error(
                    f"Failed to publish message {message.id} in {message.guild.name} ({message.guild.id}) #{message.channel.name} ({message.channel.id})"
                )

    @commands.group(aliases=["aph"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def autopublisher(self, ctx):
        """Manage AutoPublisher setting."""

    @autopublisher.command()
    async def toggle(self, ctx: commands.Context, toggle: bool):
        """Toggle AutoPublisher enable or disable.

        It's disabled by default.

        Note: This cog requires News Channel. If you don't have it, you can't use this cog.
        Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server).
        """
        guild = ctx.guild
        if guild.features is None or "NEWS" not in guild.features:
            return await ctx.send(
                "This server doesn't have News Channel feature to use this cog."
            )
        await self.config.guild(ctx.guild).toggle.set(toggle)
        if toggle:
            await ctx.send("AutoPublisher is now enabled.")
        else:
            await ctx.send("AutoPublisher is now disabled.")

    @autopublisher.command(aliases=["view"])
    async def settings(self, ctx: commands.Context):
        """Show AutoPublisher setting."""
        config = await self.config.guild(ctx.guild).toggle()
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=f"AutoPublisher is currently **{'enabled' if config else 'disabled'}**.",
            color=0xE91E63,
        )
        await ctx.send(embed=embed)

    @autopublisher.command()
    async def version(self, ctx):
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        await ctx.send(
            box(f"{'Author':<10}: {author}\n{'Version':<10}: {version}", lang="yaml")
        )
