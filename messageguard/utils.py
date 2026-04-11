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
from red_commons.logging import getLogger


log = getLogger("red.maxcogs.messageguard.utils")


# idk why i did this but it makes the code cleaner in some places so here we are
def has_manage_messages(
    channel: discord.TextChannel | discord.Thread | discord.ForumChannel,
    me: discord.Member,
) -> bool:
    return channel.permissions_for(me).manage_messages


def has_send_messages(
    channel: discord.TextChannel | discord.Thread | discord.ForumChannel,
    me: discord.Member,
) -> bool:
    return channel.permissions_for(me).send_messages


def can_moderate(
    channel: discord.TextChannel | discord.Thread | discord.ForumChannel,
    me: discord.Member,
) -> bool:
    perms = channel.permissions_for(me)
    return perms.manage_messages and perms.send_messages


def log_missing_permissions(
    channel: discord.TextChannel | discord.Thread,
    guild: discord.Guild,
    feature: str,
) -> None:
    log.warning(
        "[%s] Missing manage_messages or send_messages in %s (%s / %s)",
        feature,
        channel,
        guild.name,
        guild.id,
    )


# again here we are, this is just to clean up the code a bit and make it more readable in some places.


def is_forwarded_message(message: discord.Message) -> bool:
    reference = message.reference
    return reference is not None and reference.type == discord.MessageReferenceType.forward


def has_allowed_role(member: discord.Member, allowed_roles: set[int]) -> bool:
    return any(role.id in allowed_roles for role in member.roles)


async def send_forward_warning(message: discord.Message, warn_message: str) -> None:
    if has_send_messages(message.channel, message.guild.me):
        await message.channel.send(
            f"{message.author.mention} {warn_message}",
            delete_after=15,
        )


async def send_spoiler_warning(
    message: discord.Message,
    warn_message: str,
    delete_after: int,
    use_embed: bool,
    embed_color: discord.Color,
) -> None:
    """Send a spoiler warning"""
    mentions = discord.AllowedMentions(users=True, roles=False, everyone=False)
    if use_embed:
        embed = discord.Embed(
            title="Spoiler Warning",
            description=warn_message,
            color=embed_color,
        )
        await message.channel.send(
            f"{message.author.mention}",
            embed=embed,
            delete_after=delete_after,
            allowed_mentions=mentions,
        )
    else:
        await message.channel.send(
            f"{message.author.mention}, {warn_message}",
            delete_after=delete_after,
            allowed_mentions=mentions,
        )


async def send_log(
    message: discord.Message,
    feature: str,
    color: discord.Color,
    log_channel_id: int,
) -> None:
    """Send a log message to the specified log channel."""
    guild = message.guild
    if not guild:
        return
    log_channel = guild.get_channel(log_channel_id)
    if not log_channel or not isinstance(log_channel, discord.TextChannel):
        return
    me = guild.me
    if not log_channel.permissions_for(me).send_messages:
        log.warning(
            "[%s] Missing send_messages in log channel %s (%s)",
            feature,
            log_channel,
            guild.id,
        )
        return
    if not log_channel.permissions_for(me).embed_links:
        log.warning(
            "[%s] Missing embed_links in log channel %s (%s)",
            feature,
            log_channel,
            guild.id,
        )
        return
    content = message.content or "*No text content*"
    if len(content) > 4096:
        content = content[:4093] + "..."

    embed = discord.Embed(
        title=f"[{feature}] Message Deleted",
        description=content,
        color=color,
        timestamp=message.created_at,
    )
    embed.set_author(
        name=f"{message.author} ({message.author.id})",
        icon_url=message.author.display_avatar.url,
    )
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    embed.add_field(name="Author", value=message.author.mention, inline=True)
    embed.add_field(name="Jump URL", value=f"[Jump to message]({message.jump_url})", inline=True)
    if message.attachments:
        attachment_urls = [a.url for a in message.attachments]
        current_field: list[str] = []
        field_index = 1
        for url in attachment_urls:
            test = "\n".join([*current_field, url])
            if len(test) > 1024:
                embed.add_field(
                    name=f"Attachments (Part {field_index})",
                    value="\n".join(current_field),
                    inline=False,
                )
                field_index += 1
                current_field = [url]
            else:
                current_field.append(url)
        if current_field:
            name = "Attachments" if field_index == 1 else f"Attachments (Part {field_index})"
            embed.add_field(name=name, value="\n".join(current_field), inline=False)

    try:
        await log_channel.send(embed=embed)
    except discord.HTTPException as e:
        log.error(
            "[%s] Failed to send log to %s (%s): %s",
            feature,
            log_channel,
            guild.id,
            e,
        )


async def send_restrict_warning(
    message: discord.Message,
    warning_message: str,
    title: str,
    delete_after: int,
    use_embed: bool,
    mentionable: bool,
) -> None:
    """Send a warning for a deleted restricted-channel message."""
    me = message.guild.me
    can_embed = message.channel.permissions_for(me).embed_links

    if use_embed and not can_embed:
        log.warning(
            "[RestrictPosts] Missing embed_links in %s (%s). Falling back to text.",
            message.channel,
            message.guild.id,
        )

    if use_embed and can_embed:
        author_prefix = message.author.mention if mentionable else message.author.display_name
        embed = discord.Embed(
            title=title,
            description=f"{author_prefix}: {warning_message}",
            color=0xFF0000,
        )
        await message.channel.send(
            embed=embed,
            delete_after=delete_after,
            mention_author=mentionable,
        )
    else:
        content = (
            f"{message.author.mention} {warning_message}"
            if mentionable
            else f"{message.author.display_name} {warning_message}"
        )
        await message.channel.send(
            content,
            delete_after=delete_after,
            mention_author=mentionable,
        )
