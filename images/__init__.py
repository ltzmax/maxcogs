from asyncio import create_task

from .images import Images

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)

# Logic from fixator10 https://github.com/fixator10/Fixator10-Cogs/blob/5b06d9f490e3dedada281ab60beb97626cb1a795/moreutils/__init__.py#L9
async def setup_after_ready(bot):
    await bot.wait_until_red_ready()
    cog = Images(bot)
    for name, command in cog.all_commands.items():
        if not command.parent:
            if bot.get_command(name):
                command.name = f"i{command.name}"
            for alias in command.aliases:
                if bot.get_command(alias):
                    command.aliases[command.aliases.index(alias)] = f"i{alias}"
    bot.add_cog(cog)


def setup(bot):
    create_task(setup_after_ready(bot))
