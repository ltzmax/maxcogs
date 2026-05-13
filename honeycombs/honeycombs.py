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
import random
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Final, cast

import aiohttp
import discord
from red_commons.logging import getLogger
from redbot.core import Config, bank, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu

from .view import HoneycombView


log = getLogger("red.maxcogs.honeycombs")

MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "JPEG/JPG",
    b"\x89PNG": "PNG",
    b"GIF8": "GIF",
    b"RIFF": "WEBP",
}

DEFAULT_SHAPE_ODDS: dict[str, int] = {
    "circle": 20,
    "triangle": 20,
    "star": 20,
    "umbrella": 8,
}


class GameState:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.active = False
        self.players: dict[int, dict[str, Any]] = {}
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None


class HoneyCombs(commands.Cog):
    """Play Honeycombs."""

    __version__: Final[str] = "2.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/HoneyCombs.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=34562809777, force_registration=True)
        self.cache = {"global": {}, "guilds": {}}
        self.game_states = {}
        self.locks = {}
        self._game_tasks: dict[int, asyncio.Task] = {}
        self.session = aiohttp.ClientSession()
        default_guild = {
            "players": {},
            "game_active": False,
            "default_start_image": None,
            "shapes": ["circle⭕️", "triangle△", "star⭐️", "umbrella☂️"],
            "shape_odds": DEFAULT_SHAPE_ODDS,
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
        await self.bot.wait_until_ready()
        self.cache["global"] = await self.config.all()
        for guild in self.bot.guilds:
            self.cache["guilds"][guild.id] = await self.config.guild(guild).all()

    async def get_guild_config(self, guild: discord.Guild):
        if guild.id not in self.cache["guilds"]:
            self.cache["guilds"][guild.id] = await self.config.guild(guild).all()
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
        for guild_id, task in list(self._game_tasks.items()):
            task.cancel()
            game_state = self.game_states.get(guild_id)
            if game_state and game_state.active:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    await self.config.guild(guild).players.clear()
                    await self.config.guild(guild).game_active.set(False)
        self._game_tasks.clear()

    async def run_game(self, ctx: commands.Context):
        game_state = self.get_game_state(ctx.guild)
        guild_config = await self.get_guild_config(ctx.guild)

        if not game_state.players:
            await ctx.send("No players joined the game.")
            game_state.active = False
            return

        default_minutes = guild_config["default_minutes"]
        game_state.end_time = datetime.now(timezone.utc) + timedelta(minutes=default_minutes)
        end_timestamp = int(game_state.end_time.timestamp())

        embed = discord.Embed(
            title="Honeycombs Challenge",
            color=await ctx.embed_color(),
            description=(
                f"Let the game begin!\n"
                f"The bot will finish <t:{end_timestamp}:R> to decide whether you Pass or are Eliminated.\n"
                f"Good luck!"
            ),
        )
        embed.add_field(name="Players:", value=len(game_state.players))
        await ctx.send(embed=embed)

        await asyncio.sleep(default_minutes * 60)

        winning_price = self.cache["global"]["winning_price"]
        losing_price = self.cache["global"]["losing_price"]
        currency_name = await bank.get_currency_name(ctx.guild)
        guild_config = await self.get_guild_config(ctx.guild)
        shape_odds = guild_config.get("shape_odds", dict(DEFAULT_SHAPE_ODDS))

        passed_players, failed_players = [], []
        error_messages = []

        for num, data in game_state.players.items():
            user = ctx.guild.get_member(data["user_id"])
            if user:
                shape = data["shape"]
                shape_key = next((k for k in shape_odds if k in shape.lower()), None)
                chance = shape_odds.get(shape_key, 20) / 100 if shape_key else 0.20
                player_label = (
                    f"Player {num} - {user.display_name} (ID: {user.id}) | Shape: {shape}"
                )

                if random.random() < chance:
                    if winning_price > 0:
                        try:
                            await bank.deposit_credits(user, winning_price)
                            passed_players.append(player_label)
                        except Exception as e:
                            error_messages.append(
                                f"Failed to deposit {winning_price} {currency_name} to {user.mention}: {e!s}"
                            )
                            passed_players.append(f"{player_label} - Deposit Failed")
                    else:
                        passed_players.append(player_label)
                    try:
                        dm_embed = discord.Embed(
                            title="🎉 You Passed!",
                            description=(
                                "You successfully carved your shape!"
                                + (
                                    f"\n\nYou received **{humanize_number(winning_price)} {currency_name}**."
                                    if winning_price > 0
                                    else ""
                                )
                            ),
                            color=discord.Color.green(),
                        )
                        dm_embed.set_footer(text=f"Game was held in {ctx.guild.name}")
                        await user.send(embed=dm_embed)
                    except (discord.HTTPException, discord.Forbidden):
                        log.error(f"Could not send DM to {user} about game results.")
                else:
                    if losing_price > 0:
                        try:
                            if await bank.can_spend(user, losing_price):
                                await bank.withdraw_credits(user, losing_price)
                                failed_players.append(player_label)
                            else:
                                error_messages.append(
                                    f"{user.mention} has insufficient {currency_name} to cover the loss."
                                )
                                failed_players.append(f"{player_label} - Withdrawal Failed")
                        except Exception as e:
                            error_messages.append(
                                f"Failed to withdraw {losing_price} {currency_name} from {user.mention}: {e!s}"
                            )
                            failed_players.append(f"{player_label} - Withdrawal Failed")
                    else:
                        failed_players.append(player_label)
                    try:
                        dm_embed = discord.Embed(
                            title="💀 You were Eliminated.",
                            description=(
                                "Your shape broke during the challenge."
                                + (
                                    f"\n\nYou lost **{humanize_number(losing_price)} {currency_name}**."
                                    if losing_price > 0
                                    else ""
                                )
                            ),
                            color=discord.Color.red(),
                        )
                        dm_embed.set_footer(text=f"Game was held in {ctx.guild.name}")
                        await user.send(embed=dm_embed)
                    except (discord.HTTPException, discord.Forbidden):
                        log.error(f"Could not send DM to {user} about game results.")

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
                name="Winning Price:",
                value=f"{humanize_number(winning_price)} {currency_name}",
            )
            embed.add_field(
                name="Losing Price:",
                value=f"{humanize_number(losing_price)} {currency_name}",
            )
        embed.set_footer(text="Thank you for playing!")
        file = discord.File(BytesIO(full_content.encode()), filename="honeycombs_results.txt")
        await ctx.send(embed=embed, file=file)

        game_state.players.clear()
        game_state.active = False
        self._game_tasks.pop(ctx.guild.id, None)

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def honeycombs(self, ctx: commands.Context):
        """
        Start a game of Honeycombs.

        You need at least 2 players to start the game.
        The maximum number of players is 456.
        """
        guild_config = await self.get_guild_config(ctx.guild)
        game_state = self.get_game_state(ctx.guild)
        async with self.get_lock(ctx.guild):
            if game_state.active:
                return await ctx.send(
                    "A game is already in progress in this server.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                )

            if (
                guild_config["mod_only_command"]
                and not cast(discord.Member, ctx.author).guild_permissions.manage_messages
            ):
                return await ctx.send(
                    "This command is only available to moderators.",
                    reference=ctx.message.to_reference(fail_if_not_exists=False),
                )

            game_state.active = True
        game_state.start_time = datetime.now(timezone.utc) + timedelta(minutes=2)
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
        task = self.bot.loop.create_task(self.wait_for_players(ctx, view))
        self._game_tasks[ctx.guild.id] = task

    async def wait_for_players(self, ctx: commands.Context, view: HoneycombView):
        guild_config = await self.get_guild_config(ctx.guild)
        game_state = self.get_game_state(ctx.guild)
        minimum_players = guild_config["minimum_players"]
        await asyncio.sleep(120)

        if len(game_state.players) < minimum_players:
            await ctx.channel.send(
                f"Not enough players entered the game ({len(game_state.players)}/{minimum_players}). Game has been canceled."
            )
            game_state.active = False
            game_state.players.clear()
            self._game_tasks.pop(ctx.guild.id, None)
            return

        view.stop()
        await view.on_timeout()
        await self.run_game(ctx)

    @commands.group()
    @commands.guild_only()
    async def honeycombset(self, ctx: commands.Context):
        """Settings for the HoneyCombs cog."""

    @honeycombset.command(name="checklist")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def checklist(self, ctx: commands.Context):
        """
        Check the list of players in the current game.

        Shows all players who have joined along with their player numbers.
        """
        game_state = self.get_game_state(ctx.guild)
        if not game_state.players:
            return await ctx.send("No ongoing game found.")

        player_list = [f"Player {number}" for number in game_state.players]
        pages = ["\n".join(player_list[i : i + 10]) for i in range(0, len(player_list), 10)]
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
        if not game_state.players and not game_state.active:
            return await ctx.send("Game settings are already reset.")

        view = ConfirmView(ctx.author, disable_buttons=True)
        await ctx.send("Are you sure you want to reset the game settings?", view=view)
        await view.wait()
        if view.result:
            task = self._game_tasks.pop(ctx.guild.id, None)
            if task:
                task.cancel()
            game_state.players.clear()
            game_state.active = False
            default_guild = {
                "players": {},
                "game_active": False,
                "default_start_image": None,
                "shapes": ["circle⭕️", "triangle△", "star⭐️", "umbrella☂️"],
                "shape_odds": DEFAULT_SHAPE_ODDS,
                "mod_only_command": False,
                "minimum_players": 2,
                "default_minutes": 10,
            }
            self.cache["guilds"][ctx.guild.id] = default_guild
            await self.config.guild(ctx.guild).clear()
            await ctx.send("Game settings have been reset.")
        else:
            await ctx.send("Game settings were not reset.")

    @honeycombset.group(name="setimage", aliases=["setimg"], invoke_without_command=True)
    @commands.admin()
    async def setimage(self, ctx: commands.Context, *, image_url: str | None = None):
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

        try:
            async with self.session.get(image_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return await ctx.send("Failed to set the start image. URL is invalid.")
                data = await r.read()
        except aiohttp.ClientError:
            return await ctx.send("Failed to set the start image. Client error.")
        except asyncio.TimeoutError:
            return await ctx.send("Failed to set the start image. Timeout error.")

        if not data or not any(data.startswith(sig) for sig in MAGIC_BYTES):
            return await ctx.send(
                f"Failed to set the start image. Only {humanize_list(list(MAGIC_BYTES.values()))} format is supported."
            )

        await self.update_guild_config(ctx.guild, "default_start_image", image_url)
        await ctx.send("The start image has been set.")

    @setimage.command(name="clear", aliases=["reset"])
    @commands.admin()
    async def setimage_clear(self, ctx: commands.Context):
        """Clear the start image (disables it)."""
        await self.update_guild_config(ctx.guild, "default_start_image", None)
        await ctx.send("The start image has been cleared.")

    @commands.admin()
    @honeycombset.command(name="modonly")
    async def mod_only(self, ctx: commands.Context, state: bool | None = None):
        """
        Set whether only moderators can start the game.

        If set to True, only moderators can start the game.
        If set to False, anyone can start the game.
        """
        if state is None:
            guild_config = await self.get_guild_config(ctx.guild)
            state = not guild_config["mod_only_command"]
        await self.update_guild_config(ctx.guild, "mod_only_command", state)
        await ctx.send(f"Mod only command has been set to {state}.")

    @commands.admin()
    @honeycombset.command(name="endtime")
    async def endtime(self, ctx: commands.Context, default_minutes: commands.Range[int, 10, 720]):
        """
        Change the default minutes for when the game should end.

        The default is 10 minutes.
        The maximum is 720 minutes (12 hours).
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

        The default minimum is 2 players.
        """
        await self.update_guild_config(ctx.guild, "minimum_players", minimum_players)
        await ctx.send(f"The minimum number of players has been set to {minimum_players}.")

    @commands.admin()
    @honeycombset.command(name="shapeodds")
    async def shape_odds_cmd(
        self,
        ctx: commands.Context,
        shape: str,
        percentage: commands.Range[int, 1, 99],
    ):
        """
        Set the pass-chance percentage for a specific shape.

        Shape must be one of: circle, triangle, star, umbrella.
        Percentage is 1–99 (e.g. 20 means a 20% chance of passing).

        Default values:
        - circle: 20%
        - triangle: 20%
        - star: 20%
        - umbrella: 8%
        """
        shape = shape.lower()
        valid_shapes = list(DEFAULT_SHAPE_ODDS.keys())
        if shape not in valid_shapes:
            return await ctx.send(f"Invalid shape. Must be one of: {humanize_list(valid_shapes)}.")
        guild_config = await self.get_guild_config(ctx.guild)
        odds = dict(guild_config.get("shape_odds", DEFAULT_SHAPE_ODDS))
        odds[shape] = percentage
        await self.update_guild_config(ctx.guild, "shape_odds", odds)
        await ctx.send(f"Pass chance for **{shape}** has been set to **{percentage}%**.")

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
        guild_config = await self.get_guild_config(ctx.guild)
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
            name="Minimum Players",
            value=guild_config.get("minimum_players", 2),
            inline=False,
        )
        embed.add_field(
            name="Default Game Duration",
            value=f"{guild_config.get('default_minutes', 10)} minutes",
            inline=False,
        )
        shape_odds = guild_config.get("shape_odds", DEFAULT_SHAPE_ODDS)
        odds_display = "\n".join(f"{shape}: {pct}%" for shape, pct in shape_odds.items())
        embed.add_field(
            name="Shape Pass Odds",
            value=odds_display,
            inline=False,
        )
        start_image_url = guild_config.get("default_start_image", None)
        start_image_value = (
            f"[View Start Image]({start_image_url})" if start_image_url else "Not set"
        )
        embed.add_field(name="Start Image", value=start_image_value, inline=False)
        await ctx.send(embed=embed)
