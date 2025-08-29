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

achievements = [
    {
        "key": "egg_collector",
        "name": "Egg Collector",
        "description": "Obtain 100 Common Eggs",
        "condition_type": "egg",
        "condition_key": "common",
        "condition_value": 100,
        "reward": 500,
    },
    {
        "key": "silver_surfer",
        "name": "Silver Surfer",
        "description": "Obtain 50 Silver Eggs",
        "condition_type": "egg",
        "condition_key": "silver",
        "condition_value": 50,
        "reward": 1000,
    },
    {
        "key": "golden_touch",
        "name": "Golden Touch",
        "description": "Obtain 25 Gold Eggs",
        "condition_type": "egg",
        "condition_key": "gold",
        "condition_value": 25,
        "reward": 2000,
    },
    {
        "key": "shiny_egg_hunter",
        "name": "Shiny Egg Hunter",
        "description": "Obtain 3 Shiny Eggs",
        "condition_type": "egg",
        "condition_key": "shiny",
        "condition_value": 3,
        "reward": 3000,
    },
    {
        "key": "legendary_hunter",
        "name": "Legendary Hunter",
        "description": "Obtain 1 Legendary Egg",
        "condition_type": "egg",
        "condition_key": "legendary",
        "condition_value": 1,
        "reward": 10000,
    },
    {
        "key": "mythical_master",
        "name": "Mythical Master",
        "description": "Obtain 1 Mythical Egg",
        "condition_type": "egg",
        "condition_key": "mythical",
        "condition_value": 1,
        "reward": 20000,
    },
    {
        "key": "streak_master_10",
        "name": "Streak Master (10)",
        "description": "Achieve a hunt streak of 10",
        "condition_type": "streak",
        "condition_value": 10,
        "reward": 100,
    },
    {
        "key": "streak_master_20",
        "name": "Streak Master (20)",
        "description": "Achieve a hunt streak of 20",
        "condition_type": "streak",
        "condition_value": 20,
        "reward": 200,
    },
    {
        "key": "streak_master_50",
        "name": "Streak Master (50)",
        "description": "Achieve a hunt streak of 50",
        "condition_type": "streak",
        "condition_value": 50,
        "reward": 5000,
    },
    {
        "key": "streak_master_100",
        "name": "Streak Master (100)",
        "description": "Achieve a hunt streak of 100",
        "condition_type": "streak",
        "condition_value": 100,
        "reward": 10000,
    },
    {
        "key": "streak_master_200",
        "name": "Streak Master (200)",
        "description": "Achieve a hunt streak of 200",
        "condition_type": "streak",
        "condition_value": 200,
        "reward": 20000,
    },
    {
        "key": "gem_finder",
        "name": "Gem Finder",
        "description": "Collect 10 Hidden Gems",
        "condition_type": "gems",
        "condition_value": 10,
        "reward": 100000,
    },
]
