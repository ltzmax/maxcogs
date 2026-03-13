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

from typing import Union

import discord
from red_commons.logging import getLogger

log = getLogger("red.maxcogs.forwarddeleter.utils")


def is_forwarded_message(message: discord.Message) -> bool:
    """Determine if the message is forwarded."""
    reference = message.reference
    return reference is not None and reference.type == discord.MessageReferenceType.forward


def has_allowed_role(member: discord.Member, allowed_roles: set[int]) -> bool:
    """Check if the member has any allowed roles."""
    return any(role.id in allowed_roles for role in member.roles)


async def check_permissions(
    channel: Union[discord.TextChannel, discord.Thread], guild: discord.Guild
) -> bool:
    """Verify if the bot has manage_messages permission in the channel or thread."""
    perms = channel.permissions_for(guild.me)
    if not perms.manage_messages:
        log.warning(f"Missing manage_messages permission in {channel.mention} ({guild.id})")
        return False
    return True


async def send_warning(message: discord.Message, warn_message: str) -> None:
    """Send a warning to the user in the channel."""
    if message.channel.permissions_for(message.guild.me).send_messages:
        await message.channel.send(
            f"{message.author.mention} {warn_message}",
            delete_after=15,
        )
