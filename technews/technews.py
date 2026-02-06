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
import logging
from datetime import datetime
from typing import Final

import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red

from .views import NewsLayout

log = getLogger("red.maxcogs.technews")

# Small todo for later:
# - Add role ping role for when news is posted, and add that to the status command output. Also add a command to set that role.


class TechNews(commands.Cog):
    """Auto posts new articles from Wccftech to a specified channel in your server."""

    __version__: Final[str] = "1.0.0"
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

    def cog_unload(self):
        self.check_feed.cancel()

    @tasks.loop(minutes=1)
    async def check_feed(self):
        try:
            all_guild_configs = await self.config.all_guilds()
            for guild_id, guild_data in all_guild_configs.items():
                channel_id = guild_data.get("channel_id")
                if not channel_id:
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                channel = guild.get_channel(channel_id)
                if (
                    not channel
                    or not channel.permissions_for(guild.me).send_messages
                    or not channel.permissions_for(guild.me).embed_links
                ):
                    log.warning(f"no permission or channel missing in {guild.name}")
                    continue

                feed = feedparser.parse(self.feed_url)
                if feed.bozo or not feed.entries:
                    continue

                entries = sorted(
                    feed.entries,
                    key=lambda e: e.get("published_parsed") or datetime.min.timetuple(),
                    reverse=True,
                )
                last_link = guild_data.get("last_article_link")
                if last_link is None:
                    newest_entry = entries[0]
                    newest_link = newest_entry.get("link")

                    if newest_link:
                        await self.post_article(channel, newest_entry)
                        await self.config.guild(guild).last_article_link.set(newest_link)
                        log.info(
                            f"First-time post in {guild.name}: {newest_entry.get('title', 'no title')}"
                        )
                    continue

                new_articles = []
                for entry in entries:
                    link = entry.get("link")
                    if not link:
                        continue
                    if link == last_link:
                        break
                    new_articles.append(entry)

                if not new_articles:
                    continue

                for entry in reversed(new_articles):
                    await self.post_article(channel, entry)
                    await self.config.guild(guild).last_article_link.set(entry.link)
                    await asyncio.sleep(1.5)
        except discord.HTTPException as e:
            log.error(f"Failed to post TechNews article: {e}", exc_info=True)

    async def post_article(self, channel: discord.TextChannel, entry):
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
            except discord.HTTPException as e:
                log.error(f"Failed to parse article content for image: {e}", exc_info=True)

        view = NewsLayout(
            title=title, description=description, image_url=image_url, article_url=link
        )
        try:
            await channel.send(
                view=view,
            )
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
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set or clear the channel for tech news in this server."""
        guild = ctx.guild
        if channel is None:
            await self.config.guild(guild).channel_id.clear()
            await self.config.guild(guild).last_article_link.clear()
            return await ctx.send("Tech news auto-posting has been **disabled** in this server.")

        if (
            not channel.permissions_for(guild.me).send_messages
            or not channel.permissions_for(guild.me).embed_links
        ):
            log.warning(
                f"no permission to send messages or embed links in the channel {channel.name} of guild {guild.name}"
            )
            return await ctx.send("I don't have permission to send messages in that channel.")

        await self.config.guild(guild).channel_id.set(channel.id)
        await ctx.send(f"Tech news will now be posted in {channel.mention}")

    @technews.command(name="status")
    async def status(self, ctx):
        """
        Check the current tech news posting status for this server.
        """
        guild = ctx.guild
        channel_id = await self.config.guild(guild).channel_id()
        last_link = await self.config.guild(guild).last_article_link()
        channel = ctx.guild.get_channel(channel_id) if channel_id else None

        status = (
            f"**Posting channel:** {channel.mention if channel else 'Not set'}\n"
            f"**Last posted article link:** {last_link or 'None'}"
        )
        await ctx.send(status)

    # This command is hidden and for debugging purposes only,
    # as it allows reposting the latest article regardless of whether it's new or not.
    @technews.command(name="forcepost", hidden=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def forcepost_latest(self, ctx):
        """Force post the latest article for debugging purposes."""
        feed = feedparser.parse(self.feed_url)
        if not feed.entries:
            return await ctx.send("No entries in feed.")
        channel = ctx.channel
        await self.post_article(channel, feed.entries[0])
        await ctx.send("Posted the current latest article above for debugging.")
