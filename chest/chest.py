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
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Final, Literal, Optional

import discord
import os
from databases import Database
from discord.ext import tasks
from discord.ext.commands.converter import EmojiConverter
from discord.ext.commands.errors import EmojiNotFound
from emoji import EMOJI_DATA
from redbot.core import Config, bank, commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu
from tabulate import tabulate

from .view import ChestView

log = logging.getLogger("red.maxcogs.chest")


class Chest(commands.Cog):
    """First to click the button gets random credits to their `[p]bank balance`."""

    __version__: Final[str] = "2.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Chest.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=34562809)
        default_guild = {
            "channel": None,  # I can't choose the channel for you so it's None.
            "role": None,  # I can't choose the role for you so it's None.
        }
        default_global = {
            "max_coins": 5000,  # Default random between 1 and 5,000 coins.
            "chance": 30,  # Default 30% fail rate.
            "toggle": False,  # Default disabled because yes, not alot want default enabled(?)
            "default_spawn_image": "https://pngimg.com/uploads/treasure_chest/treasure_chest_PNG78.png",  # Default image.
            "default_claim_image": "https://pngimg.com/uploads/treasure_chest/treasure_chest_PNG130.png",  # Default image.
            "default_fail_image": "https://pngimg.com/uploads/treasure_chest/treasure_chest_PNG40.png",  # Default image.
            "emoji": "🪙",  # Default emoji on the button.
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.remaining_times = {}
        self.DATABASE_URL = f"sqlite:///{cog_data_path(self)}/time_left.db"
        self.database = Database(self.DATABASE_URL)
        self.send_chest.start()
        self.bot.loop.create_task(self.initialize())

    def cog_unload(self):
        self.send_chest.cancel()
        self.bot.loop.create_task(self.database.disconnect())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def initialize(self):
        """
        Initialize the database and load all task states.
        """
        await self.database.connect()
        await self.init_db()
        await self.load_all_task_states()

    async def init_db(self):
        """
        Initialize the database and create the table if it doesn't exist.
        """
        query = """
        CREATE TABLE IF NOT EXISTS timer_table (
            guild_id INTEGER PRIMARY KEY,
            next_chest_time TEXT
        )
        """
        await self.database.execute(query=query)

    async def save_task_state(self, guild_id: int):
        """
        Save the task state to the database.
        """
        next_chest_time = datetime.now() + self.remaining_times[guild_id]
        query = """
            INSERT INTO timer_table (guild_id, next_chest_time)
            VALUES (:guild_id, :next_chest_time)
            ON CONFLICT(guild_id) DO UPDATE SET next_chest_time=excluded.next_chest_time
        """
        values = {"guild_id": guild_id, "next_chest_time": next_chest_time.isoformat()}
        await self.database.execute(query=query, values=values)
        log.info(f"Saved task state for guild {guild_id}. Next Spawn: {next_chest_time}")

    async def load_task_state(self, guild_id: int):
        """
        Load the task state from the database.
        """
        query = """
            SELECT next_chest_time FROM timer_table WHERE guild_id = :guild_id
        """
        result = await self.database.fetch_one(query=query, values={"guild_id": guild_id})
        if result:
            next_chest_time = datetime.fromisoformat(result["next_chest_time"])
            self.remaining_times[guild_id] = next_chest_time - datetime.now()
            log.info(f"Loaded task state for guild {guild_id}. Next Spawn: {next_chest_time}")
        else:
            self.remaining_times[guild_id] = timedelta(hours=4)

    async def load_all_task_states(self):
        """
        Load all task states from the database.
        """
        query = """
            SELECT guild_id, next_chest_time FROM timer_table
        """
        results = await self.database.fetch_all(query=query)
        for result in results:
            guild_id = result["guild_id"]
            next_chest_time = datetime.fromisoformat(result["next_chest_time"])
            self.remaining_times[guild_id] = next_chest_time - datetime.now()

    async def delete_task_state(self, guild_id: int):
        """
        Delete the task state from the database.
        """
        query = """
            DELETE FROM timer_table WHERE guild_id = :guild_id
        """
        await self.database.execute(query=query, values={"guild_id": guild_id})

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        Remove the task state when the bot leaves a guild.
        """
        if guild.id in self.remaining_times:
            del self.remaining_times[guild.id]
            await self.delete_task_state(guild.id)
            log.info(f"Deleted task state for guild {guild.id}.")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """
        Remove the task state when the channel is deleted.
        """
        if channel.guild.id in self.remaining_times:
            del self.remaining_times[channel.guild.id]
            await self.delete_task_state(channel.guild.id)
            log.info(f"Deleted task state for guild {channel.guild.id}.")

        if await self.config.guild(channel.guild).channel() == channel.id:
            await self.config.guild(channel.guild).channel.clear()
            log.info(f"Cleared channel for guild {channel.guild.id}.")

    @tasks.loop(minutes=1)
    async def send_chest(self):
        """
        Task to send a chest in the channel every 4 hours.
        """
        for guild in self.bot.guilds:
            if guild.id not in self.remaining_times:
                await self.load_task_state(guild.id)
            if self.remaining_times[guild.id].total_seconds() <= 0:
                channel_id = await self.config.guild(guild).channel()
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if (
                            not channel.permissions_for(guild.me).embed_links
                            or not channel.permissions_for(guild.me).send_messages
                        ):
                            log.warning(
                                f"Missing permissions to send chest in {channel.mention} ({guild.name})"
                            )
                            continue
                        role = await self.config.guild(guild).role()
                        if role:
                            role = guild.get_role(role)
                            if role:
                                view = ChestView(self.bot, self.config, channel)
                                await view.init_view()
                                message = await channel.send(
                                    embed=await view.get_embed(),
                                    view=view,
                                    content=role.mention,
                                    allowed_mentions=discord.AllowedMentions(
                                        roles=True, users=False
                                    ),
                                )
                                view.message = message  # Store the message in the view
                        else:
                            view = ChestView(self.bot, self.config, channel)
                            await view.init_view()
                            message = await channel.send(embed=await view.get_embed(), view=view)
                            view.message = message  # Store the message in the view

                        # Update remaining_time before saving the task state
                        self.remaining_times[guild.id] = timedelta(hours=4)
                        await self.save_task_state(guild.id)
            else:
                self.remaining_times[guild.id] -= timedelta(minutes=1)

    @send_chest.before_loop
    async def before_send_chest(self):
        """
        Wait until the bot is ready before starting the task.
        """
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            await self.load_task_state(guild.id)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_can_manage_channel()
    async def chestset(self, ctx: commands.Context):
        """Configure the chest game"""

    @chestset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Set the channel for the chest game.

        Use the command again to disable chest from spawning.
        """
        if channel is None:
            await self.config.guild(ctx.guild).channel.clear()
            if ctx.guild.id in self.remaining_times:
                del self.remaining_times[ctx.guild.id]
                await self.delete_task_state(ctx.guild.id)
                log.info(f"Deleted task state for guild {ctx.guild.id}.")
            return await ctx.send("Cleared channel. I won't send anymore!")
        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            and not channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                "I do not have permission to `send_messages` or `embed_links` in that channel."
            )

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}. Sending a chest now!")

        view = ChestView(self.bot, self.config, channel)
        await view.init_view()
        message = await channel.send(embed=await view.get_embed(), view=view)
        view.message = message

        self.remaining_times[ctx.guild.id] = timedelta(hours=4)
        await self.save_task_state(ctx.guild.id)

    @chestset.command()
    async def role(self, ctx: commands.Context, role: discord.Role = None):
        """
        Set the role for the chest game.

        Use the command again to disable chest from spawning.
        """
        if role is None:
            await self.config.guild(ctx.guild).role.clear()
            return await ctx.send("Cleared role. I won't ping anymore!")
        if role >= ctx.guild.me.top_role:
            return await ctx.send("You can't set a role higher than my top role.")
        if role.is_default():
            return await ctx.send("You can't set a role with ``@everyone`` or ``@here``.")
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send(
            f"Chest game role set to {role.mention}. I will ping this role when a chest spawns.",
            allowed_mentions=discord.AllowedMentions(roles=False),
        )

    @chestset.command()
    @commands.bot_has_permissions(embed_links=True)
    async def settings(self, ctx: commands.Context):
        """Show current settings"""
        channel = await self.config.guild(ctx.guild).channel()
        if channel:
            channel = ctx.guild.get_channel(channel)
        else:
            channel = None
        coins = await self.config.max_coins()
        chance = await self.config.chance()
        emoji = await self.config.emoji()
        embed = discord.Embed(title="Chest Game Settings", color=0x00FF00)
        embed.add_field(name="Channel:", value=channel, inline=False)
        if await self.bot.is_owner(ctx.author):
            embed.add_field(
                name="Max Coins per chest:",
                value=f"{humanize_number(coins)}",
                inline=False,
            )
            embed.add_field(
                name="Fail Rate:",
                value=f"{humanize_number(chance)}%",
            )
            embed.add_field(
                name="Emoji:",
                value=f"{emoji}",
            )
        await ctx.send(embed=embed)

    @chestset.command()
    @commands.bot_has_permissions(embed_links=True)
    async def version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)

    @chestset.group()
    @commands.is_owner()
    async def owner(self, ctx: commands.Context):
        """Group owner commands."""

    @owner.command(aliases=["setimage"])
    async def image(
        self,
        ctx: commands.Context,
        image_type: Literal["spawn", "claim", "fail"],
        image: str = None,
    ):
        """
        Set a new default image.

        Args:
            ctx (discord.Context): The command context.
            image_type (str): The type of image to update (spawn, claim or fail).
            image (str, optional): The URL of the image or None if an attachment is provided. Defaults to None.
        """
        # Check if an attachment is provided
        if ctx.message.attachments:
            # Get the first attachment
            attachment = ctx.message.attachments[0]
            # Check if the attachment has a valid extension
            if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                await ctx.send("Invalid image format. Only PNG, JPG, GIF, and JPEG are allowed.")
                return
            # Use the attachment as the image
            image_url = attachment.url
        # Check if a URL is provided
        elif image:
            # Check if the URL has a valid extension
            if not image.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                await ctx.send("Invalid image format. Only PNG, JPG, GIF, and JPEG are allowed.")
                return
            # Use the URL as the image
            image_url = image
        else:
            await ctx.send("Please provide an image URL or attachment.")
            return

        # Update the image based on the image type
        if image_type.lower() == "spawn":
            await self.config.default_spawn_image.set(image_url)
            await ctx.send("Default spawn image updated!")
        elif image_type.lower() == "claim":
            await self.config.default_claim_image.set(image_url)
            await ctx.send("Default claim image updated!")
        elif image_type.lower() == "fail":
            await self.config.default_fail_image.set(image_url)
            await ctx.send("Default fail image updated!")

    @owner.command(aliases=["credits"])
    async def credit(self, ctx: commands.Context, coins: int):
        """
        Change how much credits users can get from claiming.

        Default is 5,000. (it random select between 1 and 5,000)
        """
        if coins <= 10:
            return await ctx.send("Please enter a value greater than 10")
        red_economy_name = await bank.get_currency_name(ctx.guild)
        await self.config.max_coins.set(coins)
        await ctx.send(
            f"The max {red_economy_name} is now set to {humanize_number(coins)}\nI will now choose any random {red_economy_name} between 1 and {humanize_number(coins)}"
        )

    @owner.command(aloases=["failrate"])
    async def rate(self, ctx: commands.Context, fail_rate: commands.Range[int, 1, 100]):
        """
        Change the fail rate to a different.

        Default is 30% fail rate.

        **Example**:
        - `[p]chestset rate 40` This will make you fail 40% of time to get coins.

        **Arguments**:
        - `<fail_rate>` The number of whichever % you want users to fail.
            - Cannot be longer than 100 and less than 1.
        """
        await self.config.chance.set(fail_rate)
        await ctx.send(f"Fail rate has been set to {fail_rate}%")

    @owner.command()
    async def toggle(self, ctx: commands.Context):
        """
        Toggle whether you want to use image(s) in spawn/claim embed or not.

        Default is Disabled.
        """
        await self.config.toggle.set(not await self.config.toggle())
        toggle = await self.config.toggle()
        await ctx.send(f"Image usage is now {'enabled' if toggle else 'disabled'}.")

    @owner.command(aliases=["setemoji"])
    async def emoji(self, ctx: commands.Context, emoji_input: Optional[str]):
        """
        Change the default emoji on the button.

        Leave blank to reset back to default.
        Note that your bot must share the same server as the emoji for the custom emoji to work.
        """
        if emoji_input:
            try:
                # Use EmojiConverter to convert the emoji argument
                emoji_obj = await EmojiConverter().convert(ctx, emoji_input)
                emoji_str = str(emoji_obj)
            except EmojiNotFound:
                if emoji_input in EMOJI_DATA:
                    emoji_str = emoji_input
                else:
                    await ctx.send(f"'{emoji_input}' is not a valid emoji.")
                    return

            await self.config.emoji.set(emoji_str)
            await ctx.send(f"Default emoji has been set to {emoji_str}")
        else:
            await self.config.emoji.set("🪙")
            await ctx.send("I've reset back to default!")

    @owner.command()
    async def debug(self, ctx: commands.Context):
        """
        Debug the database.

        This will show all the records in the database table for debugging purposes.
        It will show the guild_id and the next_chest_time for each record.
        """
        query = """
            SELECT * FROM timer_table
        """
        results = await self.database.fetch_all(query=query)

        if not results:
            await ctx.send("No records found.")
            return

        # Convert the results to a list of dictionaries
        results_list = []
        for result in results:
            result_dict = dict(result)
            if "next_chest_time" in result_dict:
                result_dict["next_chest_time"] = datetime.fromisoformat(
                    result_dict["next_chest_time"]
                ).replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
            results_list.append(result_dict)

        # Manually split the results into chunks of 15
        chunks = [results_list[i : i + 15] for i in range(0, len(results_list), 15)]
        # Format each chunk using tabulate
        pages = [
            box(tabulate(chunk, headers="keys", tablefmt="pretty"), lang="yaml")
            for chunk in chunks
        ]
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @owner.group(name="reset")
    async def owner_reset(self, ctx: commands.Context):
        """Manage the chest game resets."""

    @owner_reset.command(name="resetsetting", aliases=["settingreset", "rsetting"])
    async def owner_reset_resetsetting(self, ctx: commands.Context):
        """Reset back to default setting"""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Are you sure you want to reset Chest settings?", view=view)
        await view.wait()
        if view.result:
            await self.config.clear()
            await ctx.send("Settings have been reset to default!")
        else:
            await ctx.send("Alright, i won't reset anything!")

    @owner_reset.command(name="resetdb")
    async def owner_reset_resetdb(self, ctx: commands.Context):
        """Reset the database."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Are you sure you want to reset the database?", view=view)
        await view.wait()
        if view.result:
            query = """
                DROP TABLE IF EXISTS timer_table
            """
            await self.database.execute(query=query)
            await self.init_db()
            log.info("Database has been reset successfully.")
            await ctx.send("Database has been reset!")
        else:
            await ctx.send("Alright, i won't reset the database!")

    @owner_reset.command(name="resetguilddb", aliases=["guildresetdb", "rgdb", "resetguild"])
    async def owner_reset_resetguilddb(self, ctx: commands.Context, guild_id: int):
        """Reset the database for a specific guild."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            f"Are you sure you want to reset the database for guild {guild_id}?", view=view
        )
        await view.wait()
        if view.result:
            query = """
                DELETE FROM timer_table WHERE guild_id = :guild_id
            """
            await self.database.execute(query=query, values={"guild_id": guild_id})
            await self.load_task_state(guild_id)
            log.info(f"Database for guild {guild_id} has been reset successfully.")
            await ctx.send(f"Database for guild {guild_id} has been reset!")
        else:
            await ctx.send("Alright, i won't reset the database!")
