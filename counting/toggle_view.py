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

from typing import Any

import discord
from red_commons.logging import getLogger
from redbot.core import commands

log = getLogger("red.maxcogs.counting.toggle_view")
TOGGLES: list[tuple[str, str]] = [
    ("toggle", "Counting"),
    ("toggle_delete_after", "Delete After"),
    ("use_silent", "Silent"),
    ("toggle_reactions", "Reactions"),
    ("same_user_to_count", "Same User"),
    ("allow_ruin", "Ruin Count"),
    ("toggle_progress", "Progress"),
    ("toggle_goal_delete", "Goal Delete"),
    ("toggle_edit_message", "Edit Message"),
    ("toggle_next_number_message", "Count Message"),
]


def _build_embed(settings: dict[str, Any], color: discord.Color) -> discord.Embed:
    lines = []
    for key, label in TOGGLES:
        state = settings.get(key, False)
        icon = "✅" if state else "❌"
        status = "Enabled" if state else "Disabled"
        lines.append(f"{icon} **{label:<18}** {status}")

    embed = discord.Embed(
        title="⚙️ Counting Toggle Setup",
        description="\n".join(lines),
        color=color,
    )
    embed.set_footer(text="Click a button to toggle. Changes save immediately.")
    return embed


class ToggleSetupView(discord.ui.View):

    def __init__(
        self,
        ctx: commands.Context,
        settings_manager,
        settings: dict[str, Any],
    ) -> None:
        super().__init__(timeout=120)
        self.ctx = ctx
        self.settings_manager = settings_manager
        self.settings = dict(settings)
        self.message: discord.Message | None = None
        self._add_buttons()

    def _add_buttons(self) -> None:
        for index, (key, label) in enumerate(TOGGLES):
            state = self.settings.get(key, False)
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.success if state else discord.ButtonStyle.danger,
                custom_id=key,
                row=index // 5,
            )
            button.callback = self._make_callback(key)
            self.add_item(button)

    def _make_callback(self, config_key: str):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id not in [self.ctx.author.id] + list(self.ctx.bot.owner_ids):
                return await interaction.response.send_message(
                    "You are not allowed to use this.", ephemeral=True
                )

            new_value = not self.settings.get(config_key, False)
            self.settings[config_key] = new_value
            await self.settings_manager.update_guild(self.ctx.guild, config_key, new_value)
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == config_key:
                    item.style = (
                        discord.ButtonStyle.success if new_value else discord.ButtonStyle.danger
                    )
                    break

            embed = _build_embed(self.settings, await self.ctx.embed_color())
            await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException as e:
                log.error("Failed to disable toggle setup view on timeout: %s", e)
            except RuntimeError:
                # Bot is shutting down and the aiohttp session is already closed
                pass
