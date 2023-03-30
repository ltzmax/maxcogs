import discord

from redbot.core import Config, commands, app_commands

SPOILER_REGEX = r"||(.+?)||"


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__ = "MAX"
    __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild = {"enabled": False, "ignored_channels": [], "ignored_roles": []}
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx):
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if not message.guild:
            return
        if message.author.bot:
            return
        if (
            message.channel.id
            in await self.config.guild(message.guild).ignored_channels()
        ):
            return
        if any(
            [
                role.id in await self.config.guild(message.guild).ignored_roles()
                for role in message.author.roles
            ]
        ):
            return
        if self.bot.is_automod_immune(author):
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if any([word in message.content for word in SPOILER_REGEX]):
            await message.delete()

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx):
        """No spoiler in this server."""

    @nospoiler.command()
    async def toggle(self, ctx):
        """Toggle the spoiler filter."""
        if permission := ctx.channel.permissions_for(ctx.author).manage_messages:
            if not permission:
                return await ctx.send(
                    "I don't have permission to `manage_messages` to toggle spoiler filter.\ni need this permission to be able to remove spoiler messages."
                )
        if await self.config.guild(ctx.guild).enabled():
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Spoiler filter disabled.")
        else:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("Spoiler filter enabled.")

    @nospoiler.command()
    @app_commands.describe(channel="The channel to ignore or remove from ignore list.")
    async def ignorechannel(self, ctx, channel: discord.TextChannel):
        """Add or remove Ignore a channel."""
        if permission := channel.permissions_for(ctx.author).manage_messages:
            if not permission:
                return await ctx.send(
                    "I don't have permission to `manage_messages` to remove spoiler there."
                )
        if channel.id in await self.config.guild(ctx.guild).ignored_channels():
            await self.config.guild(ctx.guild).ignored_channels.set(
                [
                    c
                    for c in await self.config.guild(ctx.guild).ignored_channels()
                    if c != channel.id
                ]
            )
            await ctx.send(f"{channel.mention} is no longer ignored.")
        else:
            await self.config.guild(ctx.guild).ignored_channels.set(
                await self.config.guild(ctx.guild).ignored_channels() + [channel.id]
            )
            await ctx.send(f"{channel.mention} is now ignored.")

    @nospoiler.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx):
        """Show the settings."""
        config = await self.config.guild(ctx.guild).all()
        enabled = config["enabled"]
        ignored_channels = ", ".join([f"<#{c}>" for c in config["ignored_channels"]])
        if not ignored_channels:
            ignored_channels = "None"
        embed = discord.Embed(title="NoSpoiler settings", color=await ctx.embed_color())
        embed.add_field(name="Enabled", value=enabled)
        embed.add_field(name="Ignored channels", value=ignored_channels)
        await ctx.send(embed=embed)
