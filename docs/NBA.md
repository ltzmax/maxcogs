## NOTE (OPTIONAL)
This cog uses ``redis`` for the auto updates of scores under which you set from ``[p]nbaset channel``. You can follow the instructions here: <https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/> for your operating system. 

## NBA Cog that provides NBA game updates, schedules, and news.

# [p]nbaset
Settings for NBA.<br/>
 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]nbaset view
View the channel and team settings.<br/>
 - Usage: `[p]nbaset view`
## [p]nbaset clear
Clear the channel and team settings.<br/>
 - Usage: `[p]nbaset clear`
## [p]nbaset channel
Set the channel to send NBA game updates to.<br/>

**Note:**<br/>
You can only set one channel and one team per server.<br/>

**Examples:**<br/>
- `[p]nbaset channel #nba heat` - it will send updates to #nba for the Miami Heat.<br/>

**Arguments:**<br/>
- `channel`: The channel to send NBA game updates to.<br/>
- `team`: The team to get the game updates for.<br/>

**Vaild Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trailblazers, warriors, wizards<br/>
 - Usage: `[p]nbaset channel <channel> <team>`
# [p]nba (Hybrid Command)
Get the current NBA schedule for next game.<br/>
 - Usage: `[p]nba`
 - Slash Usage: `/nba`
 - Checks: `server_only`
## [p]nba scoreboard (Hybrid Command)
Get the current NBA scoreboard.<br/>

- Scoreboard updates everyday between 12:00 PM ET and 1:00 PM ET.<br/>
    - Feel free to convert the time to your timezone from https://dateful.com/time-zone-converter.<br/>

**Note**:<br/>
- The NBA's regular season runs from October to April.<br/>
- The [playoffs](https://www.nba.com/playoffs) is in April to June.<br/>
- The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.<br/>

**Examples:**<br/>
- `[p]nba scoreboard` - Returns the current NBA scoreboard.<br/>
- `[p]nba scoreboard heat` - Returns the current NBA scoreboard for the Miami Heat.<br/>

**Arguments:**<br/>
- `[team]` - The team you want to get the scoreboard for. If not specified, it will return all games.<br/>
 - Usage: `[p]nba scoreboard [team=None]`
 - Slash Usage: `/nba scoreboard [team=None]`
 - Aliases: `score and scores`
## [p]nba news (Hybrid Command)
Get latest nba news<br/>
 - Usage: `[p]nba news`
 - Slash Usage: `/nba news`
 - Cooldown: `1 per 3.0 seconds`
## [p]nba schedule (Hybrid Command)
Get the current NBA schedule for next game.<br/>

**Arguments:**<br/>
    - `[team]`: The team name to filter the schedule.<br/>

**Note**:<br/>
- The NBA's regular season runs from October to April.<br/>
- The [playoffs](https://www.nba.com/playoffs) is in April to June.<br/>
- The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.<br/>

**Vaild Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trailblazers, warriors, wizards<br/>
 - Usage: `[p]nba schedule [team]`
 - Slash Usage: `/nba schedule [team]`
 - Aliases: `nextgame and s`
 - Cooldown: `1 per 3.0 seconds`
