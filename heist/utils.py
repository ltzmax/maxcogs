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

import datetime
from typing import Dict

ITEMS: Dict[str, tuple] = {
    "wooden_shield": (
        "🛡️",
        {"type": "shield", "cost": 3000, "reduction": 0.03, "duration_hours": 24},
    ),
    "iron_shield": (
        "🛡️",
        {"type": "shield", "cost": 7000, "reduction": 0.05, "duration_hours": 36},
    ),
    "steel_shield": (
        "🛡️",
        {"type": "shield", "cost": 12000, "reduction": 0.07, "duration_hours": 48},
    ),
    "titanium_shield": (
        "🛡️",
        {"type": "shield", "cost": 20000, "reduction": 0.09, "duration_hours": 60},
    ),
    "diamond_shield": (
        "🛡️",
        {"type": "shield", "cost": 35000, "reduction": 0.12, "duration_hours": 72},
    ),
    "full": ("🛡️", {"type": "shield", "cost": 100000, "reduction": 1.0, "duration_hours": 96}),
    "bike_tool": ("🔧", {"type": "tool", "cost": 500, "boost": 0.1, "for_heist": "street_bike"}),
    "car_tool": ("🔓", {"type": "tool", "cost": 1000, "boost": 0.15, "for_heist": "street_car"}),
    "motorcycle_tool": (
        "🛠️",
        {"type": "tool", "cost": 800, "boost": 0.12, "for_heist": "street_motorcycle"},
    ),
    "pickpocket_gloves": (
        "🧤",
        {"type": "tool", "cost": 200, "boost": 0.05, "for_heist": "pocket_steal"},
    ),
    "crowbar": ("🪓", {"type": "tool", "cost": 300, "boost": 0.07, "for_heist": "atm_smash"}),
    "glass_cutter": (
        "🔪",
        {"type": "tool", "cost": 600, "boost": 0.10, "for_heist": "jewelry_store"},
    ),
    "brass_knuckles": (
        "🥊",
        {"type": "tool", "cost": 800, "boost": 0.12, "for_heist": "fight_club"},
    ),
    "laser_jammer": (
        "📡",
        {"type": "tool", "cost": 1500, "boost": 0.15, "for_heist": "art_gallery"},
    ),
    "hacking_device": (
        "💾",
        {"type": "tool", "cost": 2500, "boost": 0.15, "for_heist": "casino_vault"},
    ),
    "store_key": (
        "🔑",
        {"type": "tool", "cost": 400, "boost": 0.08, "for_heist": "store_robbery"},
    ),
    "lockpick_kit": (
        "🗝️",
        {"type": "tool", "cost": 1800, "boost": 0.14, "for_heist": "museum_relic"},
    ),
    "grappling_hook": (
        "🪝",
        {"type": "tool", "cost": 2000, "boost": 0.15, "for_heist": "luxury_yacht"},
    ),
    "street_bike": ("🚲", {"type": "loot", "min_sell": 1500, "max_sell": 3500}),
    "street_car": ("🚗", {"type": "loot", "min_sell": 20000, "max_sell": 30000}),
    "street_motorcycle": ("🏍️", {"type": "loot", "min_sell": 8000, "max_sell": 12000}),
    "pocket_loot": ("💰", {"type": "loot", "min_sell": 100, "max_sell": 500}),
    "jewelry": ("💍", {"type": "loot", "min_sell": 5000, "max_sell": 15000}),
    "painting": ("🖼️", {"type": "loot", "min_sell": 20000, "max_sell": 80000}),
    "relic": ("🏺", {"type": "loot", "min_sell": 30000, "max_sell": 120000}),
    "yacht_loot": ("🛥️", {"type": "loot", "min_sell": 40000, "max_sell": 150000}),
    "scrap_metal": ("🧱", {"type": "material", "min_sell": 100, "max_sell": 300}),
    "tech_parts": ("🔩", {"type": "material", "min_sell": 200, "max_sell": 500}),
    "rare_alloy": ("🪙", {"type": "material", "min_sell": 500, "max_sell": 1000}),
    "reinforced_wooden_shield": (
        "🛡️",
        {"type": "shield", "reduction": 0.05, "duration_hours": 24},
    ),
    "enhanced_pickpocket_gloves": (
        "🧤",
        {"type": "tool", "boost": 0.08, "for_heist": "pocket_steal"},
    ),
    "reinforced_iron_shield": (
        "🛡️",
        {"type": "shield", "reduction": 0.07, "duration_hours": 36},
    ),
    "reinforced_steel_shield": (
        "🛡️",
        {"type": "shield", "reduction": 0.09, "duration_hours": 48},
    ),
    "reinforced_titanium_shield": (
        "🛡️",
        {"type": "shield", "reduction": 0.11, "duration_hours": 60},
    ),
    "reinforced_diamond_shield": (
        "🛡️",
        {"type": "shield", "reduction": 0.15, "duration_hours": 72},
    ),
    "enhanced_crowbar": (
        "🪓",
        {"type": "tool", "boost": 0.10, "for_heist": "atm_smash"},
    ),
    "enhanced_glass_cutter": (
        "🔪",
        {"type": "tool", "boost": 0.13, "for_heist": "jewelry_store"},
    ),
    "enhanced_brass_knuckles": (
        "🥊",
        {"type": "tool", "boost": 0.15, "for_heist": "fight_club"},
    ),
    "enhanced_laser_jammer": (
        "📡",
        {"type": "tool", "boost": 0.18, "for_heist": "art_gallery"},
    ),
    "enhanced_hacking_device": (
        "💾",
        {"type": "tool", "boost": 0.18, "for_heist": "casino_vault"},
    ),
    "enhanced_store_key": (
        "🔑",
        {"type": "tool", "boost": 0.11, "for_heist": "store_robbery"},
    ),
    "enhanced_lockpick_kit": (
        "🗝️",
        {"type": "tool", "boost": 0.17, "for_heist": "museum_relic"},
    ),
    "enhanced_grappling_hook": (
        "🪝",
        {"type": "tool", "boost": 0.18, "for_heist": "luxury_yacht"},
    ),
    "enhanced_bike_tool": (
        "🔧",
        {"type": "tool", "boost": 0.13, "for_heist": "street_bike"},
    ),
    "enhanced_car_tool": (
        "🔓",
        {"type": "tool", "boost": 0.18, "for_heist": "street_car"},
    ),
    "enhanced_motorcycle_tool": (
        "🛠️",
        {"type": "tool", "boost": 0.15, "for_heist": "street_motorcycle"},
    ),
}

