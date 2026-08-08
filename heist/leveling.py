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

from red_commons.logging import getLogger


log = getLogger("red.cogs.heist.leveling")

MAX_LEVEL = 120
BASE_XP_REWARD = 212
_WOW_XP_TABLE = [
    400, 900, 1400, 2100, 2800, 3600, 4500, 5400, 6500, 7600,
    8800, 10100, 11400, 12900, 14400, 16000, 17700, 19400, 21300, 23200,
    25200, 27300, 29400, 31700, 34000, 36400, 38900, 41400, 44300, 47400,
    50800, 54500, 58600, 62800, 67100, 71600, 76100, 80800, 85700, 90700,
    95800, 101000, 106300, 111800, 117500, 123200, 129100, 135100, 141200, 147500,
    153900, 160400, 167100, 173900, 180800, 187900, 195000, 202300, 209800,
]


def _level_up_cost(n: int) -> int:
    """XP required to go from level `n` to level `n + 1`."""
    if n <= len(_WOW_XP_TABLE):
        return _WOW_XP_TABLE[n - 1]
    # Beyond real WoW's level-60 cap: continue the same accelerating curve.
    return round(65 * n**2 - 190 * n - 6100)


def _compute_threshold(level: int) -> int:
    """XP required to reach `level` from level 1 (cumulative)."""
    return sum(_level_up_cost(n) for n in range(1, level))


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


def xp_progress(total_xp: int, level: int) -> tuple[int, int, int, float]:
    """Return (level, xp_into_level, xp_needed_for_level, pct).

    `level` is the player's stored level (see note on award_xp below on why
    this isn't derived from total_xp here). xp_into_level: XP earned since
    start of current level. xp_needed_for_level: total XP span of current
    level. pct: 0.0-1.0 progress through current level.
    """
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

    Every heist type awards the same flat BASE_XP_REWARD, which then scales
    with the player's current level at the same rate the level-up cost curve
    grows, so the number of heists needed per level stays roughly constant
    instead of trivializing into 1 heist = 1 level, or ballooning as levels
    climb.

    IMPORTANT: level is read from the stored `level` config field, not
    recomputed from xp against XP_TABLE. It only ever ratchets forward from
    that stored value. If it were recomputed from scratch every time, tuning
    the XP curve later (like we did repeatedly this session) would silently
    change everyone's displayed level based on the same stored xp number,
    which looks like a "reset" even though no xp was lost. Storing level and
    only ever advancing it forward means past progress is never revisited by
    future curve tweaks.
    """
    old_xp = await cog.config.user(member).xp()
    old_level = await cog.config.user(member).level()

    if caught:
        return old_level, old_level, 0

    level_multiplier = _level_up_cost(old_level) / _level_up_cost(1)
    scaled_base_xp = max(1, round(BASE_XP_REWARD * level_multiplier))

    xp_gained = scaled_base_xp if success else max(1, int(scaled_base_xp * 0.20))
    new_xp = old_xp + xp_gained

    # Ratchet forward from the stored level only — never recompute from
    # scratch, so a future curve change can't demote anyone.
    new_level = old_level
    while new_level < MAX_LEVEL and new_xp >= XP_TABLE[new_level]:
        new_level += 1

    # Cap XP at max level threshold
    if new_level >= MAX_LEVEL:
        new_xp = min(new_xp, XP_TABLE[MAX_LEVEL - 1])

    await cog.config.user(member).xp.set(new_xp)
    if new_level != old_level:
        await cog.config.user(member).level.set(new_level)
    return old_level, new_level, xp_gained
