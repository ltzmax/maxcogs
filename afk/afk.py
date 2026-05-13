"""
MIT License

Copyright (c) 2026-present ltzmax

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

import contextlib
from datetime import datetime, timezone

import discord
from dcv2nav import LayoutViewPaginator
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red


log = getLogger("red.maxapp.afk")

PINGS_PER_PAGE = 10


class AFK(commands.Cog):
    """AFK status cog."""

    __version__ = "1.0.0"
    __author__ = "MAX"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/docs/AFK.md"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=9876543234567876543, force_registration=True
        )

        default_guild = {
            "afk_role": None,
            "nickname_afk": False,
        }

        default_member = {
            "afk": False,
            "message": "",
            "timestamp": None,
            "pings": [],
            "autoremove": True,
            "delete_after": None,
        }

        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Handle data deletion requests."""
        all_members = await self.config.all_members()
        for guild_id in all_members:
            await self.config.member_from_ids(guild_id, user_id).clear()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _set_afk(self, member: discord.Member, message: str) -> None:
        await self.config.member(member).afk.set(True)
        await self.config.member(member).message.set(message)
        await self.config.member(member).timestamp.set(self._now_iso())
        await self.config.member(member).pings.set([])
        role_id = await self.config.guild(member.guild).afk_role()
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                with contextlib.suppress(discord.HTTPException):
                    await member.add_roles(role, reason="AFK status set")

        nickname_afk = await self.config.guild(member.guild).nickname_afk()
        if (
            nickname_afk
            and member.guild.me.guild_permissions.manage_nicknames
            and member.guild.owner_id != member.id
            and member.guild.me.top_role > member.top_role
        ):
            current = member.display_name
            if not current.startswith("[AFK] "):
                with contextlib.suppress(discord.HTTPException):
                    await member.edit(nick=f"[AFK] {current[:26]}", reason="AFK status set")

    async def _remove_afk(self, member: discord.Member) -> None:
        await self.config.member(member).afk.set(False)
        await self.config.member(member).message.set("")
        await self.config.member(member).timestamp.set(None)

        role_id = await self.config.guild(member.guild).afk_role()
        if role_id:
            role = member.guild.get_role(role_id)
            if role and role in member.roles:
                with contextlib.suppress(discord.HTTPException):
                    await member.remove_roles(role, reason="AFK status removed")

        if (
            member.guild.me.guild_permissions.manage_nicknames
            and member.guild.owner_id != member.id
            and member.guild.me.top_role > member.top_role
        ):
            current = member.display_name
            if current.startswith("[AFK] "):
                new_nick = current[6:].strip() or None
                with contextlib.suppress(discord.HTTPException):
                    await member.edit(nick=new_nick, reason="AFK status removed")

    def _build_ping_pages(self, pings: list[dict]) -> list[str]:
        """Build paginated string pages from the pings list."""
        pages = []
        chunks = [pings[i : i + PINGS_PER_PAGE] for i in range(0, len(pings), PINGS_PER_PAGE)]
        total = len(pings)
        for page_num, chunk in enumerate(chunks, start=1):
            lines = [f"## 📬 Pings while you were AFK ({total} total)\n"]
            for idx, ping in enumerate(chunk, start=(page_num - 1) * PINGS_PER_PAGE + 1):
                ts = ping.get("timestamp", "")
                discord_ts = ""
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        discord_ts = f" • <t:{int(dt.timestamp())}:R>"
                    except ValueError:
                        pass

                content_preview = ping.get("content", "")
                if len(content_preview) > 80:
                    content_preview = content_preview[:80] + "…"

                channel_mention = (
                    f"<#{ping['channel_id']}>" if ping.get("channel_id") else "Unknown channel"
                )
                author_mention = (
                    f"<@{ping['author_id']}>" if ping.get("author_id") else "Unknown user"
                )

                lines.append(
                    f"**{idx}.** {author_mention} in {channel_mention}{discord_ts}\n"
                    f"> {content_preview or '*(no text content)*'}\n"
                )
            pages.append("\n".join(lines))
        return pages

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        if not isinstance(message.author, discord.Member):
            return
        author_data = await self.config.member(message.author).all()
        if author_data["afk"] and author_data["autoremove"]:
            ctx = await self.bot.get_context(message)
            if ctx.valid:
                return

            await self._remove_afk(message.author)
            prefixes = await self.bot.get_prefix(message)
            if isinstance(prefixes, str):
                prefixes = [prefixes]
            text_prefixes = [p for p in prefixes if not p.startswith("<@")]
            prefix = text_prefixes[0] if text_prefixes else prefixes[0]
            text = (
                "## 👋 Welcome Back!\n"
                "Your AFK status has been removed.\n"
                f"Use `{prefix}afkset list` to see who pinged you."
            )
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
            with contextlib.suppress(discord.HTTPException):
                await message.channel.send(view=view)
            return

        for mention in message.mentions:
            if mention.bot or mention == message.author:
                continue
            if not isinstance(mention, discord.Member):
                continue

            mention_data = await self.config.member(mention).all()
            if not mention_data["afk"]:
                continue
            afk_message = mention_data["message"] or "No message set."
            ts_str = mention_data.get("timestamp")
            discord_ts = ""
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str)
                    discord_ts = f" (since <t:{int(dt.timestamp())}:R>)"
                except ValueError:
                    pass

            delete_after = await self.config.member(mention).delete_after()
            text = (
                f"**{discord.utils.escape_markdown(mention.display_name)}** is currently AFK{discord_ts}.\n"
                f"> {discord.utils.escape_markdown(afk_message)}"
            )
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
            with contextlib.suppress(discord.HTTPException):
                await message.channel.send(view=view, delete_after=delete_after)
            content_preview = message.content or ""
            ping_entry = {
                "author_id": message.author.id,
                "channel_id": message.channel.id,
                "message_id": message.id,
                "content": content_preview[:200],
                "timestamp": self._now_iso(),
            }
            async with self.config.member(mention).pings() as pings:
                pings.append(ping_entry)
                # Cap at 100 pings to avoid unbounded growth
                if len(pings) > 100:
                    pings[:] = pings[-100:]

    @commands.command()
    @commands.guild_only()
    async def afk(
        self, ctx: commands.Context, *, message: str = "I'm away from my keyboard."
    ) -> None:
        """Set your AFK status with an optional message.

        When someone pings you, they'll see your AFK message and
        your pings will be logged for when you return.

        **Examples:**
        - `[p]afk` - sets AFK with default message
        - `[p]afk Out for lunch, back soon!` - sets AFK with a custom message
        """
        if len(message) > 200:
            return await ctx.send("Your AFK message must be 200 characters or fewer.")
        already_afk = await self.config.member(ctx.author).afk()
        await self._set_afk(ctx.author, message)

        verb = "updated" if already_afk else "set"
        embed_text = (
            f"## 💤 AFK {verb.capitalize()}\n"
            f"Your AFK message:\n**{discord.utils.escape_markdown(message)}**"
        )
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(embed_text)))
        await ctx.send(view=view)

    @commands.group()
    @commands.guild_only()
    async def afkset(self, ctx: commands.Context) -> None:
        """AFK settings."""

    @afkset.command(name="deleteafter")
    async def afkset_deleteafter(self, ctx: commands.Context, seconds: int | None) -> None:
        """Set how long AFK notifications should last before being deleted.

        Pass a number of seconds (5–3600) to set a duration, or nothing to disable auto-deletion.

        **Examples:**
        - `[p]afkset deleteafter 30` - delete notifications after 30 seconds
        - `[p]afkset deleteafter` - keep notifications indefinitely
        """
        if seconds is not None and seconds < 5:
            return await ctx.send("Please provide at least 5 seconds, or leave blank to disable.")

        if seconds is not None and seconds > 3600:
            return await ctx.send(
                "Please provide a number of seconds no greater than 3600 (1 hour), or leave blank to disable."
            )

        await self.config.member(ctx.author).delete_after.set(seconds)
        if seconds is None:
            text = (
                "## ⏱️ AFK Notification Duration\nAFK notifications will now persist indefinitely."
            )
        else:
            text = f"## ⏱️ AFK Notification Duration\nAFK notifications will now be deleted after {seconds} second(s)."

        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
        await ctx.send(view=view)

    @afkset.command(name="list")
    async def afkset_list(self, ctx: commands.Context) -> None:
        """View pings you received while AFK.

        The list is cleared after viewing it.
        """
        pings = await self.config.member(ctx.author).pings()

        if not pings:
            view = discord.ui.LayoutView()
            view.add_item(
                discord.ui.Container(
                    discord.ui.TextDisplay("## 📭 No Pings\nNo one pinged you while you were AFK.")
                )
            )
            return await ctx.send(view=view)

        pages = self._build_ping_pages(pings)
        await self.config.member(ctx.author).pings.set([])
        if len(pages) == 1:
            view = discord.ui.LayoutView()
            view.add_item(discord.ui.Container(discord.ui.TextDisplay(pages[0])))
            await ctx.send(view=view)
        else:
            view = LayoutViewPaginator(pages, ctx)
            view.message = await ctx.send(view=view)

    @afkset.command(name="autoremove")
    async def afkset_autoremove(self, ctx: commands.Context) -> None:
        """Toggle auto-removing your AFK status when you send a message.

        When enabled (default), your AFK is cleared the next time you chat.
        When disabled, you must set a new AFK or it stays indefinitely.
        """
        current = await self.config.member(ctx.author).autoremove()
        new = not current
        await self.config.member(ctx.author).autoremove.set(new)

        state = "**enabled** ✅" if new else "**disabled** ❌"
        text = f"## ⚙️ Auto-Remove AFK\nAuto-remove is now {state}.\n\n" + (
            "Your AFK will be removed the next time you send a message."
            if new
            else "Your AFK will remain until you manually set a new one."
        )
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
        await ctx.send(view=view)

    @afkset.command(name="role")
    @commands.admin_or_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def afkset_role(
        self, ctx: commands.Context, *, role: discord.Role | None = None
    ) -> None:
        """Set (or clear) the role assigned to AFK members.

        Pass a role name/mention to set it, or nothing to clear it.

        **Examples:**
        - `[p]afkset role AFK` - assign the AFK role
        - `[p]afkset role` - remove the configured AFK role
        """
        if role is None:
            await self.config.guild(ctx.guild).afk_role.set(None)
            text = "## 🎭 AFK Role\nAFK role has been **cleared**. No role will be assigned when members go AFK."
        else:
            if role >= ctx.guild.me.top_role:
                return await ctx.send(
                    "I can't assign that role, it's equal to or above my highest role."
                )
            await self.config.guild(ctx.guild).afk_role.set(role.id)
            text = (
                f"## 🎭 AFK Role\nAFK role set to **{discord.utils.escape_markdown(role.name)}**."
            )

        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
        await ctx.send(view=view)

    @afkset.command(name="nickname")
    @commands.admin_or_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def afkset_nickname(self, ctx: commands.Context) -> None:
        """Toggle prepending `[AFK]` to members' nicknames when they go AFK.

        Requires the bot to have **Manage Nicknames** permission and be
        above the target member in the role hierarchy.
        """
        current = await self.config.guild(ctx.guild).nickname_afk()
        new = not current
        await self.config.guild(ctx.guild).nickname_afk.set(new)

        state = "**enabled** ✅" if new else "**disabled** ❌"
        text = f"## 🏷️ AFK Nickname\nAFK nickname prefix is now {state}.\n\n" + (
            "Members will have `[AFK]` prepended to their nickname when they go AFK "
            "(only when the bot is above them in the role hierarchy)."
            if new
            else "Nicknames will no longer be modified when members go AFK."
        )
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
        await ctx.send(view=view)

    @afkset.command(name="settings")
    @commands.admin_or_permissions(manage_guild=True)
    async def afkset_settings(self, ctx: commands.Context) -> None:
        """View current AFK settings."""
        role_id = await self.config.guild(ctx.guild).afk_role()
        nickname_afk = await self.config.guild(ctx.guild).nickname_afk()

        role_text = "None"
        if role_id:
            role = ctx.guild.get_role(role_id)
            if role:
                role_text = role.name

        text = (
            f"## ⚙️ AFK Settings\n"
            f"**AFK Role:** {discord.utils.escape_markdown(role_text)}\n"
            f"**Nickname Prefix:** {'✅ Enabled' if nickname_afk else '❌ Disabled'}"
        )
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
        await ctx.send(view=view)
