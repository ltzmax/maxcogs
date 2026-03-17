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

from datetime import datetime

import discord


class NewsLayout(discord.ui.LayoutView):
    def __init__(
        self, title: str, description: str, image_url: str | None, article_url: str
    ) -> None:
        super().__init__(timeout=None)

        main_container = discord.ui.Container(accent_color=discord.Color.from_rgb(0, 120, 215))
        main_container.add_item(discord.ui.TextDisplay(f"**{title}**"))
        main_container.add_item(discord.ui.TextDisplay(description))
        action_row = discord.ui.ActionRow()
        action_row.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Read Full Article",
                url=article_url,
                emoji="🔗",
            )
        )
        main_container.add_item(action_row)
        if image_url:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=image_url, description="Article preview image")
            main_container.add_item(gallery)

        main_container.add_item(discord.ui.Separator())
        now = datetime.utcnow()
        timestamp_markdown = f"<t:{int(now.timestamp())}:f>"
        main_container.add_item(discord.ui.TextDisplay(f"*From Wccftech • {timestamp_markdown}*"))
        self.add_item(main_container)
