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

from typing import Any, Final, Literal, Optional

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

from .view import RestartButton, URLModal

log = getLogger("red.maxcogs.redupdate")


class RedUpdate(commands.Cog):
    """Update [botname] to latest dev/stable changes."""

    __author__: Final[str] = "MAX, kuro"
    __version__: Final[str] = "1.10.0"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x1A108201, force_registration=True)
        self.config.register_global(redupdate_url=[])

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def _send_update_success(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"Successfully updated {self.bot.user.name}.",
            color=await ctx.embed_color(),
        )
        embed.set_footer(text="Restart required to apply changes!")
        view = RestartButton(ctx, self.bot)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    async def _send_update_failure(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Error in redupdate",
            description="You need to have Shell from JackCogs loaded and installed to use this command.",
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.gray,
                label="JackCogs repo",
                url="https://github.com/jack1142/JackCogs",
            )
        )
        await ctx.send(embed=embed, view=view)

    async def _perform_update(self, ctx: commands.Context, package: str):
        shell = self.bot.get_cog("Shell")
        if not shell:
            await self._send_update_failure(ctx)
            return False
        await shell._shell_command(
            ctx, f"pip install -U --force-reinstall {package}", send_message_on_success=False
        )
        await self._send_update_success(ctx)
        return True

    @commands.is_owner()
    @commands.group(aliases=["redset"])
    async def redupdateset(self, ctx: commands.Context):
        """Setting commands for redupdate cog."""

    @redupdateset.command(name="url")
    async def redupdateset_url(self, ctx: commands.Context):
        """Set your custom fork url of red."""
        view = URLModal(ctx, self.config)
        view.message = await ctx.send(
            f"Please enter your custom fork URL\n-# If you're unsure of what url, see `{ctx.prefix}redset whatlink`.",
            view=view,
        )

    @redupdateset.command(name="whatlink", aliases=["whaturl"])
    async def redupdateset_whatlink(self, ctx: commands.Context):
        """Show what a valid link looks like."""
        embed = discord.Embed(
            title="What a valid link looks like",
            color=await ctx.embed_color(),
            description="This is what a valid link should look like for your fork or if you are using red's main development url.",
        )

        examples = {
            "Public Forks": (
                "For public forks, you need to use the `https` link.",
                "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot",
            ),
            "Private Forks": (
                "For private forks, you need to use the `ssh` link instead of `https`.",
                "git+ssh://git@github.com/yourusername/yourrepo@YOUR_BRANCH_HERE#egg=Red-DiscordBot",
            ),
        }

        for name, (desc, link) in examples.items():
            embed.add_field(name=name, value=desc, inline=False)
            embed.add_field(name="Example Link:", value=box(link, lang="yaml"), inline=False)

        embed.add_field(
            name="Link should end with:", value=box("#egg=Red-DiscordBot", lang="cs"), inline=False
        )
        embed.add_field(
            name="How does it work?",
            value="This link is used to update the bot to your fork instead of red's main repo.",
            inline=False,
        )
        embed.set_footer(text=f"Use `{ctx.prefix}redset url` to set your custom URL.")
        await ctx.send(embed=embed)

    @redupdateset.command(name="reseturl")
    async def redupdateset_reseturl(self, ctx: commands.Context):
        """Reset the url to default."""
        await self.config.redupdate_url.clear()
        await ctx.tick()

    @redupdateset.command(name="settings")
    async def redupdateset_settings(self, ctx: commands.Context):
        """Show the url for redupdate cog."""
        url = await self.config.redupdate_url() or "Not set"
        try:
            await ctx.author.send(f"Your current fork url is:\n`{url}`")
            await ctx.tick()
        except discord.Forbidden:
            await ctx.send("Please enable DMs from this server to view your settings.")

    @commands.is_owner()
    @commands.command(usage="[version]")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def updatered(self, ctx: commands.Context, version: Optional[Literal["dev"]]):
        """
        Update [botname] to latest changes.

        Arguments:
        - `[version]`: `dev` to update to latest dev changes. Stable by default.
        """
        packages = {
            None: "Red-DiscordBot",
            "dev": "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot",
        }
        package = packages[version]

        if not version:
            await self._perform_update(ctx, package)
            return

        embed = discord.Embed(title="Red Update Information", color=await ctx.embed_color())
        embed.add_field(
            name="⚠️Warning⚠️",
            value="This will update to latest dev changes which may include breaking changes that may not work with some cogs. Do you wanna continue?",
            inline=False,
        )
        embed.add_field(
            name="Note:",
            value=f"Use `{ctx.clean_prefix}updatered` for stable updates instead.",
            inline=False,
        )
        embed.set_footer(text="Confirm to update to latest dev changes.")
        confirm_view = ConfirmView(ctx.author, disable_buttons=True)
        confirm_view.message = await ctx.send(embed=embed, view=confirm_view)
        await confirm_view.wait()

        if confirm_view.result:
            await self._perform_update(ctx, package)
        else:
            await ctx.send("Update to dev changes cancelled.")

    @commands.is_owner()
    @commands.command(aliases=["updatefork"])
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def forkupdate(self, ctx: commands.Context):
        """Update [botname] to your fork.

        This will update to your fork and not to red's main repo. Make sure you have set the url using `redset url` before using this command.

        Note: If you do not have a fork, you can use `updatered` to update to latest stable changes.
        """
        fork_url = await self.config.redupdate_url()
        prefix = ctx.clean_prefix

        if not fork_url:
            return await ctx.send(f"Set your fork URL using `{prefix}redset url` first.")

        if (
            fork_url
            == "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        ):
            return await ctx.send(f"Set a custom fork URL using `{prefix}redset url` first.")

        await self._perform_update(ctx, fork_url)
