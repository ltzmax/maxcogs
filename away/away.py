# This cog was orginially made by kato & dia ♡#0666.
# This repo/cog had no license, 
# but permission to continue the cog was granted.
# https://github.com/TheDiscordHistorian/historian-cogs

import logging

import discord
from redbot.core import Config, commands

log = logging.getLogger("red.maxcogs.away")


class Away(commands.Cog):
    """Set yourself as away."""

    __version__ = "0.2.0"
    __author__ = "dia ♡#0666, max & TheDiscordHistorian (kato#0666)"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return (
            f"{pre_processed}\n**Cog Version:** {self.__version__}\n**Author:** {self.__author__}"
        )

    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.config = Config.get_conf(
            self, identifier=0x390440438, force_registration=True
        )
        default_guild = {
            "role": None,
            "delete_after": None,
            "delete": False,
        }
        default_member = {
            "away": False,
            "message": None,
            "nick": False,
            "autoback": False,
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    async def initialize(self):
        self.cache = await self.config.all_guilds()

    async def update_guild_cache(self, guild: discord.Guild):
        self.cache[guild.id] = await self.config.guild(guild).all()

    def _format_message(self, user: discord.Member, message: str):
        embed = discord.Embed(
            description=message,
            color=user.color,
        )
        embed.set_author(name=str(user), icon_url=self._format_avatar(user))
        embed.set_footer(text=f"{user.display_name} is currently away.")
        return embed

    def _format_avatar(self, user: discord.Member) -> str:
        return user.display_avatar.url

    @commands.Cog.listener("on_message_without_command")
    async def _away_trigger(self, message: discord.Message) -> None:

        if message.guild is None:
            return
        if message.author.bot:
            return
        guild = message.guild
        if not message.channel.permissions_for(guild.me).send_messages:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if not await self.bot.ignored_channel_or_guild(message):
            return
        if not await self.bot.allowed_by_whitelist_blacklist(message.author):
            return
        if not message.mentions:
            return
        for mention in message.mentions:
            data = await self.config.member(mention).all()
            if data["away"] is False:
                continue
            if data["message"] is None:
                continue
            g_data = self.cache.get(guild.id)
            if g_data != None:
                if g_data["delete_after"] is not None and g_data["delete"] is True:
                    await message.channel.send(
                        embed=self._format_message(mention, data["message"]),
                        delete_after=g_data["delete_after"],
                        reference=message.to_reference(fail_if_not_exists=False),
                        allowed_mentions=discord.AllowedMentions(users=False, roles=False),
                        mention_author=False,
                    )
                else:
                    await message.channel.send(
                        embed=self._format_message(mention, data["message"]),
                        reference=message.to_reference(fail_if_not_exists=False),
                        allowed_mentions=discord.AllowedMentions(users=False, roles=False),
                        mention_author=False,
                    )
            else:
                await message.channel.send(
                    embed=self._format_message(mention, data["message"]),
                    reference=message.to_reference(fail_if_not_exists=False),
                    allowed_mentions=discord.AllowedMentions(users=False, roles=False),
                    mention_author=False,
                )

    @commands.Cog.listener("on_message_without_command")
    async def _auto_back_moment(self, message: discord.Message) -> None:

        if message.guild is None:
            return
        if message.author.bot:
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if not await self.bot.ignored_channel_or_guild(message):
            return
        if not await self.bot.allowed_by_whitelist_blacklist(message.author):
            return
        data = await self.config.member(message.author).all()
        if data["away"] is False:
            return
        if data["autoback"] is False:
            return
        async with self.config.member(message.author).all() as a:
            a["away"] = False
            a["message"] = None
        await message.channel.send(
            f"Welcome back {message.author.mention}, I removed your AFK",
            delete_after=5,
            reference=message.to_reference(fail_if_not_exists=False),
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            mention_author=False,
        )
        if data["nick"] is True:
            try:
                await message.author.edit(nick=None)
            except discord.HTTPException as e:
                log.error(f"Failed to edit nickname due to: {e}")

    @commands.hybrid_command(aliases=["afk"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def away(self, ctx: commands.Context, *, message: str):
        """
        Set your away status.

        Use `[p]back` to remove your away status.
        """

        if ctx.guild.id in self.cache:
            data = self.cache[ctx.guild.id]
        else:
            data = await self.config.guild(ctx.guild)()
        if data["role"] != None:
            await ctx.author.add_roles(discord.Object(data["role"]))
        _userdata = await self.config.member(ctx.author).all()
        if _userdata["nick"] is True:
            try:
                await ctx.author.edit(
                    nick="[AFK] {}".format(ctx.author.name[:25])
                )  # to be safe lets use 25.
            except discord.HTTPException as e:
                log.error(f"Failed to edit nickname due to: {e}")
        async with self.config.member(ctx.author).all() as a:
            a["away"] = True
            a["message"] = message
        embed = discord.Embed(
            description=f"{ctx.author.mention} is now away.\n**Reason:** {message}",
            color=await ctx.embed_color(),
        )
        embed.set_author(name=str(ctx.author), icon_url=self._format_avatar(ctx.author))
        embed.set_footer(text=f"You're now away.")
        if data["delete_after"] is not None and data["delete"] is True:
            return await ctx.send(embed=embed, delete_after=data["delete_after"])
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def back(self, ctx: commands.Context):
        """Remove your away status.

        Use `[p]away <message>` to set your away status.
        """

        if not await self.config.member(ctx.author).away():
            return await ctx.maybe_send_embed("You're not away.")
        if ctx.guild.id in self.cache:
            data = self.cache[ctx.guild.id]
        else:
            data = await self.config.guild(ctx.guild).all()
        if data["role"] != None:
            if ctx.author._roles.has(data["role"]):
                await ctx.author.remove_roles(discord.Object(data["role"]))
        _userdata = await self.config.member(ctx.author).all()
        if _userdata["nick"] is True:
            try:
                await ctx.author.edit(nick=None)
            except discord.HTTPException as e:
                log.error(f"Failed to edit nickname due to: {e}")
        async with self.config.member(ctx.author).all() as a:
            a["away"] = False
            a["message"] = None
        embed = discord.Embed(
            description=f"{ctx.author.mention} is now back.",
            color=await ctx.embed_color(),
        )
        embed.set_author(name=str(ctx.author), icon_url=self._format_avatar(ctx.author))
        embed.set_footer(text=f"You're now back.")
        if data["delete_after"] is not None and data["delete"] is True:
            return await ctx.send(embed=embed, delete_after=data["delete_after"])
        await ctx.send(embed=embed)

    @commands.group(aliases=["afkset"])
    async def awayset(self, ctx: commands.Context):
        """Manage away settings."""

    @awayset.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def role(self, ctx: commands.Context, role: discord.Role):
        """Set the role to be used for away status."""

        if role.position >= ctx.me.top_role.position:
            return await ctx.send("You can't assign roles higher / equal to my own.")
        if role.position >= ctx.author.top_role.position:
            return await ctx.send("You can't assign roles higher / equal to your own.")
        await self.config.guild(ctx.guild).role.set(role.id)
        await self.update_guild_cache(ctx.guild)
        await ctx.send(
            f"Away role set to {role.mention}.",
        )

    @awayset.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def toggle(self, ctx: commands.Context, delete: bool):
        """Toggle whether to delete away messages or not."""

        await self.config.guild(ctx.guild).delete.set(delete)
        await self.update_guild_cache(ctx.guild)
        await ctx.send(f"Away delete set to {delete}.")

    @awayset.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def timeout(self, ctx: commands.Context, delete_after: int):
        """Set the amount of time in seconds to delete the message after [p]away."""

        if delete_after < 5:
            return await ctx.send("The minimum is 5 seconds.")
        await self.config.guild(ctx.guild).delete_after.set(delete_after)
        await self.update_guild_cache(ctx.guild)
        await ctx.send(f"Away delete after set to {delete_after}.")

    @awayset.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def autoback(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to automatically get back from away.

        Pass `True` to enable, `False` to disable.
        """
        await self.config.member(ctx.author).autoback.set(toggle)
        await ctx.send(f"Away autoback set to {toggle}.")

    @awayset.command()
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nick(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to change the nickname to `name + [away]`

        Pass `True` to enable, `False` to disable.
        """
        await self.config.member(ctx.author).nick.set(toggle)
        await ctx.send(f"Away nick set to {toggle}.")
