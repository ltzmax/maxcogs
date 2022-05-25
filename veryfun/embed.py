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

log = logging.getLogger("red.maxcogs.veryfun")

NEKOS = "https://nekos.best/api/v2/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


async def api_call(self, ctx, action: str):
    async with ctx.typing():
        pass
    async with self.session.get(NEKOS + action) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        url = await response.json()
        return url


async def embedgen(self, ctx, user, url, action: str):
    anime_name = url["results"][0]["anime_name"]
    image = url["results"][0]["url"]

    emb = discord.Embed(
        colour=await ctx.embed_color(),
        description=f"**{ctx.author.mention}** {action} {f'**{str(user.mention)}**' if user.id != ctx.author.id else 'themselves'}!",
    )
    emb.set_footer(
        text=f"Powered by nekos.best | Anime: {anime_name}",
        icon_url=ICON,
    )
    emb.set_image(url=image)
    try:
        await ctx.send(embed=emb)
    except discord.HTTPException as e:
        meg = "Something went wrong. Please contact bot owner for infromation."
        # Based on https://github.com/flaree/flare-cogs/blob/501f8d25d939fa183b18addde96ad06eb26d4890/giveaways/giveaways.py#L473
        if await self.bot.is_owner(ctx.author):
            meg += "Something went wrong. Check your console for more details."
        await ctx.send(meg)
        log.error(e)
