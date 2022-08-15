import random

from redbot.core import commands

BADGES = {
    "kanto": [2, 3, 4, 5, 6, 7, 8, 9],
    "johto": [10, 11, 12, 13, 14, 15, 16, 17],
    "hoenn": [18, 19, 20, 21, 22, 23, 24, 25],
    "sinnoh": [26, 27, 28, 29, 30, 31, 32, 33],
    "unova": [34, 35, 36, 37, 38, 39, 40, 41],
    "kalos": [44, 45, 46, 47, 48, 49, 50, 51],
}

GENERATIONS = {
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
GEN_KEYS = list(GENERATIONS.keys())

STYLES = {"default": 3, "black": 50, "collector": 96, "dp": 5, "purple": 43}
TRAINERS = {
    "ash": 13,
    "red": 922,
    "ethan": 900,
    "lyra": 901,
    "brendan": 241,
    "may": 255,
    "lucas": 747,
    "dawn": 856,
}


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
