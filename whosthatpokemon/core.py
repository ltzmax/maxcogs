import asyncio
from io import BytesIO
from typing import Any, Dict, Optional
from PIL import Image
from redbot.core.data_manager import bundled_data_path


async def get_data(self, url: str) -> Dict[str, Any]:
    try:
        async with self.session.get(url) as response:
            if response.status != 200:
                self.log.error(
                    f"Failed to get data from {url} with status code {response.status}"
                )
                return {"http_code": response.status}
            return await response.json()
    except asyncio.TimeoutError:
        self.log.error(f"Request to {url} timed out.")
        return {"http_code": 408}


async def generate_image(self, poke_id: str, *, hide: bool) -> Optional[BytesIO]:
    base_image = Image.open(bundled_data_path(self) / "template.webp").convert("RGBA")
    bg_width, bg_height = base_image.size
    base_url = f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{poke_id}.png"
    try:
        async with self.session.get(base_url) as response:
            if response.status != 200:
                return None
            data = await response.read()
    except asyncio.TimeoutError:
        return None
    pbytes = BytesIO(data)
    poke_image = Image.open(pbytes)
    poke_width, poke_height = poke_image.size
    poke_image_resized = poke_image.resize(
        (int(poke_width * 1.6), int(poke_height * 1.6))
    )

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
    pbytes.close()
    base_image.close()
    poke_image.close()
    return temp
