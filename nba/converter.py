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

import re
from datetime import datetime, timezone

import pytz
from red_commons.logging import getLogger

log = getLogger("red.maxcogs.nba.converter")

TODAY_SCOREBOARD = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_2.json"
ESPN_NBA_NEWS = "http://www.espn.com/espn/rss/nba/news"
PLAYBYPLAY = "https://cdn.nba.com/static/json"

TEAM_NAMES = [
    "heat",
    "bucks",
    "bulls",
    "cavaliers",
    "celtics",
    "clippers",
    "grizzlies",
    "hawks",
    "hornets",
    "jazz",
    "kings",
    "knicks",
    "lakers",
    "magic",
    "mavericks",
    "nets",
    "nuggets",
    "pacers",
    "pelicans",
    "pistons",
    "raptors",
    "rockets",
    "sixers",
    "spurs",
    "suns",
    "thunder",
    "timberwolves",
    "trail blazers",
    "warriors",
    "wizards",
]
TEAM_NAME_TO_API: dict[str, str] = {
    "heat": "Heat",
    "bucks": "Bucks",
    "bulls": "Bulls",
    "cavaliers": "Cavaliers",
    "celtics": "Celtics",
    "clippers": "Clippers",
    "grizzlies": "Grizzlies",
    "hawks": "Hawks",
    "hornets": "Hornets",
    "jazz": "Jazz",
    "kings": "Kings",
    "knicks": "Knicks",
    "lakers": "Lakers",
    "magic": "Magic",
    "mavericks": "Mavericks",
    "nets": "Nets",
    "nuggets": "Nuggets",
    "pacers": "Pacers",
    "pelicans": "Pelicans",
    "pistons": "Pistons",
    "raptors": "Raptors",
    "rockets": "Rockets",
    "sixers": "76ers",
    "spurs": "Spurs",
    "suns": "Suns",
    "thunder": "Thunder",
    "timberwolves": "Timberwolves",
    "trail blazers": "Trail Blazers",
    "warriors": "Warriors",
    "wizards": "Wizards",
}

# Canonical emoji name for each team, used when uploading/looking up application emojis.
# Application emojis are global (not per-guild) and managed via the owner-only sync command.
TEAM_EMOJI_NAMES: dict[str, str] = {
    "Heat": "heat",
    "Bucks": "milwaukee_bucks",
    "Bulls": "chicago_bulls",
    "Cavaliers": "cleveland_cavaliers",
    "Celtics": "boston_celtics",
    "Clippers": "los_angeles_clippers",
    "Grizzlies": "memphis_grizzlies",
    "Hawks": "atlanta_hawks",
    "Hornets": "charlotte_hornets",
    "Jazz": "utah_jazz",
    "Kings": "sacramento_kings",
    "Knicks": "new_york_knicks",
    "Lakers": "los_angeles_lakers",
    "Magic": "orlando_magic",
    "Mavericks": "dallas_mavericks",
    "Nets": "brooklyn_nets",
    "Nuggets": "denver_nuggets",
    "Pacers": "indiana_pacers",
    "Pelicans": "new_orleans_pelicans",
    "Pistons": "detroit_pistons",
    "Raptors": "toronto_raptors",
    "Rockets": "houston_rockets",
    "76ers": "philadelphia_76ers",
    "Spurs": "san_antonio_spurs",
    "Suns": "phoenix_suns",
    "Thunder": "oklahoma_city_thunder",
    "Timberwolves": "minnesota_timberwolves",
    "Trail Blazers": "portland_trail_blazers",
    "Warriors": "golden_state_warriors",
    "Wizards": "washington_wizards",
}
# Runtime cache populated by NBA.load_application_emojis() on cog load.
# Maps team name → "<:emoji_name:emoji_id>" string ready for embed use.
team_emojis: dict[str, str] = {}

