import asyncio
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Final

import aiohttp
import discord
import orjson
from redbot.core import commands
from redbot.core.utils.views import SetApiView

log = logging.getLogger("red.maxcogs.isscog")
DEORBIT_INFO = "The ISS is set to end its mission with a controlled deorbit into the Pacific Ocean’s Point Nemo around 2030-2031, as planned by NASA and its international partners."


class Iss(commands.Cog):
    """Track the International Space Station's location and details."""

    __version__: Final[str] = "1.0.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/iss.html"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        self.google_maps_api_key = None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def initialize(self):
        """Initialize the cog and fetch API tokens."""
        tokens = await self.bot.get_shared_api_tokens("google")
        self.google_maps_api_key = tokens.get("maps")

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        asyncio.create_task(self.session.close())

    async def fetch_json(self, url: str) -> dict:
        """Helper to fetch JSON with error handling."""
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return orjson.loads(await resp.read())
                log.error(f"Failed to fetch {url} - Status: {resp.status}")
                return None
        except aiohttp.ClientConnectionError as e:
            log.error(f"Connection error to {url}: {str(e)}")
            return None
        except asyncio.TimeoutError:
            log.error(f"Timeout fetching {url}")
            return None
        except orjson.JSONDecodeError as e:
            log.error(f"Failed to decode JSON from {url}: {str(e)}")
            return None

    async def fetch_map_image(self, lat: float, lon: float) -> bytes:
        """Fetch static map image from Google Maps API."""
        if not self.google_maps_api_key:
            return None

        map_url = (
            "https://maps.googleapis.com/maps/api/staticmap?"
            f"center={lat},{lon}&zoom=2&size=400x300&scale=2"
            f"&markers=color:red|{lat},{lon}"
            f"&key={self.google_maps_api_key}"
        )

        try:
            async with self.session.get(map_url) as resp:
                if resp.status == 200:
                    return await resp.read()
                log.error(f"Failed to fetch map image - Status: {resp.status}")
                return None
        except Exception as e:
            log.error(f"Error fetching map image: {str(e)}")
            return None

    @commands.group(name="iss", invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def iss_location(self, ctx: commands.Context):
        """Get the current location, crew, and detailed status of the ISS."""
        await ctx.typing()

        if self.google_maps_api_key is None:
            await self.initialize()

        wti_url = "https://api.wheretheiss.at/v1/satellites/25544?units=kilometers"
        wti_data = await self.fetch_json(wti_url)
        if not wti_data:
            return await ctx.send("Failed to fetch ISS details. Try again later!")

        lat = wti_data["latitude"]
        lon = wti_data["longitude"]
        altitude = round(wti_data["altitude"])
        velocity = round(wti_data["velocity"])
        visibility = wti_data["visibility"].capitalize()
        footprint = round(wti_data["footprint"])
        timestamp = wti_data["timestamp"]
        daynum = wti_data["daynum"]
        solar_lat = wti_data["solar_lat"]
        solar_lon = wti_data["solar_lon"]

        crew_url = "http://api.open-notify.org/astros.json"
        crew_data = await self.fetch_json(crew_url)
        if crew_data and crew_data.get("people"):
            crew_list = ", ".join([p["name"] for p in crew_data["people"] if p["craft"] == "ISS"])
        else:
            crew_list = "No crew data available"
            await ctx.send(
                "Couldn’t fetch ISS crew info due to a timeout—showing location data only."
            )

        embed = discord.Embed(
            title="International Space Station",
            description=f"Detailed real-time status of the ISS.\n{DEORBIT_INFO}\n\nLast Updated: <t:{timestamp}:R>",
            color=await ctx.embed_color(),
        )
        embed.add_field(name="Latitude:", value=f"{lat}°", inline=True)
        embed.add_field(name="Longitude:", value=f"{lon}°", inline=True)
        embed.add_field(name="Altitude:", value=f"{altitude} km", inline=True)
        embed.add_field(name="Speed:", value=f"{velocity:,} km/h", inline=True)
        embed.add_field(name="Visibility:", value=visibility, inline=True)
        embed.add_field(name="Footprint:", value=f"{footprint:,} km", inline=True)
        embed.add_field(name="Solar Latitude:", value=f"{solar_lat}°", inline=True)
        embed.add_field(name="Solar Longitude:", value=f"{solar_lon}°", inline=True)
        embed.add_field(name="Julian Day:", value=f"{daynum}", inline=True)
        embed.add_field(name="Crew Aboard:", value=crew_list or "No data", inline=False)

        # Add map image if API key is available
        if self.google_maps_api_key:
            map_image = await self.fetch_map_image(lat, lon)
            if map_image:
                embed.set_image(url="attachment://iss_map.png")

        embed.set_footer(text="All information shown is from public sources from NASA.")
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        googlemap = discord.ui.Button(
            style=style,
            label="View on Map",
            url=f"https://www.google.com/maps?q={lat},{lon}",
        )
        view.add_item(item=googlemap)

        if self.google_maps_api_key and map_image:
            file = discord.File(BytesIO(map_image), filename="iss_map.png")
            await ctx.send(embed=embed, view=view, file=file)
        else:
            await ctx.send(embed=embed, view=view)

    @commands.is_owner()
    @iss_location.command(name="setup")
    @commands.bot_has_permissions(embed_links=True)
    async def iss_setup(self, ctx: commands.Context):
        """Instructions to set up the Google Maps API key for ISS map images."""
        embed = discord.Embed(
            title="ISS Cog Setup - Google Maps API (OPTIONAL)",
            description="This is complete Optional to use and are up to yourself if you wish to show map in the embed.\nFollow these steps to enable map images in the ISS command:",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="1. Sign Up",
            value="Go to [Google Maps Platform](https://mapsplatform.google.com/) and sign in with a Google account.",
            inline=False,
        )
        embed.add_field(
            name="2. Create a Project",
            value="Click `Get Started`, create a project (e.g., `ISS Tracker`), and go to the Google Cloud Console.",
            inline=False,
        )
        embed.add_field(
            name="3. Enable APIs",
            value="In **APIs & Services > Library**, enable the **Maps Static API**.",
            inline=False,
        )
        embed.add_field(
            name="4. Get API Key",
            value="Go to **APIs & Services > Credentials**, click **Create Credentials > API Key**, and copy the key.",
            inline=False,
        )
        embed.add_field(
            name="5. Set Up Billing",
            value="In **Billing**, link a payment method. You get $200 free credit monthly (~100,000 map requests), "
            "but requests beyond that cost $2 per 1,000 (see [pricing](https://mapsplatform.google.com/pricing/)).",
            inline=False,
        )
        embed.add_field(
            name="6. Add Key to Bot",
            value=f"Run: `{ctx.prefix}set api google maps YOUR_API_KEY` (replace `YOUR_API_KEY` with your key).",
            inline=False,
        )
        embed.add_field(
            name="Notes",
            value="- Restrict the key to `Maps Static API` in Credentials for security (optional).\n"
            f"- Reload the cog with `{ctx.prefix}reload iss` after setting the key.\n"
            "- The free tier is usually enough for small bots; monitor usage in the Google Cloud Console.",
            inline=False,
        )
        embed.set_footer(
            text="Note: i have not tested the cog with api key, Please report any issue."
        )
        default_keys = {"maps": ""}
        view = SetApiView("google", default_keys)
        await ctx.send(embed=embed, view=view)
