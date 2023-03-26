import contextlib
import io
from typing import Dict, List, Optional, TypedDict

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .config import DefaultGuild, get_config
from .const import CAP_DETECTOR, LOG, WARN_MESSAGE, WARN_MESSAGE_DELETE_COOLDOWN


class IgnoredObjects(TypedDict):
    roles: Dict[int, List[int]]
    channels: Dict[int, List[int]]


class CapSpam(commands.Cog):
    """Prevent spamming in caps"""

    bot: Red
    config: Config
    _enabled_guilds_ids: List[int]
    _guilds_logging_channels: Dict[int, Optional[int]]
    _ignored_objects: IgnoredObjects

    __ready: bool

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = get_config()

        self._enabled_guilds_ids = []
        self._ignored_objects = IgnoredObjects(
            roles={},
            channels={},
        )

        self.__ready = False

    __version__ = "0.1.0"
    __author__ = "MAX, ScarletRav3n, Predeactor"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/capspam/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(
        self, *, requester: str, user_id: int
    ) -> Dict[str, str]:
        """Nothing to delete"""
        return {}

    @commands.group(name="capspam")
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def capspam(self, _: commands.GuildContext):
        """CapSpam settings"""

    @capspam.command(name="enable", aliases=["toggle"])
    async def capspam_enable(self, ctx: commands.GuildContext, *, toggle: bool):
        """
        Enable CapSpam in your server.

        __Parameters__

        **toggle** : `Boolean`
            Enable or disable CapSpam in this server.
        """
        state = ctx.guild.id in self._enabled_guilds_ids

        if not ctx.me.guild_permissions.manage_messages:
            await ctx.send(
                'I am missing the "Manage Messages" permission, add it to me so you can enable CapSpam.'
            )
            return

        if state == toggle:
            await ctx.send(f"Your server is already set to `{state}`.")
            return

        await self.config.guild(ctx.guild).enabled.set(toggle)
        if toggle:
            self._enabled_guilds_ids.append(ctx.guild.id)
        else:
            self._enabled_guilds_ids.remove(ctx.guild.id)

        await ctx.send(f"CapSpam has set your server to `{toggle}`.")

    @capspam.group(name="ignore")
    async def capspam_ignore(self, _: commands.GuildContext):
        """
        Manage the roles/channels ignore settings.

        See `[p]capspam info` for a list of ignored roles/channels.
        """

    @capspam_ignore.command(name="addroles", aliases=["roles", "role"])
    async def capspam_ignore_addroles(
        self, ctx: commands.GuildContext, *roles: discord.Role
    ):
        """
        Add one or more roles to be ignored by CapSpam.

        If the author of the message has one of the ignored roles, he won't be treated by CapSpam filtering.

        __Parameters__

        **roles** : `List of server roles`
            The roles to add.
        """
        if not roles:
            return await ctx.send_help()

        roles_ids = [role.id for role in roles]
        ignored_roles = await self.config.guild(ctx.guild).ignored_roles()

        can_be_added = [
            role_id for role_id in roles_ids if role_id not in ignored_roles
        ]
        not_added = [role_id for role_id in roles_ids if role_id in ignored_roles]

        ignored_roles.extend(can_be_added)
        await self.config.guild(ctx.guild).ignored_roles.set(ignored_roles)
        self._ignored_objects["roles"][ctx.guild.id] = ignored_roles

        msg = ""
        if can_be_added:
            msg += "**Added roles:**\n\n{roles}\n\n".format(
                roles="\n".join([f"- {i}" for i in can_be_added])
            )
        if not_added:
            msg += "**Roles already added:**\n\n{roles}".format(
                roles="\n".join([f"- {i}" for i in not_added])
            )
        await ctx.send(msg)

    @capspam_ignore.command(
        name="removeroles", aliases=["removerole", "remrole", "rmrole"]
    )
    async def capspam_ignore_removeroles(
        self, ctx: commands.GuildContext, *roles: discord.Role
    ):
        """
        Remove one or more roles to be ignored by CapSpam.

        __Parameters__

        **roles** : `List of server roles`
            The roles to remove.
        """
        if not roles:
            return await ctx.send_help()

        roles_ids = [role.id for role in roles]
        ignored_roles: List[int] = await self.config.guild(ctx.guild).ignored_roles()

        can_be_removed = [role_id for role_id in roles_ids if role_id in ignored_roles]
        not_removed = [role_id for role_id in roles_ids if role_id not in ignored_roles]

        new_ignored_roles = [
            role for role in ignored_roles if role not in can_be_removed
        ]
        await self.config.guild(ctx.guild).ignored_roles.set(new_ignored_roles)
        self._ignored_objects["roles"][ctx.guild.id] = new_ignored_roles

        msg = ""
        if can_be_removed:
            msg += "**Roles removed:**\n\n{roles}\n\n".format(
                roles="\n".join([f"- {i}" for i in can_be_removed])
            )
        if not_removed:
            msg += "**Roles already not ignored:**\n\n{roles}".format(
                roles="\n".join([f"- {i}" for i in not_removed])
            )
        await ctx.send(msg)

    @capspam_ignore.command(name="addchannels", aliases=["channels", "channel"])
    async def capspam_ignore_addchannels(
        self, ctx: commands.GuildContext, *channels: discord.TextChannel
    ):
        """
        Add one or more channels to be ignored by CapSpam.

        If the author of the message has one of the ignored channels, he won't be treated by CapSpam filtering.

        __Parameters__

        **channels** : `List of server channels`
            The channels to add.
        """
        if not channels:
            return await ctx.send_help()

        channels_ids = [channel.id for channel in channels]
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()

        can_be_added = [
            channel_id
            for channel_id in channels_ids
            if channel_id not in ignored_channels
        ]
        not_added = [
            channel_id for channel_id in channels_ids if channel_id in ignored_channels
        ]

        ignored_channels.extend(can_be_added)
        await self.config.guild(ctx.guild).ignored_channels.set(ignored_channels)
        self._ignored_objects["channels"][ctx.guild.id] = ignored_channels

        msg = ""
        if can_be_added:
            msg += "**Added channels:**\n\n{channels}\n\n".format(
                channels="\n".join([f"- {i}" for i in can_be_added])
            )
        if not_added:
            msg += "**Channels already added:**\n\n{channels}".format(
                channels="\n".join([f"- {i}" for i in not_added])
            )
        await ctx.send(msg)

    @capspam_ignore.command(name="removechannels", aliases=["remchannel", "rmchannel"])
    async def capspam_ignore_removechannels(
        self, ctx: commands.GuildContext, *channels: discord.TextChannel
    ):
        """
        Remove one or more channels to be ignored by CapSpam.

        __Parameters__

        **channels** : `List of server channels`
            The channels to remove.
        """
        if not channels:
            return await ctx.send_help()

        channels_ids = [channel.id for channel in channels]
        ignored_channels = await self.config.guild(ctx.guild).ignored_channels()

        can_be_removed = [
            channel_id for channel_id in channels_ids if channel_id in ignored_channels
        ]
        not_removed = [
            channel_id
            for channel_id in channels_ids
            if channel_id not in ignored_channels
        ]

        new_ignored_channels = [
            channel for channel in ignored_channels if channel not in can_be_removed
        ]
        await self.config.guild(ctx.guild).ignored_channels.set(new_ignored_channels)
        self._ignored_objects["channels"][ctx.guild.id] = new_ignored_channels

        msg = ""
        if can_be_removed:
            msg += "**Channels removed:**\n\n{channels}\n\n".format(
                channels="\n".join([f"- {i}" for i in can_be_removed])
            )
        if not_removed:
            msg += "**Channels already not ignored:**\n\n{channels}".format(
                channels="\n".join([f"- {i}" for i in not_removed])
            )
        await ctx.send(msg)

    @capspam.command("view", aliases=["settings", "setting"])
    @commands.has_permissions(embed_links=True)
    async def capspam_view(self, ctx: commands.GuildContext):
        """
        Show the informations about CapSpam in your server.
        """
        data: DefaultGuild = await self.config.guild(ctx.guild).all()  # type: ignore

        embed = discord.Embed(
            title=f"CapSpam settings for {ctx.guild.name} ({ctx.guild.id})"
        )
        embed.add_field(name="Enabled", value=f"`{data['enabled']}`", inline=False)
        embed.add_field(
            name="Ignored Roles IDs",
            value="\n".join(f"`{ignored}`" for ignored in data["ignored_roles"])
            or "None added.",
            inline=False,
        )
        embed.add_field(
            name="Ignored Channels IDs",
            value="\n".join([f"`{ignored}`" for ignored in data["ignored_channels"]])
            or "None added.",
        )

        await ctx.send(embed=embed)

    @capspam.command(name="export", hidden=True)
    async def capspam_export(self, ctx: commands.GuildContext):
        """
        Export the CapSpam settings.

        Returned in a JSON format.
        """
        data = await self.config.guild(ctx.guild).all()
        file = discord.File(io.StringIO(str(data)), f"capspam-{ctx.guild.id}.json")
        await ctx.send(f"Report for guild ID: {ctx.guild.id}", file=file)

    @capspam.command(name="version")
    async def capspam_version(self, ctx: commands.Context):
        """Shows the version of the cog"""
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Cog Version:",
                description=f"Author: {self.__author__}\nVersion: {self.__version__}",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(
                f"Cog Version: {self.__version__}\nAuthor: {self.__author__}"
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Basic checks
        if not self.__ready:
            return

        ctx: commands.Context = await self.bot.get_context(message)
        if not ctx.guild:
            return
        if ctx.guild.id not in self._enabled_guilds_ids:  # type: ignore
            return

        # Make sure we have the perms
        if not ctx.me.guild_permissions.manage_messages:
            await self.config.guild(ctx.guild).enabled.set(False)
            self._enabled_guilds_ids.remove(ctx.guild.id)  # type: ignore
            LOG.info(
                f"Ignored message: Missing permissions: {message.author.display_name}: {message.guild.name}"
            )
            return

        # Ignore roles/channels
        if ctx.channel.id in self._ignored_objects["channels"].get(ctx.guild.id, []):  # type: ignore
            return
        roles_ids = [role.id for role in ctx.author.roles]
        if any(
            role_id in self._ignored_objects["roles"].get(ctx.guild.id, [])
            for role_id in roles_ids
        ):  # type: ignore
            return

        # Pre-checks (Automod immunity/Is bot)
        if immune := await self.bot.is_automod_immune(ctx):
            print(immune)
            return
        if ctx.author.bot:  # type: ignore
            return

        # Actually run the thing :p
        if msg_trigger := CAP_DETECTOR.findall(message.content):
            with contextlib.suppress(discord.Forbidden, discord.NotFound):
                await message.delete()
            await ctx.send(
                WARN_MESSAGE.format(author=ctx.author),
                delete_after=WARN_MESSAGE_DELETE_COOLDOWN,
            )

    async def setup(self):
        await self.bot.wait_until_red_ready()

        for guild_id, guild_data in (await self.config.all_guilds()).items():
            guild_data: DefaultGuild
            if guild_data["enabled"]:
                LOG.info(f"Enabled {guild_id}")
                self._enabled_guilds_ids.append(guild_id)

            if channels_ids := guild_data["ignored_channels"]:
                LOG.info(
                    f"Ignoring channels {', '.join([str(i) for i in channels_ids])}"
                )
                self._ignored_objects["channels"][guild_id] = channels_ids

            if roles_ids := guild_data["ignored_roles"]:
                LOG.info(f"Ignoring roles {', '.join([str(i) for i in roles_ids])}")
                self._ignored_objects["roles"][guild_id] = roles_ids

        LOG.debug("CapSpam ready.")
        self.__ready = True


async def setup(bot: Red):
    cog = CapSpam(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog.setup())
