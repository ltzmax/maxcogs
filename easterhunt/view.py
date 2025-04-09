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

import discord

log = logging.getLogger("red.maxcogs.easterhunt.view")


class EasterWork(discord.ui.View):
    def __init__(self, cog, user):
        super().__init__(timeout=180)
        self.cog = cog
        self.user = user

    async def disable_buttons(self):
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(f"Failed to edit message: {e}")

    async def on_timeout(self) -> None:
        await self.disable_buttons()

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.id == self.user.id:
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Stealer", style=discord.ButtonStyle.red)
    async def stealer(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await self.disable_buttons()
        await self.cog.start_job(interaction, "stealer", self.user)

    @discord.ui.button(label="Store Clerk", style=discord.ButtonStyle.green)
    async def store_clerk(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await self.disable_buttons()
        await self.cog.start_job(interaction, "store_clerk", self.user)

    @discord.ui.button(label="Egg Giver", style=discord.ButtonStyle.blurple)
    async def egg_giver(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await self.disable_buttons()
        await self.cog.start_job(interaction, "egg_giver", self.user)
