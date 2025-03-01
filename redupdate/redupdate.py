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

import logging
from typing import Any, Final, Literal, Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

from .view import RestartButton, URLModal

log = logging.getLogger("red.maxcogs.redupdate")


async def redupdate(self, ctx: commands.Context):
    embed = discord.Embed(
        description="Successfully updated {}.".format(self.bot.user.name),
        color=await ctx.embed_color(),
    )
    embed.set_footer(text="Restart required to apply changes!")
    view = RestartButton(ctx, self.bot)
    message = await ctx.send(embed=embed, view=view)
    view.message = message


async def failedupdate(self, ctx: commands.Context):
    msg = "You need to have Shell from JackCogs loaded and installed to use this command."
    embed = discord.Embed(
        title="Error in redupdate",
        description=msg,
        color=await ctx.embed_color(),
    )
    view = discord.ui.View()
    style = discord.ButtonStyle.gray
    jack = discord.ui.Button(
        style=style,
        label="JackCogs repo",
        url="https://github.com/jack1142/JackCogs",
    )
    view.add_item(item=jack)
    return await ctx.send(embed=embed, view=view)


class RedUpdate(commands.Cog):
    """Update [botname] to latest dev/stable changes."""

    __author__: Final[str] = "MAX, kuro"
    __version__: Final[str] = "1.8.0"
    __docs__: Final[str] = "https://docs.maxapp.tv/redupdate.html"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0x1A108201, force_registration=True)
        default_global = {
            "redupdate_url": [],
        }
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.is_owner()
    @commands.group(aliases=["redset"])
    async def redupdateset(self, ctx: commands.Context):
        """Setting commands for redupdate cog."""

    @redupdateset.command(name="url")
    async def redupdateset_url(self, ctx: commands.Context):
        """Set your custom fork url of red.

        Has to be vaild link such as `git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot` else it will not work.
        """
        view = URLModal(ctx, self.config)
        view.message = await ctx.send(
            f"Please enter your custom fork URL\n-# If you're unsure of what url, see `{ctx.prefix}redset whaturl`.",
            view=view,
        )

    @redupdateset.command(name="whatlink", aliases=["whaturl"])
    async def redupdateset_whatlink(self, ctx: commands.Context) -> None:
        """Show what a valid link looks like."""
        embed = discord.Embed(
            title="What a valid link looks like",
            color=await ctx.embed_color(),
            description="This is what a valid link should look like for your fork or if you are using red's main development url.",
        )

        public_fork_example = (
            "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        )
        private_fork_example = (
            "git+ssh://git@github.com/yourusername/yourrepo@YOUR_BRANCH_HERE#egg=Red-DiscordBot"
        )

        embed.add_field(
            name="Public Forks:",
            value="For public forks, you need to use the `https` link.",
            inline=False,
        )
        embed.add_field(
            name="Example Link:",
            value=box(public_fork_example, lang="yaml"),
        )
        embed.add_field(
            name="Private Forks:",
            value="For private forks, you need to use the `ssh` link instead of `https`.",
            inline=False,
        )
        embed.add_field(
            name="Example Link:",
            value=box(private_fork_example, lang="yaml"),
        )
        embed.add_field(
            name="Link should end with:",
            value=box("#egg=Red-DiscordBot", lang="cs"),
            inline=False,
        )
        embed.add_field(
            name="How does it work?",
            value="This link is used to update the bot to your fork instead of red's main repo and is used to update to latest changes from your fork.",
            inline=False,
        )
        embed.set_footer(
            text="Make sure you have a valid link before setting it using `redset url`."
        )
        await ctx.send(embed=embed)

    @redupdateset.command(name="reseturl")
    async def redupdateset_reseturl(self, ctx: commands.Context):
        """Reset the url to default."""
        await self.config.redupdate_url.clear()
        await ctx.tick()

    @redupdateset.command(name="settings")
    async def redupdateset_settings(self, ctx: commands.Context):
        """Show the url for redupdate cog."""
        url = await self.config.redupdate_url()
        try:
            await ctx.author.send(
                f"Your current fork url is:\n`{url}`",
            )
            await ctx.tick()
        except discord.Forbidden:
            await ctx.send(
                "You have disabled DMs from this server, please enable it to view your settings.",
            )

    @redupdateset.command(name="version")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdateset_version(self, ctx: commands.Context):
        """Shows information about the cog."""
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
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)

    @commands.is_owner()
    @commands.command(usage="[version]")
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def updatered(
        self,
        ctx: commands.Context,
        version: Optional[Literal["dev"]],
    ):
        """
        Update [botname] to latest changes.

        It will update to latest stable changes by default unless you specify `dev` as version.

        Arguments:
        - `[version]`: `dev` to update to latest dev changes. `stable` by default already.
        """
        package = (
            "Red-DiscordBot"
            if not version
            else "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        )
        confirm_view = ConfirmView(ctx.author, disable_buttons=True)
        if not version:
            await self._update(ctx, package)
            return

        embed = discord.Embed(
            title="Red Update Information",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="⚠️Warning⚠️",
            value="This will update to latest dev changes and may include breaking changes that can break cogs that does not support latest dev changes. Are you sure you want to continue?",
            inline=False,
        )
        embed.add_field(
            name="Note:",
            value="If you are not sure what you are doing, it is recommended to update to latest stable changes instead of dev changes. Use ``{prefix}updatered`` to update to latest stable changes without specifying ``dev``.".format(
                prefix=ctx.clean_prefix
            ),
            inline=False,
        )
        embed.set_footer(
            text="Be sure you want to update to latest dev changes before continuing!"
        )
        confirm_view.message = await ctx.send(embed=embed, view=confirm_view)
        await confirm_view.wait()
        if confirm_view.result:
            await self._update(ctx, package)
        else:
            await ctx.send("You have cancelled the update to latest dev changes.")

    async def _update(self, ctx: commands.Context, package: str):
        shell = self.bot.get_cog("Shell")
        if not shell:
            await failedupdate(self, ctx)
            return
        await shell._shell_command(
            ctx,
            f"pip install -U --force-reinstall {package}",
            send_message_on_success=False,
        )
        await redupdate(self, ctx)

    @commands.is_owner()
    @commands.command(aliases=["updatefork"])
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def forkupdate(self, ctx: commands.Context):
        """Update [botname] to your fork.

        This will update to your fork and not to red's main repo. Make sure you have set the url using `redset url` before using this command.

        Note: If you do not have a fork, you can use `updatered` to update to latest stable changes.
        """
        fork_url = await self.config.redupdate_url()
        if not fork_url:
            return await ctx.send(
                "You need to set your fork url using `{prefix}redset url` before using this command.".format(
                    prefix=ctx.clean_prefix
                )
            )
        if (
            fork_url
            == "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        ):
            return await ctx.send(
                "You cannot use this command until you've set your fork. Please remember to set your fork url using `{prefix}redset url`.".format(
                    prefix=ctx.clean_prefix
                )
            )
        try:
            await ctx.bot.get_cog("Shell")._shell_command(
                ctx, f"pip install -U --force-reinstall {fork_url}", send_message_on_success=False
            )
        except AttributeError:
            return await failedupdate(self, ctx)
        await redupdate(self, ctx)
