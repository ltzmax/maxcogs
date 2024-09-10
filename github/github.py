"""
MIT License

Copyright (c) 2021-2024 Obi-Wan3
Copyright (c) 2022-present ltzmax

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

import re
import typing
from datetime import datetime, timezone
from typing import Final, List
from urllib.parse import urlparse

import aiohttp
import discord
import feedparser
import html2text
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import escape, pagify

from .converters import ExplicitNone

# Constants
COLOR = 0x7289DA
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Regular expressions
TOKEN_REGEX: re.Pattern = re.compile(r"token=(.*)")
COMMIT_REGEX: re.Pattern = re.compile(r"https://github\.com/.*?/.*?/commit/(.*?)")
USER_REPO_BRANCH_REGEX: re.Pattern = re.compile(r"/(.*?)/(.*?)/?(commits)?/(.*?(?=\.atom))?")

LONG_COMMIT_REGEX: re.Pattern = re.compile(r"^<pre.*?>|</pre>$|(?<=\n)\n+")
LONG_RELEASE_REGEX: re.Pattern = re.compile(r"^<pre.*?>|</pre>$|(?<=\n)\n+")

# Error messages
NO_ROLE = "You do not have the required role!"
NOT_FOUND = "I could not find that feed."


class GitHub(commands.Cog):
    """
    GitHub RSS Commit Feeds

    Customizable system for GitHub commit updates similar to the webhook.
    """

    __version__: Final[str] = "1.0.1"
    __author__: Final[List[str]] = ["MAX", "Obi-Wan3"]
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/GitHub.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 14000605, force_registration=True)

        default_global = {"interval": 3}
        default_guild = {
            "channel": None,
            "role": None,
            "limit": 5,
            "color": None,
            "notify": True,
            "timestamp": True,
            "short": True,
        }
        default_member = {"feeds": {}}

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

        self._github_rss.start()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def cog_unload(self):
        self._github_rss.cancel()

    async def initialize(self):
        global_conf = await self.config.all()

        # Change loop interval if necessary
        if global_conf["interval"] != 3:
            self._github_rss.change_interval(minutes=global_conf["interval"])

        # Check whether config migration is necessary
        if global_conf.get("migrated"):
            return

        # Loop through each guild
        for guild_id, guild_data in (await self.config.all_guilds()).items():
            if guild_data.get("migrated") or not guild_data.get("feeds"):
                continue

            # Loop through each member
            for member_id, member_data in guild_data["feeds"].items():
                async with self.config.member_from_ids(
                    guild_id=guild_id, member_id=int(member_id)
                ).feeds() as member_feeds:
                    # Loop through each feed
                    for feed_name, feed_data in member_data.items():
                        user, repo, branch, token = await self._parse_url(feed_data["url"])
                        member_feeds[feed_name] = {
                            "user": user,
                            "repo": repo,
                            "branch": branch,
                            "token": token,
                            "channel": feed_data.get("channel", None),
                            "time": feed_data["time"],
                        }

            # Guild config has been migrated
            async with self.config.guild_from_id(guild_id).all() as guild_config:
                guild_config["migrated"] = True

        # All guild configs have been migrated
        async with self.config.all() as global_config:
            global_config["migrated"] = True

    @staticmethod
    def _escape(text: str):
        return escape(text, formatting=True)

    @staticmethod
    async def _repo_url(**user_and_repo):
        return f"https://github.com/{user_and_repo['user']}/{user_and_repo['repo']}/"

    @staticmethod
    async def _invalid_url(ctx: commands.Context):
        return f"Invalid GitHub URL. Try doing `{ctx.clean_prefix}github whatlinks` to see the accepted formats."

    @staticmethod
    async def _url_from_config(feed_config: dict):
        final_url = f"https://github.com/{feed_config['user']}/{feed_config['repo']}"

        if feed_config["branch"]:
            token = f"?token={feed_config['token']}" if feed_config["token"] else ""

            if feed_config["branch"] == "releases":
                return final_url + f"/{feed_config['branch']}.atom{token}"

            return final_url + f"/commits/{feed_config['branch']}.atom{token}"

        else:
            return final_url + f"/commits.atom"

    @staticmethod
    async def _fetch(url: str, valid_statuses: list):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.read()
                if resp.status not in valid_statuses:
                    return False
        return feedparser.parse(html)

    @staticmethod
    async def new_entries(entries, last_time):
        entries_new = []
        for e in entries:
            e_time = (
                datetime.strptime(e.updated, TIME_FORMAT).replace(tzinfo=timezone.utc).timestamp()
            )
            if e_time > last_time:
                entries_new.insert(0, e)
            else:
                break
        return entries_new, datetime.now(tz=timezone.utc)

    @staticmethod
    async def _parse_url(url: str):
        # Strip <link>
        if url[0] == "<" and url[-1] == ">":
            url = url[1:-1]

        parsed_url = urlparse(url)
        if not (
            user_repo_branch := USER_REPO_BRANCH_REGEX.search(
                parsed_url.path
                if (parsed_url.path.endswith("/") or ".atom" in parsed_url.path)
                else parsed_url.path + "/"
            )
        ):
            return None, None, None, None

        user, repo, branch, token = (
            user_repo_branch.group(1),
            user_repo_branch.group(2),
            user_repo_branch.group(4),
            (TOKEN_REGEX.fullmatch(parsed_url.query).group(1) if parsed_url.query else None),
        )

        # Set branch to None if it is commits.atom
        if branch == "commits":
            branch = None

        if (
            parsed_url.scheme != "https"
            or parsed_url.netloc != "github.com"
            or not user
            or not repo
            or (token and not branch)
            or (not user_repo_branch.group(3) and branch and branch != "releases")
        ):
            return None, None, None, None

        return user, repo, branch, token

    async def _parse_url_input(self, url: str, branch: str):
        user, repo, parsed_branch, token = await self._parse_url(url)
        if not any([user, repo, parsed_branch, token]):
            return None

        return {
            "user": user,
            "repo": repo,
            "branch": parsed_branch if token else branch,
            "token": token,
        }

    async def _get_feed_channel(self, bot: discord.Member, guild_channel: int, feed_channel):
        channel = None
        if feed_channel:
            channel = self.bot.get_channel(feed_channel)
        elif guild_channel:
            channel = self.bot.get_channel(guild_channel)
        if not (
            channel
            and channel.permissions_for(bot).send_messages
            and channel.permissions_for(bot).embed_links
        ):
            channel = None
        return channel

    async def _commit_embeds(
        self, entries: list, feed_link: str, color: int, timestamp: bool, short: bool
    ):
        if not entries:
            return None

        user, repo, branch, __ = await self._parse_url(feed_link + ".atom")

        if branch == "releases":
            embed = discord.Embed(
                title=f"[{user}/{repo}] New release published: {entries[0].title}",
                color=color if color is not None else COLOR,
                url=entries[0].link,
            )
            if not short:
                embed.description = html2text.html2text(entries[0].content[0].value)

        else:
            num = min(len(entries), 10)
            desc = ""
            for e in entries[:num]:
                if short:
                    desc += f"[`{COMMIT_REGEX.fullmatch(e.link).group(1)[:7]}`]({e.link}) {self._escape(e.title)} – {self._escape(e.author)}\n"
                else:
                    desc += f"[`{COMMIT_REGEX.fullmatch(e.link).group(1)[:7]}`]({e.link}) – {self._escape(e.author)}\n{LONG_COMMIT_REGEX.sub('', e.content[0].value)}\n\n"

            embed = discord.Embed(
                title=f"[{repo}:{branch}] {num} new commit{'s' if num > 1 else ''}",
                color=color if color is not None else COLOR,
                description=desc,
                url=feed_link if num > 1 else entries[0].link,
            )

        if timestamp:
            embed.timestamp = datetime.strptime(entries[0].updated, TIME_FORMAT).replace(
                tzinfo=timezone.utc
            )

        embed.set_author(
            name=entries[0].author,
            url=f"https://github.com/{entries[0].author}",
            icon_url=entries[0].media_thumbnail[0]["url"],
        )
        return embed

    @commands.is_owner()
    @commands.command(name="ghinterval", hidden=True)
    async def _interval(self, ctx: commands.Context, interval_in_minutes: int):
        """
        Set the global fetch interval for GitHub.

        Depending on the size of your bot, you may want to modify the interval for which the bot fetches all feeds for updates (default is 3 minutes).
        """
        await self.config.interval.set(interval_in_minutes)
        self._github_rss.change_interval(minutes=interval_in_minutes)
        return await ctx.send(
            f"I will now check for commit updates every {interval_in_minutes} minutes (change takes effect next loop)."
        )

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.admin_or_permissions(administrator=True)
    @commands.group(name="githubset", aliases=["ghset"])
    async def _github_set(self, ctx: commands.Context):
        """GitHub Settings"""

    @_github_set.command(name="short")
    async def _set_short(self, ctx: commands.Context, short: bool):
        """Set whether the GitHub message content should just include the title."""
        await self.config.guild(ctx.guild).short.set(short)
        return await ctx.send(
            f"The GitHub RSS feed message content length has been set to `{'short' if short else 'full'}`."
        )

    @_github_set.command(name="color")
    async def _set_color(
        self,
        ctx: commands.Context,
        hex_color: typing.Union[discord.Color, ExplicitNone],
    ):
        """Set the GitHub RSS feed embed color for the server (enter "None" to reset)."""
        await self.config.guild(ctx.guild).color.set(
            hex_color.value if hex_color is not None else None
        )
        return await ctx.send(
            f"The GitHub RSS feed embed color has been set to {hex_color if hex_color else 'the default'}."
        )

    @_github_set.command(name="notify")
    async def _set_notify(self, ctx: commands.Context, true_or_false: bool):
        """Set whether to send repo addition/removal notices to the channel."""
        await self.config.guild(ctx.guild).notify.set(true_or_false)
        return await ctx.send(
            f"Repo addition/removal notifications will {'now' if true_or_false else 'no longer'} be sent."
        )

    @_github_set.command(name="channel")
    async def _set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the default GitHub RSS feed channel."""

        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links):
            return await ctx.send(
                f"I do not have the necessary permissions (send messages & embed links) in {channel.mention}!"
            )

        await self.config.guild(ctx.guild).channel.set(channel.id)
        return await ctx.send(f"The GitHub RSS feed channel has been set to {channel.mention}.")

    @_github_set.command(name="role")
    async def _set_role(self, ctx: commands.Context, role: discord.Role = None):
        """Set the GitHub role requirement.

        Note: Only those who are a mod or has permissions `manage_channels` can add / remove.
        This is for you to lock to a speficially role to those with the permission to add / remove.
        Only those who have the role can add / remove feeds, if they dont have the role, they will not be able to use this command.
        """
        if not role:
            await self.config.guild(ctx.guild).role.set(None)
            return await ctx.send(f"The GitHub RSS feed role requirement has been removed.")
        else:
            await self.config.guild(ctx.guild).role.set(role.id)
            return await ctx.send(f"The GitHub RSS feed role has been set to {role.mention}.")

    @_github_set.command(name="limit")
    async def _set_limit(self, ctx: commands.Context, num: int = 5):
        """Set the GitHub RSS feed limit per user."""
        if num < 1:
            return await ctx.send("Please enter a positive integer!")
        await self.config.guild(ctx.guild).limit.set(num)
        return await ctx.send(f"The GitHub RSS feed limit per user has been set to {num}.")

    @_github_set.command(name="timestamp")
    async def _set_timestamp(self, ctx: commands.Context, true_or_false: bool):
        """Set whether GitHub RSS feed embeds should include a timestamp."""
        await self.config.guild(ctx.guild).timestamp.set(true_or_false)
        return await ctx.send(
            f"GitHub feed embeds will {'now' if true_or_false else 'no longer'} have timestamps."
        )

    @_github_set.command(name="force")
    async def _force(self, ctx: commands.Context, user: discord.Member, name: str):
        """Force a specific GitHub feed to post the last commit."""

        async with self.config.member(user).feeds() as feeds:
            if not (feed_config := feeds.get(name)):
                return await ctx.send(NOT_FOUND)

        url = await self._url_from_config(feed_config)
        if not (parsed := await self._fetch(url, [200])):
            return await ctx.send(await self._invalid_url(ctx))

        if feed_config["channel"]:
            channel = ctx.guild.get_channel(feed_config["channel"])
        else:
            channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).channel())

        guild_config = await self.config.guild(ctx.guild).all()

        if channel and channel.permissions_for(ctx.guild.me).embed_links:
            return await channel.send(
                embed=await self._commit_embeds(
                    entries=[parsed.entries[0]],
                    feed_link=parsed.feed.link,
                    color=guild_config["color"],
                    timestamp=guild_config["timestamp"],
                    short=guild_config["short"],
                )
            )
        else:
            return await ctx.send(
                "Either the set channel has been removed or I do not have permissions to send embeds in the channel."
            )

    @_github_set.command(name="forceall")
    async def _force_all(self, ctx: commands.context):
        """Force a run of the GitHub feed fetching coroutine."""
        async with ctx.typing():
            await self._github_rss.coro(self, guild_to_check=ctx.guild.id)
        return await ctx.tick()

    @_github_set.command(name="rename")
    async def _set_rename(
        self, ctx: commands.Context, user: discord.Member, old_name: str, new_name: str
    ):
        """Rename a user's GitHub RSS feed."""

        async with self.config.member(user).feeds() as feeds:
            if new_name in feeds:
                return await ctx.send("The new name is already being used!")

            if old_name not in feeds:
                return await ctx.send(NOT_FOUND)

            feeds[new_name] = feeds.pop(old_name)

        return await ctx.send("Feed successfully renamed.")

    @_github_set.command(name="channeloverride")
    async def _set_channel_override(
        self,
        ctx: commands.Context,
        user: discord.Member,
        feed_name: str,
        channel: discord.TextChannel = None,
    ):
        """Set a channel override for a feed (leave empty to reset)."""

        if channel and not (
            channel.permissions_for(ctx.guild.me).send_messages
            and channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                f"I do not have the necessary permissions (send messages & embed links) in {channel.mention}!"
            )

        async with self.config.member(user).feeds() as feeds:
            if feed_name not in feeds:
                return await ctx.send(NOT_FOUND)

            feeds[feed_name]["channel"] = channel.id if channel else None

        return await ctx.send("Feed channel successfully overridden.")

    @_github_set.command(name="listall")
    async def _list_all(self, ctx: commands.Context):
        """List all GitHub RSS feeds in the server."""

        feeds_string = ""
        async with ctx.typing():
            for member_id, member_data in (await self.config.all_members(ctx.guild)).items():
                if len(member_data["feeds"]) < 1:
                    continue
                feeds_string += f"{(await self.bot.get_or_fetch_user(member_id)).mention}: `{len(member_data['feeds'])}` feed(s) \n"
                for name, feed in member_data["feeds"].items():
                    feeds_string += f"- `{name}`: <{await self._repo_url(**feed)}>\n"
                feeds_string += "\n"

        if not feeds_string:
            return await ctx.send("No GitHub RSS feeds have been set up in this server yet.")

        embeds: typing.List[discord.Embed] = []
        for page in pagify(feeds_string, delims=["\n\n"]):
            embeds.append(discord.Embed(description=page, color=await ctx.embed_color()))

        embeds[0].title = "Server GitHub RSS Feeds"
        for embed in embeds:
            await ctx.send(embed=embed)

    @_github_set.command(name="view")
    async def _view(self, ctx: commands.Context):
        """View the server settings for GitHub."""
        settings = await self.config.guild(ctx.guild).all()

        if channel := settings["channel"]:
            if not (channel := ctx.guild.get_channel(channel)):
                channel = None

        if role := settings["role"]:
            if not (role := ctx.guild.get_role(role)):
                role = None

        return await ctx.send(
            embed=discord.Embed(
                title="GitHub Server Settings",
                description=f"**Channel:** {channel.mention if channel else None}\n**Role:** {role.mention if role else None}\n**Limit:** {settings['limit']}\n**Color:** {str(discord.Color(settings['color'])) if settings['color'] else 'Default'}\n**Short:** {settings['short']}\n**Notify:** {settings['notify']}\n**Timestamp:** {settings['timestamp']}",
                color=await ctx.embed_color(),
            )
        )

    @commands.guild_only()
    @commands.mod_or_permissions(manage_channels=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.group(name="github", aliases=["gh"])
    async def _github(self, ctx: commands.Context):
        """GitHub RSS Commit Feeds"""

    @_github.command(name="whatlinks")
    async def _what_links(self, ctx: commands.Context):
        """What links can you submit to `[p]github add`?"""
        e = discord.Embed(
            title=f"What links can you submit to `{ctx.clean_prefix}github add`?",
            color=await ctx.embed_color(),
        )
        e.add_field(
            name="Public Repositories",
            inline=False,
            value=f"Just use your repo url and specify a branch if needed. For example, ```{ctx.clean_prefix}github add TestRepo https://github.com/user/repo/ <optional_branch>```",
        )
        e.add_field(
            name="Private Repositories (This Currently Does Not Work.)",
            inline=False,
            #    value=f'Inside the "commits" page for a chosen branch, use inspect element to search for the `.atom` link in the page html. Copy the entire url (with `?token=`); do **not** specify a value for the branch parameter. For example, ```{ctx.clean_prefix}github add TestRepo https://github.com/user/repo/commits/branch.atom?token=token```',
            value="Private Repositories cannot be added via rss (or more like this cog at this moment).",
        )
        return await ctx.send(embed=e)

    @_github.command(name="get", aliases=["fetch", "test"])
    async def _get(
        self,
        ctx: commands.Context,
        entries: typing.Optional[int],
        url: str,
        branch: str = None,
    ):
        """Test out fetching a GitHub repository url."""

        if not (user_repo_branch_token := await self._parse_url_input(url, branch)):
            return await ctx.send(await self._invalid_url(ctx))

        url = await self._url_from_config(user_repo_branch_token)

        if not (parsed := await self._fetch(url, [200])):
            return await ctx.send(await self._invalid_url(ctx))

        guild_config = await self.config.guild(ctx.guild).all()

        return await ctx.send(
            embed=await self._commit_embeds(
                entries=parsed.entries[:entries] if entries else [parsed.entries[0]],
                feed_link=parsed.feed.link,
                color=guild_config["color"],
                timestamp=guild_config["timestamp"],
                short=guild_config["short"],
            )
        )

    @_github.command(name="add")
    async def _add(self, ctx: commands.Context, name: str, url: str, branch: str = ""):
        """
        Add a GitHub RSS feed to the server.

        For the accepted link formats, see `[p]github whatlinks`.
        """
        guild_config = await self.config.guild(ctx.guild).all()

        # Check role requirement
        if (role := guild_config["role"]) and role not in [r.id for r in ctx.author.roles]:
            return await ctx.send(NO_ROLE)

        # Filter name
        if len(name) > 20:
            return await ctx.send("That feed name is too long!")
        name = self._escape(name)

        # Get channel
        if not (
            (channel := guild_config["channel"]) and (channel := ctx.guild.get_channel(channel))
        ):
            return await ctx.send("The mods have not set up a GitHub RSS feed channel yet.")

        # Get RSS feed url
        if not (user_repo_branch_token := await self._parse_url_input(url, branch)):
            return await ctx.send(await self._invalid_url(ctx))
        url = await self._url_from_config(user_repo_branch_token)

        # Fetch and parse
        if not (parsed := await self._fetch(url, [200, 304])):
            return await ctx.send(await self._invalid_url(ctx))

        # Set user config
        async with self.config.member(ctx.author).feeds() as feeds:

            # Checks
            if name in feeds:
                return await ctx.send("There is already a feed with that name!")
            for n in feeds.values():
                if (
                    user_repo_branch_token["user"] == n["user"]
                    and user_repo_branch_token["repo"] == n["repo"]
                    and user_repo_branch_token["branch"] == n["branch"]
                ):
                    return await ctx.send(
                        "There is already a feed for that repository and branch!"
                    )
            if len(feeds) >= guild_config["limit"]:
                return await ctx.send(
                    f"You already have {guild_config['limit']} feeds in this server!"
                )

            feeds[name] = {
                "user": user_repo_branch_token["user"],
                "repo": user_repo_branch_token["repo"],
                "branch": user_repo_branch_token["branch"],
                "token": user_repo_branch_token["token"],
                "channel": None,
                "time": datetime.now(tz=timezone.utc).timestamp(),
            }

        # Send confirmation
        if guild_config["notify"]:
            await channel.send(
                embed=discord.Embed(
                    color=discord.Color.green(),
                    description=f"[[{user_repo_branch_token['repo']}:{(await self._parse_url(parsed.feed.link+'.atom'))[2]}]]({await self._repo_url(**user_repo_branch_token)}) has been added by {ctx.author.mention}",
                )
            )

        # Send last feed entry
        await channel.send(
            embed=await self._commit_embeds(
                entries=[parsed.entries[0]],
                feed_link=parsed.feed.link,
                color=guild_config["color"],
                timestamp=guild_config["timestamp"],
                short=guild_config["short"],
            )
        )

        return await ctx.send("Feed successfully added.")

    @_github.command(name="remove", aliases=["delete"])
    async def _remove(self, ctx: commands.Context, name: str):
        """Remove a GitHub RSS feed from the server."""

        guild_config = await self.config.guild(ctx.guild).all()
        if (role := guild_config["role"]) and role not in [r.id for r in ctx.author.roles]:
            return await ctx.send(NO_ROLE)

        name = self._escape(name)

        # Delete from config
        async with self.config.member(ctx.author).feeds() as feeds:
            if not (to_remove := feeds.get(name)):
                return await ctx.send(
                    f"There is no feed with that name! Try checking your feeds with `{ctx.clean_prefix}github list`."
                )
            del feeds[name]

        # Send confirmation
        if guild_config["notify"]:
            channel = await self._get_feed_channel(
                ctx.guild.me, guild_config["channel"], to_remove["channel"]
            )
            await channel.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"[[{to_remove['repo']}:{to_remove['branch'] or 'main'}]]({await self._repo_url(**to_remove)}) has been removed by {ctx.author.mention}",
                )
            )

        return await ctx.send("Feed successfully removed.")

    @_github.command(name="list")
    async def _list(self, ctx: commands.Context):
        """List your GitHub RSS feeds in the server."""

        guild_config = await self.config.guild(ctx.guild).all()
        if (role := guild_config["role"]) and role not in [r.id for r in ctx.author.roles]:
            return await ctx.send(NO_ROLE)

        feeds_string = ""
        async with self.config.member(ctx.author).feeds() as feeds:
            for name, feed in feeds.items():
                feeds_string += f"`{name}`: <{await self._repo_url(**feed)}>\n"

        if not feeds_string:
            return await ctx.send(
                f"No feeds found. Try adding one with `{ctx.clean_prefix}github add`!"
            )

        embeds: typing.List[discord.Embed] = []
        for page in pagify(feeds_string):
            embeds.append(discord.Embed(description=page, color=await ctx.embed_color()))

        embeds[0].title = "Your GitHub RSS Feeds"
        for embed in embeds:
            await ctx.send(embed=embed)

    @tasks.loop(minutes=3)
    async def _github_rss(self, guild_to_check=None):
        # Loop through each guild
        for guild_id, guild_config in (await self.config.all_guilds()).items():

            # Check for single guild
            if guild_to_check and guild_id != guild_to_check:
                continue

            if (
                not (guild := self.bot.get_guild(guild_id))  # Bot no longer in guild
                or not (
                    channel := self.bot.get_channel(guild_config["channel"])
                )  # Guild channel not found
                or not channel.permissions_for(
                    guild.me
                ).send_messages  # Cannot send in guild channel
                or not channel.permissions_for(
                    guild.me
                ).embed_links  # Cannot embed links in guild channel
            ):
                continue

            # Loop through each member
            async for member_id, member_data in AsyncIter(
                (await self.config.all_members(guild)).items(), steps=100
            ):

                # Loop through each feed
                for name, feed in member_data["feeds"].items():
                    url = await self._url_from_config(feed)

                    # Fetch & parse feed
                    if not (parsed := await self._fetch(url, [200])):
                        continue

                    # Find new entries
                    new_entries, new_time = await self.new_entries(parsed.entries, feed["time"])

                    # Create feed embed
                    if e := await self._commit_embeds(
                        entries=new_entries,
                        feed_link=parsed.feed.link,
                        color=guild_config["color"],
                        timestamp=guild_config["timestamp"],
                        short=guild_config["short"],
                    ):

                        # Get channel (guild vs feed override)
                        ch = channel
                        if feed["channel"]:
                            if not (
                                (ch := guild.get_channel(feed["channel"]))
                                and ch.permissions_for(guild.me).send_messages
                                and ch.permissions_for(guild.me).embed_links
                            ):
                                ch = None

                        # Send feed embed
                        if ch:
                            await ch.send(embed=e)

                        # Set time to feed config
                        async with self.config.member_from_ids(
                            guild_id, member_id
                        ).feeds() as member_feeds:
                            member_feeds[name]["time"] = new_time.timestamp()

    @_github_rss.before_loop
    async def _before_github_rss(self):
        await self.bot.wait_until_red_ready()
