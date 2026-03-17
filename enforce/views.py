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

import discord
from red_commons.logging import getLogger
from redbot.core import Config

log = getLogger("red.maxcogs.enforce.views")


class AcceptView(discord.ui.View):
    """Accept view with timeout"""

    def __init__(self, config: Config, author: discord.User):
        super().__init__(timeout=120)
        self.config = config
        self.author = author
        self.original_message: discord.Message | None = None

    async def on_timeout(self) -> None:
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True

        if self.original_message is None:
            log.debug("on_timeout called but original_message is None - no edit possible")
            return

        try:
            await self.original_message.edit(view=self)
            log.debug("View timed out - buttons disabled on original message")
        except (discord.NotFound, discord.HTTPException) as e:
            log.info(f"Could not edit message on timeout: {type(e).__name__} - {e}")

    @discord.ui.button(label="Accept Terms", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user.id != self.author.id:
            return await interaction.response.send_message(
                "You are not the author of this command.", ephemeral=True
            )

        await self.config.user(user).accepted_tos.set(True)
        await self.config.user(user).accepted_at.set(int(interaction.created_at.timestamp()))

        button.disabled = True
        accepted_embed = discord.Embed(
            title="Thank you!",
            description=(
                "You have accepted the Terms of Service and Privacy Policy.\n"
                "You may now use all commands."
            ),
            color=0xB1FF00,
        )

        try:
            if self.original_message:
                await self.original_message.edit(embed=accepted_embed, view=self)
                await interaction.response.defer()
            else:
                await interaction.response.edit_message(embed=accepted_embed, view=self)
        except (discord.NotFound, discord.HTTPException) as e:
            log.info(f"Could not edit message on accept: {type(e).__name__} - {e}")
            await interaction.response.send_message(embed=accepted_embed, ephemeral=True)
