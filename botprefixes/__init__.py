import re

import discord
from redbot.core.bot import Red, commands


class BotPrefixes(commands.Cog):
    """Mention to get the bot current prefixes."""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if await self.bot.allowed_by_whitelist_blacklist(who=message.author) is False:
            return
        if not re.compile(rf"^(?:<@!?)?{self.bot.user.id}(?:>)?$").match(message.content):
            return
        prefixes = await self.bot.get_prefix(message)
        if f"<@!{self.bot.user.id}> " in prefixes:
            prefixes.remove(f"<@!{self.bot.user.id}> ")
        if not prefixes:
            return
        await message.channel.send(
            "My prefixes are:\n{}".format(", ".join(f"`{prefix}`" for prefix in prefixes))
        )


async def setup(bot: Red):
    await bot.add_cog(BotPrefixes(bot))
