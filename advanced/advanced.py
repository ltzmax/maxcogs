import asyncio
import contextlib

import discord
import logging
from redbot.core import Config, commands
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

log = logging.getLogger("red.maxcogs.advanced")


class Advanced(commands.Cog):
    """Attempt to restart or shutdown [botname]."""

    __version__ = "0.0.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            rest_default="Are you sure you want to restart?",
            rest_confirm="Restarting...",
            rest_deny="Alright, i won't restart",
            shutdown_default="Are you sure you want to shutdown?",
            shutdown_confirm="Shutting down.. \N{WAVING HAND SIGN}",
            shutdown_deny="Fine, i won't shutdown!",
        )

    def cog_unload(self):
        global shutdown, restart
        if shutdown:
            try:
                self.bot.remove_command("shutdown")
            except Exception as e:
                log.info(e)
            self.bot.add_command(shutdown)
        if restart:
            try:
                self.bot.remove_command("restart")
            except Exception as e:
                log.info(e)
            self.bot.add_command(restart)

    @commands.is_owner()
    @commands.group()
    async def advancedset(self, ctx):
        """Settings to change restart and shutdown messages."""

    @advancedset.command(name="version")
    async def advancedset_version(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)

    @advancedset.group(aliases=["rest"])
    async def restart(self, ctx):
        """Settings for restart."""

    @restart.command(name="add", usage="<message>")
    async def restart_add(self, ctx, *, message: str = None):
        """Change the restart description message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.rest_default.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 1000:
            return await ctx.send("Your message must be 1000 or fewer in length.")
        if message:
            await self.config.rest_default.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @restart.command(name="confirm", aliases=["conf"], usage="<message>")
    async def restart_confirm(self, ctx, *, message: str = None):
        """Change the restart confirm message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.rest_confirm.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 1000:
            return await ctx.send("Your message must be 1000 or fewer in length.")
        if message:
            await self.config.rest_confirm.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @restart.command(name="deny", usage="<message>")
    async def restart_deny(self, ctx, *, message: str = None):
        """Change the restart deny message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.rest_deny.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 1000:
            return await ctx.send("Your message must be 1000 or fewer in length.")
        if message:
            await self.config.rest_deny.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @advancedset.group(aliases=["shut"])
    async def shutdown(self, ctx):
        """Settings for shutdown."""

    @shutdown.command(name="add", usage="<message>")
    async def shutdown_add(self, ctx, *, message: str = None):
        """Change the shutdown description message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.shutdown_default.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 1000:
            return await ctx.send("Your message must be 1000 or fewer in length.")
        if message:
            await self.config.shutdown_default.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @shutdown.command(name="confirm", aliases=["conf"], usage="<message>")
    async def shutdown_confirm(self, ctx, *, message: str = None):
        """Change the shutdown confirm message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.shutdown_confirm.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 2000:
            return await ctx.send("Your message must be 2000 or fewer in length.")
        if message:
            await self.config.shutdown_confirm.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @shutdown.command(name="deny", usage="<message>")
    async def shutdown_deny(self, ctx, *, message: str = None):
        """Change the shutdown deny message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.shutdown_deny.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 2000:
            return await ctx.send("Your message must be 2000 or fewer in length.")
        if message:
            await self.config.shutdown_deny.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @commands.is_owner()
    @commands.command(name="shutdown")
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _shutdown(self, ctx: commands.Context):
        """Shuts down [botname]."""
        em = discord.Embed(title=await self.config.shutdown_default())
        em.colour = await ctx.embed_color()
        msg = await ctx.send(embed=em)

        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=15)
        except asyncio.TimeoutError:
            em = discord.Embed(title="You took to long to response.")
            em.colour = await ctx.embed_color()
            await msg.edit(embed=em)
            with contextlib.suppress(discord.HTTPException):
                await msg.clear_reactions()
            return
        else:
            if pred.result is True:
                em = discord.Embed(title=await self.config.shutdown_confirm())
                em.colour = await ctx.embed_color()
                await msg.edit(embed=em)
                with contextlib.suppress(
                    discord.HTTPException, await ctx.bot.shutdown()
                ) as e:
                    log.info(e)
            else:
                em = discord.Embed(title=await self.config.shutdown_deny())
                em.colour = await ctx.embed_color()
                await msg.edit(embed=em)
                with contextlib.suppress(discord.HTTPException):
                    log.info("Shutdown denied.")

    @commands.is_owner()
    @commands.command(name="restart")
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _restart(self, ctx: commands.Context):
        """Attempts to restart [botname]."""
        em = discord.Embed(title=await self.config.rest_default())
        em.colour = await ctx.embed_color()
        msg = await ctx.send(embed=em)

        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=15)
        except asyncio.TimeoutError:
            em = discord.Embed(title="You took too long to response.")
            em.colour = await ctx.embed_color()
            await msg.edit(embed=em)
            with contextlib.suppress(discord.HTTPException):
                await msg.clear_reactions()
            return
        else:
            if pred.result is True:
                em = discord.Embed(title=await self.config.rest_confirm())
                em.colour = await ctx.embed_color()
                await msg.edit(embed=em)
                with contextlib.suppress(
                    discord.HTTPException, await ctx.bot.shutdown(restart=True)
                ) as e:
                    log.info(e)
            else:
                em = discord.Embed(title=await self.config.rest_deny())
                em.colour = await ctx.embed_color()
                await msg.edit(embed=em)
                with contextlib.suppress(discord.HTTPException):
                    log.info("Restart denied.")


def setup(bot):
    adv = Advanced(bot)
    global restart
    global shutdown
    restart = bot.remove_command("restart")
    shutdown = bot.remove_command("shutdown")
    bot.add_cog(adv)
