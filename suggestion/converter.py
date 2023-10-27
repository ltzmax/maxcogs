from redbot.core import commands
try:
    from emoji import UNICODE_EMOJI_ENGLISH as EMOJI_DATA
except ImportError:
    from emoji import EMOJI_DATA

class EmojiConverter(commands.EmojiConverter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument in EMOJI_DATA:
            return argument
        return str(await super().convert(ctx, argument))
