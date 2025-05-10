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

from .view import HoneycombView

log = logging.getLogger("red.maxcogs.honeycombs")


class HoneyCombs(commands.Cog):
    """Play a game similar to Sugar Honeycombs, inspired by the Netflix series Squid Game."""

    __version__: Final[str] = "1.4.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=34562809777, force_registration=True)
        default_guild = {
            "players": {},  # List of players
            "game_active": False,  # Default game is inactive
            "default_start_image": "https://i.maxapp.tv/4c76241E.png",  # Default start image
            "shapes": ["circle⭕️", "triangle△", "star⭐️", "umbrella☂️"],  # Default shapes
            "mod_only_command": False,  # Default mod only command is False
            "minimum_players": 5,  # Default minimum number of players
            "default_minutes": 10,  # Default minutes to 10.
            "default_start_minutes": 2,  # Default start minutes to 2
        }
        default_global = {
            "winning_price": 100,  # Default winning price
            "losing_price": 100,  # Default losing price
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def cog_unload(self) -> None:
        await self.session.close()
        for guild in self.bot.guilds:
            await self.config.guild(guild).players.clear()
            await self.config.guild(guild).game_active.set(False)

    async def run_game(self, ctx):
        guild_config = self.config.guild(ctx.guild)
        players = await guild_config.players()
        if not players:
            await ctx.send("No players joined the game.")
            await guild_config.game_active.set(False)
            return

        default_minutes = await guild_config.default_minutes()
        end_time = int((datetime.now() + timedelta(minutes=default_minutes)).timestamp())
        embed = discord.Embed(
            title="Sugar Honeycombs Challenge",
            color=await ctx.embed_color(),
            description=f"Let the game begin!\nThe bot will finish <t:{end_time}:R> to decide whether you Pass or Eliminated.\nGood luck!",
        )
        embed.add_field(name="Players:", value=len(players))
        embed.set_footer(text="I would like to expend a heartfelt welcome to you all.")
        await ctx.send(embed=embed)
        await discord.utils.sleep_until(datetime.now() + timedelta(minutes=default_minutes))

        winning_price = await self.config.winning_price()
        losing_price = await self.config.losing_price()
        currency_name = await bank.get_currency_name(ctx.guild)

        passed_players, failed_players = [], []
        for num, data in players.items():
            user = ctx.guild.get_member(data["user_id"])
            if user:
                shape = data["shape"]
                chance = 0.08 if shape == "umbrella☂️" else 0.2
                if random.random() < chance:
                    try:
                        await bank.deposit_credits(user, winning_price)
                        passed_players.append(
                            f"Player {num}, Shape: {shape} - (User ID: {data['user_id']})"
                        )
                    except errors.BalanceTooHigh:
                        log.error("User's balance is too high for the winning price of the game.")
                else:
                    await bank.withdraw_credits(user, losing_price)
                    failed_players.append(
                        f"Player {num}, Shape: {shape} - (User ID: {data['user_id']})"
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
        full_content = passed_content + failed_content

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
        await guild_config.players.clear()
        await guild_config.game_active.set(False)

    @commands.guild_only()
    @commands.hybrid_command(name="honeycombs")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def honeycombs(self, ctx: commands.Context):
        """
        Start a game of Sugar Honeycombs.

        You need at least 5 players to start the game.
        The maximum number of players is 456.
        """
        guild_config = self.config.guild(ctx.guild)
        if await guild_config.game_active():
            return await ctx.send(
                "A game is already in progress in this server.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        if (
            await guild_config.mod_only_command()
            and not ctx.author.guild_permissions.manage_messages
        ):
            return await ctx.send(
                "This command is only available to moderators.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )

        await guild_config.game_active.set(True)
        default_start_time = await guild_config.default_start_minutes()
        end_time = int((datetime.now() + timedelta(minutes=default_start_time)).timestamp())
        view = HoneycombView(self, ctx.guild)
        winning_price = await self.config.winning_price()
        losing_price = await self.config.losing_price()
        total_price = winning_price + losing_price
        currency_name = await bank.get_currency_name(ctx.guild)

        embed = discord.Embed(
            title="Sugar Honeycombs Challenge",
            color=await ctx.embed_color(),
            description=f"Click the button to join! Game starts <t:{end_time}:R>.",
        )
        embed.add_field(
            name="Price To Enter:",
            value=(
                f"{humanize_number(total_price)} {currency_name}"
                if total_price != 0
                else "Free To Enter"
            ),
        )

        img = await guild_config.default_start_image()
        if img:
            embed.set_image(url=img)
        minimum_players = await guild_config.minimum_players()
        embed.set_footer(text=f"Need at least {minimum_players} players to start the game.")

        message = await ctx.send(embed=embed, view=view)
        view.message = message
        await self.wait_for_players(ctx, view)

    async def wait_for_players(self, ctx: commands.Context, view: HoneycombView):
        guild_config = self.config.guild(ctx.guild)
        default_start_minutes = await guild_config.default_start_minutes()
        minimum_players = await guild_config.minimum_players()
        await discord.utils.sleep_until(datetime.now() + timedelta(minutes=default_start_minutes))

        players = await guild_config.players()
        if len(players) < minimum_players:
            await ctx.send(
                f"Not enough players entered the game ({len(players)}/{minimum_players}). Game has been canceled."
            )
            await guild_config.game_active.set(False)
            await guild_config.players.clear()
            return

        for item in view.children:
            item.disabled = True
        await view.message.edit(view=view)
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
        players = await self.config.guild(ctx.guild).players()
        if not players:
            return await ctx.send("No ongoing game found.")
        player_list = []
        for player_number, player_data in players.items():
            title = "List of players"
            player_list.append(f"{header(title, 'medium')}\nPlayer {player_number}")

        pages = [humanize_list(player_list[i : i + 10]) for i in range(0, len(player_list), 10)]
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
        data = await self.config.guild(ctx.guild).all()
        if not data["players"] and not data["game_active"]:
            return await ctx.send("Game settings are already reset.")

        view = ConfirmView(ctx.author, disable_buttons=True)
        message = await ctx.send("Are you sure you want to reset the game settings?", view=view)
        await view.wait()
        if view.result:
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
                log.error(e)
            except asyncio.TimeoutError as e:
                return await ctx.send("Failed to set the start image. Timeout error.")
                log.error(e)

        image_formats = ["JPG", "JPEG", "PNG", "GIF", "WEBP"]
        if not data or not any(data.startswith(bytes(f"{sig}", "utf-8")) for sig in image_formats):
            return await ctx.send(
                f"Failed to set the start image. Only {humanize_list(image_formats)} format is supported."
            )

        await self.config.guild(ctx.guild).default_start_image.set(image_url)
        await ctx.send("The start image has been set.")

    @commands.admin()
    @setimage.command(name="clear", aliases=["reset"])
    async def setimage_clear(self, ctx: commands.Context):
        """Reset the start image to default."""
        await self.config.guild(ctx.guild).default_start_image.clear()
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
            state = not await self.config.guild(ctx.guild).mod_only_command()
        await self.config.guild(ctx.guild).mod_only_command.set(state)
        await ctx.send(f"Mod only command has been set to {state}.")

    @commands.admin()
    @honeycombset.command(name="endtime")
    async def endtime(self, ctx: commands.Context, default_minutes: commands.Range[int, 10, 720]):
        """
        Change the default minutes for when the game should end.

        **Please note**
        - This is for the length of the game to run for, not the length of when the game starts.

        The default minutes is 10.
        The maximum number of minutes is 720 (12 hours).

        **Examples**:
        - `[p]honeycombset defaultminutes 20` - Set the default number of minutes to 20 minutes.
        - `[p]honeycombset defaultminutes 60` - Set the default number of minutes to 60 minutes. (1 hour)
        You can use [unitconverters](https://www.unitconverters.net/time/minutes-to-hours.htm) to convert minutes to hours.

        **Arguments**:
        - `<default_minutes>`: The default number of minutes for the game.
        """
        await self.config.guild(ctx.guild).default_minutes.set(default_minutes)
        await ctx.send(f"The default minutes has been set to {default_minutes} minutes.")

    @commands.admin()
    @honeycombset.command(name="starttime")
    async def starttime(
        self, ctx: commands.Context, default_start_minutes: commands.Range[int, 2, 20]
    ):
        """
        Change the default minutes for the game to start for.

        **Please note**
        - This is for the length of the game to start for, not the length of when the game ends.

        The default minutes is 2.
        The maximum minutes is 20.
        """
        await self.config.guild(ctx.guild).default_start_minutes.set(default_start_minutes)
        await ctx.send(f"The default minutes has been set to {default_start_minutes} minutes.")

    @commands.admin()
    @honeycombset.command(name="minimumplayers")
    async def minimum_players(
        self, ctx: commands.Context, minimum_players: commands.Range[int, 2, 15]
    ):
        """
        Set the minimum number of players needed to start a game.

        The default minimum number of players is 5.
        """
        await self.config.guild(ctx.guild).minimum_players.set(minimum_players)
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
        The winning price is the amount of credits a player will receive if they pass the game.
        """
        currency_name = await bank.get_currency_name(ctx.guild)
        await self.config.winning_price.set(amount)
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
        The losing price is the amount of credits a player will lose if they fail the game.
        """
        currency_name = await bank.get_currency_name(ctx.guild)
        await self.config.losing_price.set(amount)
        await ctx.send(
            f"The losing price has been set to {humanize_number(amount)} {currency_name}."
        )

    @commands.mod()
    @honeycombset.command(name="settings")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """View the current game settings."""
        guild_data = await self.config.guild(ctx.guild).all()
        global_data = await self.config.all()
        currency_name = await bank.get_currency_name(ctx.guild)

        embed = discord.Embed(
            title="Current Game Settings",
            description="View the current game settings.",
            color=await ctx.embed_color(),
        )
        # Only owner can see the winning and losing price
        # since they are the only ones who can change them.
        if await self.bot.is_owner(ctx.author):
            embed.add_field(
                name="Winning Price",
                value=f"{humanize_number(global_data.get('winning_price', 0))} {currency_name}",
            )
            embed.add_field(
                name="Losing Price",
                value=f"{humanize_number(global_data.get('losing_price', 0))} {currency_name}",
            )
        embed.add_field(
            name="Mod Only Command", value=guild_data.get("mod_only_command", False), inline=False
        )
        embed.add_field(
            name="Minimum Players", value=guild_data.get("minimum_players", 5), inline=False
        )
        embed.add_field(
            name="Default ongoing game minutes",
            value=guild_data.get("default_minutes", 10),
            inline=False,
        )
        embed.add_field(
            name="Default Start Minutes",
            value=guild_data.get("default_start_minutes", 2),
            inline=False,
        )
        start_image_url = guild_data.get("default_start_image", None)
        if start_image_url:
            start_image_value = hyperlink("View Start Image", start_image_url)
        else:
            start_image_value = "Not set"
        embed.add_field(name="Start Image", value=start_image_value, inline=False)

        await ctx.send(embed=embed)
