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
from datetime import datetime
from typing import Final, Union

import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red

from .views import NewsLayout
from .utils import _can_post, ChannelOrThread

log = getLogger("red.maxcogs.technews")


class TechNews(commands.Cog):
    """Auto posts new articles from Wccftech to a specified channel in your server."""

    __version__: Final[str] = "1.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/technews/README.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5823741293, force_registration=True)
        default_guild = {
            "channel_id": None,
            "last_article_link": None,
        }
        self.config.register_guild(**default_guild)
        self.feed_url = "https://wccftech.com/feed/"
        self.check_feed.start()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Nothing to delete."""
        return

    async def cog_unload(self):
        self.check_feed.cancel()

    def _resolve_channel(self, guild: discord.Guild, channel_id: int) -> ChannelOrThread | None:
        """
        Resolve a stored channel_id to either a TextChannel or a Thread.
        guild.get_channel_or_thread() handles both cases in one call.
        """
        return guild.get_channel_or_thread(channel_id)

    async def _fetch_feed(self):
        """Fetch and parse the RSS feed in a thread so the event loop isn't blocked."""
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)
        if feed.bozo and not feed.entries:
            log.warning(
                f"Feed returned bozo error (no entries): {getattr(feed, 'bozo_exception', 'unknown')}"
            )
            return None
        if feed.bozo:
            log.debug(
                f"Feed has bozo flag but entries present, continuing: {getattr(feed, 'bozo_exception', 'unknown')}"
            )
        return feed

    @tasks.loop(minutes=1)
    async def check_feed(self):
        try:
            feed = await self._fetch_feed()
            if not feed or not feed.entries:
                return

            entries = sorted(
                feed.entries,
                key=lambda e: e.get("published_parsed") or datetime.min.timetuple(),
                reverse=True,
            )

            all_guild_configs = await self.config.all_guilds()
            await asyncio.gather(
                *[
                    self._process_guild(guild_id, guild_data, entries)
                    for guild_id, guild_data in all_guild_configs.items()
                ]
            )

        except Exception as e:
            log.error(f"Unexpected error in check_feed: {e}", exc_info=True)

    async def _process_guild(self, guild_id: int, guild_data: dict, entries: list):
        """Handle feed processing for a single guild."""
        channel_id = guild_data.get("channel_id")
        if not channel_id:
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = self._resolve_channel(guild, channel_id)
        if not channel:
            log.warning(f"Channel/thread {channel_id} not found in {guild.name}")
            return

        if not _can_post(guild.me, channel):
            kind = "thread" if isinstance(channel, discord.Thread) else "channel"
            log.warning(
                f"Cannot post to {kind} {getattr(channel, 'name', channel_id)} in {guild.name} "
                f"— missing permissions or thread is archived/locked."
            )
            return

        last_link = guild_data.get("last_article_link")

        # First-time setup: post the most recent article and record it
        if last_link is None:
            newest_entry = entries[0]
            newest_link = newest_entry.get("link")
            if newest_link:
                await self.post_article(channel, newest_entry)
                await self.config.guild(guild).last_article_link.set(newest_link)
                log.info(
                    f"First-time post in {guild.name}: {newest_entry.get('title', 'no title')}"
                )
            return

        new_articles = []
        for entry in entries:
            link = entry.get("link")
            if not link:
                continue
            if link == last_link:
                break
            new_articles.append(entry)

        if not new_articles:
            return

        for entry in reversed(new_articles):
            await self.post_article(channel, entry)
            await self.config.guild(guild).last_article_link.set(entry.link)
            await asyncio.sleep(1.5)

    async def post_article(self, channel: ChannelOrThread, entry):
        title = entry.get("title", "No title")
        description = entry.get("summary", "No description available.")

        if description:
            soup = BeautifulSoup(description, "html.parser")
            description = soup.get_text(separator=" ").strip()
            description = (description[:700] + "...") if len(description) > 700 else description

        link = entry.get("link", "")

        image_url = None
        if "media_content" in entry:
            for media in entry.media_content:
                if media.get("medium") == "image" and "url" in media:
                    image_url = media["url"]
                    break

        if not image_url and "content" in entry and entry.content:
            try:
                soup = BeautifulSoup(entry.content[0].value, "html.parser")
                img = soup.find("img")
                if img and img.get("src"):
                    image_url = img["src"]
            except Exception as e:
                log.error(f"Failed to parse article content for image: {e}", exc_info=True)

        view = NewsLayout(
            title=title, description=description, image_url=image_url, article_url=link
        )
        try:
            await channel.send(view=view)
        except discord.HTTPException as e:
            log.error(f"Failed sending technews article: {e}", exc_info=True)

    @check_feed.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.guild_only()
    @commands.group(name="technews")
    @commands.admin_or_permissions(manage_guild=True)
    async def technews(self, ctx):
        """Manage Wccftech news auto-posting."""

    @technews.command(name="channel")
    async def set_channel(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.Thread] = None,
    ):
        """Set or clear the channel or thread for tech news in this server.

        Supports both regular text channels and active threads.

        Note: changing the channel does not reset the last posted article.
        The bot will only post articles newer than the last one it posted.

        **Examples:**
        - `[p]technews channel #news` - post to a text channel.
        - `[p]technews channel #some-thread` - post to a thread.
        - `[p]technews channel` - disable auto-posting.
        """
        guild = ctx.guild
        if channel is None:
            await self.config.guild(guild).channel_id.clear()
            await self.config.guild(guild).last_article_link.clear()
            return await ctx.send("Tech news auto-posting has been **disabled** in this server.")

        if not _can_post(guild.me, channel):
            if isinstance(channel, discord.Thread) and channel.archived:
                return await ctx.send(
                    f"{channel.mention} is archived or locked. Please choose an active thread."
                )
            return await ctx.send(
                f"I don't have permission to send messages or embed links in {channel.mention}."
            )

        await self.config.guild(guild).channel_id.set(channel.id)
        kind = "thread" if isinstance(channel, discord.Thread) else "channel"
        await ctx.send(f"Tech news will now be posted in {channel.mention} ({kind}).")

    @technews.command(name="status")
    async def status(self, ctx):
        """Check the current tech news posting status for this server."""
        guild = ctx.guild
        channel_id = await self.config.guild(guild).channel_id()
        last_link = await self.config.guild(guild).last_article_link()

        channel = self._resolve_channel(guild, channel_id) if channel_id else None
        if channel:
            kind = " (thread)" if isinstance(channel, discord.Thread) else ""
            channel_display = f"{channel.mention}{kind}"
        else:
            channel_display = "Not set"

        await ctx.send(
            f"**Posting channel:** {channel_display}\n"
            f"**Last posted article link:** {last_link or 'None'}"
        )

    # This command is hidden and for debugging purposes only,
    # as it allows reposting the latest article regardless of whether it's new or not.
    @technews.command(name="forcepost", hidden=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def forcepost_latest(self, ctx):
        """Force post the latest article for debugging purposes."""
        channel = ctx.channel
        if not _can_post(ctx.guild.me, channel):
            return await ctx.send("I don't have permission to post in this channel or thread.")

        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)
        if not feed.entries:
            return await ctx.send("No entries in feed.")
        await self.post_article(channel, feed.entries[0])
        await ctx.send("Posted the current latest article above for debugging.")
