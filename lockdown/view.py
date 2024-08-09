import discord


class UnlockView(discord.ui.View):
    def __init__(self, ctx, reason):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.reason = reason

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == interaction.user.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Unlock Channel", style=discord.ButtonStyle.green, emoji="🔓")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ctx.cog.manage_lock(self.ctx, "unlock", reason=self.reason)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"🔓 {interaction.user.mention} This channel has now been unlocked",
            ephemeral=True,
        )
