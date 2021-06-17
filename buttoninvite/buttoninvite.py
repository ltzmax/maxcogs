import discord
from dislash.interactions import ActionRow, Button, ButtonStyle
from redbot.core import Config, commands


class ButtonInvite(commands.Cog):
    """Sends the invite for [botname] with button.

    To set permission level use `[p]inviteset perms`, and you can change description by using `[p]invmsg`."""

    __author__ = "MAX"
    __version__ = "0.4.1 alpha"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("invite")
        self.config = Config.get_conf(self, identifier=12435434124)
        self.def_msg = "Thank you for inviting {}\n\n**Click on the button!**"
        self.config.register_global(msg=self.def_msg, emoji=None)

    @commands.is_owner()
    @commands.group()
    async def invmsg(self, ctx):
        """Settings to change invite message shown in the embed."""

    @invmsg.command()
    async def add(self, ctx, *, message):
        """Change the invite message shown in the embed."""
        await self.config.msg.set(message)
        if await ctx.embed_requested():
            emb = discord.Embed(
                description=("Sucessfully set the invite message"),
                color=await ctx.embed_color(),
            )
            await ctx.reply(embed=emb, mention_author=False)
        else:
            await ctx.send("Sucessfully set the invite message")

    @invmsg.command()
    async def reset(self, ctx):
        """Reset the invite message back to default."""
        await self.config.msg.set(self.def_msg)
        if await ctx.embed_requested():
            emb = discord.Embed(
                description=("Reset the invite message back to default"),
                color=await ctx.embed_color(),
            )
            await ctx.reply(embed=emb, mention_author=False)
        else:
            await ctx.send("Reset the invite message back to default")

    @commands.is_owner()
    @commands.group()
    async def invemoji(self, ctx):
        """Settings to change invite emoji shown in the embed."""

    @invemoji.command(name="add")
    async def add_emoji(self, ctx, emoji):
        """Change the invite emoji shown in the button."""
        await self.config.emoji.set(emoji)
        if await ctx.embed_requested():
            emb = discord.Embed(
                description=(f"Sucessfully set the emoji to {emoji}"),
                color=await ctx.embed_color(),
            )
            await ctx.reply(embed=emb, mention_author=False)
        else:
            await ctx.send(f"Sucessfully set the emoji to {emoji}")

    @invemoji.command(name="reset")
    async def reset_emoji(self, ctx):
        """Remove the emoji in the button."""
        await self.config.emoji.set(None)
        if await ctx.embed_requested():
            emb = discord.Embed(
                description=("Removed the emoji"),
                color=await ctx.embed_color(),
            )
            await ctx.reply(embed=emb, mention_author=False)
        else:
            await ctx.send("Removed the emoji")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def invite(self, ctx):
        """Shows [botname]'s invite link.

        To set permission level use `[p]inviteset perms`.
        You can change description by using `[p]invmsg`."""

        servers = str(len(self.bot.guilds))
        name = ctx.bot.user.name
        settings = await self.config.all()
        embed = discord.Embed(
            title=f"{name}",
            color=await ctx.embed_color(),
            url=(ctx.bot.user.avatar_url_as(static_format="png")),
            description=(settings["msg"]).format(name),
        )
        embed.set_thumbnail(url=ctx.bot.user.avatar_url_as(static_format="png"))
        embed.set_footer(text=f"Server count: {servers}")
        await ctx.send(
            embed=embed,
            components=[
                ActionRow(
                    Button(
                        style=ButtonStyle.link,
                        emoji=settings["emoji"],
                        label="Invite me",
                        url=(await self.bot.get_cog("Core")._invite_url()),
                    ),
                )
            ],
        )
