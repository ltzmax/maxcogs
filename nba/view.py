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

import aiohttp
import discord

from .converter import PLAYBYPLAY


class PlayByPlay(discord.ui.View):
    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    @discord.ui.button(label="View Play by Play", style=discord.ButtonStyle.blurple, emoji="🏀")
    async def view_play_by_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{PLAYBYPLAY}/liveData/playbyplay/playbyplay_{self.game_id}.json"
            ) as response:
                play_by_play_data = await response.json()

        last_actions = play_by_play_data["game"]["actions"][-9:]

        embed = discord.Embed(
            title="Play by Play",
            color=0x3820F0,
            description="Latest Play by Play update before score update",
        )
        for action in last_actions:
            description = action.get("description", "N/A")
            area = action.get("area", "N/A")
            area_details = action.get("areaDetail", "N/A")
            sub_type = action.get("subType", "N/A")
            side = action.get("side", "N/A")
            action_type = action.get("actionType", "N/A")
            shot_type = action.get("shotDistance", "N/A")
            point = action.get("pointsTotal", "N/A")
            embed.add_field(
                name=f"Team: {action.get('teamTricode', 'N/A')}",
                value=f"**Description**: {description}\n**Points Total**: {point}\n**Action Type**: {action_type}\n**Shot Distance**: {shot_type}\n**Area**: {area}\n**Area Details**: {area_details}\n**SubType**: {sub_type}\n**Side**: {side}",
            )
            embed.set_footer(text="🏀Provided by NBA")
        await interaction.response.send_message(embed=embed, ephemeral=True)
