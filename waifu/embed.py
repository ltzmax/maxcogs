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

log = logging.getLogger("red.maxcogs.waifu")

NEKOS_API = "https://nekos.best/api/v2/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


async def api_call(self, ctx):
    async with self.session.get(NEKOS_API + "waifu") as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        url = await response.json()
        return url


async def embedgen(self, ctx, url):
    artist_name = url["results"][0]["artist_name"]
    source_url = url["results"][0]["source_url"]
    artist_href = url["results"][0]["artist_href"]
    emb = discord.Embed(
        title="Here's a pic of waifus",
        description=f"**Artist:** [{artist_name}]({artist_href})\n**Source:** {source_url}",
    )
    emb.colour = await ctx.embed_color()
    emb.set_image(url=url["results"][0]["url"])
    emb.set_footer(text="Powered by nekos.best", icon_url=ICON)
    view = discord.ui.View()
    style = discord.ButtonStyle.gray
    artist = discord.ui.Button(
        style=style,
        label="Artist",
        url=artist_href,
    )
    source = discord.ui.Button(
        style=style,
        label="Source",
        url=source_url,
    )
    image = discord.ui.Button(
        style=style,
        label="Open Image",
        url=url["results"][0]["url"],
    )
    view.add_item(item=artist)
    view.add_item(item=source)
    view.add_item(item=image)
    try:
        await ctx.send(embed=emb, view=view)
    except discord.HTTPException as e:
        meg = "Something went wrong. Please contact bot owner for infromation."
        # Based on https://github.com/flaree/flare-cogs/blob/501f8d25d939fa183b18addde96ad06eb26d4890/giveaways/giveaways.py#L473
        if await self.bot.is_owner(ctx.author):
            meg += "Something went wrong. Check your console for more details."
        await ctx.send(meg)
        log.error(e)
