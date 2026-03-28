# NBA

NBA information cog.<br/>- Get the current NBA schedule for the next game.<br/>- Get the current NBA scoreboard.<br/>- Get the latest NBA news.<br/>- Set the channel to send NBA game updates to.

## [p]nbaset

Settings for NBA.<br/>

 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]nbaset reset

Reset the channel and team settings.<br/>

 - Usage: `[p]nbaset reset`
 - Aliases: `clear`

### [p]nbaset channel

Set the channel to send NBA game updates to.<br/>

**Note:**<br/>
You can only set one channel and one team per server.<br/>

**Examples:**<br/>
- `[p]nbaset channel #nba heat` - it will send updates to #nba for the Miami Heat.<br/>

**Arguments:**<br/>
- `channel`: The channel to send NBA game updates to.<br/>
- `team`: The team to get the game updates for.<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>

 - Usage: `[p]nbaset channel <channel> <team>`

### [p]nbaset settings

View the channel and team settings.<br/>

 - Usage: `[p]nbaset settings`

## [p]nba (Hybrid Command)

Get the current NBA schedule for next game.<br/>

 - Usage: `[p]nba`
 - Slash Usage: `/nba`
 - Checks: `guild_only`

### [p]nba schedule (Hybrid Command)

Get the current NBA schedule for next game.<br/>

**Arguments:**<br/>
    - `[team]`: The team name to filter the schedule.<br/>

**Note**:<br/>
- The NBA's regular season runs from October to April.<br/>
- The [playoffs](https://www.nba.com/playoffs) is in April to June.<br/>
- The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>

 - Usage: `[p]nba schedule [team]`
 - Slash Usage: `/nba schedule [team]`
 - Aliases: `nextgame and s`
 - Cooldown: `1 per 3.0 seconds`

### [p]nba news (Hybrid Command)

Get latest NBA news.<br/>

 - Usage: `[p]nba news`
 - Slash Usage: `/nba news`
 - Cooldown: `1 per 3.0 seconds`

### [p]nba scoreboard (Hybrid Command)

Get the current NBA scoreboard.<br/>

- Scoreboard updates everyday between 12:00 PM ET and 1:00 PM ET.<br/>

**Note**:<br/>
- The NBA's regular season runs from October to April.<br/>
- The [playoffs](https://www.nba.com/playoffs) is in April to June.<br/>
- The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.<br/>

**Examples:**<br/>
- `[p]nba scoreboard` - Returns the current NBA scoreboard.<br/>
- `[p]nba scoreboard heat` - Returns the current NBA scoreboard for the Miami Heat.<br/>

**Arguments:**<br/>
- `[team]` - The team you want to get the scoreboard for.<br/>

 - Usage: `[p]nba scoreboard [team=None]`
 - Slash Usage: `/nba scoreboard [team=None]`
 - Aliases: `score and scores`
 - Cooldown: `1 per 3.0 seconds`

