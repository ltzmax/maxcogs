import discord
from redbot.core import commands
from typing import Any, Final
from redbot.core.utils.chat_formatting import box

class RedUpdate(commands.Cog):
    """Update [botname] to latest dev changes."""

    __author__: Final[str] = "MAX, kuro"
    __version__: Final[str] = "1.0.0"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/redupdate/README.md"

    def __init__(self, bot):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return


    @commands.is_owner()
    @commands.command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdate(self, ctx: commands.Context):
        """Update [botname] to latest dev changes."""
        package = "git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot"
        shell = self.bot.get_cog("Shell")
        try:
            await shell._shell_command(
                ctx,
                f"pip install -U --force-reinstall {package}",
                send_message_on_success=False,
            )
        except AttributeError:
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
        embed = discord.Embed(
            description="Successfully updated {}.".format(self.bot.user.name),
            color=await ctx.embed_color(),
        )
        embed.set_footer(text="Restart required to apply changes!")
        await ctx.send(embed=embed, silent=True)

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def redupdateinfo(self, ctx: commands.Context):
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
        await ctx.send(embed=embed)
