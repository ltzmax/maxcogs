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
from redbot.core.utils.chat_formatting import header

log = getLogger("red.maxcogs.easterhunt.view")


class EasterWork(discord.ui.LayoutView):
    def __init__(self, cog, user):
        super().__init__(timeout=180)
        self.cog = cog
        self.user = user

        main_container = discord.ui.Container(accent_color=discord.Color.blurple())
        title = "The Easter Bunny’s hiring! Pick a job"
        main_container.add_item(discord.ui.TextDisplay(f"{header(title, 'medium')}"))
        combined_desc = (
            "- **Stealer**: Snag eggs from unsuspecting users.\n"
            "- **Store Clerk**: Sell eggs at the Egg Emporium.\n"
            "- **Egg Giver**: Spread Easter cheer with free eggs.\n"
            "- **Egg Painter**: Paint eggs for rewards.\n"
            "- **Gem Miner**: Mine for hidden gems.\n"
            "   - (Require completion of `Egg Collector` achievement)"
        )
        main_container.add_item(discord.ui.TextDisplay(combined_desc))
        action_row = discord.ui.ActionRow()
        action_row.add_item(JobSelect(self.cog, self.user))
        main_container.add_item(action_row)
        main_container.add_item(discord.ui.TextDisplay("Every shift lasts 5 minutes."))
        self.add_item(main_container)

    async def disable_items(self):
        for item in self.walk_children():
            if hasattr(item, "disabled"):
                item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error(f"Failed to edit message: {e}")

    async def on_timeout(self) -> None:
        await self.disable_items()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You are not allowed to use this interaction.", ephemeral=True
            )
            return False
        return True


class JobSelect(discord.ui.Select):
    def __init__(self, cog, user):
        self.cog = cog
        self.user = user
        options = [
            discord.SelectOption(label="Stealer", value="stealer", emoji="🕵️"),
            discord.SelectOption(label="Store Clerk", value="store_clerk", emoji="🏪"),
            discord.SelectOption(label="Egg Giver", value="egg_giver", emoji="🥚"),
            discord.SelectOption(label="Egg Painter", value="egg_painter", emoji="🎨"),
            discord.SelectOption(label="Gem Miner", value="gem_miner", emoji="💎"),
        ]
        super().__init__(
            placeholder="Choose a job...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        job_type = self.values[0]
        await self.view.disable_items()
        await self.cog.start_job(interaction, job_type, self.user)
        self.view.stop()
