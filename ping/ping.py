import time
import discord

from redbot.core import checks, Config, commands
from redbot.core.utils import chat_formatting as chat

class Ping(commands.Cog):
    """Reply with latency of bot"""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return
    
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("ping")

    @commands.command()
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ping(self, ctx):
        """Reply with latency of bot."""
        latency = self.bot.latency * 1000
        emb = discord.Embed(title="Pong!", color=discord.Color.red())
        emb.add_field(
            name="Discord API", value=chat.box(str(round(latency)) + " ms"),
        )
        emb.add_field(name="Message", value=chat.box("…"))
        emb.add_field(name="Typing", value=chat.box("…"))
        # Thanks preda and fixator for the good improvements done with this command.
        if len(self.bot.latencies) > 1:
            # The chances of this in near future is almost 0, but who knows, what future will bring to us?
            shards = [
                f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)}ms"
                for shard, pingt in self.bot.latencies
            ]
            emb.add_field(name="Shards", value=chat.box("\n".join(shards)))
        # in future this may be removed or changed with improvements, if you wanna keep it as it is, pin it in your cog list.
        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000
        emb.colour = await ctx.embed_color()
        emb.set_field_at(
            1,
            name="Message",
            value=chat.box(
                str(int((message.created_at - ctx.message.created_at).total_seconds() * 1000))
                + " ms"
            ),
        )
        emb.set_field_at(2, name="Typing", value=chat.box(str(round(ping)) + " ms"))

        await message.edit(embed=emb)
