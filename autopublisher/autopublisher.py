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
from typing import Any, Dict, Final, List, Literal, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.views import ConfirmView

log = logging.getLogger("red.maxcogs.autopublisher")


class ChannelView(discord.ui.View):
    def __init__(self, bot: Red, config: Config, guild_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.config = config
        self.guild_id = guild_id
        self.selected_channel = None
        # Initialize the select menu
        self.select = discord.ui.Select(placeholder="Select a news channel")
        self.select.callback = self.select_callback
        self.set_select_options()
        self.add_item(self.select)
        # Add buttons below the select menu
        self.confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
        self.confirm_button.callback = self.confirm_button_callback
        self.add_item(self.confirm_button)
        self.remove_button = discord.ui.Button(label="Remove", style=discord.ButtonStyle.red)
        self.remove_button.callback = self.remove_button_callback
        self.add_item(self.remove_button)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    def set_select_options(self):
        # This method sets the options for the select menu
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            channels = [channel for channel in guild.text_channels if channel.is_news()]
            self.select.options = [
                discord.SelectOption(label=channel.name, value=str(channel.id))
                for channel in channels
            ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_channel = self.bot.get_channel(int(interaction.data["values"][0]))
        await interaction.response.send_message(
            f"Selected channel: {self.selected_channel}", ephemeral=True
        )

    async def confirm_button_callback(self, interaction: discord.Interaction):
        if self.selected_channel:
            async with self.config.guild_from_id(
                self.guild_id
            ).ignored_channels() as ignored_channels:
                if self.selected_channel.id not in ignored_channels:
                    ignored_channels.append(self.selected_channel.id)
                    await interaction.response.send_message(
                        f"Confirmed and ignored channel: {self.selected_channel}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"Channel {self.selected_channel} is already ignored.",
                        ephemeral=True,
                    )
        else:
            await interaction.response.send_message("No channel selected.", ephemeral=True)

    async def remove_button_callback(self, interaction: discord.Interaction):
        if self.selected_channel:
            async with self.config.guild_from_id(
                self.guild_id
            ).ignored_channels() as ignored_channels:
                if self.selected_channel.id in ignored_channels:
                    ignored_channels.remove(self.selected_channel.id)
                    await interaction.response.send_message(
                        f"Removed channel from ignored list: {self.selected_channel}",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        f"Channel {self.selected_channel} is not in the ignored list.",
                        ephemeral=True,
                    )
        else:
            await interaction.response.send_message("No channel selected.", ephemeral=True)


class AutoPublisher(commands.Cog):
    """Automatically push news channel messages."""

    __version__: Final[str] = "2.1.4"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/AutoPublisher.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=15786223, force_registration=True)
        default_guild: Dict[str, Union[bool, List[int]]] = {
            "toggle": False,
            "ignored_channels": [],
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message) -> None:
        """Publish message to news channel."""
        if message.guild is None:
            return

        # Reduce the number of return statements: Having many return statements can make the code harder to follow.
        # You can combine some of the conditions using logical operators. Cool right?
        isAutoPublisherEnabled = await self.config.guild(message.guild).toggle()
        ignoredChannels = await self.config.guild(message.guild).ignored_channels()
        isCogDisabled = await self.bot.cog_disabled_in_guild(self, message.guild)
        hasPermissions = (
            message.guild.me.guild_permissions.manage_messages
            and message.guild.me.guild_permissions.view_channel
        )
        isNewsFeatureEnabled = "NEWS" in message.guild.features
        isTextChannel = isinstance(message.channel, discord.TextChannel)
        isNewsChannel = isTextChannel and message.channel.is_news()

        if (
            not isAutoPublisherEnabled
            or message.channel.id in ignoredChannels
            or isCogDisabled
            or not hasPermissions
        ):
            return
        if not isNewsFeatureEnabled:
            if isAutoPublisherEnabled:
                await self.config.guild(message.guild).toggle.set(False)
                log.warning(
                    f"AutoPublisher has been disabled in {message.guild} due to News Channel feature is not enabled."
                )
            return
        if not isNewsChannel and isTextChannel:
            return
        if isTextChannel and isNewsChannel:
            try:
                await asyncio.sleep(0.5)
                await asyncio.wait_for(message.publish(), timeout=60)
            except (
                discord.HTTPException,
                discord.Forbidden,
                asyncio.TimeoutError,
            ) as e:
                log.error(e)

    @commands.group(aliases=["aph", "autopub"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def autopublisher(self, ctx: commands.Context) -> None:
        """Manage AutoPublisher setting."""

    @autopublisher.command()
    @commands.bot_has_permissions(manage_messages=True, view_channel=True)
    async def toggle(self, ctx: commands.Context):
        """Toggle AutoPublisher enable or disable.

        - It's disabled by default.
            - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.

        **Note:**
        - This cog requires News Channel. If you don't have it, you can't use this cog.
            - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)
        """
        if "NEWS" not in ctx.guild.features:
            view = discord.ui.View()
            style = discord.ButtonStyle.gray
            discordinfo = discord.ui.Button(
                style=style,
                label="Learn more here",
                url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                emoji="<:icons_info:880113401207095346>",
            )
            view.add_item(item=discordinfo)
            return await ctx.send(
                f"Your server doesn't have News Channel feature. Please enable it first.",
                view=view,
            )
        await self.config.guild(ctx.guild).toggle.set(
            not await self.config.guild(ctx.guild).toggle()
        )
        toggle = await self.config.guild(ctx.guild).toggle()
        await ctx.send(f"AutoPublisher has been {'enabled' if toggle else 'disabled'}.")

    @autopublisher.command()
    async def ignorechannel(self, ctx: commands.Context):
        """Ignore a news channel to prevent AutoPublisher from publishing messages in it.

        Please note select menu's can't view more than 25 channels.

        - This command will show a select menu to choose one or more news channel(s) to ignore.

        **Note:**
        - Use `Confirm` button to confirm the selected channel(s) to ignore.
        - Use `Remove` button to remove the selected channel(s) from the ignored list.
        """
        if not "NEWS" in ctx.guild.features:
            view = discord.ui.View()
            style = discord.ButtonStyle.gray
            discordinfo = discord.ui.Button(
                style=style,
                label="Learn more here",
                url="https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server",
                emoji="<:icons_info:880113401207095346>",
            )
            view.add_item(item=discordinfo)
            return await ctx.send(
                f"Your server doesn't have News Channel feature. Please enable it first.",
                view=view,
            )

        # Check if there are any news channels
        news_channels = [channel for channel in ctx.guild.text_channels if channel.is_news()]
        if not news_channels:
            return await ctx.send("There are no news channels available to ignore.")

        view = ChannelView(self.bot, self.config, ctx.guild.id)
        message = await ctx.send("Select a news channel to ignore:", view=view)
        view.message = message  # Set the message reference in the view

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command(aliases=["view"])
    async def settings(self, ctx: commands.Context) -> None:
        """Show AutoPublisher setting."""
        data = await self.config.guild(ctx.guild).all()
        toggle = data["toggle"]
        channels = data["ignored_channels"]
        ignored_channels: List[str] = []
        for channel in channels:
            channel = ctx.guild.get_channel(channel)
            ignored_channels.append(channel.mention)
        msg = (
            f"AutoPublisher is currently {'enabled' if toggle else 'disabled'}.\n"
            f"Ignored channels: {humanize_list(ignored_channels) if ignored_channels else 'None'}"
        )
        embed = discord.Embed(
            title="AutoPublisher Setting",
            description=msg,
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @autopublisher.command()
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

    @autopublisher.command()
    async def reset(self, ctx: commands.Context) -> None:
        """Reset AutoPublisher setting."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset AutoPublisher setting?", view=view
        )
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            await ctx.send("AutoPublisher setting has been reset.")
        else:
            await ctx.send("AutoPublisher setting reset has been cancelled.")
