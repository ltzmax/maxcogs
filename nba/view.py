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

import re

import aiohttp
import discord
from red_commons.logging import getLogger

from .converter import PLAYBYPLAY


log = getLogger("red.maxcogs.nba.view")


class PreGameView(discord.ui.View):
    """Persistent view with watch links for the pre-game notification."""

    def __init__(self, game_id: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Watch on NBA.com",
                emoji="🏀",
                style=discord.ButtonStyle.link,
                url=f"https://www.nba.com/game/{game_id}",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="NBA League Pass",
                emoji="📺",
                style=discord.ButtonStyle.link,
                url="https://www.nba.com/leaguepass",
            )
        )


class PlayByPlay(discord.ui.View):
    def __init__(self, game_id):
        super().__init__(timeout=None)
        self.game_id = game_id

    @discord.ui.button(label="View Play by Play", style=discord.ButtonStyle.blurple, emoji="🏀")
    async def view_play_by_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        url = f"{PLAYBYPLAY}/liveData/playbyplay/playbyplay_{self.game_id}.json"
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as response:
                if response.status != 200:
                    return await interaction.response.send_message(
                        f"Failed to fetch play-by-play data (status {response.status}).",
                        ephemeral=True,
                    )
                play_by_play_data = await response.json()
        except aiohttp.ClientError as e:
            log.error("Network error fetching play-by-play for game %s: %s", self.game_id, e)
            return await interaction.response.send_message(
                "Network error fetching play-by-play. Please try again.", ephemeral=True
            )

        actions = play_by_play_data.get("game", {}).get("actions", [])
        if not actions:
            return await interaction.response.send_message(
                "No play-by-play data available yet.", ephemeral=True
            )

        last_actions = actions[-9:]
        embed = discord.Embed(
            title="Play by Play",
            color=0x3820F0,
            description="Only the last 9 actions are displayed",
        )
        for action in last_actions:
            embed.add_field(
                name=f"Team: {action.get('teamTricode', 'N/A')}",
                value=(
                    f"**Description**: {action.get('description', 'N/A')}\n"
                    f"**Points Total**: {action.get('pointsTotal', 'N/A')}\n"
                    f"**Action Type**: {action.get('actionType', 'N/A')}\n"
                    f"**Shot Distance**: {action.get('shotDistance', 'N/A')}\n"
                    f"**Area**: {action.get('area', 'N/A')}\n"
                    f"**Area Details**: {action.get('areaDetail', 'N/A')}\n"
                    f"**SubType**: {action.get('subType', 'N/A')}\n"
                    f"**Side**: {action.get('side', 'N/A')}"
                ),
            )
        embed.set_footer(text="🏀Provided by NBA")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class GameMenu(discord.ui.View):
    def __init__(self, pages, ctx):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = 0
        self.message = None
        self.author = ctx[0].author if isinstance(ctx, list) else ctx.author

        options = [
            discord.SelectOption(
                label=(
                    re.sub(r"<:[^:]+:\d+>\s*", "", embed.fields[0].name).replace(":", "").strip()
                    + " vs "
                    + re.sub(r"<:[^:]+:\d+>\s*", "", embed.fields[1].name).replace(":", "").strip()
                )[:100],
                value=str(i),
            )
            for i, embed in enumerate(pages)
        ]
        self.select_menu.options = options

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.HTTPException as e:
            log.error("Failed to edit GameMenu on timeout: %s", e)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(
                "I cannot let you interact with this menu because you are not the author.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.select(placeholder="Choose a match", options=[])
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_page = int(self.select_menu.values[0])
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
