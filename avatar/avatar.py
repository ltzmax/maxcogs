import discord
from redbot.core import commands


class Avatar(commands.Cog):
    """Shows users current avatar or your own."""

    def __init__(self, bot):
        self.bot = bot
        self.session = nekosbest.Client()

    __version__ = "0.0.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command(aliases=["av"])
    @commands.bot_has_permissions(embed_links=True)
    async def avatar(self, ctx: commands.Context, *, user: discord.Member = None):
        """Get a user's avatar."""
        if user is None:
            user = ctx.author

        if user.is_avatar_animated():
            avatar.url = avatar.with_static_format("gif", size=4096)
        else:
            avatar.url = avatar.with_static_format("png", size=4096)

        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=await ctx.embed_color(),
        )
        embed.set_image(url=avatar.url)
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        item = discord.ui.Button(
            style=style,
            label="Avatar",
            url=str(user.avatar.with_static_format("png", size=4096)),
        )
        view.add_item(item=item)
        await ctx.send(embed=emb, view=view)
