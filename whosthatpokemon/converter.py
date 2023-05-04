from random import randint

from redbot.core import commands


class Generation(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        allowed_gens = [f"gen{x}" for x in range(1, 9)]
        if argument.lower() not in allowed_gens:
            ctx.command.reset_cooldown(ctx)
            raise commands.BadArgument("Only `gen1` to `gen8` values are allowed.")

        if argument == "gen1":
            return randint(1, 151)
        elif argument == "gen2":
            return randint(152, 251)
        elif argument == "gen3":
            return randint(252, 386)
        elif argument == "gen4":
            return randint(387, 493)
        elif argument == "gen5":
            return randint(494, 649)
        elif argument == "gen6":
            return randint(650, 721)
        elif argument == "gen7":
            return randint(722, 809)
        elif argument == "gen8":
            return randint(810, 898)
        else:
            return randint(1, 898)
