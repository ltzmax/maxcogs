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
from operator import itemgetter
from typing import Dict, Final, List, Optional

import aiohttp
import discord
import orjson
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, commands
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = getLogger("red.maxcogs.earthquake")


class Earthquake(commands.Cog):
    """Real-time worldwide earthquake alerts from USGS."""

    __version__: Final[str] = "1.1.0"
    __author__: Final[str] = "MAX"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=3456280979299368980690420, force_registration=True
        )
        default_settings = {
            "channel": None,
            "ping_role": None,
            "min_magnitude": 4.5,
            "safety_message": "*Monitor local news and follow instructions from emergency officials.*",
        }
        default_global = {
            "last_processed_time": 0,
        }
        self.config.register_guild(**default_settings)
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession(json_serialize=orjson.dumps)
        self.earthquake_check.start()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    def cog_unload(self):
        self.earthquake_check.cancel()
        self.bot.loop.create_task(self.session.close())

    async def get_guild_settings(self) -> Dict[int, Dict]:
        """Cache guild settings to reduce config calls."""
        return {guild.id: await self.config.guild(guild).all() for guild in self.bot.guilds}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError),
        after=lambda retry_state: logger.warning(
            f"Retrying USGS fetch (attempt {retry_state.attempt_number})"
        ),
    )
    async def fetch_earthquakes(self, min_magnitude: float = 1.0) -> List[Dict]:
        """Fetch recent earthquakes from USGS API with optional magnitude filter."""
        url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{min_magnitude}_hour.geojson"
        async with self.session.get(url, timeout=10) as response:
            if response.status != 200:
                logger.error(f"USGS API returned {response.status}")
                return []
            data = await response.json(loads=orjson.loads)
            if not isinstance(data, dict) or "features" not in data:
                logger.error("Invalid USGS API response format")
                return []
            return [
                eq
                for eq in data["features"]
                if isinstance(eq, dict) and "properties" in eq and "geometry" in eq
            ]

    def cog_unload(self):
        self.earthquake_check.cancel()
        if not self.session.closed:
            self.bot.loop.create_task(self.session.close())

    @tasks.loop(seconds=60)
    async def earthquake_check(self):
        """Check for new earthquakes and post alerts to configured guilds."""
        try:
            guild_settings = await self.get_guild_settings()
            if not guild_settings:
                return

            min_magnitudes = [
                settings["min_magnitude"]
                for settings in guild_settings.values()
                if settings.get("channel")
            ]
            fetch_magnitude = min(min_magnitudes, default=4.5) if min_magnitudes else 4.5
            earthquakes = await self.fetch_earthquakes(min_magnitude=fetch_magnitude)
            if not earthquakes:
                return

            last_processed_time = await self.config.last_processed_time()
            valid_earthquakes = [
                eq
                for eq in earthquakes
                if eq["properties"].get("time", 0) > last_processed_time
                and isinstance(eq["properties"].get("mag"), (int, float))
                and "time" in eq["properties"]
            ]
            new_earthquakes = sorted(
                valid_earthquakes, key=lambda eq: eq["properties"]["time"], reverse=True
            )
            if not new_earthquakes:
                return

            await self.config.last_processed_time.set(new_earthquakes[0]["properties"]["time"])
            for guild_id, settings in guild_settings.items():
                channel_id = settings.get("channel")
                if not channel_id:
                    continue
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue

                min_magnitude = settings["min_magnitude"]
                for earthquake in new_earthquakes:
                    magnitude = earthquake["properties"].get("mag")
                    if magnitude is None or magnitude < min_magnitude:
                        continue
                    send_time = datetime.datetime.now(datetime.timezone.utc)
                    await self.post_earthquake(guild, channel, earthquake)

        except asyncio.CancelledError:
            logger.info("Earthquake check task cancelled during shutdown")
            raise
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Error in earthquake_check: {e}", exc_info=True)

    async def post_earthquake(
        self, guild: discord.Guild, channel: discord.TextChannel, earthquake: dict
    ):
        """Post an earthquake alert to the specified channel with enhanced details."""
        properties = earthquake["properties"]
        geometry = earthquake["geometry"]
        magnitude = properties.get("mag", 0.0)
        place = properties.get("place", "Unknown location")
        time = discord.utils.format_dt(
            datetime.datetime.fromtimestamp(properties["time"] / 1000, tz=datetime.timezone.utc),
            style="F",
        )
        url = properties.get("url", "https://earthquake.usgs.gov/")
        depth = (
            round(geometry["coordinates"][2], 1)
            if geometry
            and len(geometry["coordinates"]) > 2
            and isinstance(geometry["coordinates"][2], (int, float))
            else "Unknown"
        )
        tsunami = "Yes" if properties.get("tsunami", 0) == 1 else "No"
        felt_reports = properties.get("felt")
        alert_level = properties.get("alert")

        if (
            not channel.permissions_for(guild.me).send_messages
            or not channel.permissions_for(guild.me).embed_links
        ):
            logger.warning(
                f"Missing permissions in {channel.name} ({guild.name}) for earthquake alerts"
            )
            return

        embed = discord.Embed(
            title=f"Magnitude {magnitude:.1f} Earthquake",
            description=f"**Location:** {place}\n**Time:** {time}",
            url=url,
            color=self.get_magnitude_color(magnitude),
        )

        details = []
        details.append(f"**Depth:** {depth} km" if depth != "Unknown" else "**Depth:** Unknown")
        details.append(f"**Tsunami Warning:** {tsunami}")

        # The following fields may be null or missing in some earthquakes
        # felt: This field counts user-submitted “Did You Feel It?” reports. For minor earthquakes (e.g., <M4.0) or those in remote areas, few or no reports at all may be submitted, resulting in null.
        # alert: The PAGER (Prompt Assessment of Global Earthquakes for Response) alert level is computed for significant earthquakes based on estimated impact. For minor events or those still being analyzed, it’s often null or not assessed.
        if felt_reports is not None:
            details.append(f"**Felt Reports:** {felt_reports}")
        if alert_level is not None:
            details.append(f"**Alert Level:** {alert_level.capitalize()}")

        embed.add_field(name="Details", value="\n".join(details), inline=False)
        embed.add_field(
            name="Safety Reminder",
            value=await self.config.guild(guild).safety_message(),
            inline=False,
        )
        embed.set_footer(text=f"USGS | ID: {earthquake['id']}")
        ping_role_id = await self.config.guild(guild).ping_role()
        content = (
            guild.get_role(ping_role_id).mention
            if ping_role_id and guild.get_role(ping_role_id)
            else ""
        )

        try:
            await channel.send(
                content=content, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True)
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to send earthquake alert in {guild.name}: {e}")

    @staticmethod
    def get_magnitude_color(magnitude: float) -> discord.Color:
        """Return a color based on earthquake magnitude."""
        if magnitude < 3.0:
            return discord.Color.green()
        elif magnitude < 5.0:
            return discord.Color.gold()
        elif magnitude < 7.0:
            return discord.Color.orange()
        return discord.Color.red()

    @earthquake_check.before_loop
    async def before_earthquake_check(self):
        await self.bot.wait_until_ready()

    @commands.group(aliases=["eqset", "earthquake"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def earthquakeset(self, ctx: commands.Context):
        """
        Configure earthquake alerts for this server.

        ⚠️**WARNING**⚠️
        This cog provides informational alerts only and may have 15–30 minute delays. Always prioritize local authorities for real-time safety information.
        """

    @earthquakeset.command(name="channel")
    async def set_channel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Set or clear the channel for earthquake alerts."""
        if channel:
            if (
                not channel.permissions_for(ctx.guild.me).send_messages
                or not channel.permissions_for(ctx.guild.me).embed_links
            ):
                return await ctx.send(
                    "I need `send_messages` and `embed_links` permissions in that channel."
                )
            await self.config.guild(ctx.guild).channel.set(channel.id)
            await ctx.send(f"Earthquake alerts will be sent to {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).channel.set(None)
            await ctx.send("Earthquake alerts disabled for this server.")

    @earthquakeset.command(name="role")
    @commands.bot_has_permissions(manage_roles=True)
    async def set_role(self, ctx: commands.Context, role: Optional[discord.Role]):
        """Set or clear the role to ping for earthquake alerts."""
        if role:
            if role >= ctx.guild.me.top_role:
                return await ctx.send("That role is higher than my highest role.")
            if role.is_default() or role.is_everyone() or role.name == "@here":
                return await ctx.send("Cannot set `@everyone` or `@here` as ping roles.")
            await self.config.guild(ctx.guild).ping_role.set(role.id)
            await ctx.send(f"Earthquake alerts will ping {role.mention}.")
        else:
            await self.config.guild(ctx.guild).ping_role.set(None)
            await ctx.send("Role pings disabled for earthquake alerts.")

    @earthquakeset.command(name="magnitude")
    async def set_magnitude(
        self, ctx: commands.Context, magnitude: commands.Range[float, 1.0, 10.0] = 4.5
    ):
        """
        Set the minimum magnitude for earthquake alerts.

        **Note:** Setting a lower magnitude will increase the frequency of notifications, as it includes smaller earthquakes that may not be significant in your area or other. It is recommended to set a higher threshold (e.g., 4.5 or higher) to receive alerts only for significant events.

        **Example:**
        - `[p]earthquakeset magnitude 5.0` to set the minimum magnitude to 5.0.
        - `[p]earthquakeset magnitude` to reset to the default value of 4.5.

        **Arguments:**
        - `[magnitude]`: The minimum magnitude for alerts (default is 4.5, range 1.0 to 10.0).
        """
        await self.config.guild(ctx.guild).min_magnitude.set(magnitude)
        await ctx.send(
            f"Minimum magnitude for alerts set to {magnitude:.1f}.\n-# Note: Lower values may result in frequent notifications."
        )

    @earthquakeset.command(name="safety")
    async def set_safety_message(self, ctx: commands.Context, *, message: str = None):
        """Set or clear a custom safety message for alerts."""
        if message:
            if message and len(message) > 1024:
                return await ctx.send("Safety message cannot exceed 1024 characters in length.")
            await self.config.guild(ctx.guild).safety_message.set(message)
            await ctx.send("Custom safety message set.")
        else:
            await self.config.guild(ctx.guild).safety_message.set(
                "*Monitor local news and follow instructions from emergency officials.*"
            )
            await ctx.send("Safety message reset to default.")

    @earthquakeset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def show_settings(self, ctx: commands.Context):
        """Show current earthquake alert settings."""
        channel_id = await self.config.guild(ctx.guild).channel()
        ping_role_id = await self.config.guild(ctx.guild).ping_role()
        min_magnitude = await self.config.guild(ctx.guild).min_magnitude()
        safety_message = await self.config.guild(ctx.guild).safety_message()
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        ping_role = ctx.guild.get_role(ping_role_id) if ping_role_id else None

        embed = discord.Embed(title="Earthquake Alert Settings", color=await ctx.embed_color())
        embed.add_field(
            name="Alert Channel", value=channel.mention if channel else "None", inline=False
        )
        embed.add_field(
            name="Ping Role", value=ping_role.mention if ping_role else "None", inline=False
        )
        embed.add_field(name="Minimum Magnitude", value=f"{min_magnitude:.1f}", inline=False)
        embed.add_field(name="Safety Message", value=safety_message, inline=False)
        await ctx.send(embed=embed)
