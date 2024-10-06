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


def parse_duration(duration):
    """
    Parse the duration string from the NBA API.
    """
    match = re.match(r"PT(?:(\d+)M)?(?:(\d+\.\d+)?S)?", duration)
    if match:
        minutes = match.group(1) or "0"
        seconds = int(float(match.group(2))) if match.group(2) else 0
        return f"{minutes}:{str(seconds).zfill(2)}"
    else:
        return "0:00"


def get_games(schedule):
    """
    Get scheduled games from the NBA json.
    """
    games = [
        {
            "home_team": game["homeTeam"].get("teamName", "Unknown"),
            "away_team": game["awayTeam"].get("teamName", "Unknown"),
            "timestamp": int(
                datetime.strptime(game["gameDateTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ),
            "arena": game.get("arenaName", "Unknown"),
            "arenastate": game.get("arenaState", "Unknown"),
            "arena_city": game.get("arenaCity", "Unknown"),
        }
        for date in schedule["leagueSchedule"]["gameDates"]
        for game in date["games"]
        if int(
            datetime.strptime(game["gameDateTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        >= datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
    ]
    return games
