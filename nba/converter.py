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

import logging
import re
from datetime import datetime, timezone

import pytz

log = logging.getLogger("red.maxcogs.nba.converter")
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

# Please do not change the names of the teams, as they are used to match the team names from the NBA API.
team_emojis = {
    "Heat": "<:heat:1337072557286756444>",
    "Bucks": "<:milwaukee_bucks:1337077115157479576>",
    "Bulls": "<:chicago_bulls:1337076752098394193>",
    "Cavaliers": "<:cleveland_cavaliers:1337076799103963198>",
    "Celtics": "<:boston_celtics:1337076672217743453>",
    "Clippers": "<:los_angeles_clippers:1337077028632924221>",
    "Grizzlies": "<:memphis_grizzlies:1347872827839348797>",
    "Hawks": "<:atlanta_hawks:1337076371045744723>",
    "Hornets": "<:charlotte_hornets:1347873894660444172>",
    "Jazz": "<:utah_jazz:1337076534271279175>",
    "Kings": "<:sacramento_kings:1337076620640518174>",
    "Knicks": "<:new_york_knicks:1337077172656934964>",
    "Lakers": "<:los_angeles_lakers:1337077057170964481>",
    "Magic": "<:orlando_magic:1337077193729114214>",
    "Mavericks": "<:dallas_mavericks:1337076831672733796>",
    "Nets": "<:brooklyn_nets:1337076712424603668>",
    "Nuggets": "<:denver_nuggets:1347873502065332224>",
    "Pacers": "<:indiana_pacers:1337076420467228756>",
    "Pelicans": "<:new_orleans_pelicans:1337077141136736297>",
    "Pistons": "<:detroit_pistons:1337076923469402192>",
    "Raptors": "<:toronto_raptors:1337076580270346301>",
    "Rockets": "<:houston_rockets:1337077003614027796>",
    "76ers": "<:philadelphia_76ers:1337076955631194214>",
    "Spurs": "<:san_antonio_spurs:1337076455536070686>",
    "Suns": "<:phoenix_suns:1337077081124769822>",
    "Thunder": "<:oklahoma_city_thunder:1337076867278045184>",
    "Timberwolves": "<:minnesota_timberwolves:1337077256505262162>",
    "Trail Blazers": "<:portland_trail_blazers:1337076642866135072>",
    "Warriors": "<:golden_state_warriors:1337076978112528405>",
    "Wizards": "<:washington_wizards:1337076493716815903>",
}


def parse_game_time_to_seconds(duration):
    """
    Parse the duration string from the NBA API into total seconds for comparison.
    """
    if not duration or duration == "PT0M0S":  # Handle empty or zero-time strings
        return 0

    # Pattern for PT format
    match_pt = re.match(r"PT(?:(\d+)M)?(?:(\d+)(?:\.(\d+))?S)?", duration)
    # Pattern for MM:SS format (optional, if API might return this)
    match_mmss = re.match(r"(\d+):(\d+)", duration)

    if match_pt:
        minutes = int(match_pt.group(1) or 0)
        seconds = int(match_pt.group(2) or 0)
        milliseconds = int(match_pt.group(3) or 0) if match_pt.group(3) else 0
    elif match_mmss:
        minutes = int(match_mmss.group(1))
        seconds = int(match_mmss.group(2))
        milliseconds = 0
    else:
        log.error(
            f"Unexpected duration format: {duration} - defaulting to 0 seconds", exc_info=True
        )
        return 0

    # Cap minutes at 12 for NBA quarters
    minutes = min(minutes, 12)

    total_seconds = minutes * 60 + seconds + (milliseconds / 1000 if milliseconds else 0)
    return total_seconds


def parse_duration(duration):
    """
    Parse the duration string from the NBA API, handling various cases where
    minutes or seconds might not be explicitly stated or in different formats.
    """
    # Pattern for PT format
    match_pt = re.match(r"PT(?:(\d+)M)?(?:(\d+)(?:\.(\d+))?S)?", duration)
    # Pattern for MM:SS format
    match_mmss = re.match(r"(\d+):(\d+)", duration)

    if match_pt:
        minutes = int(match_pt.group(1) or 0)
        seconds = int(match_pt.group(2) or 0)
        milliseconds = int(match_pt.group(3) or 0)
    elif match_mmss:
        minutes = int(match_mmss.group(1))
        seconds = int(match_mmss.group(2))
        milliseconds = 0
    else:
        log.error(f"Unexpected duration format: {duration} - defaulting to 0:00", exc_info=True)
        return "0:00"

    # Cap minutes at 12 for NBA quarters
    minutes = min(minutes, 12)

    if minutes == 0 and seconds == 0 and milliseconds == 0:
        return "0:00"

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
    """
    Get the start and end timestamps for the current hour in Eastern Time.
    This function is used to when the scoreboard is updated each day(s).
    """
    now_utc = datetime.now(pytz.utc)
    now_et = now_utc.astimezone(pytz.timezone("US/Eastern"))
    # Define the start and end times in Eastern Time
    start_time_et = now_et.replace(hour=12, minute=0, second=0, microsecond=0)
    end_time_et = now_et.replace(hour=13, minute=0, second=0, microsecond=0)
    # Convert the start and end times to UTC
    start_time_utc = start_time_et.astimezone(pytz.utc)
    end_time_utc = end_time_et.astimezone(pytz.utc)
    # Get the start and end timestamps
    start_timestamp = int(start_time_utc.timestamp())
    end_timestamp = int(end_time_utc.timestamp())
    return start_timestamp, end_timestamp


def get_leaders_info(game):
    """
    Get the leaders information for the home and away teams.
    """
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
                        if timestamp >= datetime.utcnow().replace(tzinfo=timezone.utc).timestamp():
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
                    log.error(f"Error processing game data: {e}")
    except Exception as e:
        log.error(f"Error processing schedule data: {e}")
    return games
