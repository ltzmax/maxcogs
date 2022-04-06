from inspect import getsource, getcomments
from textwrap import indent
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class SourceCode(commands.Cog):
    """Get source code of a command."""

    __version__ = "0.2.0"
    __author__ = "MAX, Fixator10"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(aliases=["source", "showcode"])
    async def sourcecode(self, ctx, *, command: str):
        """
        Get the source code of a command
        """
        command = self.bot.get_command(command)
        if command is None:
            return await ctx.send("That command was not found.")
        try:
            source_code = getsource(command.callback)
            if comments := getcomments(command.callback):
                firstline = source_code.split("\n", 1)[0]
                indent_size = len(firstline) - len(firstline.lstrip(" "))
                source_code = indent(comments, " " * indent_size) + source_code
        except OSError:
            return await ctx.send(
                "That doesn't seem to be a valid command, try any other command."
            )
        temp_pages = []
        pages = []
        for page in pagify(source_code, escape_mass_mentions=True, page_length=1977):
            temp_pages.append(box(page, "py"))
        max_i = len(temp_pages)
        i = 1
        for page in temp_pages:
            pages.append(f"`Page {i}/{max_i}`\n" + page)
            i += 1
        await menu(ctx, pages, controls=DEFAULT_CONTROLS)
