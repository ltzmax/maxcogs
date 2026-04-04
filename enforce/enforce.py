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
from datetime import timedelta
from typing import Final

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.antispam import AntiSpam
from redbot.core.utils.chat_formatting import header
from redbot.core.utils.views import ConfirmView

from .views import AcceptView

log = getLogger("red.maxcogs.tosenforcer")


class Enforce(commands.Cog):
    """Requires users to accept ToS and privacy policy before using any bot commands."""

    __version__: Final[str] = "0.0.1c"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/enforce/README.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9842069111, force_registration=True)
        self.config.register_global(
            tos_url="https://i.maxapp.tv/d6761E.png",
            privacy_url="https://i.maxapp.tv/75771F.png",
            tos_enforcement_enabled=False,
            prompt_title="Terms of Service Required",
            prompt_description=(
                "To use this bot you must accept our **Terms of Service** and **Privacy Policy**.\n\n"
                "**ToS:** {tos_url}\n"
                "**Privacy Policy:** {privacy_url}\n\n"
                "Click **Accept** below to continue."
            ),
            prompt_footer="You won't be able to use commands until you accept.",
        )
        self.config.register_user(accepted_tos=False, accepted_at=None)
        self.tos_prompt_antispam = {}
        self._cleanup_task = None
        self.bot.add_check(self.tos_global_check)

    async def cog_load(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_antispam())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Delete stored data for a user."""
        await self.config.user_from_id(user_id).clear()

    async def cog_unload(self) -> None:
        self.bot.remove_check(self.tos_global_check)
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def tos_global_check(self, ctx: commands.Context) -> bool:
        if ctx.author.bot:
            return True
        # let owner bypass ToS enforcement.
        if await self.bot.is_owner(ctx.author):
            return True

        if not await self.config.tos_enforcement_enabled():
            return True

        if await self.config.user(ctx.author).accepted_tos():
            self.tos_prompt_antispam.pop(ctx.author.id, None)
            return True

        user_id = ctx.author.id
        if user_id not in self.tos_prompt_antispam:
            self.tos_prompt_antispam[user_id] = AntiSpam([(timedelta(seconds=60), 2)])

        antispam = self.tos_prompt_antispam[user_id]
        if antispam.spammy:
            log.info("Skipping ToS prompt for %s - antispam triggered", user_id)
            return False

        antispam.stamp()
        try:
            await self.send_tos_prompt(ctx)
        except (discord.Forbidden, discord.HTTPException) as e:
            log.warning("Failed to send ToS prompt to %s: %s", ctx.author.id, e)
        return False

    async def _cleanup_antispam(self) -> None:
        """Periodically remove antispam entries for users who have since accepted ToS."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)
            # Only remove entries for users that have now accepted preserve active cooldowns.
            to_remove = []
            for uid in list(self.tos_prompt_antispam.keys()):
                try:
                    if await self.config.user_from_id(uid).accepted_tos():
                        to_remove.append(uid)
                except Exception:
                    pass
            for uid in to_remove:
                self.tos_prompt_antispam.pop(uid, None)

    async def send_tos_prompt(self, ctx: commands.Context):
        tos_url = await self.config.tos_url()
        privacy_url = await self.config.privacy_url()
        title = await self.config.prompt_title()
        raw_desc = await self.config.prompt_description()
        try:
            description = raw_desc.format(tos_url=tos_url, privacy_url=privacy_url)
        except KeyError as e:
            log.error(
                "prompt_description is missing placeholder %s falling back to raw text. "
                "Use {tos_url} and {privacy_url} in your description.", e,
            )
            description = raw_desc
        footer = await self.config.prompt_footer()

        if ctx.guild:
            perm_check = ctx.channel.permissions_for(ctx.guild.me)
            if not perm_check.send_messages or not perm_check.embed_links:
                log.warning(
                    "Cannot send ToS prompt in %s#%s (%s) - missing permissions",
                    ctx.guild.name, ctx.channel.name, ctx.channel.id,
                )
                return
        else:
            # In DMs, the bot usually has permission to send messages/embeds by default anyway.
            pass

        view = AcceptView(self.config, ctx.author)
        embed = discord.Embed(
            title=title,
            description=description,
            color=0xC30101,
        )
        embed.set_footer(text=footer)
        message = await ctx.send(
            embed=embed,
            view=view,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )
        view.original_message = message

    @commands.group(aliases=["enforceset", "enforce"])
    @commands.is_owner()
    async def tosconfig(self, ctx):
        """Manage ToS enforcement settings."""

    @tosconfig.command(name="toggle")
    async def toggle_enforcement(self, ctx):
        """Toggle ToS enforcement on or off."""
        current = await self.config.tos_enforcement_enabled()
        await self.config.tos_enforcement_enabled.set(not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"ToS enforcement {status}.")

    @tosconfig.command(name="set")
    async def set_link(self, ctx: commands.Context, tos_or_privacy: str, *, url: str):
        """
        Set ToS or Privacy Policy link.

        **Example**:
        - `[p]tosconfig set tos <url>`
        - `[p]tosconfig set privacy <url>`
        """
        tos_or_privacy = tos_or_privacy.lower().strip()
        url = url.strip().strip("<>")
        if not (url.startswith("http://") or url.startswith("https://")):
            return await ctx.send("❌ Invalid URL! Must start with http:// or https://")

        if tos_or_privacy == "tos":
            await self.config.tos_url.set(url)
            await ctx.send(f"✅ **Terms of Service** link set to:\n<{url}>")

        elif tos_or_privacy == "privacy":
            await self.config.privacy_url.set(url)
            await ctx.send(f"✅ **Privacy Policy** link set to:\n<{url}>")
        else:
            await ctx.send(
                f"❌ Invalid type! Use `tos` or `privacy`.\nExample: `{ctx.clean_prefix}tosconfig set tos https://example.com/tos`"
            )

    @tosconfig.command(name="settitle")
    async def set_title(self, ctx, *, title: str):
        """Set custom prompt title."""
        if len(title) > 256:
            return await ctx.send("Title is too long. Must be under 256 characters.")
        await self.config.prompt_title.set(title)
        await ctx.send(f"Prompt title set to: {title}")

    @tosconfig.command(name="setfooter")
    async def set_footer(self, ctx, *, footer: str):
        """Set custom prompt footer."""
        if len(footer) > 256:
            return await ctx.send("Footer is too long. Must be under 256 characters.")
        await self.config.prompt_footer.set(footer)
        await ctx.send(f"Prompt footer set to: {footer}")

    @tosconfig.command(name="setdesc", aliases=["setdescription", "setprompt"])
    async def set_description(self, ctx, *, desc: str):
        """Set custom prompt description.

        Use `{tos_url}` and `{privacy_url}` as placeholders for the privacy policy and terms of service url.
        """
        if len(desc) > 2000:
            return await ctx.send("Description is too long. Must be under 2000 characters.")
        if "{tos_url}" not in desc or "{privacy_url}" not in desc:
            return await ctx.send(
                "Description must include both `{tos_url}` and `{privacy_url}` placeholders.\nExample: `To use this bot, you must accept our ToS ({tos_url}) and Privacy Policy ({privacy_url}).`"
            )
        await self.config.prompt_description.set(desc)
        await ctx.send("Prompt description updated.")

    @tosconfig.command(name="resetsettings")
    async def reset_settings(self, ctx):
        """Reset all ToS settings to default."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset all ToS settings to default?\n"
            "⚠️ This will also reset the ToS and Privacy Policy URLs and **disable enforcement**.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.clear_all_globals()
            await ctx.send("ToS settings reset to default.")
        else:
            await ctx.send("Reset cancelled.")

    @tosconfig.command(name="resetuser")
    async def reset_user(self, ctx, user: discord.User | None = None):
        """
        Reset ToS acceptance for a user.

        If no user is specified, resets for the command invoker.
        """
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset ToS acceptance for this user?", view=view
        )
        await view.wait()
        if view.result:
            target = user or ctx.author
            await self.config.user(target).accepted_tos.set(False)
            await self.config.user(target).accepted_at.set(None)
            await ctx.send(f"ToS acceptance reset for {target} ({target.id}).")
        else:
            await ctx.send("Reset cancelled.")

    @tosconfig.command(name="resetall")
    async def reset_all(self, ctx):
        """Reset ToS acceptance for all users."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        title = "⚠️DANGER: This will reset ALL users ToS acceptance.⚠️"
        view.message = await ctx.send(
            f"{header(title, 'medium')}\n"
            "Everyone will have to accept again on their next command.\n"
            "**Are you sure you want to do this?**",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.clear_all_users()
            await ctx.send("ToS acceptance reset for all users.")
        else:
            await ctx.send("Reset cancelled.")

    @tosconfig.command(name="checkuser")
    async def check_user(self, ctx: commands.Context, user: discord.User | None = None) -> None:
        """Check when a user accepted the ToS."""
        target = user or ctx.author
        user_cfg = await self.config.user(target).all()
        accepted = user_cfg.get("accepted_tos", False)
        accepted_at = user_cfg.get("accepted_at")

        if not accepted:
            return await ctx.send(f"{target} ({target.id}) has not accepted the ToS yet.")

        if accepted_at:
            timestamp = f"<t:{accepted_at}:F> (<t:{accepted_at}:R>)"
        else:
            timestamp = "Unknown (accepted before timestamp tracking was added)"
        await ctx.send(f"{target} ({target.id}) accepted the ToS on {timestamp}.")

    @tosconfig.command(name="showsettings")
    @commands.bot_has_permissions(embed_links=True)
    async def show_settings(self, ctx):
        """Show current ToS enforcement settings."""
        all_settings = await self.config.all()
        tos_url = all_settings.get("tos_url")
        privacy_url = all_settings.get("privacy_url")
        enforcement_enabled = all_settings.get("tos_enforcement_enabled")
        title = all_settings.get("prompt_title")
        description = all_settings.get("prompt_description")
        footer = all_settings.get("prompt_footer")
        embed = discord.Embed(
            title="Current ToS Enforcement Settings", color=await ctx.embed_color()
        )
        embed.add_field(name="Enforcement Enabled", value=str(enforcement_enabled), inline=False)
        embed.add_field(name="ToS URL", value=tos_url, inline=False)
        embed.add_field(name="Privacy Policy URL", value=privacy_url, inline=False)
        embed.add_field(name="Prompt Title", value=title, inline=False)
        try:
            resolved_desc = description.format(tos_url=tos_url, privacy_url=privacy_url)
        except KeyError:
            resolved_desc = description
        if len(resolved_desc) > 1024:
            resolved_desc = resolved_desc[:1021] + "..."
        embed.add_field(name="Prompt Description", value=resolved_desc, inline=False)
        embed.add_field(name="Prompt Footer", value=footer, inline=False)
        await ctx.send(embed=embed)
