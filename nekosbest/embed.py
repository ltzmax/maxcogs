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

NEKOS_API = "https://nekos.best/api/v2/"
ICON = "https://nekos.best/logo_short.png"


async def api_call(self, ctx, endpoint: str):
    await ctx.typing()
    async with self.session.get(NEKOS_API + endpoint) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        url = await response.json()
        return url


async def embedgen(self, ctx, url, endpoint: str):
    artist_name = url["results"][0]["artist_name"]
    source_url = url["results"][0]["source_url"]
    artist_href = url["results"][0]["artist_href"]
    image = url["results"][0]["url"]

    emb = discord.Embed(
        title=f"Here's a picture of a {endpoint}",
        description=f"**Artist:** [{artist_name}]({artist_href})\n**Source:** {source_url}",
    )
    emb.colour = await ctx.embed_color()
    emb.set_image(url=image)
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
        url=image,
    )
    view.add_item(item=artist)
    view.add_item(item=source)
    view.add_item(item=image)
    await ctx.send(embed=emb, view=view)
