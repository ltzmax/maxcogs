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

# Remove command logic originally from: https://github.com/mikeshardmind/SinbadCogs/tree/v3/messagebox
# Speed test logic from https://github.com/PhasecoreX/PCXCogs/tree/master/netspeed

import asyncio
import concurrent
import logging
import time

import discord
import speedtest
import random
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import humanize_list

old_ping = None
log = logging.getLogger("red.maxcogs.customping")


async def random_custom_gif(ctx: commands.Context):
    gifs = await ctx.cog.config.ping_custom_gifs()
    if gifs:
        return random.choice(gifs)
    else:
        await ctx.cog.config.ping_gifs.set(False)
    return None


class CustomPing(commands.Cog):
    """A more information rich ping message."""

    __version__ = "1.0.4"
    __author__ = humanize_list(["phenom4n4n", "ltzmax"])
    __docs__ = "https://maxcogs.gitbook.io/maxcogs/cogs/customping"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=325236743863625234572,
            force_registration=True,
        )
        default_global = {
            "host_latency": True,
            "ping_gifs": False,
            "ping_custom_gifs": [],
        }
        self.config.register_global(**default_global)
        self.settings = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def cog_load(self):
        self.settings = await self.config.all()

    async def red_delete_data_for_user(self, **kwargs):
        return

    def cog_unload(self):
        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except:
                pass
            self.bot.add_command(old_ping)

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.group(invoke_without_command=True)
    async def ping(self, ctx):
        """View bot latency."""
        start = time.monotonic()
        ref = ctx.message.to_reference(fail_if_not_exists=False)
        message = await ctx.send("Pinging...", reference=ref)
        end = time.monotonic()
        totalPing = round((end - start) * 1000, 2)
        e = discord.Embed(
            title="Pinging..", description=f"`{'Overall Latency':<16}`:{totalPing}ms"
        )
        await asyncio.sleep(0.25)
        try:
            await message.edit(content=None, embed=e)
        except discord.NotFound:
            return

        botPing = round(self.bot.latency * 1000, 2)
        e.description = e.description + f"\n`{'Discord WS':<16}`:{botPing}ms"
        await asyncio.sleep(0.25)

        averagePing = (botPing + totalPing) / 2
        if averagePing >= 1000:
            color = discord.Colour.red()
        elif averagePing >= 200:
            color = discord.Colour.orange()
        else:
            color = discord.Colour.green()

        e.set_image(url=await random_custom_gif(ctx))

        if not self.settings["host_latency"]:
            e.title = "Pong!"

        e.color = color
        try:
            await message.edit(embed=e)
        except discord.NotFound:
            return
        if not self.settings["host_latency"]:
            return

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        try:
            s = speedtest.Speedtest(secure=True)
            await loop.run_in_executor(executor, s.get_servers)
            await loop.run_in_executor(executor, s.get_best_server)
        except Exception as exc:
            log.exception(
                "An exception occured while fetching host latency.", exc_info=exc
            )
            host_latency = "`Failed`"
        else:
            result = s.results.dict()
            host_latency = round(result["ping"], 2)
            host_latency = f"{host_latency}ms"

        e.title = "Pong!"
        e.description = e.description + f"\n`{'Host Latency':<16}`:{host_latency}"
        await asyncio.sleep(0.25)
        try:
            await message.edit(embed=e)
        except discord.NotFound:
            return

    @ping.command()
    async def moreinfo(self, ctx: commands.Context):
        """Ping with additional latency stastics."""
        now = discord.utils.utcnow().timestamp()
        receival_ping = round((now - ctx.message.created_at.timestamp()) * 1000, 2)

        e = discord.Embed(
            title="Pinging..",
            description=f"`{'Receival Latency':<13}`:{receival_ping}ms",
        )

        send_start = time.monotonic()
        message = await ctx.send(embed=e)
        send_end = time.monotonic()
        send_ping = round((send_end - send_start) * 1000, 2)
        e.description += f"\n`{'Send Latency':<16}`:{send_ping}ms"
        await asyncio.sleep(0.25)

        edit_start = time.monotonic()
        try:
            await message.edit(embed=e)
        except discord.NotFound:
            return
        edit_end = time.monotonic()
        edit_ping = round((edit_end - edit_start) * 1000, 2)
        e.description += f"\n`{'Edit Latency':<16}`:{edit_ping}ms"

        average_ping = (receival_ping + send_ping + edit_ping) / 3
        if average_ping >= 1000:
            color = discord.Colour.red()
        elif average_ping >= 200:
            color = discord.Colour.orange()
        else:
            color = discord.Colour.green()

        e.color = color
        e.title = "Pong!"

        await asyncio.sleep(0.25)
        try:
            await message.edit(embed=e)
        except discord.NotFound:
            return

    @ping.command()
    async def shards(self, ctx: commands.Context):
        """View latency for all shards."""
        description = []
        latencies = []
        for shard_id, shard in self.bot.shards.items():
            latency = round(shard.latency * 1000, 2)
            latencies.append(latency)
            description.append(f"#{shard_id}: {latency}ms")
        average_ping = sum(latencies) / len(latencies)
        if average_ping >= 1000:
            color = discord.Colour.red()
        elif average_ping >= 200:
            color = discord.Colour.orange()
        else:
            color = discord.Colour.green()
        e = discord.Embed(
            color=color, title="Shard Pings", description="\n".join(description)
        )
        e.set_footer(text=f"Average: {round(average_ping, 2)}ms")
        await ctx.send(embed=e)

    @commands.is_owner()
    @commands.group()
    async def pingset(self, ctx: commands.Context):
        """Manage CustomPing settings."""

    @pingset.command(name="hostlatency")
    async def pingset_hostlatency(
        self, ctx: commands.Context, true_or_false: bool = None
    ):
        """Toggle displaying host latency on the ping command."""
        target_state = (
            true_or_false
            if true_or_false is not None
            else not (await self.config.host_latency())
        )
        await self.config.host_latency.set(target_state)
        self.settings["host_latency"] = target_state
        word = " " if target_state else " not "
        await ctx.send(
            f"Host latency will{word}be displayed on the `{ctx.clean_prefix}ping` command."
        )

    @pingset.command(name="addgif")
    async def pingset_addgif(self, ctx: commands.Context, gif_url: str):
        """Add a custom gif to the ping command."""
        async with self.config.ping_custom_gifs() as gifs:
            gifs.append(gif_url)
        await ctx.send("Custom gif added.")

    @pingset.command(name="removegif")
    async def pingset_removegif(self, ctx: commands.Context, gif_url: str):
        """Remove a custom gif from the ping command."""
        async with self.config.ping_custom_gifs() as gifs:
            gifs.remove(gif_url)
        await ctx.send("Custom gif removed.")

    @pingset.command(name="listgifs")
    async def pingset_listgifs(self, ctx: commands.Context):
        """List all custom gifs."""
        gifs = await self.config.ping_custom_gifs()
        if not gifs:
            return await ctx.send("No custom gifs have been added.")
        await ctx.send(
            f"Custom gifs:\n{humanize_list(gifs)}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @pingset.command(name="cleargifs")
    async def pingset_cleargifs(self, ctx: commands.Context):
        """Clear all custom gifs."""
        await self.config.ping_custom_gifs.set([])
        await ctx.send("Custom gifs cleared.")

    @pingset.command(name="togglegifs")
    async def pingset_togglegifs(
        self, ctx: commands.Context, true_or_false: bool = None
    ):
        """Toggle displaying gifs on the ping command."""
        if not await self.config.ping_custom_gifs():
            return await ctx.send(
                "You must add a custom gif before you can toggle gifs."
            )
        target_state = (
            true_or_false
            if true_or_false is not None
            else not (await self.config.ping_gifs())
        )
        await self.config.ping_gifs.set(target_state)
        self.settings["ping_gifs"] = target_state
        word = " " if target_state else " not "
        await ctx.send(
            f"Gifs will{word}be displayed on the `{ctx.clean_prefix}ping` command."
        )

    @pingset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def pingset_settings(self, ctx: commands.Context):
        """View current settings."""
        data = await self.config.all()
        host_latency = data["host_latency"]
        ping_gifs = data["ping_gifs"]
        e = discord.Embed(
            title="CustomPing Settings",
            description="""
            **Host Latency**: {host_latency}
            **Gifs**: {ping_gifs}
            """.format(
                host_latency=host_latency,
                ping_gifs=ping_gifs,
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=e)


async def setup(bot):
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)

    cog = CustomPing(bot)
    await bot.add_cog(cog)