RECIPES: Dict[str, dict] = {
    "reinforced_wooden_shield": {
        "materials": {"scrap_metal": 5},
        "result": "reinforced_wooden_shield",
        "quantity": 1,
    },
    "enhanced_pickpocket_gloves": {
        "materials": {"tech_parts": 3},
        "result": "enhanced_pickpocket_gloves",
        "quantity": 1,
    },
    "reinforced_iron_shield": {
        "materials": {"scrap_metal": 7, "rare_alloy": 2},
        "result": "reinforced_iron_shield",
        "quantity": 1,
    },
    "reinforced_steel_shield": {
        "materials": {"scrap_metal": 10, "rare_alloy": 3},
        "result": "reinforced_steel_shield",
        "quantity": 1,
    },
    "reinforced_titanium_shield": {
        "materials": {"scrap_metal": 12, "rare_alloy": 4},
        "result": "reinforced_titanium_shield",
        "quantity": 1,
    },
    "reinforced_diamond_shield": {
        "materials": {"scrap_metal": 15, "rare_alloy": 5},
        "result": "reinforced_diamond_shield",
        "quantity": 1,
    },
    "enhanced_crowbar": {
        "materials": {"scrap_metal": 4, "tech_parts": 2},
        "result": "enhanced_crowbar",
        "quantity": 1,
    },
    "enhanced_glass_cutter": {
        "materials": {"tech_parts": 4, "rare_alloy": 1},
        "result": "enhanced_glass_cutter",
        "quantity": 1,
    },
    "enhanced_brass_knuckles": {
        "materials": {"scrap_metal": 5, "tech_parts": 2},
        "result": "enhanced_brass_knuckles",
        "quantity": 1,
    },
    "enhanced_laser_jammer": {
        "materials": {"tech_parts": 5, "rare_alloy": 2},
        "result": "enhanced_laser_jammer",
        "quantity": 1,
    },
    "enhanced_hacking_device": {
        "materials": {"tech_parts": 6, "rare_alloy": 3},
        "result": "enhanced_hacking_device",
        "quantity": 1,
    },
    "enhanced_store_key": {
        "materials": {"scrap_metal": 3, "tech_parts": 2},
        "result": "enhanced_store_key",
        "quantity": 1,
    },
    "enhanced_lockpick_kit": {
        "materials": {"tech_parts": 5, "rare_alloy": 2},
        "result": "enhanced_lockpick_kit",
        "quantity": 1,
    },
    "enhanced_grappling_hook": {
        "materials": {"scrap_metal": 6, "rare_alloy": 3},
        "result": "enhanced_grappling_hook",
        "quantity": 1,
    },
    "enhanced_bike_tool": {
        "materials": {"scrap_metal": 3, "tech_parts": 1},
        "result": "enhanced_bike_tool",
        "quantity": 1,
    },
    "enhanced_car_tool": {
        "materials": {"scrap_metal": 5, "tech_parts": 3},
        "result": "enhanced_car_tool",
        "quantity": 1,
    },
    "enhanced_motorcycle_tool": {
        "materials": {"scrap_metal": 4, "tech_parts": 2},
        "result": "enhanced_motorcycle_tool",
        "quantity": 1,
    },
}

