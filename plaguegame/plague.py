"""
MIT License

Copyright (c) 2020-2023 phenom4n4n
Copyright (c) 2023-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import random
from collections import Counter

import discord
from redbot.core import Config, app_commands, bank, commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import (
    box,
    humanize_list,
    humanize_number,
    pagify,
)
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu, start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.views import ConfirmView

from .converters import Curable, FuzzyHuman, Infectable, hundred_int

hn = humanize_number


class GameState:
    INFECTED = "infected"
    HEALTHY = "healthy"


class GameRole:
    DOCTOR = "Doctor"
    PLAGUEBEARER = "Plaguebearer"
    USER = "User"


class NotificationType:
    INFECT = "infect"
    CURE = "cure"
    DOCTOR = "doctor"
    PLAGUEBEARER = "plaguebearer"


async def is_infected(ctx):
    userState = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameState()
    return userState == GameState.INFECTED


async def is_healthy(ctx):
    userState = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameState()
    return userState == GameState.HEALTHY


async def is_doctor(ctx):
    userRole = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameRole()
    return userRole == GameRole.DOCTOR


async def not_doctor(ctx):
    userRole = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameRole()
    return userRole != GameRole.DOCTOR


async def not_plaguebearer(ctx):
    userRole = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameRole()
    return userRole != GameRole.PLAGUEBEARER


async def has_role(ctx: commands.Context) -> bool:
    userRole = await ctx.bot.get_cog("Plague").config.user(ctx.author).gameRole()
    return userRole != GameRole.USER


class Plague(commands.Cog):
    """A plague game."""

    __version__ = "1.0.8"
    __author__ = humanize_list(["phenom4n4n", "ltzmax"])
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/docs/Plague.md"

    def format_help_for_context(self, ctx):
        pre_processed = super().format_help_for_context(ctx)
        n = "\n" if "\n\n" not in pre_processed else ""
        return f"{pre_processed}{n}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2395486659, force_registration=True)
        default_global = {"plagueName": "Plague", "logChannel": None, "rate": 75}
        default_user = {
            "gameRole": GameRole.USER,
            "gameState": GameState.HEALTHY,
            "notifications": False,
        }
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)
        # Context Menu for viewing plague profiles
        # https://github.com/Rapptz/discord.py/issues/7823#issuecomment-1086830458
        self.ctx_menu = app_commands.ContextMenu(
            name="View Plague Profile",
            callback=self.plague_profile_context,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int):
        await self.config.user_from_id(user_id).clear()

    async def generate_plague_profile(self, member):
        data = await self.config.user(member).all()
        userRole = data["gameRole"]
        userState = data["gameState"]

        notifications = data["notifications"]
        if notifications:
            notifications = "Enabled"
        else:
            notifications = "Disabled"

        if userRole == GameRole.DOCTOR:
            thumbnail = "https://max.shx.gg/6GJ6zTXmI.png"
        elif userRole == GameRole.PLAGUEBEARER:
            thumbnail = "https://cdna.artstation.com/p/assets/images/images/015/285/028/large/john-yakimow-plaguebear.jpg?1547774010"
        elif userState == GameState.INFECTED:
            thumbnail = (
                "https://cdn.pixabay.com/photo/2020/04/29/07/54/coronavirus-5107715_960_720.png"
            )
        else:
            thumbnail = "https://static.thenounproject.com/png/2090399-200.png"

        embed = discord.Embed(title="Plague Profile", colour=0x7289DA)
        embed.add_field(name="Role:", value=userRole)
        embed.add_field(name="State:", value=userState)
        embed.add_field(name="Notifications:", value=notifications, inline=False)
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(name=member, icon_url=member.avatar.url)
        return embed

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.command("plagueprofile")
    async def plagueProfile(self, ctx, *, member: FuzzyHuman = None):
        """Show's your Plague Game profile"""
        member = member or ctx.author
        embed = await self.generate_plague_profile(member)
        await ctx.send(embed=embed)

    async def plague_profile_context(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        """View a user's plague profile from a context menu.

        Parameters
        -----------
        member: discord.Member
            The member to view the profile of.
        """
        await interaction.response.defer(ephemeral=True)
        embed = await self.generate_plague_profile(member)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.check(is_infected)
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.guild_only()
    @commands.command(aliases=["cough"], cooldown_after_parsing=True)
    async def infect(self, ctx, *, member: Infectable):
        """Infect another user. You must be infected to use this command."""
        rate = await self.config.rate()
        chance = random.randint(1, 100)
        if chance <= rate:
            result = await self.infect_user(ctx=ctx, user=member)
            await ctx.send(result)
        else:
            await ctx.send(
                f"Luckily **{member.name}** was wearing a mask so they didn't get infected."
            )

    @commands.check(is_doctor)
    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.guild_only()
    @commands.command(cooldown_after_parsing=True)
    async def cure(self, ctx, *, member: Curable):
        """Cure a user. You must be a Doctor to use this command."""
        result = await self.cure_user(ctx=ctx, user=member)
        await ctx.send(result)

    @commands.command()
    async def plaguenotify(self, ctx):
        """Enable/Disable Plague Game notifications."""
        notifications = await self.config.user(ctx.author).notifications()
        if notifications != False:
            await self.config.user(ctx.author).notifications.set(False)
            message = "You will no longer be sent Plague Game notifications."
        else:
            await self.config.user(ctx.author).notifications.set(True)
            message = "You will now be sent Plague Game notifications."

        await ctx.send(message)

    @commands.check(not_doctor)
    @commands.check(is_healthy)
    @bank.cost(10000)
    @commands.command(aliases=["plaguedoc"])
    async def plaguedoctor(self, ctx):
        """Become a doctor for 10,000 currency.

        You must be healthy to study at medical school."""
        currency = await bank.get_currency_name(ctx.guild)
        await self.config.user(ctx.author).gameRole.set(GameRole.DOCTOR)
        await self.notify_user(ctx, ctx.author, NotificationType.DOCTOR)
        await ctx.send(f"{ctx.author} has spent 10,000 {currency} and become a Doctor.")

    @commands.check(not_plaguebearer)
    @commands.check(is_infected)
    @bank.cost(10000)
    @commands.command()
    async def plaguebearer(self, ctx):
        """Become a plaguebearer for 10,000 currency.

        You must be infected to mutate into a plaguebearer."""
        currency = await bank.get_currency_name(ctx.guild)
        await self.config.user(ctx.author).gameRole.set(GameRole.PLAGUEBEARER)
        await self.notify_user(ctx, ctx.author, NotificationType.PLAGUEBEARER)
        await ctx.send(f"{ctx.author} has spent 10,000 {currency} and become a Plaguebearer.")

    @commands.check(has_role)
    @bank.cost(10000)
    @commands.command()
    async def resign(self, ctx):
        """Quit being a doctor or plaguebearer for 10,000 currency.

        You must be infected to mutate into a plaguebearer."""
        currency = await bank.get_currency_name(ctx.guild)
        await self.config.user(ctx.author).gameRole.set(GameRole.USER)
        await ctx.send(
            f"{ctx.author} has spent 10,000 {currency}- to resign from their current job."
        )

    @commands.check(not_doctor)
    @commands.check(is_healthy)
    @bank.cost(5000)
    @commands.command()
    async def infectme(self, ctx):
        """Get infected for 5,000 currency.

        Why would you willingly infect yourself?"""
        await ctx.send(await self.infect_user(ctx, ctx.author))

    @commands.check(not_plaguebearer)
    @commands.check(is_infected)
    @bank.cost(5000)
    @commands.command()
    async def treatme(self, ctx):
        """Get cured from the plague for 5,000 currency.

        This is America, so the health care is expensive."""
        await ctx.send(await self.cure_user(ctx, ctx.author))

    @commands.is_owner()
    @commands.group()
    async def plagueset(self, ctx):
        """Settings for the Plague game."""

    @plagueset.command()
    async def name(self, ctx, *, name: str = None):
        """Set's the plague's name. Leave blank to show the current name."""
        plagueName = await self.config.plagueName()
        if not name:
            message = f"The current plague's name is `{plagueName}`."
        else:
            await self.config.plagueName.set(name)
            message = f"Set the current plague's name to `{name}`."
        await ctx.send(message)

    @plagueset.command("infect")
    async def manual_infect(self, ctx, *, user: discord.User):
        """Manually infect a user."""
        result = await self.infect_user(ctx=ctx, user=user)
        await ctx.send(result)

    @plagueset.command("cure")
    async def manual_cure(self, ctx, *, user: discord.User):
        """Manually cure a user."""
        result = await self.cure_user(ctx=ctx, user=user)
        await ctx.send(result)

    @plagueset.group(invoke_without_command=True)
    async def infected(self, ctx):
        """Sends a list of the infected users."""
        user_list = await self.config.all_users()
        infected_list = []
        for user, data in user_list.items():
            user = ctx.bot.get_user(user)
            if user:
                userState = data["gameState"]
                if userState == GameState.INFECTED:
                    infected_list.append(f"{user.mention} - {user}")
        if infected_list:
            infected_list = "\n".join(infected_list)
            color = await ctx.embed_color()
            if len(infected_list) > 2000:
                embeds = []
                infected_pages = list(pagify(infected_list))
                for index, page in enumerate(infected_pages, start=1):
                    embed = discord.Embed(color=color, title="Infected Users", description=page)
                    embed.set_footer(text=f"{index}/{len(infected_pages)}")
                    embeds.append(embed)
                await menu(ctx, embeds, DEFAULT_CONTROLS)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        color=color,
                        title="Infected Users",
                        description=infected_list,
                    )
                )
        else:
            await ctx.send("No one has been infected yet..")

    @infected.command("guild")
    async def guild_infected(self, ctx, *, guild: discord.Guild = None):
        """Sends a list of the infected users in a guild."""
        if not guild:
            guild = ctx.guild
        user_list = await self.config.all_users()
        infected_list = []
        for user, data in user_list.items():
            user = guild.get_member(user)
            if user:
                userState = data["gameState"]
                if userState == GameState.INFECTED:
                    infected_list.append(f"{user.mention} - {user}")
        if infected_list:
            infected_list = "\n".join(infected_list)
            color = await ctx.embed_color()
            if len(infected_list) > 2000:
                embeds = []
                infected_pages = list(pagify(infected_list))
                for index, page in enumerate(infected_pages, start=1):
                    embed = discord.Embed(color=color, title="Infected Members", description=page)
                    embed.set_footer(text=f"{index}/{len(infected_pages)}")
                    embeds.append(embed)
                await menu(ctx, embeds, DEFAULT_CONTROLS)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        color=color,
                        title="Infected Members",
                        description=infected_list,
                    )
                )
        else:
            await ctx.send("No one has been infected yet..")

    @plagueset.command()
    async def healthy(self, ctx):
        """Sends a list of the healthy users."""
        user_list = await self.config.all_users()
        healthy_list = []
        for user, data in user_list.items():
            user = ctx.bot.get_user(user)
            if user:
                userState = data["gameState"]
                if userState == GameState.HEALTHY:
                    healthy_list.append(f"{user.mention} - {user}")
        if healthy_list:
            healthy_list = "\n".join(healthy_list)
            color = await ctx.embed_color()
            if len(healthy_list) > 2000:
                embeds = []
                healthy_pages = list(pagify(healthy_list))
                for index, page in enumerate(healthy_pages, start=1):
                    embed = discord.Embed(color=color, title="Healthy Users", description=page)
                    embed.set_footer(text=f"{index}/{len(healthy_pages)}")
                    embeds.append(embed)
                await menu(ctx, embeds, DEFAULT_CONTROLS)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        color=color,
                        title="Healthy Users",
                        description=healthy_list,
                    )
                )
        else:
            await ctx.send("No one stored is healthy..")

    @plagueset.command("doctor")
    async def set_doctor(self, ctx, user: discord.User):
        """Set a doctor."""
        await self.config.user(user).gameRole.set(GameRole.DOCTOR)
        await self.config.user(user).gameState.set(GameState.HEALTHY)
        await self.notify_user(ctx, user, NotificationType.DOCTOR)
        await ctx.tick()

    @plagueset.command("plaguebearer")
    async def set_plaguebearer(self, ctx, user: discord.User):
        """Set a plaguebearer."""
        await self.config.user(user).gameRole.set(GameRole.PLAGUEBEARER)
        await self.config.user(user).gameState.set(GameState.INFECTED)
        await self.notify_user(ctx, user, NotificationType.PLAGUEBEARER)
        await ctx.tick()

    @plagueset.command("channel")
    async def plagueset_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the log channel"""
        if not channel:
            channel = ctx.channel
        await self.config.logChannel.set(channel.id)
        await ctx.send(f"Set {channel.mention} as the log channel.")

    @plagueset.command("reset")
    async def plagueset_reset(self, ctx):
        """Reset the entire Plague Game."""
        msg = await ctx.send("Are you sure you want to reset the current Plague Game?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Action cancelled.")
        else:
            if pred.result is True:
                await self.config.clear_all()
                await ctx.send("All data reset.")
            else:
                await ctx.send("Action cancelled.")

    @plagueset.command(name="resetuser")
    async def reset_user(self, ctx, user: discord.User):
        """Reset a user."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            f"Are you sure you want to reset **{user}**?\nThis will reset all their data from this cog.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.user(user).clear()
            await ctx.send(f"**{user}** has been reset.")
        else:
            await ctx.send("Action cancelled.")

    @plagueset.command("rate")
    async def plagueset_rate(self, ctx: commands.Context, rate: hundred_int):
        """Set the Plague Game infection rate."""
        await self.config.rate.set(rate)
        await ctx.send(f"The Plague Game rate has been set to {rate}%.")

    @plagueset.command("settings", aliases=["showsettings"])
    async def plagueset_settings(self, ctx: commands.Context):
        """View the Plague Game settings."""
        data = await self.config.all()
        channel = self.bot.get_channel(data["logChannel"])
        channel = channel.mention if channel else "None"
        description = [
            f"`{'Name':<16}`:{data['plagueName']}",
            f"`{'Log Channel':<16}`:{channel}",
            f"`{'Infection Rate':<16}`:{data['rate']}%",
        ]
        e = discord.Embed(
            color=await ctx.embed_color(),
            description="\n".join(description),
        )
        e.set_author(name="Plague Game Settings", icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=e)

    async def get_plague_stats(self) -> Counter:
        data = Counter()
        async for user_data in AsyncIter((await self.config.all_users()).values()):
            data[user_data["gameRole"]] += 1
            data[user_data["gameState"]] += 1
        return data

    @plagueset.command("stats")
    async def plagueset_stats(self, ctx: commands.Context):
        """View plague game stats."""
        data = await self.get_plague_stats()
        infected = hn(data[GameState.INFECTED])
        health = hn(data[GameState.HEALTHY])
        doctors = hn(data[GameRole.DOCTOR])
        plaguebear = hn(data[GameRole.PLAGUEBEARER])
        jobless = hn(data[GameRole.USER])
        description = [
            f"`{'Infected Users':<16}`:{infected}",
            f"`{'Healhy Users':<16}`:{health}",
            f"`{'Doctors':<16}`:{doctors}",
            f"`{'Plaguebearers':<16}`:{plaguebear}",
            f"`{'Jobless Users':<16}`:{jobless}",
        ]
        e = discord.Embed(
            title=f"{await self.config.plagueName()} Stats",
            color=await ctx.embed_color(),
            description=("\n".join(description)),
        )
        e.set_footer(text=f"Total: {humanize_number(sum(data.values()))}")
        await ctx.send(embed=e)

    @plagueset.command(name="version")
    @commands.bot_has_permissions(embed_links=True)
    async def plagueset_version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
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

    async def infect_user(self, ctx, user: discord.User, auto=False):
        game_data = await self.config.all()
        plagueName = game_data["plagueName"]

        channel_id = game_data["logChannel"]
        channel = ctx.bot.get_channel(channel_id)
        autoInfect = f" since **{ctx.author}** didn't wear a mask" if auto else ""

        await self.config.user(user).gameState.set(GameState.INFECTED)
        await self.notify_user(ctx, user, NotificationType.INFECT)
        if channel:
            await channel.send(
                f"💀| **{user}** on `{ctx.guild}` was just infected with {plagueName} by **{ctx.author}**{autoInfect}."
            )
        return f"**{user.name}** has been infected with {plagueName}{autoInfect}."

    async def cure_user(self, ctx, user: discord.User):
        game_data = await self.config.all()
        plagueName = game_data["plagueName"]
        channel_id = game_data["logChannel"]
        channel = ctx.bot.get_channel(channel_id)

        await self.config.user(user).gameState.set(GameState.HEALTHY)
        await self.notify_user(ctx, user, NotificationType.CURE)
        if channel:
            await channel.send(
                f"✨| **{user}** on `{ctx.guild}` was just cured from {plagueName} by **{ctx.author}**."
            )
        return f"**{user.name}** has been cured from {plagueName}."

    async def notify_user(self, ctx, user: discord.User, notificationType: str):
        if not await self.config.user(user).notifications():
            return
        prefixes = await ctx.bot.get_valid_prefixes(ctx.guild)

        plagueName = await self.config.plagueName()
        if notificationType == NotificationType.INFECT:
            title = f"You have been infected with {plagueName}!"
            description = (
                f"{ctx.author} infected you. You now have access to `{prefixes[-1]}infect`."
            )
        elif notificationType == NotificationType.CURE:
            title = f"You have been cured from {plagueName}!"
            description = f"{ctx.author} cured you."
        elif notificationType == NotificationType.DOCTOR:
            title = "You are now a Doctor!"
            description = f"{ctx.author} has set you as a Doctor. You now have access to `{prefixes[-1]}cure`."
        elif notificationType == NotificationType.PLAGUEBEARER:
            title = "You are now a Plaguebearer!"
            description = f"{ctx.author} has set you as a Plaguebearer. You now have access to `{prefixes[-1]}infect`."

        embed = discord.Embed(title=title, description=description)
        embed.set_footer(text=f"Use `{prefixes[-1]}plaguenotify` to disable these notifications.")
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if not ctx.channel.permissions_for(ctx.me).send_messages:
            return
        if not ctx.guild or ctx.cog == self or not ctx.message.mentions:
            return
        if await self.bot.cog_disabled_in_guild(self, ctx.guild):
            return
        number = random.randint(1, 10)
        if number > 3:
            return
        perp = await self.config.user(ctx.author).all()
        state = perp["gameState"]
        if state != GameState.INFECTED:
            return

        not_bots = [user for user in ctx.message.mentions if not user.bot]
        infectables = []
        for user in not_bots:
            victim_data = await self.config.user(user).all()
            if (victim_data["gameState"] != GameState.INFECTED) and (
                victim_data["gameRole"] != GameRole.DOCTOR
            ):
                infectables.append(user)
        if not infectables:
            return
        victim = random.choice(infectables)
        result = await self.infect_user(ctx, victim, True)
        await ctx.send(result)
