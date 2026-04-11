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

# NOTE: This file is not imported by any part of the cog.
# The functions that were here have been moved to their canonical locations:
#   - fetch_data           - api.py
#   - generate_image       - image.py
#   - _format_*            - formatters.py
#   - create_pokemon_embed - formatters.py
#
# This file is kept as a placeholder to avoid breaking any external references,
# but all logic should be sourced from the modules above.

from .api import fetch_data as fetch_data
from .formatters import ( 
    MAX_DESCRIPTION_LENGTH as MAX_DESCRIPTION_LENGTH,
    _format_abilities as _format_abilities,
    _format_game_indices as _format_game_indices,
    _format_height_weight as _format_height_weight,
    _format_list as _format_list,
    _format_stats as _format_stats,
    _format_types as _format_types,
    _get_official_artwork as _get_official_artwork,
    _truncate_description as _truncate_description,
    create_pokemon_embed as create_pokemon_embed,
)
from .image import generate_image as generate_image