HEISTS: Dict[str, dict] = {
    "pocket_steal": {
        "emoji": "🕶️",
        "risk": 0.01,
        "min_reward": 100,
        "max_reward": 300,
        "cooldown": datetime.timedelta(minutes=30),
        "min_success": 50,
        "max_success": 80,
        "duration": datetime.timedelta(minutes=2),
        "min_loss": 100,
        "max_loss": 300,
        "police_chance": 0.05,
        "jail_time": datetime.timedelta(hours=1),
        "material_drop_chance": 0.2,
    },
    "atm_smash": {
        "emoji": "🏧",
        "risk": 0.04,
        "min_reward": 500,
        "max_reward": 3000,
        "cooldown": datetime.timedelta(minutes=45),
        "min_success": 35,
        "max_success": 65,
        "duration": datetime.timedelta(minutes=3),
        "min_loss": 300,
        "max_loss": 1500,
        "police_chance": 0.05,
        "jail_time": datetime.timedelta(hours=2),
        "material_drop_chance": 0.25,
    },
    "store_robbery": {
        "emoji": "🏬",
        "risk": 0.05,
        "min_reward": 1000,
        "max_reward": 5000,
        "cooldown": datetime.timedelta(hours=1),
        "min_success": 30,
        "max_success": 60,
        "duration": datetime.timedelta(minutes=5),
        "min_loss": 500,
        "max_loss": 2000,
        "police_chance": 0.15,
        "jail_time": datetime.timedelta(hours=3),
        "material_drop_chance": 0.3,
    },
    "jewelry_store": {
        "emoji": "💎",
        "risk": 0.07,
        "min_reward": 600,
        "max_reward": 900,
        "cooldown": datetime.timedelta(hours=2),
        "min_success": 25,
        "max_success": 55,
        "duration": datetime.timedelta(minutes=6),
        "min_loss": 2000,
        "max_loss": 7000,
        "police_chance": 0.2,
        "jail_time": datetime.timedelta(hours=4),
        "material_drop_chance": 0.35,
    },
    "fight_club": {
        "emoji": "🥊",
        "risk": 0.10,
        "min_reward": 10000,
        "max_reward": 40000,
        "cooldown": datetime.timedelta(hours=3),
        "min_success": 20,
        "max_success": 50,
        "duration": datetime.timedelta(minutes=8),
        "min_loss": 5000,
        "max_loss": 15000,
        "police_chance": 0.25,
        "jail_time": datetime.timedelta(hours=5),
        "material_drop_chance": 0.4,
    },
    "art_gallery": {
        "emoji": "🖼️",
        "risk": 0.15,
        "min_reward": 1000,
        "max_reward": 6000,
        "cooldown": datetime.timedelta(hours=4),
        "min_success": 15,
        "max_success": 45,
        "duration": datetime.timedelta(minutes=12),
        "min_loss": 10000,
        "max_loss": 30000,
        "police_chance": 0.3,
        "jail_time": datetime.timedelta(hours=6),
        "material_drop_chance": 0.45,
    },
    "casino_vault": {
        "emoji": "🎰",
        "risk": 0.20,
        "min_reward": 50000,
        "max_reward": 200000,
        "cooldown": datetime.timedelta(hours=5),
        "min_success": 10,
        "max_success": 40,
        "duration": datetime.timedelta(minutes=15),
        "min_loss": 20000,
        "max_loss": 100000,
        "police_chance": 0.35,
        "jail_time": datetime.timedelta(hours=8),
        "material_drop_chance": 0.5,
    },
    "museum_relic": {
        "emoji": "🏺",
        "risk": 0.18,
        "min_reward": 10000,
        "max_reward": 50000,
        "cooldown": datetime.timedelta(hours=4),
        "min_success": 12,
        "max_success": 42,
        "duration": datetime.timedelta(minutes=14),
        "min_loss": 15000,
        "max_loss": 60000,
        "police_chance": 0.4,
        "jail_time": datetime.timedelta(hours=12),
        "material_drop_chance": 0.55,
    },
    "luxury_yacht": {
        "emoji": "🛥️",
        "risk": 0.17,
        "min_reward": 10000,
        "max_reward": 80000,
        "cooldown": datetime.timedelta(hours=4),
        "min_success": 13,
        "max_success": 43,
        "duration": datetime.timedelta(minutes=13),
        "min_loss": 15000,
        "max_loss": 70000,
        "police_chance": 0.45,
        "jail_time": datetime.timedelta(hours=24),
        "material_drop_chance": 0.6,
    },
    "street_bike": {
        "emoji": "🚲",
        "risk": 0.03,
        "min_reward": 10,
        "max_reward": 20,
        "cooldown": datetime.timedelta(hours=1),
        "min_success": 20,
        "max_success": 60,
        "duration": datetime.timedelta(minutes=3),
        "min_loss": 500,
        "max_loss": 2000,
        "police_chance": 0.1,
        "jail_time": datetime.timedelta(hours=2),
        "material_drop_chance": 0.15,
    },
    "street_motorcycle": {
        "emoji": "🏍️",
        "risk": 0.05,
        "min_reward": 30,
        "max_reward": 900,
        "cooldown": datetime.timedelta(hours=2),
        "min_success": 15,
        "max_success": 50,
        "duration": datetime.timedelta(minutes=5),
        "min_loss": 2000,
        "max_loss": 8000,
        "police_chance": 0.15,
        "jail_time": datetime.timedelta(hours=3),
        "material_drop_chance": 0.2,
    },
    "street_car": {
        "emoji": "🚗",
        "risk": 0.08,
        "min_reward": 100,
        "max_reward": 5000,
        "cooldown": datetime.timedelta(hours=3),
        "min_success": 10,
        "max_success": 40,
        "duration": datetime.timedelta(minutes=8),
        "min_loss": 8000,
        "max_loss": 20000,
        "police_chance": 0.2,
        "jail_time": datetime.timedelta(hours=4),
        "material_drop_chance": 0.25,
    },
    "corporate": {
        "emoji": "🏢",
        "risk": 0.12,
        "min_reward": 25000,
        "max_reward": 100000,
        "cooldown": datetime.timedelta(hours=4),
        "min_success": 10,
        "max_success": 50,
        "duration": datetime.timedelta(minutes=10),
        "min_loss": 10000,
        "max_loss": 50000,
        "police_chance": 0.3,
        "jail_time": datetime.timedelta(hours=8),
        "material_drop_chance": 0.35,
    },
    "bank": {
        "emoji": "🏦",
        "risk": 0.25,
        "min_reward": 100000,
        "max_reward": 500000,
        "cooldown": datetime.timedelta(hours=6),
        "min_success": 5,
        "max_success": 40,
        "duration": datetime.timedelta(minutes=15),
        "min_loss": 50000,
        "max_loss": 250000,
        "police_chance": 0.35,
        "jail_time": datetime.timedelta(hours=12),
        "material_drop_chance": 0.45,
    },
    "elite": {
        "emoji": "💎",
        "risk": 0.35,
        "min_reward": 500000,
        "max_reward": 1000000,
        "cooldown": datetime.timedelta(hours=8),
        "min_success": 5,
        "max_success": 30,
        "duration": datetime.timedelta(minutes=20),
        "min_loss": 250000,
        "max_loss": 500000,
        "police_chance": 0.4,
        "jail_time": datetime.timedelta(hours=12),
        "material_drop_chance": 0.5,
    },
}
