import logging

import discord

log = logging.getLogger("red.maxcogs.veryfun")

NEKOS = "https://nekos.best/api/v1/"
ICON = "https://cdn.discordapp.com/icons/850825316766842881/070d7465948cdcf9004630fa8629627b.webp?size=1024"


async def api_call(self, ctx, action: str):
    async with self.session.get(NEKOS + action) as response:
        if response.status != 200:
            return await ctx.send("Something went wrong while trying to contact API.")
        url = await response.json()
        return url


async def embedgen(self, ctx, user, url, action: str):
    emb = discord.Embed(
        colour=await ctx.embed_color(),
        description=f"**{ctx.author.mention}** {action} {f'**{str(user.mention)}**' if user else 'themselves'}!",
    )
    emb.set_footer(
        text="Powered by nekos.best | Anime: %s" % (url["anime_name"]),
        icon_url=ICON,
    )
    emb.set_image(url=url["url"])
    try:
        await ctx.send(
            "{}".format(user.mention),
            allowed_mentions=discord.AllowedMentions(
                users=await self.config.guild(
                    ctx.guild
                ).mention()  # based on https://github.com/fixator10/Fixator10-Cogs/blob/e950123e2a4839a0637c495d2ef5213055d422db/leveler/commands/profiles.py#L38
            ),
            embed=emb,
        )
    except discord.HTTPException as e:
        await ctx.send(
            "Something went wrong while posting. Check your console for details."
        )
        log.error(f"Command '{ctx.command.name}' failed to post: {e}")
