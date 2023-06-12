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
import discord
import logging
import asyncio

from redbot.core import commands, Config, app_commands
from redbot.core.utils.chat_formatting import box

log = logging.getLogger("red.maxcogs.autopublisher")

DISCORD_INFO = "<https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server>"

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

    __version__ = "0.1.10"
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
    async def on_message_without_command(self, message: discord.Message):
        """Publish message to news channel."""
        guild = message.guild
        if message.guild is None:
            return
        if not await self.config.guild(guild).toggle():
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if (
            not message.guild.me.guild_permissions.manage_messages
            or not message.guild.me.guild_permissions.view_channel
        ):
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                log.info(
                    "AutoPublisher has been disabled in %s (%s) due to missing permissions.", guild.name, guild.id
                )
            return
        if "NEWS" not in guild.features:
            if await self.config.guild(message.guild).toggle():
                await self.config.guild(message.guild).toggle.set(False)
                log.info(
                    "AutoPublisher has been disabled in %s (%s) due to missing News Channel feature.", guild.name, guild.id
                )
            return
        if not message.channel.is_news():
            return
        if message.channel.is_news():
            try:
                await asyncio.sleep(3)  # delay it 3 seconds to publish.
                await asyncio.wait_for(message.publish(), timeout=60)
            except (
                discord.HTTPException,
                discord.Forbidden,
                asyncio.TimeoutError,
            ) as e:
                log.error(
                    "Failed to publish message in %s (%s)\n%s", guild.name, guild.id, e
                )

    @commands.hybrid_group(aliases=["aph", "autopub"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def autopublisher(self, ctx):
        """Manage AutoPublisher setting."""

    @autopublisher.command()
    @app_commands.describe(toggle="Enable or disable AutoPublisher.")
    async def toggle(self, ctx: commands.Context, toggle: bool):
        """Toggle AutoPublisher enable or disable.

        > This cog have a 3 secoud delay on each messages you post in a news channel to be sent to the channels users are following.

        - It's disabled by default.
            - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.

        **Note:**
        - This cog requires News Channel. If you don't have it, you can't use this cog.
            - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)
        """
        guild = ctx.guild
        if "NEWS" not in guild.features:
            return await ctx.send(
                "This server doesn't have News Channel feature to use this cog.\nLearn more here on how to enable:\n{DISCORD_INFO}".format(
                    DISCORD_INFO=DISCORD_INFO
                ),
                ephemeral=True,
            )
        if (
            not guild.me.guild_permissions.manage_messages
            or not guild.me.guild_permissions.view_channel
        ):
            return await ctx.send(
                "I don't have `manage_messages` or `view_channel` permission to use this cog.",
                ephemeral=True,
            )
        await self.config.guild(ctx.guild).toggle.set(toggle)
        if toggle:
            await ctx.send("AutoPublisher is now enabled.")
        else:
            await ctx.send("AutoPublisher is now disabled.")

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(aliases=["view"], with_app_command=False)
    async def settings(self, ctx: commands.Context):
        """Show AutoPublisher setting."""
        config = await self.config.guild(ctx.guild).toggle()
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=f"AutoPublisher is currently **{'enabled' if config else 'disabled'}**.",
            color=0xE91E63,
        )
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(with_app_command=False)
    async def version(self, ctx):
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)
