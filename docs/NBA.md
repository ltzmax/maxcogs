NBA Cog that provides NBA game updates, schedules, and news.

# [p]nba (Hybrid Command)
Get the current NBA schedule for next game.<br/>
 - Usage: `[p]nba`
 - Slash Usage: `/nba`
 - Checks: `server_only`
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
 - Aliases: `nextgame`
 - Cooldown: `1 per 3.0 seconds`
# [p]nbaset
Set the NBA game updates channel and team.<br/>
 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]nbaset clear
Clear the NBA game updates channel and team.<br/>
 - Usage: `[p]nbaset clear`
## [p]nbaset team
Update a new team to get the NBA game updates for.<br/>

**Arguments:**<br/>
- `<team>`: The team name to get the game updates from.<br/>
    - The team you are selecting, will be the team you will get the game updates for in the channel with the latest scores with the team they are playing against.<br/>

**Vaild Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>
 - Usage: `[p]nbaset team <team>`
## [p]nbaset view
View the current NBA game updates channel and team.<br/>
 - Usage: `[p]nbaset view`
## [p]nbaset channel
Set the channel to send NBA game updates.<br/>

NOTE: you can only set one channel for NBA game updates, it is not possible to set multiple channels for different teams.<br/>

**Arguments:**<br/>
- `<channel>`: The channel to send NBA game updates.<br/>
- `<team>`: The team name to get the game updates from.<br/>
    - The team you are selecting, will be the team you will get the game updates for in the channel with the latest scores with the team they are playing against.<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>
 - Usage: `[p]nbaset channel <channel> <team>`
