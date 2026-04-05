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
from redbot.core import Config


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
        send_kwargs: dict[str, Any] = {"content": content, "silent": silent}
        if delete_after is not None:
            send_kwargs["delete_after"] = delete_after
        return await channel.send(**send_kwargs)
    except discord.Forbidden:
        logger.warning(
            "Missing send permissions in %s#%s (%s)",
            channel.guild.name,
            channel.name,
            channel.id,
        )
    except discord.HTTPException as e:
        logger.warning("Failed to send message in %s: %s", channel.id, e)
    return None


async def delete_message(message: discord.Message) -> None:
    """Delete a message with error handling."""
    try:
        await message.delete()
    except discord.HTTPException as e:
        logger.warning("Failed to delete message %s in %s: %s", message.id, message.channel.id, e)


async def add_reaction(message: discord.Message, reaction: str) -> None:
    """Add a reaction with a small delay to avoid rate limits."""
    await asyncio.sleep(0.3)
    try:
        await message.add_reaction(reaction)
    except discord.HTTPException as e:
        logger.warning("Failed to add reaction to %s in %s: %s", message.id, message.channel.id, e)


async def handle_invalid_count(
    message: discord.Message,
    response: str,
    settings: dict[str, Any],
    send_response: bool = True,
) -> None:
    """Delete an invalid count message and optionally send a response."""
    await delete_message(message)
    if send_response:
        delete_after = (
            settings["delete_after"] if settings.get("toggle_delete_after", False) else None
        )
        await send_message(
            message.channel,
            response,
            delete_after=delete_after,
            silent=settings["use_silent"],
        )


async def assign_ruin_role(
    config: Config, member: discord.Member, guild: discord.Guild, settings: dict[str, Any]
) -> None:
    """Assign the ruin role to a member, temporarily if a duration is set."""
    ruin_role_id = settings["ruin_role_id"]
    duration = settings["ruin_role_duration"]
    excluded_role_ids = settings["excluded_roles"]

    if not ruin_role_id:
        return

    role = guild.get_role(ruin_role_id)
    if not role or role >= guild.me.top_role:
        logger.warning("Cannot assign ruin role %s in %s (%s)", ruin_role_id, guild.name, guild.id)
        return

    if any(r.id in excluded_role_ids for r in member.roles):
        logger.warning("User %s has excluded role(s) in %s", member.display_name, guild.name)
        return

    if not guild.me.guild_permissions.manage_roles:
        logger.warning("Missing manage_roles permission in %s (%s)", guild.name, guild.id)
        return

    try:
        await member.add_roles(role, reason="Ruined the count")
        if duration:
            expiry = datetime.now(timezone.utc) + timedelta(seconds=duration)
            async with config.guild(guild).temp_roles() as temp_roles:
                temp_roles[str(member.id)] = {
                    "role_id": role.id,
                    "expiry": expiry.timestamp(),
                }
    except discord.Forbidden:
        logger.warning("Missing permissions to assign role %s in %s", role.name, guild.name)


async def remove_expired_roles(config: Config, guild: discord.Guild) -> None:
    """Remove expired temporary roles from users in a guild."""
    async with config.guild(guild).temp_roles() as temp_roles:
        to_remove = []
        now_ts = datetime.now(timezone.utc).timestamp()
        for user_id, data in temp_roles.items():
            if now_ts < data["expiry"]:
                continue
            member = guild.get_member(int(user_id))
            role = guild.get_role(data["role_id"])
            if member and role:
                try:
                    await member.remove_roles(role, reason="Temporary ruin role expired")
                except discord.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.0)
                        logger.warning(
                            "Rate limited removing role %s for %s. Retrying after %ss.",
                            role.name,
                            member.id,
                            retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        try:
                            await member.remove_roles(role, reason="Temporary ruin role expired")
                        except discord.HTTPException as retry_err:
                            logger.warning(
                                "Retry failed removing role %s for %s: %s",
                                role.name,
                                member.id,
                                retry_err,
                            )
                            continue  # Don't mark for removal; try again next tick
                    elif isinstance(e, discord.Forbidden):
                        logger.warning("Forbidden removing role %s: %s", role.name, e)
                    else:
                        logger.error("Unexpected error removing role %s: %s", role.name, e)
                        continue  # Don't mark for removal to avoid silently losing the entry
            to_remove.append(user_id)
        for user_id in to_remove:
            del temp_roles[user_id]
