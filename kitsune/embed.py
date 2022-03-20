import logging

import discord

log = logging.getLogger("red.maxcogs.kitsune")

NEKOS_API = "https://nekos.best/api/v2/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


async def api_call(self, ctx):
    async with ctx.typing():
        pass
    async with self.session.get(NEKOS_API + "kitsune") as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        url = await response.json()
        return url


async def embedgen(self, ctx, url):
    artist_name = url["results"][0]["artist_name"]
    source_url = url["results"][0]["source_url"]
    artist_href = url["results"][0]["artist_href"]
    emb = discord.Embed(
        title="Here's a pic of kitsune",
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
        meg = "Something went wrong. " "Please contact bot owner for infromation."
        # Based on https://github.com/flaree/flare-cogs/blob/501f8d25d939fa183b18addde96ad06eb26d4890/giveaways/giveaways.py#L473
        if await self.bot.is_owner(ctx.author):
            meg += "Something went wrong. Check your console for more details."
        await ctx.send(meg)
        log.error(e)
