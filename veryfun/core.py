import discord
import logging

log = logging.getLogger("red.maxcogs.veryfun")

NEKOS = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/emojis/851544845956415488.png?v=1"


async def api_call(self, ctx, action: str):
    async with self.session.get(NEKOS + action) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        if response.status == 502:
            return await ctx.send("Api is currently down, try again later.")
        url = await response.json()
        return url


async def embedgen(self, ctx, user, url, action: str):
    emb = discord.Embed(
        colour=await ctx.embed_color(),
        description=f"**{ctx.author.mention}** {action} {f'**{str(user.mention)}**' if user else 'themselves'}!",
    )
    emb.set_footer(
        text="Powered by nekos.best",
        icon_url=ICON,
    )
    try:
        emb.set_image(url=url["url"])
    except KeyError:
        return await ctx.send("I ran into an issue. please try again later.")
    try:
        await ctx.send(f"{str(user.mention)}", embed=emb)
    except discord.HTTPException as e:
        await ctx.send(
            "Something went wrong while posting. Check your console for details."
        )
        log.error(f"Command '{ctx.command.name}' failed to post: {e}")
