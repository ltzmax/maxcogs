"""
MIT License

Copyright (c) 2022-2023 phenom4n4n
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
# Original source:
# https://github.com/phenom4n4n/phen-cogs/blob/5b12bd42831bded0e52a67a4eef19616f10bbe25/roleutils/converters.py#L112-L123
import discord
import logging
from typing import Union
from redbot.core import commands

log = logging.getLogger("red.maxcogs.achievements.converters")


class EmojiConverter(commands.EmojiConverter):
    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Union[discord.Emoji, str]:
        try:
            emoji = await super().convert(ctx, argument)
        except commands.BadArgument:
            try:
                await ctx.message.add_reaction(argument)
            except discord.HTTPException as e:
                log.error(e)
                raise commands.EmojiNotFound(argument)
            else:
                emoji = argument
        return emoji
