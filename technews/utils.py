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
from typing import Union

# Type alias for supported destinations
ChannelOrThread = Union[discord.TextChannel, discord.Thread]
def _can_post(me: discord.Member, channel: ChannelOrThread) -> bool:
    """
    Check whether the bot can send messages and embed links in the given
    channel or thread.

    Threads inherit permissions from their parent channel, but also have their
    own archived/locked state that prevents posting regardless of permissions.
    """
    if isinstance(channel, discord.Thread):
        if channel.archived:
            return False
        parent = channel.parent
        if parent is None:
            return False
        perms = parent.permissions_for(me)
    else:
        perms = channel.permissions_for(me)
    return perms.send_messages and perms.embed_links
