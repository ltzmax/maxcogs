import discord
from redbot.core import commands


class ResetSpoilerFilterConfirm(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.author = ctx.author
        self.message = ctx.message
        self.value = None

    # example taken from core but with a bit modification
    # https://github.com/Cog-Creators/Red-DiscordBot/blob/44e129bc66ef71844676743c99f20560658469da/redbot/core/utils/views.py#LL194-L202C47
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.Forbidden:
            pass

    # example taken from core but with a bit modification
    # https://github.com/Cog-Creators/Red-DiscordBot/blob/44e129bc66ef71844676743c99f20560658469da/redbot/core/utils/views.py#LL417-L423C20
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.id == self.ctx.author.id:
            await interaction.response.send_message(
                ("You are not the author of this command."), ephemeral=True
            )
            return False
        return True

    # fixator10 helped me with this part of code.
    async def disable_items(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = True
        await self.disable_items(interaction)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = False
        await self.disable_items(interaction)
        self.stop()
