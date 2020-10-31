from asyncio import create_task
from redbot.core.bot import Red
from .pokeseries import PokeSeries

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)

# from https://github.com/fixator10/Fixator10-Cogs/blob/V3/adminutils/__init__.py
async def setup_after_ready(bot: Red):
    await bot.wait_until_red_ready()
    cog = PokeSeries(bot)
    for name, command in cog.all_commands.items():
        if not command.parent:
            if bot.get_command(name):
                command.name = f"p{command.name}"
            for alias in command.aliases:
                if bot.get_command(alias):
                    command.aliases[command.aliases.index(alias)] = f"p{alias}"
    bot.add_cog(cog)

def setup(bot: Red):
    create_task(setup_after_ready(bot))
