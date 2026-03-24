"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Final
import re

# ForwardDeleter
FD_WARN_MESSAGE: Final[str] = "You are not allowed to forward message(s)."
# NoSpoiler
NS_DEFAULT_WARNING: Final[str] = "Usage of spoiler is not allowed in this server."
SPOILER_REGEX = re.compile(r"(?s)\|\|(.+?)\|\|")
# RestrictPosts
RP_DEFAULT_MSG: Final[str] = (
    "Your message was deleted because it must contain an attachment or a link."
)
RP_DEFAULT_TITLE: Final[str] = "Warning"
RP_URL_REGEX = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[_@.&+-]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)
