from redbot.core import commands


class ExplicitNone(commands.Converter):
    async def convert(self, ctx, value):
        if value.lower() == "none":
            return None
        raise commands.BadArgument('Input was not "none".')
