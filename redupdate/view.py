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

import logging
import re

import discord
from redbot.core import Config

log = logging.getLogger("red.maxcogs.redupdate.view")
GITHUB = re.compile(r"^(git\+ssh://git@github\.com|git\+https://github\.com)")


class URLModalView(discord.ui.Modal, title="Set Your Custom Fork"):
    forkurl: discord.ui.TextInput = discord.ui.TextInput(
        label="Custom Fork URL",
        placeholder="Enter your fork URL here....",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class URLModal(discord.ui.View):
    def __init__(self, ctx, config):
        super().__init__(timeout=60)
        self.config = config
        self.ctx = ctx

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == self.ctx.author.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Add Your Fork", style=discord.ButtonStyle.blurple)
    async def on_submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = URLModalView()
        await interaction.response.send_modal(modal)
        await modal.wait()
        url = modal.forkurl.value  # Access the TextInput value from the modal
        if not GITHUB.match(url):
            await interaction.followup.send(
                f"This is not a valid url for your fork.\nCheck `redset whatlink` for more information.",
                ephemeral=True,
            )
            return
        if not url.endswith("#egg=Red-DiscordBot"):
            await interaction.followup.send(
                "This is not a valid url for your fork.", ephemeral=True
            )
            log.info(
                "This is not a valid url for your fork, please check `redset whatlink` for more information."
            )
            return
        data = await self.config.redupdate_url()
        if data == url:
            await interaction.followup.send("This url is already set.", ephemeral=True)
            return
        await self.config.redupdate_url.set(url)
        await interaction.followup.send("URL has been set successfully.", ephemeral=True)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await interaction.followup.send(f"An error occured: {error}", ephemeral=True)
        log.error(f"An error occured: {error}")


class RestartButton(discord.ui.View):
    def __init__(self, ctx, bot, *, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.clicked = False
        self.message = None  # Initialize the message attribute

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.HTTPException:
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.id == self.ctx.author.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        if self.clicked:
            await interaction.response.send_message(("Button already clicked."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.gray)
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clicked = True
        button.disabled = True
        await interaction.response.send_message("Restarting...", ephemeral=True)
        await interaction.message.edit(view=self)
        try:
            await self.bot.shutdown(restart=True)
        except Exception as e:
            await interaction.channel.send(f"Error restarting bot: {str(e)}")
            log.error(e)
