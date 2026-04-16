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

from typing import Any, Final, Literal

import aiohttp
import discord
import orjson
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number

from .core import ACTIONS, NEKOS
from .view import _ConfirmView


log = getLogger("red.maxcogs.nekosbest")
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class NekosBest(commands.Cog):
    """Sends random images from nekos.best + RolePlay Commands."""

    __version__: Final[str] = "2.7.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/#nekosbest"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {"command_counts": {}, "received_counts": {}}
        self.config.register_user(**default_user)

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int):
        return

    async def red_get_data_for_user(self, *, user_id: int):
        return

    async def _api_call(self, ctx: commands.Context, endpoint: str) -> dict[str, Any] | None:
        async with self.session.get(NEKOS + endpoint) as response:
            if response.status != 200:
                log.error(
                    "Something went wrong while trying to contact API. Status code: %s",
                    response.status,
                )
                return await ctx.send(
                    "Something went wrong while trying to contact API. Please try again later.",
                )
            data = await response.read()
            return orjson.loads(data)

    async def imgembedgen(
        self, ctx: commands.Context, response: dict[str, Any], category: str
    ) -> None:
        await ctx.typing()
        data = response["results"][0]
        artist = data["artist_name"]
        source = data["source_url"]
        artist_link = data["artist_href"]
        image_url = data["url"]

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    f"## Here's a picture of a {category}\n"
                    f"**Artist:** [{artist}]({artist_link})\n"
                    f"**Source:** {source}"
                ),
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(discord.UnfurledMediaItem(url=image_url))
                ),
                discord.ui.Separator(),
                discord.ui.ActionRow(
                    discord.ui.Button(
                        style=discord.ButtonStyle.link, label="Artist", url=artist_link
                    ),
                    discord.ui.Button(style=discord.ButtonStyle.link, label="Source", url=source),
                    discord.ui.Button(
                        style=discord.ButtonStyle.link, label="Open Image", url=image_url
                    ),
                ),
                discord.ui.TextDisplay("-# Powered by nekos.best"),
            )
        )
        await ctx.send(view=view)

    async def embedgen(self, ctx: commands.Context, member: discord.Member, action: str) -> None:
        url = await self._api_call(ctx, action)
        if url is None:
            return
        await ctx.typing()
        user_config = self.config.user(ctx.author)
        command_counts = await user_config.command_counts()
        command_counts[action] = command_counts.get(action, 0) + 1
        await user_config.command_counts.set(command_counts)
        count = command_counts[action]

        received_counts: dict[str, int] = {}
        if member and member != ctx.author:
            target_config = self.config.user(member)
            received_counts = await target_config.received_counts() or {}
            received_counts[action] = received_counts.get(action, 0) + 1
            await target_config.received_counts.set(received_counts)
        received_count = received_counts.get(action, 0)

        grammar = "times" if count > 1 else "time"
        received_grammar = "times" if received_count > 1 else "time"
        action_fmt = ACTIONS.get(action, action)
        anime_name = url["results"][0]["anime_name"]
        image_url = url["results"][0]["url"]

        target_str = f"{member.mention}" if member and member != ctx.author else "themselves!"
        description = f"**{ctx.author.mention} {action_fmt} {target_str}**\n"
        description += f"-# Anime: {anime_name}\n"
        if member and member != ctx.author:
            description += f"-# {member.display_name} has received {action} {humanize_number(received_count)} {received_grammar}\n"
        description += (
            f"-# {ctx.author.display_name} has used {action} {humanize_number(count)} {grammar}"
        )

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(description),
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(discord.UnfurledMediaItem(url=image_url))
                ),
                discord.ui.TextDisplay("-# Powered by nekos.best"),
            )
        )
        await ctx.send(view=view)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nekoset(self, ctx: commands.Context) -> None:
        """Settings for nekosbest cog."""

    @nekoset.command()
    @commands.is_owner()
    async def resetall(self, ctx: commands.Context) -> None:
        """Reset all command counts."""
        view = _ConfirmView(ctx.author)
        view.message = await ctx.send("Are you sure you want to reset everything?", view=view)
        await view.wait()
        if view.result:
            await self.config.clear_all_users()
            await ctx.send("All command counts have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @nekoset.command()
    async def reset(self, ctx: commands.Context, member: discord.Member) -> None:
        """Reset a user's command counts."""
        view = _ConfirmView(ctx.author)
        view.message = await ctx.send(
            f"Are you sure you want to reset everything for {member.mention}?",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.user(member).clear()
            await ctx.send(
                f"{member.mention}'s command counts have been reset.", mention_author=False
            )
        else:
            await ctx.send("Reset cancelled.")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def waifu(self, ctx: commands.Context) -> None:
        """Send a random waifu image."""
        url = await self._api_call(ctx, "waifu")
        await self.imgembedgen(ctx, url, "waifu")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def nekos(self, ctx: commands.Context) -> None:
        """Send a random neko image."""
        url = await self._api_call(ctx, "neko")
        await self.imgembedgen(ctx, url, "neko")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def kitsune(self, ctx: commands.Context) -> None:
        """Send a random kitsune image."""
        url = await self._api_call(ctx, "kitsune")
        await self.imgembedgen(ctx, url, "kitsune")

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True, send_messages=True)
    async def husbando(self, ctx: commands.Context) -> None:
        """Send a random husbando image."""
        url = await self._api_call(ctx, "husbando")
        await self.imgembedgen(ctx, url, "husbando")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def yawn(self, ctx: commands.Context, member: discord.Member) -> None:
        """yawn!"""
        await self.embedgen(ctx, member, "yawn")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def handshake(self, ctx: commands.Context, member: discord.Member) -> None:
        """handshake!"""
        await self.embedgen(ctx, member, "handshake")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def lurk(self, ctx: commands.Context, member: discord.Member) -> None:
        """Lurks!"""
        await self.embedgen(ctx, member, "lurk")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def peck(self, ctx: commands.Context, member: discord.Member) -> None:
        """peck!"""
        await self.embedgen(ctx, member, "peck")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def baka(self, ctx: commands.Context, member: discord.Member) -> None:
        """Baka baka baka!"""
        await self.embedgen(ctx, member, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cry(self, ctx: commands.Context, member: discord.Member) -> None:
        """Cry!"""
        await self.embedgen(ctx, member, "cry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def cuddle(self, ctx: commands.Context, member: discord.Member) -> None:
        """Cuddle a user!"""
        await self.embedgen(ctx, member, "cuddle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def dance(self, ctx: commands.Context, member: discord.Member) -> None:
        """Dance!"""
        await self.embedgen(ctx, member, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def feed(self, ctx: commands.Context, member: discord.Member) -> None:
        """Feeds a user!"""
        await self.embedgen(ctx, member, "feed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def hugs(self, ctx: commands.Context, member: discord.Member) -> None:
        """Hugs a user!"""
        await self.embedgen(ctx, member, "hug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def kiss(self, ctx: commands.Context, member: discord.Member) -> None:
        """Kiss a user!"""
        await self.embedgen(ctx, member, "kiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def laugh(self, ctx: commands.Context, member: discord.Member) -> None:
        """laugh!"""
        await self.embedgen(ctx, member, "laugh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pat(self, ctx: commands.Context, member: discord.Member) -> None:
        """Pats a user!"""
        await self.embedgen(ctx, member, "pat")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokes(self, ctx: commands.Context, member: discord.Member) -> None:
        # Due to conflict with pokecord cog, it has to be pokes.
        # Feel free to use alias cog if you want poke only.
        """Pokes at a user!"""
        await self.embedgen(ctx, member, "poke")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def slap(self, ctx: commands.Context, member: discord.Member) -> None:
        """Slap a user!"""
        await self.embedgen(ctx, member, "slap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smile(self, ctx: commands.Context, member: discord.Member) -> None:
        """Smile!"""
        await self.embedgen(ctx, member, "smile")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def smug(self, ctx: commands.Context, member: discord.Member) -> None:
        """Smugs at someone!"""
        await self.embedgen(ctx, member, "smug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def tickle(self, ctx: commands.Context, member: discord.Member) -> None:
        """Tickle a user!"""
        await self.embedgen(ctx, member, "tickle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wave(self, ctx: commands.Context, member: discord.Member) -> None:
        """Waves!"""
        await self.embedgen(ctx, member, "wave")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bite(self, ctx: commands.Context, member: discord.Member) -> None:
        """Bite a user!"""
        await self.embedgen(ctx, member, "bite")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def blush(self, ctx: commands.Context, member: discord.Member) -> None:
        """blushes!"""
        await self.embedgen(ctx, member, "blush")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bored(self, ctx: commands.Context, member: discord.Member) -> None:
        """You're bored!"""
        await self.embedgen(ctx, member, "bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def facepalm(self, ctx: commands.Context, member: discord.Member) -> None:
        """Facepalm at a user!"""
        await self.embedgen(ctx, member, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def happy(self, ctx: commands.Context, member: discord.Member) -> None:
        """happiness with a user!"""
        await self.embedgen(ctx, member, "happy")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def highfive(self, ctx: commands.Context, member: discord.Member) -> None:
        """highfive a user!"""
        await self.embedgen(ctx, member, "highfive")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pout(self, ctx: commands.Context, member: discord.Member) -> None:
        """Pout a user!"""
        await self.embedgen(ctx, member, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shrug(self, ctx: commands.Context, member: discord.Member) -> None:
        """Shrugs a user!"""
        await self.embedgen(ctx, member, "shrug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sleep(self, ctx: commands.Context, member: discord.Member) -> None:
        """Sleep zzzz!"""
        await self.embedgen(ctx, member, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def stare(self, ctx: commands.Context, member: discord.Member) -> None:
        """Stares at a user!"""
        await self.embedgen(ctx, member, "stare")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def think(self, ctx: commands.Context, member: discord.Member) -> None:
        """Thinking!"""
        await self.embedgen(ctx, member, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def thumbsup(self, ctx: commands.Context, member: discord.Member) -> None:
        """thumbsup!"""
        await self.embedgen(ctx, member, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wink(self, ctx: commands.Context, member: discord.Member) -> None:
        """Winks at a user!"""
        await self.embedgen(ctx, member, "wink")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    async def handhold(self, ctx: commands.Context, member: discord.Member) -> None:
        """handhold a user!"""
        await self.embedgen(ctx, member, "handhold")

    @commands.command(aliases=["vkicks"])
    @commands.bot_has_permissions(embed_links=True)
    async def vkick(self, ctx: commands.Context, member: discord.Member) -> None:
        """kick a user!"""
        await self.embedgen(ctx, member, "kick")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def punch(self, ctx: commands.Context, member: discord.Member) -> None:
        """punch a user!"""
        await self.embedgen(ctx, member, "punch")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shoot(self, ctx: commands.Context, member: discord.Member) -> None:
        """shoot a user!"""
        await self.embedgen(ctx, member, "shoot")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def yeet(self, ctx: commands.Context, member: discord.Member) -> None:
        """yeet a user far far away."""
        await self.embedgen(ctx, member, "yeet")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nod(self, ctx: commands.Context, member: discord.Member) -> None:
        """nods a user far far away."""
        await self.embedgen(ctx, member, "nod")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nope(self, ctx: commands.Context, member: discord.Member) -> None:
        """nope a user far far away."""
        await self.embedgen(ctx, member, "nope")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nom(self, ctx: commands.Context, member: discord.Member) -> None:
        """nom nom a user far far away."""
        await self.embedgen(ctx, member, "nom")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def angry(self, ctx: commands.Context, member: discord.Member) -> None:
        """angry at a user."""
        await self.embedgen(ctx, member, "angry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def run(self, ctx: commands.Context, member: discord.Member) -> None:
        """Run away from a user."""
        await self.embedgen(ctx, member, "run")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def bleh(self, ctx: commands.Context, member: discord.Member) -> None:
        """Bleh at a user."""
        await self.embedgen(ctx, member, "bleh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def blowkiss(self, ctx: commands.Context, member: discord.Member) -> None:
        """Blows kiss at a user."""
        await self.embedgen(ctx, member, "blowkiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def carry(self, ctx: commands.Context, member: discord.Member) -> None:
        """Carry a user."""
        await self.embedgen(ctx, member, "carry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def clap(self, ctx: commands.Context, member: discord.Member) -> None:
        """Claps at a user."""
        await self.embedgen(ctx, member, "clap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def confused(self, ctx: commands.Context, member: discord.Member) -> None:
        """Confused at a user."""
        await self.embedgen(ctx, member, "confused")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def kabedon(self, ctx: commands.Context, member: discord.Member) -> None:
        """Kabedon a user."""
        await self.embedgen(ctx, member, "kabedon")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def lappillow(self, ctx: commands.Context, member: discord.Member) -> None:
        """Lappillows on a user."""
        await self.embedgen(ctx, member, "lappillow")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def nya(self, ctx: commands.Context, member: discord.Member) -> None:
        """Nyaaah at a user."""
        await self.embedgen(ctx, member, "nya")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def salute(self, ctx: commands.Context, member: discord.Member) -> None:
        """Salute at a user."""
        await self.embedgen(ctx, member, "salute")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shake(self, ctx: commands.Context, member: discord.Member) -> None:
        """Shakes a user."""
        await self.embedgen(ctx, member, "shake")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def shocked(self, ctx: commands.Context, member: discord.Member) -> None:
        """Shocked at a user."""
        await self.embedgen(ctx, member, "shocked")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def sip(self, ctx: commands.Context, member: discord.Member) -> None:
        """Sips with a user."""
        await self.embedgen(ctx, member, "sip")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def spin(self, ctx: commands.Context, member: discord.Member) -> None:
        """Spins a user."""
        await self.embedgen(ctx, member, "spin")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def teehee(self, ctx: commands.Context, member: discord.Member) -> None:
        """Teeheeeheheh at a user."""
        await self.embedgen(ctx, member, "teehee")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def wag(self, ctx: commands.Context, member: discord.Member) -> None:
        """Wag at a user."""
        await self.embedgen(ctx, member, "wag")
