import discord
from redbot.core import Config, commands
from dislash.interactions import ActionRow, Button, ButtonStyle


class AdvancedInvite(commands.Cog):
    """Shows [botname]'s invite link."""

    __author__ = "MAX"
    __version__ = "0.0.4"

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
            emoji=None,
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
        """Settings to change invite description message.

        To set invite permission, use `[p]inviteset perms <level>`.
        You can generate permission level here: https://discordapi.com/permissions.html."""

    @settings.command(name="set", aliases=["add", "message"], usage="<message>")
    async def settings_add(self, ctx, *, message: str):
        """Change the invite description message.

        Leave it blank will reset the message back to default."""
        if len(message) > 2000:
            return await ctx.send("Your message must be 2000 or fewer in length.")
        if message:
            await self.config.invite_default.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set the description message to `{message}`."
            )

    @settings.command(name="emoji", usage="<emoji>")
    async def settings_emoji(self, ctx, *, emoji: str = None):
        """Change emoji from smiley to something else.

        Leave it blank will reset the emoji back to default.

        You need to set an vaild emoji, either way your `[p]invite` will not work.

        Example:
        - `[p]invite emoji <emoji>`.

        `<emoji>` is the emoji you want to set as an emoji on the button.
        """

        if not emoji:
            await self.config.emoji.set(emoji)
            await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        else:
            await self.config.emoji.set(emoji)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your emoji to {emoji}."
            )

    @settings.command(name="reset", aliases=["remove"])
    async def settings_reset(self, ctx):
        """Reset description message to default"""

        await self.config.invite_default.clear()
        await ctx.send("\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default.")

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
        embed.set_footer(
            text="This bot is made possible with support of Red-DiscordBot."
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        try:
            await ctx.send(
                embed=embed,
                components=[
                    ActionRow(
                        Button(
                            style=ButtonStyle.link,
                            emoji=(await self.config.emoji()),
                            label="Invite me",
                            url=invite,
                        )
                    )
                ],
            )
        except discord.HTTPException:
            await ctx.send(
                f"Something went wrong while trying to post invite.\nLooks like you might have set an invaild emoji see: `{ctx.clean_prefix}help settings emoji`\nIf you didn't set any emoji, please report this to MAX#1000."
            )


def setup(bot):
    advi = AdvancedInvite(bot)
    global invite
    invite = bot.remove_command("invite")
    bot.add_cog(advi)
