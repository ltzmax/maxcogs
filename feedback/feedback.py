import discord
import asyncio
from discord import app_commands
from redbot.core import Config, commands
from redbot.core.utils.predicates import MessagePredicate


class Feedback(commands.Cog):
    """Send feedback."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild = {
            "toggle": False,
            "channel": None,
        }
        self.config.register_guild(**default_guild)

    __version__ = "0.1.0"
    __author__ = "MAX"
    __docs__ = "https://readdocs.voltrabot.com/docs/Cogs/feedback"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def feedbackset(self, ctx):
        """Manage feedback settings."""

    @feedbackset.command()
    async def toggle(self, ctx: commands.Context, *, toggle: bool = None):
        """Toggle feedbacks on/off."""
        if toggle is None:
            toggle = not await self.config.guild(ctx.guild).toggle()
        await self.config.guild(ctx.guild).toggle.set(toggle)
        if toggle:
            await ctx.send("Feedbacks are now enabled.")
        else:
            await ctx.send("Feedbacks are now disabled.")

    @feedbackset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set feedback channel."""
        if channel is None:
            channel = ctx.channel
        else:
            if (
                not channel.permissions_for(ctx.me).send_messages
                or not channel.permissions_for(ctx.me).view_channel
            ):
                await ctx.send(
                    "I do not have permission to `send_messages` or `view_channel` in {channel.mention}. "
                    "Please enable and try again.".format(channel=channel)
                )
                return
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Feedback channel set to {channel.mention}")

    @feedbackset.command()
    async def reset(self, ctx: commands.Context):
        """Reset feedback settings."""
        await ctx.send(
            "Are you sure you want to reset feedback settings?\nType `yes` to confirm, Type `no` to cancel."
        )
        try:
            pred = MessagePredicate.yes_or_no(ctx, user=ctx.author)
            msg = await ctx.bot.wait_for("message", check=pred, timeout=30)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out.")
        if not pred.result:
            return await ctx.send("Cancelled and won't reset.")
        else:
            await self.config.guild(ctx.guild).clear()
            await ctx.send("Feedback settings reset.")

    @feedbackset.command(aliases=["settings"])
    async def showsettings(self, ctx: commands.Context):
        """Show feedback settings."""
        toggle = await self.config.guild(ctx.guild).toggle()
        channel = self.bot.get_channel(await self.config.guild(ctx.guild).channel())
        if channel is None:
            channel = "Not set"
        else:
            channel = channel.mention
        await ctx.send(f"Feedbacks are {toggle}.\nFeedback channel is {channel}.")

    @commands.hybrid_command()
    @app_commands.describe(feedback=("The message you want to send as feedback"))
    async def feedback(self, ctx: commands.Context, *, feedback: str):
        """Send a feedback to the server's feedback channel."""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send(
                "Feedbacks are disabled.\nAsk an admin to enable them."
            )
        channel = self.bot.get_channel(await self.config.guild(ctx.guild).channel())
        if channel is None:
            return await ctx.send(
                "Feedback channel not found.\nAsk an admin to set it."
            )
        await channel.send(f"**{ctx.author}** ({ctx.author.id})\n{feedback}")
        await ctx.send("Feedback sent.")
