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

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import discord
from red_commons.logging import getLogger

logger = getLogger("red.maxcogs.counting.utils")


async def send_message(
    channel: discord.TextChannel,
    content: str,
    *,
    delete_after: int | None = None,
    silent: bool = False,
) -> discord.Message | None:
    """Send a message with error handling."""
    try:
        send_kwargs = {"content": content, "silent": silent}
        if delete_after is not None:
            send_kwargs["delete_after"] = delete_after
        return await channel.send(**send_kwargs)
    except discord.Forbidden:
        logger.warning(
            f"Missing send permissions in {channel.guild.name}#{channel.name} ({channel.id})"
        )
    except discord.HTTPException as e:
        logger.warning(f"Failed to send message in {channel.id}: {e}")
    return None


async def delete_message(message: discord.Message) -> None:
    """Delete a message with error handling."""
    try:
        await message.delete()
    except discord.HTTPException as e:
        logger.warning(f"Failed to delete message {message.id} in {message.channel.id}: {e}")


async def add_reaction(message: discord.Message, reaction: str) -> None:
    """Add a reaction with a delay."""
    await asyncio.sleep(0.3)
    try:
        await message.add_reaction(reaction)
    except discord.HTTPException as e:
        logger.warning(f"Failed to add reaction to {message.id} in {message.channel.id}: {e}")


async def handle_invalid_count(
    message: discord.Message,
    response: str,
    settings: dict[str, any],
    send_response: bool = True,
) -> None:
    """Handle invalid counts by deleting and optionally responding."""
    await delete_message(message)
    if send_response:
        delete_after = (
            settings["delete_after"] if settings.get("toggle_delete_after", True) else None
        )
        await send_message(
            message.channel,
            response,
            delete_after=delete_after,
            silent=settings["use_silent"],
        )


async def assign_ruin_role(
    bot: discord.Client,
    member: discord.Member, 
    guild: discord.Guild, 
    settings: dict[str, any]
) -> None:
    """Assign the ruin role to a member, temporarily if a duration is set."""
    ruin_role_id = settings["ruin_role_id"]
    duration = settings["ruin_role_duration"]
    excluded_role_ids = settings["excluded_roles"]

    if not ruin_role_id:
        return

    role = guild.get_role(ruin_role_id)
    if not role or role >= guild.me.top_role:
        logger.warning(f"Cannot assign ruin role {role.name} in {guild.name} ({guild.id})")
        return

    if any(r.id in excluded_role_ids for r in member.roles):
        logger.warning(f"User {member.display_name} has excluded role(s) in {guild.name}")
        return

    try:
        if not guild.me.guild_permissions.manage_roles:
            logger.warning(f"Missing manage_roles permission in {guild.name} ({guild.id})")
            return
        await member.add_roles(role, reason="Ruined the count")
        if duration:
            expiry = datetime.now(timezone.utc) + timedelta(seconds=duration)
            async with bot.config.guild(guild).temp_roles() as temp_roles:
                temp_roles[str(member.id)] = {
                    "role_id": role.id,
                    "expiry": expiry.timestamp(),
                }
    except discord.Forbidden:
        logger.warning(f"Missing permissions to assign role {role.name} in {guild.name}")


async def remove_expired_roles(bot: discord.Client, guild: discord.Guild) -> None:
    """Remove expired temporary roles from users in a guild."""
    async with bot.config.guild(guild).temp_roles() as temp_roles:
        to_remove = []
        for user_id, data in temp_roles.items():
            if datetime.now(timezone.utc).timestamp() >= data["expiry"]:
                member = guild.get_member(int(user_id))
                role = guild.get_role(data["role_id"])
                if member and role:
                    try:
                        await member.remove_roles(role, reason="Temporary ruin role expired")
                    except discord.Forbidden as e:
                        logger.warning(f"Failed to remove role {role.name}: {e}")
                to_remove.append(user_id)
        for user_id in to_remove:
            del temp_roles[user_id]
