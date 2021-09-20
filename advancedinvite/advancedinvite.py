import discord
from redbot.core import Config, commands
from dislash.interactions import ActionRow, Button, ButtonStyle


class AdvancedInvite(commands.Cog):
    """Shows [botname]'s invite link."""

    __author__ = "MAX"
    __version__ = "0.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            invite_default="Thank you for inviting {}.",
            invite_footer="This bot is made possible with support of Red-DiscordBot.",
        )

    def cog_unload(self):
        global invite
        if invite:
            try:
                self.bot.remove_command("invite")
            except:
                pass
            self.bot.add_command(invite)

    @commands.is_owner()
    @commands.group()
    async def settings(self, ctx):
        """Settings to change invite description and footer message.

        To set invite permission, use `[p]inviteset perms <level>`.
        You can generate permission level here: https://discordapi.com/permissions.html."""

    @settings.command(name="add", aliases=["set", "description"], usage="<message>")
    async def settings_add(self, ctx, *, message=None):
        """Change the invite description message.

        Leave it blank will reset the message back to default."""
        if message:
            await self.config.invite_default.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set the description message to `{message}`."
            )
        else:
            await self.config.invite_default.clear()
            await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )

    @settings.command(name="footer", usage="<message>")
    async def settings_footer(self, ctx, *, message=None):
        """Change the footer message.

        Leave it blank will reset the message back to default."""
        if message:
            await self.config.invite_footer.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set the footer message to `{message}`."
            )
        else:
            await self.config.invite_footer.clear()
            await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def invite(self, ctx):
        """Shows [botname]'s invite link."""

        name = ctx.bot.user.name

        invite = await self.bot.get_cog("Core")._invite_url()
        embed = discord.Embed(
            title=f"{name}",
            colour=await ctx.embed_color(),
            url=ctx.bot.user.avatar_url_as(static_format="png"),
            description=(await self.config.invite_default()).format(name),
        )
        embed.set_footer(text=await self.config.invite_footer())
        embed.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        await ctx.send(
            embed=embed,
            components=[
                ActionRow(
                    Button(
                        style=ButtonStyle.link,
                        label="Invite me",
                        url=invite,
                    )
                )
            ],
        )


def setup(bot):
    advi = AdvancedInvite(bot)
    global invite
    invite = bot.remove_command("invite")
    bot.add_cog(advi)
