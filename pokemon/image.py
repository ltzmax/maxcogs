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

import asyncio
from functools import partial
from io import BytesIO

import aiohttp
from PIL import Image
from red_commons.logging import getLogger
from redbot.core.data_manager import bundled_data_path


log = getLogger("red.maxcogs.whosthatpokemon.image")
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)


def _build_image(template_path: str, raw_data: bytes, hide: bool) -> BytesIO:
    """
    CPU-bound PIL compositing — always run via run_in_executor, never directly.
    """
    base_image = Image.open(template_path).convert("RGBA")
    bg_width, bg_height = base_image.size

    pbytes = BytesIO(raw_data)
    poke_image = Image.open(pbytes)
    poke_width, poke_height = poke_image.size
    poke_image_resized = poke_image.resize((int(poke_width * 1.6), int(poke_height * 1.6)))

    try:
        if hide:
            p_load = poke_image_resized.load()  # type: ignore
            for y in range(poke_image_resized.size[1]):
                for x in range(poke_image_resized.size[0]):
                    if p_load[x, y] == (0, 0, 0, 0):  # type: ignore
                        continue
                    p_load[x, y] = (1, 1, 1)  # type: ignore

        paste_w = int((bg_width - poke_width) / 10)
        paste_h = int((bg_height - poke_height) / 4)
        base_image.paste(poke_image_resized, (paste_w, paste_h), poke_image_resized)

        temp = BytesIO()
        base_image.save(temp, "png")
        temp.seek(0)
        return temp
    finally:
        pbytes.close()
        base_image.close()
        poke_image.close()
        poke_image_resized.close()


async def generate_image(cog, poke_id: str, *, hide: bool) -> BytesIO | None:
    """Fetch the Pokémon sprite and composite it onto the template image."""
    base_url = f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{poke_id}.png"
    try:
        async with cog.session.get(base_url, timeout=_DEFAULT_TIMEOUT) as response:
            if response.status != 200:
                return None
            raw_data = await response.read()
    except aiohttp.ClientError as e:
        log.error("Failed to fetch sprite from %s: %s", base_url, e)
        return None

    template_path = str(bundled_data_path(cog) / "template.webp")
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None, partial(_build_image, template_path, raw_data, hide)
        )
    except Exception as e:
        log.error("Failed to build Pokémon image for %s: %s", poke_id, e, exc_info=True)
        return None
