"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio

import discord
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
            "title": "Feedback",
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
    async def channel(
        self, ctx: commands.Context, *, channel: discord.TextChannel = None
    ):
        """Set the feedback channel."""
        if channel:
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
            await ctx.send(f"Feedback channel set to {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).channel.set(None)
            await ctx.send("Feedback channel reset.")

    @feedbackset.command()
    async def title(self, ctx: commands.Context, *, title: str = None):
        """Set the feedback title."""
        # To allow limited characters in title, this is based on the code from JojoCogs
        # https://github.com/Just-Jojo/JojoCogs/blob/4b8c34c47ce05e77a0def45f972f3efa23ac9b6f/advancedinvite/advanced_invite.py#L248-L254
        if not title:
            await self.config.guild(ctx.guild).title.set(None)
            return await ctx.send("Feedback title reset.")
        if len(title) > 256:
            return await ctx.send("Title cannot be longer than 256 characters.")

        await self.config.guild(ctx.guild).title.set(title)
        await ctx.send(f"Feedback title set to `{title}`.")

    @feedbackset.command(aliases=["clear"])
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

    @commands.bot_has_permissions(embed_links=True)
    @feedbackset.command(aliases=["settings", "view"])
    async def showsettings(self, ctx: commands.Context):
        """Show feedback settings."""
        config = await self.config.guild(ctx.guild).all()
        if config["channel"] is None:
            channel = "Not set"
        else:
            channel = self.bot.get_channel(config["channel"]).mention
        if config["toggle"]:
            toggle = "Enabled"
        else:
            toggle = "Disabled"

        if config["title"] is None:
            title = "Feedback"
        else:
            title = config["title"]

        embed = discord.Embed(
            title="Feedback settings",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="Feedback is",
            value=f"{toggle}",
            inline=False,
        )
        embed.add_field(
            name="Feedback channel is",
            value=f"{channel}",
            inline=False,
        )
        embed.add_field(
            name="Current title is",
            value=f"{title}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @feedbackset.command()
    async def version(self, ctx: commands.Context):
        """Shows the cog version."""
        message = f"Author: {self.__author__}\nVersion: {self.__version__}"
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Cog Version:",
                description=message,
                colour=await ctx.embed_colour(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"**Cog Version:**\n{message}")

    @commands.hybrid_command()
    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    @app_commands.describe(feedback=("The message you want to send as feedback"))
    async def feedback(self, ctx: commands.Context, *, feedback: str):
        """Send a feedback to the server's feedback channel."""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send(
                "Feedbacks are disabled.\nAsk an admin to enable them."
            )
        channel = self.bot.get_channel(await self.config.guild(ctx.guild).channel())
        if channel is None:
            return await ctx.send("Feedback channel not set.\nAsk an admin to set one.")
        title = await self.config.guild(ctx.guild).title()
        # If using for suggestions and wants up and down reactions
        # You can use smartreact from flapjack or other 3rd party cogs that allows this.
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=title,
                description=f"{feedback}",
                color=await ctx.embed_color(),
            )
            embed.set_footer(text=f"Author: {ctx.author}")
            await channel.send(embed=embed)
        else:
            await channel.send(f"**{ctx.author}** ({ctx.author.id})\n{feedback}")
        await ctx.send("Done.")
