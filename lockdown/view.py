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
from redbot.core import commands

logger = getLogger("red.maxcogs.lockdown.view")


class UnlockView(discord.ui.View):
    def __init__(self, ctx: commands.Context, is_thread: bool = False):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.is_thread = is_thread

        button = discord.ui.Button(
            label=f"Unlock {'Thread' if self.is_thread else 'Channel'}",
            style=discord.ButtonStyle.green,
            emoji="🔓",
        )
        button.callback = self.unlock_button
        self.add_item(button)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            logger.error(f"Failed to edit view on timeout: {e}")

    async def unlock_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                "You are not the author of this command.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        target_role = self.ctx.guild.default_role
        is_locked: bool
        if self.is_thread:
            is_locked = self.ctx.channel.locked
        else:
            overwrites = (
                self.ctx.channel.overwrites_for(target_role) or discord.PermissionOverwrite()
            )
            is_locked = overwrites.send_messages is False
        if not is_locked:
            await interaction.followup.send(
                "This thread/channel is already unlocked.", ephemeral=True
            )
        else:
            await self.ctx.cog.manage_lock(self.ctx, "unlock")
            await interaction.followup.send("Unlocked!", ephemeral=True)
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
            if self.ctx.channel.id in self.ctx.cog.lock_views:
                del self.ctx.cog.lock_views[self.ctx.channel.id]
        except discord.HTTPException as e:
            logger.error(f"Failed to edit message after unlock: {e}")
