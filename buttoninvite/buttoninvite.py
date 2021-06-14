import discord
from dislash.interactions import ActionRow, Button, ButtonStyle
from redbot.core import commands

old_invite = None


class ButtonInvite(commands.Cog):
    """Sends the invite for [botname] with button.

    To set permission level use `[p]inviteset perms`."""

    __author__ = "MAX"
    __version__ = "0.6.0a"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("invite") # cause of corelogic.

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def invite(self, ctx):
        """Shows [botname]'s invite link.

        To set permission level use `[p]inviteset perms`."""

        servers = str(len(self.bot.guilds))
        name = ctx.bot.user.name

        embed = discord.Embed(
            title=f"{name}",
            colour=discord.Colour(0x5865F2),
            url=(ctx.bot.user.avatar_url_as(static_format="png")),
            description=f"Thank you for inviting {name}\n\n**Click on the button!**",
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        embed.set_footer(text=f"Server count: {servers}")
        await ctx.send(
            embed=embed,
            components=[
                ActionRow(
                    Button(
                        style=ButtonStyle.link,
                        label="Invite me",
                        url=(await self.bot.get_cog("Core")._invite_url()),
                    ),
                )
            ],
        )
