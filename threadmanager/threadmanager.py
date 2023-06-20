import discord
from redbot.core import commands

class ThreadManager(commands.Cog):
    """close, lock, open and unlock threads."""

    __author__ = "MAX"
    __version__ = "1.0.0"
    __docs__ = "https://github.com/ltzmax/maxcogs/blob/master/threadmanager/README.md"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.group(aliases=["threads"])
    @commands.has_permissions(manage_threads=True, manage_messages=True)
    @commands.bot_has_permissions(manage_threads=True, manage_messages=True)
    async def thread(self, ctx):
        """Manage close, lock, open and unlock threads."""
        
    @thread.command()
    async def close(self, ctx):
        """Close a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        # So it doesn't reopen the thread.
        await ctx.send(f"Closed thread.")
        await ctx.channel.edit(locked=True, archived=True)

    @thread.command()
    async def lock(self, ctx):
        """Lock a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=True)
        await ctx.send(f"Locked thread.")

    @thread.command()
    async def unlock(self, ctx):
        """Unlock a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=False)
        await ctx.send(f"Unlocked thread.")

    @thread.command()
    async def open(self, ctx):
        """Open a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=False, archived=False)
        await ctx.send(f"Opened thread.")
