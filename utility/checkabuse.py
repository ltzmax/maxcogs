from .abc import MixinMeta
from redbot.core import commands
from collections import defaultdict
from redbot.core.utils.chat_formatting import (
    box,
)

class Checkabuse(MixinMeta):
    """shows spam per server."""

    @commands.is_owner()
    @commands.command()
    async def checkabuse(self, ctx):
        """This checks servers for spam."""
        c = defaultdict(int)
        u = defaultdict(int)
        me = defaultdict(int)
        me_u = defaultdict(int)
        for m in ctx.guild._state._messages:
            me[m.guild] += 1
            me_u[m.author] += 1
            if ctx.valid:
                c[(m.guild, getattr(m.guild, "owner", m.author), ctx.command.qualified_name)] += 1
                u[(m.author, ctx.command.qualified_name)] += 1
        c_offender = max(c.items(), key=lambda kv: kv[1])
        u_offender = max(u.items(), key=lambda kv: kv[1])

        me_offender = max(me.items(), key=lambda kv: kv[1])
        me_u_offender = max(me_u.items(), key=lambda kv: kv[1])
        await ctx.send(box(f"\nServer with most Message:\n{me_offender}\n\nUser with most messages:\n{me_u_offender}\n\n\nServer with most commands:\n{c_offender}\n\nUser with most commands:\n{u_offender}", lang="py"))
