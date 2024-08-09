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


def get_games(schedule):
    """
    Get scheduled games from the NBA json.
    """
    games = [
        {
            "home_team": game["homeTeam"]["teamName"],
            "away_team": game["awayTeam"]["teamName"],
            "timestamp": int(
                datetime.strptime(game["gameDateTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ),
            "arena": game["arenaName"],
            "arenastate": game["arenaState"],
            "arena_city": game["arenaCity"],
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
