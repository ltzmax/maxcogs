"""
MIT License

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

import asyncio
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp
import discord
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, app_commands, commands
from redbot.core.utils.views import SetApiView, SimpleMenu

from .tmdb_utils import PREDEFINED_CHANNELS, fetch_tmdb, person_embed, search_and_display

logger = getLogger("red.maxcogs.themoviedb")


class TheMovieDB(commands.Cog):
    """
    Search for informations of movies and TV shows from themoviedb.org.
    """

    __author__ = "MAX"
    __version__ = "2.3.0"
    __docs__ = "https://github.com/ltzmax/maxcogs/tree/master/themoviedb/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config: Config = Config.get_conf(
            self, identifier=1111238727729911, force_registration=True
        )
        default_guild = {
            "notification_channel": None,
            "channels_status": {},
            "ping_role": None,
            "use_webhook": True,
        }
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.check_for_new_trailers.start()

    async def cog_unload(self) -> None:
        """Clean up on cog unload."""
        self.check_for_new_trailers.cancel()
        if hasattr(self, "session") and self.session:
            if not self.session.closed:
                try:
                    await asyncio.wait_for(self.session.close(), timeout=5.0)
                    logger.info(f"Session closed successfully: {self.session.closed}")
                except asyncio.TimeoutError:
                    logger.warning("Session close timed out—forcing shutdown.")
                except discord.HTTPException as e:
                    logger.error(f"Error closing session: {e}", exc_info=True)
            else:
                logger.info("Session already closed.")
        logger.info("Cog unload complete.")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete."""
        return

    async def fetch_feed(self, youtube_channel_id: str) -> str | None:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={youtube_channel_id}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(
                        f"Failed to fetch feed for channel {youtube_channel_id}: HTTP {response.status}"
                    )
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching feed for channel {youtube_channel_id}: {e}")
            return None

    async def get_or_create_webhook(self, channel: discord.TextChannel) -> discord.Webhook | None:
        """Get or create a webhook for trailer notifications in the channel."""
        our_name = "Trailer Notifications"
        try:
            webhooks = await channel.webhooks()
        except (discord.Forbidden, discord.HTTPException):
            logger.error(f"Failed to fetch webhooks in {channel.name} ({channel.guild.name})")
            return None

        for wh in webhooks:
            if wh.name == our_name and wh.user == self.bot.user:
                return wh

        try:
            wh = await channel.create_webhook(name=our_name)
            return wh
        except discord.HTTPException as e:
            if e.code == 30007:  # Maximum number of webhooks reached
                await self.config.guild(channel.guild).use_webhook.set(False)
                logger.warning(
                    f"Maximum number of webhooks reached in {channel.name} ({channel.guild.name}). Disabling webhook use."
                )
            else:
                logger.error(
                    f"Failed to create webhook in {channel.name} ({channel.guild.name}): {e}"
                )
            return None
        except discord.Forbidden as e:
            logger.error(
                f"Permission denied to create webhook in {channel.name} ({channel.guild.name}): {e}"
            )
            return None

    async def check_trailers(self, guild: discord.Guild) -> None:
        guild_data = await self.config.guild(guild).all()
        notification_channel_id = guild_data.get("notification_channel")
        if not notification_channel_id:
            return

        channel_to_post = guild.get_channel(notification_channel_id)
        if not channel_to_post:
            return

        perms = channel_to_post.permissions_for(guild.me)
        if not perms.send_messages:
            logger.warning(
                f"Bot does not have send_messages permission in {channel_to_post.name} in guild {guild.name}"
            )
            return

        use_webhook = guild_data.get("use_webhook", False)
        webhook = None
        if use_webhook and perms.manage_webhooks:
            webhook = await self.get_or_create_webhook(channel_to_post)

        ping_role_id = guild_data.get("ping_role")
        ping_role = guild.get_role(ping_role_id) if ping_role_id else None
        ping_mention = f"{ping_role.mention} " if ping_role else ""
        channels_status = guild_data.get("channels_status", {})

        enabled_channels = [
            (key, details)
            for key, details in PREDEFINED_CHANNELS.items()
            if channels_status.get(key, {}).get("enabled", False)
        ]
        if not enabled_channels:
            return

        sem = asyncio.Semaphore(5)

        async def fetch_with_sem(key, details):
            async with sem:
                return key, details, await self.fetch_feed(details["id"])

        fetch_tasks = [fetch_with_sem(key, details) for key, details in enabled_channels]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        updates = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Fetch error: {result}")
                continue

            key, details, feed_data = result
            if not feed_data:
                failure_count = channels_status.get(key, {}).get("failure_count", 0) + 1
                updates[key] = {"enabled": failure_count < 3, "failure_count": failure_count}
                if failure_count >= 3:
                    disable_message = (
                        f"Disabled notifications for **{details['name']}** due to repeated failures (HTTP 404).\n"
                        "Please contact the bot owner to resolve this issue."
                    )
                    try:
                        if webhook:
                            await webhook.send(
                                content=disable_message,
                                username=self.bot.user.name,
                                avatar_url=(
                                    str(self.bot.user.avatar) if self.bot.user.avatar else None
                                ),
                                allowed_mentions=discord.AllowedMentions(roles=True),
                            )
                        else:
                            await channel_to_post.send(disable_message)
                    except (discord.Forbidden, discord.HTTPException) as e:
                        logger.error(
                            f"Failed to send disable message to {channel_to_post.name} in {guild.name}: {e}"
                        )
                    continue
            else:
                updates[key] = {"enabled": True, "failure_count": 0}

            try:
                root = ET.fromstring(feed_data)
                entries = root.findall("{http://www.w3.org/2005/Atom}entry")
                if not entries:
                    logger.debug(f"No entries in feed for {details['name']}")
                    continue

                latest_video = entries[0]
                video_id_elem = latest_video.find(
                    "{http://www.youtube.com/xml/schemas/2015}videoId"
                )
                if video_id_elem is None:
                    logger.warning(f"No video ID in latest entry for {details['name']}")
                    continue

                video_id = video_id_elem.text
                last_video_id = channels_status.get(key, {}).get("last_video_id")

                published_elem = latest_video.find("{http://www.w3.org/2005/Atom}published")
                if published_elem is None:
                    logger.warning(f"No published date in latest entry for {details['name']}")
                    continue

                published_str = published_elem.text.replace("Z", "+00:00")
                published_dt = datetime.datetime.fromisoformat(published_str)
                published_ts = published_dt.timestamp()
                last_published_ts = channels_status.get(key, {}).get("last_published_ts", 0)

                if last_published_ts == 0:
                    updates[key] = {"last_published_ts": published_ts, "last_video_id": video_id}
                    continue

                if published_ts <= last_published_ts or video_id == last_video_id:
                    logger.debug(f"No new video for {details['name']}")
                    continue

                video_url_elem = latest_video.find("{http://www.w3.org/2005/Atom}link")
                if video_url_elem is None:
                    logger.warning(f"No link in latest entry for {details['name']}")
                    continue

                video_url = video_url_elem.attrib["href"]
                # Skip YouTube Shorts
                if "/shorts/" in video_url:
                    continue

                updates[key] = {"last_published_ts": published_ts, "last_video_id": video_id}
                author_name = (
                    root.findtext(
                        "{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name"
                    )
                    or details["name"]
                )
                message = (
                    f"{ping_mention}**{author_name}** has uploaded a new video!\n{video_url}"
                ).strip()
                try:
                    if webhook:
                        await webhook.send(
                            content=message,
                            username=self.bot.user.name,
                            avatar_url=str(self.bot.user.avatar) if self.bot.user.avatar else None,
                            allowed_mentions=discord.AllowedMentions(roles=True),
                        )
                    else:
                        await channel_to_post.send(
                            content=message,
                            allowed_mentions=discord.AllowedMentions(roles=True),
                        )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"Failed to send notification to {channel_to_post.name} in {guild.name}: {e}"
                    )
            except ET.ParseError as e:
                logger.error(f"Failed to parse RSS feed for {details['name']}: {e}")
                continue
            except discord.HTTPException as e:
                logger.error(f"Unexpected error processing feed for {details['name']}: {e}")
                continue

        if updates:
            try:
                async with self.config.guild(guild).channels_status() as statuses:
                    for key, data in updates.items():
                        if key not in statuses:
                            statuses[key] = {"enabled": True, "failure_count": 0}
                        statuses[key] |= data
            except discord.HTTPException as e:
                logger.error(f"Failed to update channels_status for guild {guild.id}: {e}")

    @tasks.loop(minutes=5)
    async def check_for_new_trailers(self) -> None:
        all_guilds = await self.config.all_guilds()
        for guild_id in all_guilds:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            guild_data = all_guilds[guild_id]
            notification_channel_id = guild_data.get("notification_channel")
            if not notification_channel_id:
                continue
            channel = guild.get_channel(notification_channel_id)
            if not channel:
                continue

            perms = channel.permissions_for(guild.me)
            if not perms.send_messages or not perms.manage_webhooks:
                logger.warning(
                    f"Bot does not have send_messages or manage_webhooks permission in {channel.name} in guild {guild.name} (ID: {guild.id})"
                )
                continue

            await self.check_trailers(guild)

    @check_for_new_trailers.before_loop
    async def before_check_for_new_trailers(self) -> None:
        await self.bot.wait_until_ready()

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def tmdbset(self, ctx: commands.Context):
        """
        Configure TheMovieDB cog settings.
        """

    @tmdbset.command(name="webhook")
    async def set_webhook(self, ctx: commands.Context, use_webhook: bool) -> None:
        """
        Enable or disable the use of webhooks for trailer notifications.
        """
        if not ctx.guild.me.guild_permissions.manage_webhooks:
            return await ctx.send("I need the `Manage Webhooks` permission to use webhooks.")

        webhook_status = "enabled" if use_webhook else "disabled"
        await self.config.guild(ctx.guild).use_webhook.set(use_webhook)
        await ctx.send(f"Webhook usage for trailer notifications has been {webhook_status}.")

    @tmdbset.command(name="channel")
    async def set_channel(
        self, ctx: commands.Context, channel: discord.TextChannel | None = None
    ) -> None:
        """Set or unset the channel for video notifications."""
        guild_data = await self.config.guild(ctx.guild).all()
        channels_status = guild_data.get("channels_status", {})

        any_enabled = any(status.get("enabled", False) for status in channels_status.values())

        if channel:
            if not channel.permissions_for(ctx.me).send_messages:
                return await ctx.send(
                    f"I don't have permission to send messages in {channel.mention}. Please choose another channel or fix permissions."
                )

            await self.config.guild(ctx.guild).notification_channel.set(channel.id)
            msg = f"Video notifications will now be sent to {channel.mention}."
            if not any_enabled:
                msg += (
                    f"\nPlease enable at least one studio with `{ctx.clean_prefix}tmdbset toggle <studio_name>`.\n"
                    f"Use `{ctx.clean_prefix}tmdbset list` to see available studios."
                )
            await ctx.send(msg)
        else:
            await self.config.guild(ctx.guild).notification_channel.set(None)
            msg = "video notifications have been disabled."
            if any_enabled:
                msg += "\n(Any enabled studios will remain configured but won't notify until a channel is set again.)"
            await ctx.send(msg)

    @tmdbset.command(name="toggle")
    async def toggle_channel(self, ctx: commands.Context, *channel_names: str) -> None:
        """
        Toggle notifications for one or more studios, or all studios.

        Use `[p]tmdbset list` to see available studios. Pass 'all' to toggle all studios,
        or specify multiple studio names to toggle them at once.

        **NOTE**:
        Videos may include more than just trailers from movies or TV shows, they can also feature behind-the-scenes content or interviews. This is intended to keep you updated on new content from your favorite studios and channels.

        **Examples**:
        - `[p]tmdbset toggle marvel`
        - `[p]tmdbset toggle netflix sony amazon`
        - `[p]tmdbset toggle all`

        **Arguments**:
        - `<channel_names>`: One or more studio names to toggle, or 'all' to toggle all studios.
        """
        if not channel_names:
            return await ctx.send(
                f"Please provide at least one studio name or `all`. Use `{ctx.clean_prefix}tmdbset list` to see options."
            )

        if "all" in [name.lower() for name in channel_names]:
            if len(channel_names) > 1:
                return await ctx.send(
                    f"Cannot combine 'all' with specific studio names. Use `{ctx.clean_prefix}tmdbset toggle all` or list specific studios."
                )

            channel_keys = list(PREDEFINED_CHANNELS.keys())
        else:
            channel_keys = [name.lower() for name in channel_names]

        valid_toggles = []
        invalid_names = []
        async with self.config.guild(ctx.guild).channels_status() as statuses:
            for key in channel_keys:
                if key not in PREDEFINED_CHANNELS:
                    invalid_names.append(key)
                    continue
                if key not in statuses:
                    statuses[key] = {"enabled": True, "failure_count": 0}
                else:
                    statuses[key]["enabled"] = not statuses[key].get("enabled", False)
                    statuses[key]["failure_count"] = 0
                status = "enabled" if statuses[key]["enabled"] else "disabled"
                valid_toggles.append(f"{PREDEFINED_CHANNELS[key]['name']} (`{key}`): **{status}**")

        response = ""
        if valid_toggles:
            response += (
                "Toggled notifications:\n"
                + "\n".join(f"- {toggle}" for toggle in valid_toggles)
                + "\n"
            )
        if invalid_names:
            response += (
                "\nInvalid studio names: "
                + ", ".join(f"`{name}`" for name in invalid_names)
                + f". Use `{ctx.clean_prefix}tmdbset list` to see options."
            )

        if response:
            await ctx.send(response.strip())
        else:
            await ctx.send(
                f"No valid studios toggled. Use `{ctx.clean_prefix}tmdbset list` to see options."
            )

    @tmdbset.command(name="list", aliases=["settings"])
    async def list_channels(self, ctx: commands.Context) -> None:
        """List all available studios and their notification status."""
        guild_data = await self.config.guild(ctx.guild).all()
        notification_channel_id = guild_data.get("notification_channel")
        ping_role_id = guild_data.get("ping_role")
        webhook_status = guild_data.get("use_webhook")

        if notification_channel_id:
            channel = ctx.guild.get_channel(notification_channel_id)
            msg = f"Notification Channel: {channel.mention if channel else 'Not Set'}\n"
        else:
            msg = "Notification Channel: Not Set\n"

        if ping_role_id:
            role = ctx.guild.get_role(ping_role_id)
            msg += f"Ping Role: {role.mention if role else 'Not Set'}\n"
        else:
            msg += "Ping Role: Not Set\n"

        msg += f"Use Webhook: {'Enabled' if webhook_status else 'Disabled'}\n"

        msg += "\nAvailable Studios:\n"
        channels_status = guild_data.get("channels_status", {})
        for key, details in PREDEFINED_CHANNELS.items():
            status = (
                "Enabled" if channels_status.get(key, {}).get("enabled", False) else "Disabled"
            )
            msg += f"- {details['name']} (`{key}`): **{status}**\n"

        pages = []
        current_page = ""
        for line in msg.splitlines(keepends=True):
            if len(current_page) + len(line) > 1900:
                pages.append(current_page)
                current_page = line
            else:
                current_page += line
        if current_page:
            pages.append(current_page)
        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @tmdbset.command(name="role")
    async def set_role(self, ctx: commands.Context, role: discord.Role | None = None) -> None:
        """Set or unset a role to ping for new video notifications."""
        if role:
            if role >= ctx.guild.me.top_role:
                return await ctx.send("That role is higher than my highest role.")
            if role.is_default() or role.is_everyone() or role.name == "@here":
                return await ctx.send("Cannot set `@everyone` or `@here` as ping roles.")
            await self.config.guild(ctx.guild).ping_role.set(role.id)
            await ctx.send(f"New video notifications will now ping {role.mention}.")
        else:
            await self.config.guild(ctx.guild).ping_role.set(None)
            await ctx.send("Ping role for video notifications has been disabled ")

    @commands.is_owner()
    @tmdbset.command(name="creds")
    @commands.bot_has_permissions(embed_links=True)
    async def tmdbset_creds(self, ctx: commands.Context):
        """
        Guide to setting up the TMDB API key.

        This command will give you information on how to set up the API key.
        """
        msg = (
            "To use this cog, you need to get an API key from TheMovieDB.org.\n"
            "Here's how to do it:\n"
            "1. **Create an account**: Go to <https://www.themoviedb.org/signup> and sign up for an account.\n"
            "2. **Request a Developer API key**: Go to <https://www.themoviedb.org/settings/api> "
            "and select the Developer option. Fill out the form and wait for them to approve your request.\n"
            "3. **Get your API key**: Once approved, you will get your API key. Copy it and use the command:\n"
            f"`{ctx.clean_prefix}set api tmdb api_key <your api key>`\n"
            "The API key is used to fetch information about movies and TV shows from TheMovieDB.org."
        )
        default_keys = {"api_key": ""}
        view = SetApiView("tmdb", default_keys)
        embed = discord.Embed(
            title="TMDB API Key",
            description=msg,
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="You can also set your API key by using the button.")
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(aliases=["movies"])
    @app_commands.describe(query="The movie you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def movie(self, ctx: commands.Context, *, query: str):
        """Search for a movie.

        You can write the full name of the movie to get more accurate results.

        **Examples:**
        - `[p]movie the dark knight`
        - `[p]movie the lord of the rings`

        **Arguments:**
        - `<query>` - The movie you want to search for.
        """
        token = await ctx.bot.get_shared_api_tokens("tmdb")
        if token.get("api_key") is None:
            return await ctx.send(
                "The bot owner has not set up the API key for TheMovieDB. "
                "Please ask them to set it up."
            )
        await search_and_display(ctx, query, "movie")

    @movie.autocomplete("query")
    async def movie_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete suggestions for movie search, sorted by release date."""
        if not current:
            return []

        token = await self.bot.get_shared_api_tokens("tmdb")
        api_key = token.get("api_key")
        if not api_key:
            return []

        include_adult = str(getattr(interaction.channel, "nsfw", False)).lower()
        encoded_query = urllib.parse.quote(current)
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={encoded_query}&page=1&include_adult={include_adult}"
        async with aiohttp.ClientSession() as session:
            data = await fetch_tmdb(url, session)

        if not data or "results" not in data:
            return []

        def get_date(item: dict[str, Any]) -> float:
            date_str = item.get("release_date", "")
            if not date_str or not isinstance(date_str, str) or len(date_str) < 4:
                return float("-inf")
            try:
                year = int(date_str[:4])
                return datetime(year=year, month=1, day=1).timestamp()
            except (ValueError, TypeError):
                return float("-inf")

        sorted_results = sorted(data.get("results", []), key=get_date, reverse=True)

        return [
            app_commands.Choice(
                name=f"{result.get('title', 'Unknown')} ({result.get('release_date', '')[:4] or 'N/A'})",
                value=result.get("title", "Unknown"),
            )
            for result in sorted_results[:25]
        ]

    @commands.hybrid_command(aliases=["tv"])
    @app_commands.describe(query="The series you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def tvshow(self, ctx: commands.Context, *, query: str):
        """Search for a TV show.

        You can write the full name of the TV show to get more accurate results.

        **Examples:**
        - `[p]tv the office`
        - `[p]tv game of thrones`

        **Arguments:**
        - `<query>` - The TV show you want to search for.
        """
        token = await ctx.bot.get_shared_api_tokens("tmdb")
        if token.get("api_key") is None:
            return await ctx.send(
                "The bot owner has not set up the API key for TheMovieDB. "
                "Please ask them to set it up."
            )
        await search_and_display(ctx, query, "tv")

    @tvshow.autocomplete("query")
    async def tvshow_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete suggestions for TV show search, sorted by first air date."""
        if not current:
            return []

        token = await self.bot.get_shared_api_tokens("tmdb")
        api_key = token.get("api_key")
        if not api_key:
            return []

        include_adult = str(getattr(interaction.channel, "nsfw", False)).lower()
        encoded_query = urllib.parse.quote(current)
        url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={encoded_query}&page=1&include_adult={include_adult}"
        async with aiohttp.ClientSession() as session:
            data = await fetch_tmdb(url, session)

        if not data or "results" not in data:
            return []

        def get_date(item: dict[str, Any]) -> float:
            date_str = item.get("first_air_date", "")
            if not date_str or not isinstance(date_str, str) or len(date_str) < 4:
                return float("-inf")
            try:
                year = int(date_str[:4])
                return datetime(year=year, month=1, day=1).timestamp()
            except (ValueError, TypeError):
                return float("-inf")

        sorted_results = sorted(data.get("results", []), key=get_date, reverse=True)

        return [
            app_commands.Choice(
                name=f"{result.get('name', 'Unknown')} ({result.get('first_air_date', '')[:4] or 'N/A'})",
                value=result.get("name", "Unknown"),
            )
            for result in sorted_results[:25]
        ]

    @commands.hybrid_command()
    @app_commands.describe(query="The person you want to search for.")
    @commands.bot_has_permissions(embed_links=True)
    async def person(self, ctx: commands.Context, *, query: str):
        """Search for a person.

        You can write the full name of the person to get more accurate results.

        **Examples:**
        - `[p]person arthur`
        - `[p]person johnny depp`

        **Arguments:**
        - `<query>` - The person you want to search for.
        """
        token = await ctx.bot.get_shared_api_tokens("tmdb")
        if token.get("api_key") is None:
            return await ctx.send(
                "The bot owner has not set up the API key for TheMovieDB. "
                "Please ask them to set it up."
            )
        await person_embed(ctx, query)
