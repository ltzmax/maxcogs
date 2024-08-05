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
from typing import Any, Final, Literal, Optional

import discord
from discord.ext import tasks
from redbot.core import Config, bank, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, box
from redbot.core.utils.views import ConfirmView

from .converter import RealEmojiConverter
from .view import ChestView

log = logging.getLogger("red.maxcogs.chest")


class Chest(commands.Cog):
    """First to click the button gets random credits to their `[p]bank balance`."""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/Chest.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=34562809)
        default_guild = {
            "channel": None,  # I can't choose the channel for you so it's None.
        }
        default_global = {
            "max_coins": 5000,  # Default random between 1 and 5,000 coins.
            "chance": 30,  # Default 30% fail rate.
            "toggle": False,  # Default disabled because yes, not alot want default enabled(?)
            "default_spawn_image": "https://cdn.maxapp.tv/Geb793.png",  # Default image.
            "default_claim_image": "https://cdn.maxapp.tv/Z5m382.png",  # Default image.
            "emoji": "🪙", # Default emoji on the button.
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.send_chest.start()  # Start the send_chest task.

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    # if you change this, you also need to make sure
    # you change in view.py too.
    @tasks.loop(hours=4)
    async def send_chest(self):
        for guild in self.bot.guilds:
            channel_id = await self.config.guild(guild).channel()
            if channel_id:  # Make sure the channel is set
                channel = self.bot.get_channel(channel_id)
                if channel:  # Make sure the channel is found
                    # Make sure it has permission
                    if (
                        not channel.permissions_for(guild.me).embed_links
                        or not channel.permissions_for(guild.me).send_messages
                    ):
                        log.warning(
                            f"Missing permissions to send chest in {channel.mention} ({guild.name})"
                        )
                        continue

                    view = ChestView(self.bot, self.config, channel)
                    await view.init_view()
                    message = await channel.send(
                        embed=await view.get_embed(), view=view
                    )
                    view.message = message  # Store the message in the view

    def cog_unload(self):
        self.send_chest.cancel()

    @send_chest.before_loop
    async def before_send_chest(self):
        await self.bot.wait_until_red_ready()

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
            return await ctx.send("Cleared channel. I won't send anymore!")
        # Actually make sure your app has perm in the channel you set.
        if (
            not channel.permissions_for(ctx.guild.me).send_messages
            and not channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                "I do not have permission to `send_messages` or `embed_links` in that channel."
            )

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Chest game channel set to {channel.mention}")
        # This will make the chest spawn immediately after setting the channel,
        # so you don't have to wait hours for the first spawn.
        await asyncio.sleep(0.4)  # wait 0.4 sec before sending.
        await self.send_chest()

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

    @owner.command()
    async def setimage(
        self,
        ctx: commands.Context,
        image_type: Literal["spawn", "claim"],
        image: str = None,
    ):
        """
        Set a new default image.

        Args:
            ctx (discord.Context): The command context.
            image_type (str): The type of image to update (spawn or claim).
            image (str, optional): The URL of the image or None if an attachment is provided. Defaults to None.
        """
        # Check if an attachment is provided
        if ctx.message.attachments:
            # Get the first attachment
            attachment = ctx.message.attachments[0]
            # Check if the attachment has a valid extension
            if not attachment.filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif")
            ):
                await ctx.send(
                    "Invalid image format. Only PNG, JPG, GIF, and JPEG are allowed."
                )
                return
            # Use the attachment as the image
            image_url = attachment.url
        # Check if a URL is provided
        elif image:
            # Check if the URL has a valid extension
            if not image.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                await ctx.send(
                    "Invalid image format. Only PNG, JPG, GIF, and JPEG are allowed."
                )
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

    @owner.command(aliases=["credits"])
    async def credit(self, ctx: commands.Context, coins: int):
        """
        Change how much credits users can get from claiming.

        Default is 10,000. (it random select between 1 and 10,000)
        """
        if coins <= 10:
            return await ctx.send("Please enter a value greater than 10")
        red_economy_name = await bank.get_currency_name(ctx.guild)
        await self.config.max_coins.set(coins)
        await ctx.send(
            f"The max {red_economy_name} is now set to {humanize_number(coins)}"
        )

    @owner.command()
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

    @owner.command()
    async def setemoji(
        self, ctx: commands.Context, emoji: Optional[RealEmojiConverter]
    ):
        """
        Change the default emoji on the button.

        Leave blank to reset back to default.
        Note that your bot must share same server as the emoji for the emoji to work.
        """
        if emoji:
            await self.config.emoji.set(str(emoji))
            await ctx.send(f"Default emoji has been set to {emoji}")
        else:
            await self.config.emoji.set(str(("🪙")))
            await ctx.send("I've reset back to default!")

    @owner.command()
    async def reset(self, ctx: commands.Context):
        """Reset back to default setting"""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset Chest settings?", view=view
        )
        await view.wait()
        if view.result:
            await self.config.clear()
            await ctx.send("Settings have been reset to default!")
        else:
            await ctx.send("Alright, i won't reset anything!")