NBA_STATS_HEADERS: dict[str, str] = {
    "Host": "stats.nba.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}



def parse_duration(duration: str) -> str:
    """
    Parse a game clock string from the NBA API into a human-readable MM:SS string.
    """
    if not duration:
        return "0:00"

    match_pt = re.match(r"PT(?:(\d+)M)?(?:(\d+)(?:\.(\d+))?S)?", duration)
    match_mmss = re.match(r"(\d+):(\d+)", duration)

    if match_pt and any(match_pt.groups()):
        minutes = int(match_pt.group(1) or 0)
        seconds = int(match_pt.group(2) or 0)
        milliseconds = int(match_pt.group(3) or 0)
    elif match_mmss:
        minutes = int(match_mmss.group(1))
        seconds = int(match_mmss.group(2))
        milliseconds = 0
    else:
        log.error("Unexpected duration format: %s — defaulting to 0:00", duration)
        return "0:00"

    minutes = min(minutes, 12)
    total_seconds = minutes * 60 + seconds + (milliseconds / 1000 if milliseconds else 0)
    minutes_left = int(total_seconds // 60)
    seconds_left = int(total_seconds % 60)
    return f"{minutes_left}:{str(seconds_left).zfill(2)}"


periods = {
    0: "Pre-Game",
    1: "1st Quarter",
    2: "2nd Quarter",
    3: "3rd Quarter",
    4: "4th Quarter",
    5: "Overtime",
}


def get_time_bounds():
    """Get the start and end timestamps for the scoreboard update window in Eastern Time."""
    now_utc = datetime.now(pytz.utc)
    now_et = now_utc.astimezone(pytz.timezone("US/Eastern"))
    start_time_et = now_et.replace(hour=12, minute=0, second=0, microsecond=0)
    end_time_et = now_et.replace(hour=13, minute=0, second=0, microsecond=0)
    start_timestamp = int(start_time_et.astimezone(pytz.utc).timestamp())
    end_timestamp = int(end_time_et.astimezone(pytz.utc).timestamp())
    return start_timestamp, end_timestamp


def get_leaders_info(game):
    """Get the leaders information for the home and away teams."""
    home_leaders_str = away_leaders_str = "N/A"
    game_leaders = game.get("gameLeaders")
    if game_leaders is not None:
        home_leaders = game_leaders.get("homeLeaders")
        if home_leaders is not None:
            home_leaders_str = (
                f"**Name**: {home_leaders.get('name') or 'N/A'}\n"
                f"**JerseyNum**: {home_leaders.get('jerseyNum') or 'N/A'}\n"
                f"**Position**: {home_leaders.get('position') or 'N/A'}\n"
                f"**Points**: {home_leaders.get('points') or 'N/A'}\n"
                f"**Rebounds**: {home_leaders.get('rebounds') or 'N/A'}\n"
                f"**Assists**: {home_leaders.get('assists') or 'N/A'}"
            )
        away_leaders = game_leaders.get("awayLeaders")
        if away_leaders is not None:
            away_leaders_str = (
                f"**Name**: {away_leaders.get('name') or 'N/A'}\n"
                f"**JerseyNum**: {away_leaders.get('jerseyNum') or 'N/A'}\n"
                f"**Position**: {away_leaders.get('position') or 'N/A'}\n"
                f"**Points**: {away_leaders.get('points') or 'N/A'}\n"
                f"**Rebounds**: {away_leaders.get('rebounds') or 'N/A'}\n"
                f"**Assists**: {away_leaders.get('assists') or 'N/A'}"
            )
    return home_leaders_str, away_leaders_str


def get_games(schedule):
    """Get scheduled games from the NBA json."""
    games = []
    try:
        game_dates = schedule.get("leagueSchedule", {}).get("gameDates", [])
        for date in game_dates:
            for game in date.get("games", []):
                try:
                    game_time = game.get("gameDateTimeUTC")
                    if game_time:
                        timestamp = int(
                            datetime.strptime(game_time, "%Y-%m-%dT%H:%M:%SZ")
                            .replace(tzinfo=timezone.utc)
                            .timestamp()
                        )
                        if timestamp >= datetime.now(tz=timezone.utc).timestamp():
                            games.append(
                                {
                                    "home_team": game["homeTeam"].get("teamName", "Unknown"),
                                    "away_team": game["awayTeam"].get("teamName", "Unknown"),
                                    "timestamp": timestamp,
                                    "arena": game.get("arenaName", "Unknown"),
                                    "arenastate": game.get("arenaState", "Unknown"),
                                    "arena_city": game.get("arenaCity", "Unknown"),
                                }
                            )
                except (KeyError, ValueError) as e:
                    log.error("Error processing game data: %s", e)
    except Exception as e:
        log.error("Error processing schedule data: %s", e)
    return games
