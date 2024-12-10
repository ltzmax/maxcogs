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

from datetime import datetime, timezone

import pytz

TODAY_SCOREBOARD = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_2.json"
ESPN_NBA_NEWS = "http://www.espn.com/espn/rss/nba/news"
# PLAYBYPLAY = "https://cdn.nba.com/static/json"
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

# def parse_duration(duration):
#    """
#    Parse the duration string from the NBA API.
#    """
#    match = re.match(r"PT(?:(\d+)M)?(?:(\d+\.\d+)?S)?", duration)
#    if match:
#        minutes = match.group(1) or "0"
#        seconds = int(float(match.group(2))) if match.group(2) else 0
#        return f"{minutes}:{str(seconds).zfill(2)}"
#    else:
#        return "0:00"

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
    """
    Get scheduled games from the NBA json.
    """
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
