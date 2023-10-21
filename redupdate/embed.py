import discord
from maxcogs_utils.restart import Buttons
from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box


async def redupdate(self, ctx: commands.Context):
    embed = discord.Embed(
        description="Successfully updated {}.".format(self.bot.user.name),
        color=await ctx.embed_color(),
    )
    embed.set_footer(text="Restart required to apply changes!")
    view = Buttons(ctx)
    view.message = await ctx.send(embed=embed, view=view)


async def failedupdate(self, ctx: commands.Context):
    msg = (
        "You need to have Shell from JackCogs loaded and installed to use this command."
    )
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


async def discordpyupdate(self, ctx: commands.Context):
    embed = discord.Embed(
        title="Discord.py Updated",
        description="Successfully updated {}.".format(self.bot.user.name),
        color=await ctx.embed_color(),
    )
    embed.set_footer(text="Restart required to apply changes!")
    view = Buttons(ctx)
    view.message = await ctx.send(embed=embed, view=view)

async def redupdateinfo(self, ctx: commands.Context):
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


async def redupdateset_url(self, ctx: commands.Context, url: str):
    # Cause i'm super lazy and don't want to make a regex for this.
    # usually forks that are private uses `git+ssh://git@` instead of `https://`.
    if not url.startswith("git+ssh://git@github.com") and not url.startswith(
        "git+https://github.com"
    ):
        return await ctx.send("This is not a valid url for your fork.")
    if not url.endswith("#egg=Red-DiscordBot"):
        return await ctx.send("This is not a valid url for your fork.")
    data = await self.config.redupdate_url()
    if data == url:
        return await ctx.send("This url is already set.")
    await self.config.redupdate_url.set(url)
    await ctx.send(f"Successfully set the url to {url}.")
