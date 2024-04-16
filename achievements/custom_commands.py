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
from redbot.core import commands
from redbot.core.utils.views import ConfirmView

from .abc import MixinMeta, CompositeMetaClass

log = logging.getLogger("red.maxcogs.achievements.custom_commands")


class CustomCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.group()
    @commands.guild_only()
    @commands.guildowner()
    async def customset(self, ctx):
        """Custom achievements commands.

        Only guild owners can use these commands.

        Custom achievements are disabled by default. Enable them with `[p]customset enable`.
        This will allow you to add, remove, and list custom achievements for your server.
        """

    @customset.command()
    async def enable(self, ctx):
        """Toggle custom achievements."""
        use_default_achievements = await self.config.guild(
            ctx.guild
        ).use_default_achievements()
        await self.config.guild(ctx.guild).use_default_achievements.set(
            not use_default_achievements
        )
        if use_default_achievements:
            await ctx.send("Custom achievements are now enabled.")
        else:
            await ctx.send("Custom achievements are now disabled.")

    @customset.command()
    async def add(self, ctx, name: str, value: str):
        """Add a custom achievement.

        You must have custom achievements enabled to use this command.

        Example:
        - `[p]achievement custom add Epic 1000`
        - `[p]achievement custom add Legendary 10000`

        Arguments:
        - `<name>`: The name of the achievement. (must be between 1 and 256 characters)
        - `<value>`: The message count required to unlock the achievement. (must be an integer)
        """
        if await self.config.guild(ctx.guild).use_default_achievements():
            return await ctx.send(
                "Custom achievements are disabled.\nEnable them with `{prefix}achievement custom toggle`".format(
                    prefix=ctx.clean_prefix
                )
            )
        if len(name) > 256 or len(name) < 1:
            return await ctx.send("Name must be between 1 and 256 characters.")
        try:
            value = int(value)
        except ValueError as e:
            return await ctx.send("The value must be a number (integer).")
            log.error(e)
        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        if value in custom_achievements.values():
            return await ctx.send("That value is already an achievement.")
        if value < 5:
            return await ctx.send("The value must be at least 5.")
        if name in await self.config.guild(ctx.guild).custom_achievements():
            return await ctx.send("That achievement already exists.")
        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        custom_achievements[name] = value
        await self.config.guild(ctx.guild).custom_achievements.set(custom_achievements)
        await ctx.send(f"Added `{name}` achievement for `{value}` messages.")

    @customset.command()
    async def remove(self, ctx, name: str):
        """Remove a custom achievement.

        Example:
        - `[p]achievement custom remove Epic`
        - `[p]achievement custom remove Legendary`

        Arguments:
        - `<name>`: The name of the achievement. You can get the name from `[p]achievement list`.
        """

        custom_achievements = await self.config.guild(ctx.guild).custom_achievements()
        if name in custom_achievements:
            del custom_achievements[name]
            await self.config.guild(ctx.guild).custom_achievements.set(
                custom_achievements
            )
            await ctx.send(f"Removed `{name}` achievement.")
        else:
            await ctx.send("That achievement does not exist.")

    @customset.command()
    async def clear(self, ctx):
        """Clear all custom achievements."""
        if not await self.config.guild(ctx.guild).custom_achievements():
            return await ctx.send("There are no custom achievements to clear.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "## [WARNING] You are about to clear all custom achievements. Are you sure you want to continue?",
            view=view,
        )
        await view.wait()
        if view.result:
            await ctx.typing()
            await self.config.guild(ctx.guild).custom_achievements.set({})
            await ctx.send("Custom achievements cleared.")
            log.info(f"{ctx.author} cleared all custom achievements in {ctx.guild}.")
        else:
            await ctx.send("Not clearing.")
