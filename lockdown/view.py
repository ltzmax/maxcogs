import logging

import discord

log = logging.getLogger("red.maxcogs.lockdown.view")


class UnlockView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(e)

    @discord.ui.button(label="Unlock Channel", style=discord.ButtonStyle.green, emoji="🔓")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.id == self.ctx.author.id:
            return await interaction.response.send_message(
                "You are not the author of this command.", ephemeral=True
            )
        await self.ctx.cog.manage_lock(self.ctx, "unlock")
        button.disabled = True
        await interaction.response.edit_message(view=self)
