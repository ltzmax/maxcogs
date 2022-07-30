# This cog was orginially made by TheDiscordHistorian (kato#0666) and dia ♡#0666.
# And are now maintained by ltzmax.
# Most people knew this cog was without a license on the original repo source
# but permission to continue the cog was granted by dia #0666.
# Please continue to respect the original authors to not steal the code without permissions.
import logging
from typing import Literal

import discord
from redbot.core import Config, commands

log = logging.getLogger("red.maxcogs.away")


class Away(commands.Cog):
    """An away thingy to set away and be not away."""

    __version__ = "2.0.1"
    __author__ = "dia ♡#0666, max, TheDiscordHistorian (kato#0666)"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n**Cog Version:** {self.__version__}\n**Author:** {self.__author__}"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int,
    ):
        await self.config.user_from_id(user_id).clear()

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
        return user.display_avatar.url  # type: ignore

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
                        allowed_mentions=discord.AllowedMentions(
                            users=False, roles=False
                        ),
                        mention_author=False,
                    )
                else:
                    await message.channel.send(
                        embed=self._format_message(mention, data["message"]),
                        reference=message.to_reference(fail_if_not_exists=False),
                        allowed_mentions=discord.AllowedMentions(
                            users=False, roles=False
                        ),
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
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def away(self, ctx: commands.Context, *, message: str):
        """
        Set your away status.

        Use `[p]back` to remove your afk status.
        """
        if ctx.guild.id in self.cache:
            data = self.cache[ctx.guild.id]
        else:
            data = await self.config.guild(ctx.guild)()
        if data["role"] != None:
            try:
                await ctx.author.add_roles(discord.Object(data["role"]))
            except discord.NotFound as e:
                self.config.guild(ctx.guild).role.clear()
                log.error(f"Failed to add role due to: {e}")
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
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def back(self, ctx: commands.Context):
        """Remove your away status / get back from away.

        Use `[p]away <message>` to set your afk status.
        """
        if not await self.config.member(ctx.author).away():
            embed = discord.Embed(
                description=f"{ctx.author.mention} You're not away. Use `{ctx.clean_prefix}away <message>` to set your away status.",
                color=await ctx.embed_color(),
            )
            return await ctx.send(embed=embed, ephemeral=True)
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
    @commands.bot_has_permissions(manage_roles=True, embed_links=True)
    async def role(self, ctx: commands.Context, role: discord.Role):
        """Set the role to be used for away status."""
        if role.position >= ctx.me.top_role.position:
            embed = discord.Embed(
                description="I can't set the role to be higher than my highest role.",
                color=await ctx.embed_color(),
            )
            return await ctx.send(embed=embed)
        if role.position >= ctx.author.top_role.position:
            embed = discord.Embed(
                description="I can't set the role to be higher than your highest role.",
                color=await ctx.embed_color(),
            )
            return await ctx.send(embed=embed)
        await self.config.guild(ctx.guild).role.set(role.id)
        await self.update_guild_cache(ctx.guild)
        embed = discord.Embed(
            description=f"Set the away role to {role.mention}.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True, embed_links=True)
    async def deleterole(self, ctx: commands.Context):
        """Remove the away role set from `awayset role`."""
        await self.config.guild(ctx.guild).role.clear()
        await self.update_guild_cache(ctx.guild)
        embed = discord.Embed(
            description=f"Removed the away role.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(embed_links=True)
    async def toggle(self, ctx: commands.Context, delete: bool):
        """Toggle whether to delete away messages or not."""
        await self.config.guild(ctx.guild).delete.set(delete)
        await self.update_guild_cache(ctx.guild)
        embed = discord.Embed(
            description=f"Away delete set to {delete}.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(embed_links=True)
    async def timeout(self, ctx: commands.Context, delete_after: int):
        """Set the amount of time in seconds to delete the message after [p]away."""

        if delete_after < 5:
            return await ctx.maybe_send_embed("The minimum is 5 seconds.")
        await self.config.guild(ctx.guild).delete_after.set(delete_after)
        await self.update_guild_cache(ctx.guild)
        embed = discord.Embed(
            description=f"Set the timeout to {delete_after} seconds.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def autoback(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to automatically get back from away.

        Pass `True` to enable, `False` to disable.
        """
        await self.config.member(ctx.author).autoback.set(toggle)
        embed = discord.Embed(
            description=f"Set your autoback to {toggle}.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command(aliases=["nick"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True, embed_links=True)
    async def nickname(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to change the nickname to name + [away]

        Pass `True` to enable, `False` to disable.
        """
        await self.config.member(ctx.author).nick.set(toggle)
        embed = discord.Embed(
            description=f"Set the nickname to {toggle}.",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @awayset.command(aliases=["settings"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def showsettings(self, ctx):
        """Show the current away settings."""
        data = await self.config.guild(ctx.guild).all()
        if ctx.guild.id in self.cache:
            data = self.cache[ctx.guild.id]
        else:
            data = await self.config.guild(ctx.guild)()
        _userdata = await self.config.member(ctx.author).all()

        # to not show just role id, it's easier to show the role name instead.
        role = ctx.guild.get_role(data["role"])
        if role is None:
            role = "None"
        else:
            role = role.mention

        embed = discord.Embed(
            description=f"Current away settings for {ctx.guild.name}.",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Role", value=f"{role}", inline=False)
        embed.add_field(name="Delete", value=data["delete"], inline=False)
        embed.add_field(name="Delete after", value=data["delete_after"], inline=False)
        embed.add_field(name="Autoback:", value=_userdata["autoback"], inline=False)
        embed.add_field(name="Nick:", value=_userdata["nick"])
        await ctx.send(embed=embed)
