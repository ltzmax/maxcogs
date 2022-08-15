from typing import Dict, Sequence

GENERATIONS: Dict[str, str] = {
    "na": "Unknown",
    "rb": "Red/Blue\n(Gen. 1)",
    "gs": "Gold/Silver\n(Gen. 2)",
    "rs": "Ruby/Sapphire\n(Gen. 3)",
    "dp": "Diamond/Pearl\n(Gen. 4)",
    "bw": "Black/White\n(Gen. 5)",
    "xy": "X/Y\n(Gen. 6)",
    "sm": "Sun/Moon\n(Gen. 7)",
    "ss": "Sword/Shield\n(Gen. 8)",
}


GEN_KEYS: Sequence[str] = list(GENERATIONS.keys())


def get_generation(pokemon_id: int) -> str:
    if pokemon_id >= 1 and pokemon_id <= 151:
        generation = 1
    elif pokemon_id >= 152 and pokemon_id <= 251:
        generation = 2
    elif pokemon_id >= 252 and pokemon_id <= 386:
        generation = 3
    elif pokemon_id >= 387 and pokemon_id <= 493:
        generation = 4
    elif pokemon_id >= 494 and pokemon_id <= 649:
        generation = 5
    elif pokemon_id >= 650 and pokemon_id <= 721:
        generation = 6
    elif pokemon_id >= 722 and pokemon_id <= 809:
        generation = 7
    elif pokemon_id >= 810 and pokemon_id <= 898:
        generation = 8
    else:
        generation = 0

    return GENERATIONS[GEN_KEYS[generation]]
