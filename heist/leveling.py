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

import math

from red_commons.logging import getLogger


log = getLogger("red.cogs.heist.leveling")

MAX_LEVEL = 120

# XP table
# WoW-style: each level requires progressively more XP.
# Formula: xp_for_level(n) = floor(100 * n * (1 + 0.12 * n))
# Level 1 -> 2: 212 XP, Level 50 -> 51: ~36,200 XP, Level 119 -> 120: ~207,000 XP


def _compute_threshold(level: int) -> int:
    """XP required to reach `level` from level 1 (cumulative)."""
    return sum(math.floor(100 * n * (1 + 0.12 * n)) for n in range(1, level))


# Precompute cumulative XP thresholds for all levels.
# XP_TABLE[i] = total XP needed to be at level i+1.
# XP_TABLE[0] = 0 (level 1 starts at 0 XP)
XP_TABLE: list[int] = [_compute_threshold(lvl) for lvl in range(1, MAX_LEVEL + 2)]


def get_level(total_xp: int) -> int:
    """Return the current level for a given total XP amount."""
    level = 1
    for lvl in range(MAX_LEVEL, 0, -1):
        if total_xp >= XP_TABLE[lvl - 1]:
            level = lvl
            break
    return min(level, MAX_LEVEL)


def xp_for_next_level(total_xp: int) -> int:
    """Return XP needed to reach the next level from current total."""
    level = get_level(total_xp)
    if level >= MAX_LEVEL:
        return 0
    return XP_TABLE[level] - total_xp


def xp_progress(total_xp: int) -> tuple[int, int, int, float]:
    """Return (level, xp_into_level, xp_needed_for_level, pct).

    xp_into_level: XP earned since start of current level.
    xp_needed_for_level: total XP span of current level.
    pct: 0.0–1.0 progress through current level.
    """
    level = get_level(total_xp)
    if level >= MAX_LEVEL:
        return MAX_LEVEL, 0, 0, 1.0
    level_start = XP_TABLE[level - 1]
    level_end = XP_TABLE[level]
    span = level_end - level_start
    into = total_xp - level_start
    pct = into / span if span > 0 else 1.0
    return level, into, span, pct


def level_success_bonus(level: int) -> float:
    """Return success chance bonus from level (0.0–0.20).

    +0.5% per level, capped at +20% at level 40.
    """
    return min(level * 0.005, 0.20)


def xp_bar(pct: float, length: int = 20) -> str:
    """Dot progress bar for XP."""
    filled = min(round(pct * length), length)
    bar = "●" * filled + "○" * (length - filled)
    return f"`{bar}` {pct * 100:.1f}%"


async def award_xp(
    cog,
    member,
    heist_type: str,
    success: bool,
    caught: bool,
) -> tuple[int, int, int]:
    """Award XP for a heist outcome. Returns (old_level, new_level, xp_gained).

    - Caught: 0 XP
    - Fail: 20% of base XP
    - Success: full base XP
    """
    if caught:
        return (
            get_level(await cog.config.user(member).xp()),
            get_level(await cog.config.user(member).xp()),
            0,
        )

    from .utils import HEISTS

    heist_data = HEISTS.get(heist_type, {})
    base_xp = heist_data.get("xp_reward", 50)

    xp_gained = base_xp if success else max(1, int(base_xp * 0.20))
    old_xp = await cog.config.user(member).xp()
    old_level = get_level(old_xp)
    new_xp = old_xp + xp_gained
    new_level = min(get_level(new_xp), MAX_LEVEL)

    # Cap XP at max level threshold
    if new_level >= MAX_LEVEL:
        new_xp = min(new_xp, XP_TABLE[MAX_LEVEL - 1])

    await cog.config.user(member).xp.set(new_xp)
    return old_level, new_level, xp_gained
