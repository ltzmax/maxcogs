import discord
from redbot.core import commands


class ThreadManager(commands.Cog):
    """close, lock, open, unlock and more!"""

    __author__ = "MAX"
    __version__ = "1.0.3"
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
    @commands.hybrid_group(aliases=["threads"])
    @commands.bot_has_permissions(manage_threads=True, manage_messages=True)
    @commands.has_permissions(manage_threads=True, manage_messages=True, send_messages_in_threads=True)
    async def thread(self, ctx):
        """Manage your threads in your server."""

    @thread.command()
    async def close(self, ctx):
        """Close a thread.

        Note this does both lock and close.
        """
        audit_reason = f"Thread closed by {ctx.author} (ID: {ctx.author.id})"
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        # So it doesn't reopen the thread.
        await ctx.send(f"Closed thread.")
        await ctx.channel.edit(locked=True, archived=True, reason=audit_reason)

    @thread.command()
    async def lock(self, ctx):
        """Lock a thread."""
        audit_reason = f"Thread locked by {ctx.author} (ID: {ctx.author.id})"
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=True, reason=audit_reason)
        await ctx.send(f"Locked thread.")

    @thread.command(with_app_command=False)  # Cant use slash in archived threads.
    async def unlock(self, ctx):
        """Unlock a thread."""
        audit_reason = f"Thread unlocked by {ctx.author} (ID: {ctx.author.id})"
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=False, reason=audit_reason)
        await ctx.send(f"Unlocked thread.")

    @thread.command(with_app_command=False)  # Cant use slash in archived threads.
    async def open(self, ctx):
        """Open a thread.

        Note this does both unlock and open.
        """
        audit_reason = f"Thread opened by {ctx.author} (ID: {ctx.author.id})"
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.edit(locked=False, archived=False, reason=audit_reason)
        await ctx.send(f"Opened thread.")

    @thread.command()
    async def create(self, ctx, name: str):
        """Create a thread.

        Note: This will create a thread in the category under same channel you run the command in.
        (You will not be automatic joined to the thread, you will have to look in the thread list.)

        **Threads Discovery Button**
        - Navigate to the Threads Discovery button at the top of the channel. 
        - Once you press the Thread Discovery button, you can now browse all threads in the channel.

        **Channel Sidebar**
        - Additionally, on the desktop and browser app, you can hover over the channel name in the sidebar with your mouse to view and discover active threads and then click the See All option to view all other threads. 

        Check this image here: https://support.discord.com/hc/article_attachments/4403200760471/Thread_discover.png if you're confused to where the thread is.
        """
        # Todo for the future: Add a way to add users to the thread when created.
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("This isn't a text channel.")
        if len(name) > 100:
            return await ctx.send("Thread name can't be longer than 100 characters.")
        await ctx.channel.create_thread(name=name, auto_archive_duration=1440, reason=f"Thread created by {ctx.author} (ID: {ctx.author.id})")
        await ctx.send(f"Thread created.")

    @thread.command(aliases=["rmthread"])
    async def deletethread(self, ctx):
        """Delete a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.delete()
        await ctx.send(f"Deleted thread.")

    @thread.command()
    async def rename(self, ctx, name: str):
        """Rename a thread."""
        audit_reason = f"Thread renamed by {ctx.author} (ID: {ctx.author.id})"
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        if len(name) > 100:
            return await ctx.send("Thread name can't be longer than 100 characters.")
        await ctx.channel.edit(name=name, reason=audit_reason)
        await ctx.send(f"Renamed thread.")

    @thread.command(aliases=["rmuser"])
    async def removeuser(self, ctx, user: discord.Member):
        """Remove a user from a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.remove_user(user)
        await ctx.send(f"Removed {user} from the thread.")

    @thread.command()
    async def adduser(self, ctx, user: discord.Member):
        """Add a user to a thread."""
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.send("This isn't a thread.")
        await ctx.channel.add_user(user)
        await ctx.send(f"Added {user} to the thread.")
