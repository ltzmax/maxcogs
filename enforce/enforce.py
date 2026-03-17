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

from datetime import datetime, timedelta
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

    __version__: Final[str] = "0.0.1b"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = (
        "https://github.com/ltzmax/maxcogs/tree/master/enforce/README.md"
    )

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=9842069111, force_registration=True
        )
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
        self.bot.add_check(self.tos_global_check)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Delete stored data for a user."""
        user = self.bot.get_user(user_id)
        if user is None:
            return
        await self.config.user(user).clear()

    def cog_unload(self):
        self.bot.remove_check(self.tos_global_check)

    async def tos_global_check(self, ctx: commands.Context) -> bool:
        if ctx.author.bot:
            return True
        # let owner bypass ToS enforcement.
        if await self.bot.is_owner(ctx.author):
            return True

        if not await self.config.tos_enforcement_enabled():
            return True

        if await self.config.user(ctx.author).accepted_tos():
            return True

        user_id = ctx.author.id
        if user_id not in self.tos_prompt_antispam:
            self.tos_prompt_antispam[user_id] = AntiSpam([(timedelta(seconds=60), 1)])

        antispam = self.tos_prompt_antispam[user_id]
        if antispam.spammy:
            log.info(f"Skipping ToS prompt for {user_id} - antispam triggered")
            return False

        try:
            await self.send_tos_prompt(ctx)
        except (discord.Forbidden, discord.HTTPException) as e:
            log.warning(f"Failed to send ToS prompt to {ctx.author.id}: {e}")
        return False

    async def send_tos_prompt(self, ctx: commands.Context):
        tos_url = await self.config.tos_url()
        privacy_url = await self.config.privacy_url()
        title = await self.config.prompt_title()
        raw_desc = await self.config.prompt_description()
        description = raw_desc.format(tos_url=tos_url, privacy_url=privacy_url)
        footer = await self.config.prompt_footer()

        if ctx.guild:
            perm_check = ctx.channel.permissions_for(ctx.guild.me)
            if not perm_check.send_messages or not perm_check.embed_links:
                log.warning(
                    f"Cannot send ToS prompt in {ctx.guild.name}#{ctx.channel.name} ({ctx.channel.id}) - missing permissions"
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
    @commands.is_owner()
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
            return await ctx.send(
                "Description is too long. Must be under 2000 characters."
            )
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
            "Are you sure you want to reset all ToS settings to default?", view=view
        )
        await view.wait()
        if view.result:
            await self.config.clear_all()
            await ctx.send("ToS settings reset to default.")
        else:
            await ctx.send("Reset cancelled.")

    @tosconfig.command(name="resetuser")
    async def reset_user(self, ctx, user: discord.User = None):
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
        embed.add_field(
            name="Enforcement Enabled", value=str(enforcement_enabled), inline=False
        )
        embed.add_field(name="ToS URL", value=tos_url, inline=False)
        embed.add_field(name="Privacy Policy URL", value=privacy_url, inline=False)
        embed.add_field(name="Prompt Title", value=title, inline=False)
        embed.add_field(name="Prompt Description", value=description, inline=False)
        embed.add_field(name="Prompt Footer", value=footer, inline=False)
        await ctx.send(embed=embed)
