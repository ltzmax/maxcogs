import logging

import discord
from redbot.core import Config, commands
from redbot.core.errors import CogLoadError

try:
    from dislash.application_commands._modifications.old import send_with_components
    from dislash.interactions import ActionRow, Button, ButtonStyle
except Exception as e:
    raise CogLoadError(
        f"Can't load because: {e}\n"
        "Please install dislash by using "
        "`pip install dislash.py==1.4.9` "
        "in your console. "
        "Restart your bot if you still get this error."
    )

# CogLoadError handler from
# https://github.com/fixator10/Fixator10-Cogs/blob/9972aa58dea3a5a1a0758bca62cb8a08a7a51cc6/leveler/def_imgen_utils.py#L11-L30

log = logging.getLogger("red.maxcogs.advancedinvite")


class AdvancedInvite(commands.Cog):
    """Shows [botname]'s invite link."""

    __author__ = "MAX"
    __version__ = "0.0.19 beta"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        # monkeypatch dislash.py to not break slashtags by phen.
        if not hasattr(commands.Context, "sendi"):
            commands.Context.sendi = send_with_components
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            invite_default="Thank you for inviting {}\n\n**Invite:**\n[Click here]({})",
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
    async def advancedinvite(self, ctx):
        """Settings to change invite description message.

        To set invite permission, use `[p]inviteset perms <level>`.
        You can generate permission level here: https://discordapi.com/permissions.html."""

    @advancedinvite.command(name="set", aliases=["add"], usage="<message>")
    async def advancedinvite_set(self, ctx, *, message: str):
        """Change the description message for your invite.

        Leave it blank will reset the message back to default.
        You cannot have longer than 1000 on `<message>`.

        **Example:**
        - `[p]advancedinvite set Hello invite me pls`.

        **Arguments:**
        - `<message>` is where you set your message.
        """
        if len(message) > 1000:
            return await ctx.reply(
                "Your message must be 1000 or fewer in length.", mention_author=False
            )
        if message:
            await self.config.invite_default.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set the description message to `{message}`."
            )

    @advancedinvite.command(name="reset", aliases=["remove"])
    async def advancedinvite_reset(self, ctx):
        """Reset description message back to default."""

        await self.config.invite_default.clear()
        await ctx.send("\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default.")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def invite(self, ctx):
        """Shows [botname]'s invite link."""

        author = ctx.author

        invite = await self.bot.get_cog("Core")._invite_url()

        if author.is_on_mobile():
            # This will only send if user is on mobile.
            return await ctx.reply(
                f"Here's the bot invite for {self.bot.user.name}:\n{invite}",
                mention_author=False,
            )

        name = ctx.bot.user.name

        embed = discord.Embed(
            title=f"{name}",
            colour=await ctx.embed_color(),
            url=ctx.bot.user.avatar_url_as(static_format="png"),
            description=(await self.config.invite_default()).format(name, invite),
        )
        embed.set_footer(
            # Removing or editing this footer will not be given any support for this cog.
            text="This bot is made possible with support of Red-DiscordBot."
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        row = ActionRow(
            Button(
                style=ButtonStyle.link,
                label="Invite me",
                url=invite,
            ),
        )
        try:
            await ctx.sendi(embed=embed, components=[row])
        except discord.HTTPException as e:
            await ctx.send("Something went wrong. Check your console for details.")
            log.error(f"Command 'invite' failed: {e}")


def setup(bot):
    advi = AdvancedInvite(bot)
    global invite
    invite = bot.remove_command("invite")
    bot.add_cog(advi)
