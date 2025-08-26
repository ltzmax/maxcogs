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
import random
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Final, Optional

import aiohttp
import discord
from redbot.core import Config, bank, commands, errors
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import header, humanize_list, humanize_number, hyperlink
from redbot.core.utils.views import ConfirmView, SimpleMenu

from .bank_utils import safe_deposit, safe_withdraw
from .view import HoneycombView

log = logging.getLogger("red.maxcogs.honeycombs")


class GameState:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.active = False
        self.players = {}
        self.start_time = None
        self.end_time = None


class HoneyCombs(commands.Cog):
    """Play a game similar to Sugar Honeycombs, inspired by the Netflix series Squid Game."""

    __version__: Final[str] = "2.0.0a"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=34562809777, force_registration=True)
        self.cache = {"global": {}, "guilds": {}}
        self.game_states = {}
        self.locks = {}
        self.session = aiohttp.ClientSession()
        default_guild = {
            "players": {},
            "game_active": False,
            "default_start_image": "https://i.maxapp.tv/4c76241E.png",
            "shapes": ["circle⭕️", "triangle△", "star⭐️", "umbrella☂️"],
            "mod_only_command": False,
            "minimum_players": 2,
            "default_minutes": 10,
        }
        default_global = {
            "winning_price": 100,
            "losing_price": 100,
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.bot.loop.create_task(self.initialize_cache())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def initialize_cache(self):
        self.cache["global"] = await self.config.all()
        for guild in self.bot.guilds:
            self.cache["guilds"][guild.id] = await self.config.guild(guild).all()

    def get_guild_config(self, guild: discord.Guild):
        if guild.id not in self.cache["guilds"]:
            self.cache["guilds"][guild.id] = self.bot.loop.create_task(
                self.config.guild(guild).all()
            ).result()
        return self.cache["guilds"][guild.id]

    async def update_guild_config(self, guild: discord.Guild, key: str, value: Any):
        self.cache["guilds"][guild.id][key] = value
        await self.config.guild(guild).set_raw(key, value=value)

    async def update_global_config(self, key: str, value: Any):
        self.cache["global"][key] = value
        await self.config.set_raw(key, value=value)

    def get_game_state(self, guild: discord.Guild) -> GameState:
        if guild.id not in self.game_states:
            self.game_states[guild.id] = GameState(guild)
        return self.game_states[guild.id]

    def get_lock(self, guild: discord.Guild) -> asyncio.Lock:
        if guild.id not in self.locks:
            self.locks[guild.id] = asyncio.Lock()
        return self.locks[guild.id]

    async def cog_unload(self):
        await self.session.close()
        for guild in self.bot.guilds:
            await self.config.guild(guild).players.clear()
            await self.config.guild(guild).game_active.set(False)

    async def run_game(self, ctx: commands.Context):
        game_state = self.get_game_state(ctx.guild)
        guild_config = self.get_guild_config(ctx.guild)

        if not game_state.players:
            await ctx.send("No players joined the game.")
            game_state.active = False
            return

        default_minutes = guild_config["default_minutes"]
        game_state.end_time = datetime.now() + timedelta(minutes=default_minutes)
        end_timestamp = int(game_state.end_time.timestamp())

        embed = discord.Embed(
            title="Sugar Honeycombs Challenge",
            color=await ctx.embed_color(),
            description=f"Let the game begin!\nThe bot will finish <t:{end_timestamp}:R> to decide whether you Pass or Eliminated.\nGood luck!",
        )
        embed.add_field(name="Players:", value=len(game_state.players))
        embed.set_footer(text="I would like to expend a heartfelt welcome to you all.")
        await ctx.send(embed=embed)

        await asyncio.sleep(default_minutes * 60)

        winning_price = self.cache["global"]["winning_price"]
        losing_price = self.cache["global"]["losing_price"]
        currency_name = await bank.get_currency_name(ctx.guild)

        passed_players, failed_players = [], []
        error_messages = []

        for num, data in game_state.players.items():
            user = ctx.guild.get_member(data["user_id"])
            if user:
                shape = data["shape"]
                chance = 0.08 if shape == "umbrella☂️" else 0.2
                if random.random() < chance:
                    success, message = await safe_deposit(user, winning_price, currency_name)
                    if success:
                        passed_players.append(
                            f"Player {num}, Shape: {shape} - (User ID: {data['user_id']})"
                        )
                    else:
                        error_messages.append(message)
                        passed_players.append(
                            f"Player {num}, Shape: {shape} - (User ID: {data['user_id']}) - Deposit Failed"
                        )
                else:
                    success, message = await safe_withdraw(user, losing_price, currency_name)
                    if success:
                        failed_players.append(
                            f"Player {num}, Shape: {shape} - (User ID: {data['user_id']})"
                        )
                    else:
                        error_messages.append(message)
                        failed_players.append(
                            f"Player {num}, Shape: {shape} - (User ID: {data['user_id']}) - Withdrawal Failed"
                        )

        passed_content = (
            "Passed Players:\n" + "\n".join(passed_players)
            if passed_players
            else "No players passed."
        )
        failed_content = (
            "\n\nEliminated Players:\n" + "\n".join(failed_players)
            if failed_players
            else "\nNo players were eliminated."
        )
        error_content = "\n\nErrors:\n" + "\n".join(error_messages) if error_messages else ""
        full_content = passed_content + failed_content + error_content

        embed = discord.Embed(
            title="Here is your Results",
            color=await ctx.embed_color(),
            description="Check the attached file for the full results.",
        )
        if winning_price == 0 and losing_price == 0:
            embed.add_field(
                name="Game Entry:",
                value="This game was free to enter; no rewards were given, and no currency was lost.",
            )
        else:
            embed.add_field(
                name="Winning Price:", value=f"{humanize_number(winning_price)} {currency_name}"
            )
            embed.add_field(
                name="Losing Price:", value=f"{humanize_number(losing_price)} {currency_name}"
            )
        embed.set_footer(text="Thank you for playing!")
        file = discord.File(StringIO(full_content), filename="honeycombs_results.txt")
        await ctx.send(embed=embed, file=file)

        game_state.players.clear()
        game_state.active = False
        await self.update_guild_config(ctx.guild, "players", {})
        await self.update_guild_config(ctx.guild, "game_active", False)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def honeycombs(self, ctx: commands.Context):
        """
        Start a game of Sugar Honeycombs.

        You need at least 2 players to start the game.
        The maximum number of players is 456.
        """
        guild_config = self.get_guild_config(ctx.guild)
        game_state = self.get_game_state(ctx.guild)
        async with self.get_lock(ctx.guild):
            if game_state.active:
                return await ctx.send(
                    "A game is already in progress in this server.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                )

            if (
                guild_config["mod_only_command"]
                and not ctx.author.guild_permissions.manage_messages
            ):
                return await ctx.send(
                    "This command is only available to moderators.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                )

            game_state.active = True
            game_state.start_time = datetime.now() + timedelta(minutes=2)
            end_time = int(game_state.start_time.timestamp())
            view = HoneycombView(self, ctx.guild)

            winning_price = self.cache["global"]["winning_price"]
            losing_price = self.cache["global"]["losing_price"]
            total_price = (
                humanize_number(winning_price + losing_price)
                if (winning_price + losing_price) != 0
                else "Free"
            )
            currency_name = await bank.get_currency_name(ctx.guild)
            minimum_players = guild_config["minimum_players"]

            await view.setup(total_price, currency_name, minimum_players, end_time)
            message = await ctx.send(view=view)
            view.message = message
            await self.wait_for_players(ctx, view)

    async def wait_for_players(self, ctx: commands.Context, view: HoneycombView):
        guild_config = self.get_guild_config(ctx.guild)
        game_state = self.get_game_state(ctx.guild)
        minimum_players = guild_config["minimum_players"]
        await asyncio.sleep(120)

        if len(game_state.players) < minimum_players:
            await ctx.channel.send(
                f"Not enough players entered the game ({len(game_state.players)}/{minimum_players}). Game has been canceled."
            )
            game_state.active = False
            game_state.players.clear()
            return

        await view.on_timeout()
        await self.run_game(ctx)

    @commands.group(aliases=["squidgame", "sg"])
    @commands.guild_only()
    async def honeycombset(self, ctx: commands.Context):
        """Settings for the HoneyCombs cog."""

    @honeycombset.command(name="checklist")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def checklist(self, ctx: commands.Context):
        """
        Check the list of players in current game.

        This command will show the list of players who have joined the game along with their player numbers.
        """
        game_state = self.get_game_state(ctx.guild)
        if not game_state.players:
            return await ctx.send("No ongoing game found.")

        player_list = [f"Player {player_number}" for player_number in game_state.players.keys()]
        pages = [humanize_number(player_list[i : i + 10]) for i in range(0, len(player_list), 10)]
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @commands.admin()
    @honeycombset.command(name="reset", aliases=["clear"])
    async def reset(self, ctx: commands.Context):
        """
        Reset the game settings.

        Allow administrators to reset the game settings for the server in case of any issues or to start fresh again.
        """
        game_state = self.get_game_state(ctx.guild)
        guild_config = self.get_guild_config(ctx.guild)
        if not game_state.players and not game_state.active:
            return await ctx.send("Game settings are already reset.")

        view = ConfirmView(ctx.author, disable_buttons=True)
        message = await ctx.send("Are you sure you want to reset the game settings?", view=view)
        await view.wait()
        if view.result:
            game_state.players.clear()
            game_state.active = False
            default_guild = {
                "players": {},
                "game_active": False,
                "default_start_image": "https://i.maxapp.tv/4c76241E.png",
                "shapes": ["circle⭕️", "triangle△", "star⭐️", "umbrella☂️"],
                "mod_only_command": False,
                "minimum_players": 5,
                "default_minutes": 10,
            }
            self.cache["guilds"][ctx.guild.id] = default_guild
            await self.config.guild(ctx.guild).clear()
            await ctx.send("Game settings have been reset.")
        else:
            await ctx.send("Game settings were not reset.")

    @commands.admin()
    @honeycombset.group(name="setimage", aliases=["setimg"], invoke_without_command=True)
    async def setimage(self, ctx: commands.Context, *, image_url: Optional[str] = None):
        """
        Set the start image for the game.

        The start image is the image that will be shown when the game starts.
        You can set the image by providing a URL or by attaching an image/gif to the command.
        Only JPG / JPEG / PNG / GIF / WEBP format is supported.
        """
        await ctx.typing()
        if len(ctx.message.attachments) > 0:
            image_url = ctx.message.attachments[0].url
        elif image_url is None:
            return await ctx.send("You must provide a URL or attach an image.")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(image_url) as r:
                    if r.status != 200:
                        return await ctx.send("Failed to set the start image. URL is invalid.")
                    data = await r.read()
            except aiohttp.ClientError as e:
                return await ctx.send("Failed to set the start image. Client error.")
            except asyncio.TimeoutError as e:
                return await ctx.send("Failed to set the start image. Timeout error.")

        image_formats = ["JPG", "JPEG", "PNG", "GIF", "WEBP"]
        if not data or not any(data.startswith(bytes(f"{sig}", "utf-8")) for sig in image_formats):
            return await ctx.send(
                f"Failed to set the start image. Only {humanize_list(image_formats)} format is supported."
            )

        await self.update_guild_config(ctx.guild, "default_start_image", image_url)
        await ctx.send("The start image has been set.")

    @commands.admin()
    @setimage.command(name="clear", aliases=["reset"])
    async def setimage_clear(self, ctx: commands.Context):
        """Reset the start image to default."""
        default_image = "https://i.maxapp.tv/4c76241E.png"
        await self.update_guild_config(ctx.guild, "default_start_image", default_image)
        await ctx.send("Reset the start image.")

    @commands.admin()
    @honeycombset.command(name="modonly")
    async def mod_only(self, ctx: commands.Context, state: Optional[bool] = None):
        """
        Set whether only moderators can start the game.

        If set to True, only moderators can start the game.
        If set to False, anyone can start the game.
        """
        if state is None:
            state = not self.get_guild_config(ctx.guild)["mod_only_command"]
        await self.update_guild_config(ctx.guild, "mod_only_command", state)
        await ctx.send(f"Mod only command has been set to {state}.")

    @commands.admin()
    @honeycombset.command(name="endtime")
    async def endtime(self, ctx: commands.Context, default_minutes: commands.Range[int, 10, 720]):
        """
        Change the default minutes for when the game should end.

        The default minutes is 10.
        The maximum number of minutes is 720 (12 hours).
        """
        await self.update_guild_config(ctx.guild, "default_minutes", default_minutes)
        await ctx.send(f"The default minutes has been set to {default_minutes} minutes.")

    @commands.admin()
    @honeycombset.command(name="minimumplayers")
    async def minimum_players(
        self, ctx: commands.Context, minimum_players: commands.Range[int, 2, 15]
    ):
        """
        Set the minimum number of players needed to start a game.

        The default minimum number of players is 5.
        """
        await self.update_guild_config(ctx.guild, "minimum_players", minimum_players)
        await ctx.send(f"The minimum number of players has been set to {minimum_players}.")

    @commands.is_owner()
    @honeycombset.command(name="winningprice")
    async def winning_price(
        self, ctx: commands.Context, amount: commands.Range[int, 0, 10000000000000000000]
    ):
        """
        Set the winning price for the game.

        Set the price to 0 to disable the winning price.
        The default winning price is 100 credits.
        """
        currency_name = await bank.get_currency_name(ctx.guild)
        await self.update_global_config("winning_price", amount)
        await ctx.send(
            f"The winning price has been set to {humanize_number(amount)} {currency_name}."
        )

    @commands.is_owner()
    @honeycombset.command(name="losingprice")
    async def losing_price(
        self, ctx: commands.Context, amount: commands.Range[int, 0, 10000000000000000000]
    ):
        """
        Set the losing price for the game.

        Set the price to 0 to disable the losing price.
        The default losing price is 100 credits.
        """
        currency_name = await bank.get_currency_name(ctx.guild)
        await self.update_global_config("losing_price", amount)
        await ctx.send(
            f"The losing price has been set to {humanize_number(amount)} {currency_name}."
        )

    @commands.mod()
    @honeycombset.command(name="settings")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """View the current game settings."""
        guild_config = self.get_guild_config(ctx.guild)
        global_config = self.cache["global"]
        currency_name = await bank.get_currency_name(ctx.guild)

        embed = discord.Embed(
            title="Current Game Settings",
            description="View the current game settings.",
            color=await ctx.embed_color(),
        )
        if await self.bot.is_owner(ctx.author):
            embed.add_field(
                name="Winning Price",
                value=f"{humanize_number(global_config.get('winning_price', 0))} {currency_name}",
            )
            embed.add_field(
                name="Losing Price",
                value=f"{humanize_number(global_config.get('losing_price', 0))} {currency_name}",
            )
        embed.add_field(
            name="Mod Only Command",
            value=guild_config.get("mod_only_command", False),
            inline=False,
        )
        embed.add_field(
            name="Minimum Players", value=guild_config.get("minimum_players", 5), inline=False
        )
        embed.add_field(
            name="Default ongoing game minutes",
            value=guild_config.get("default_minutes", 10),
            inline=False,
        )
        start_image_url = guild_config.get("default_start_image", None)
        if start_image_url:
            start_image_value = f"[View Start Image]({start_image_url})"
        else:
            start_image_value = "Not set"
        embed.add_field(name="Start Image", value=start_image_value, inline=False)
        await ctx.send(embed=embed)
