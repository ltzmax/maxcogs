import logging
import re

CAP_DETECTOR = re.compile(
    r"(?x)(\b[A-Z](\S*?)[ ][A-Z](\S*?)\b)"
)
LOG = logging.getLogger("red.maxcogs.capspam")
WARN_MESSAGE = "{author.mention}, you're message has been deleted because your words contain too many caps! Watch out your shift key!"
WARN_MESSAGE_DELETE_COOLDOWN = 10
