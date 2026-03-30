# NBA

NBA information cog.<br/>- Get the current NBA schedule for the next game.<br/>- Get the current NBA scoreboard.<br/>- Get the latest NBA news.<br/>- Get standings, stat leaders, player info, rosters, and team stats.<br/>- Set the channel to send NBA game updates to.

## [p]nbaset

Settings for NBA.<br/>

 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]nbaset reset

Reset the channel and team settings.<br/>

 - Usage: `[p]nbaset reset`
 - Aliases: `clear`

### [p]nbaset emojis

Sync NBA team logos as application emojis (global, owner only).<br/>

Uploads any missing team emojis to the bot's application emoji list,<br/>
then refreshes the in-memory cache. Already-uploaded emojis are skipped.<br/>
Team logo images are fetched from the NBA CDN.<br/>

 - Usage: `[p]nbaset emojis`
 - Restricted to: `BOT_OWNER`
 - Cooldown: `1 per 900.0 seconds`

### [p]nbaset settings

View the channel and team settings.<br/>

 - Usage: `[p]nbaset settings`

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

### [p]nbaset role set

Set a role to ping 30 minutes before game starts.<br/>

 - Usage: `[p]nbaset role set <role>`

### [p]nbaset role remove

Remove the pre-game ping role.<br/>

 - Usage: `[p]nbaset role remove`

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

### [p]nba standings (Hybrid Command)

Get the current NBA standings.<br/>

Shows win/loss record, win%, games behind, home/road record, last 10, streak, and clinch indicator for every team.<br/>

**Arguments:**<br/>
- `[conference]` - Filter to `east` or `west`. Shows both if omitted.<br/>

 - Usage: `[p]nba standings [conference]`
 - Slash Usage: `/nba standings [conference]`
 - Cooldown: `1 per 10.0 seconds`

### [p]nba leaders (Hybrid Command)

Get the NBA per-game stat leaders.<br/>

**Arguments:**<br/>
- `[category]` - One of `pts`, `reb`, `ast`, `stl`, `blk`. Defaults to `pts`.<br/>

**Examples:**<br/>
- `[p]nba leaders` - Returns the top points-per-game leaders.<br/>
- `[p]nba leaders reb` - Returns the top rebounders.<br/>
- `[p]nba leaders ast` - Returns the top assist leaders.<br/>

 - Usage: `[p]nba leaders [category=pts]`
 - Slash Usage: `/nba leaders [category=pts]`
 - Cooldown: `1 per 10.0 seconds`

### [p]nba player (Hybrid Command)

Get bio and career stats for an NBA player.<br/>

**Arguments:**<br/>
- `<name>` - The player's name to look up (e.g. `LeBron James`).<br/>

**Examples:**<br/>
- `[p]nba player LeBron James`<br/>
- `[p]nba player curry`<br/>

 - Usage: `[p]nba player <name>`
 - Slash Usage: `/nba player <name>`
 - Cooldown: `1 per 10.0 seconds`

### [p]nba roster (Hybrid Command)

Get the current roster for an NBA team.<br/>

**Arguments:**<br/>
- `<team>` - The team name (e.g. `lakers`, `celtics`).<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>

 - Usage: `[p]nba roster <team>`
 - Slash Usage: `/nba roster <team>`
 - Cooldown: `1 per 10.0 seconds`

### [p]nba teamstats (Hybrid Command)

Get season averages for an NBA team.<br/>

Shows per-game averages for points, rebounds, assists, steals, blocks, turnovers, shooting splits, and plus/minus.<br/>

**Arguments:**<br/>
- `<team>` - The team name (e.g. `warriors`, `heat`).<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>

 - Usage: `[p]nba teamstats <team>`
 - Slash Usage: `/nba teamstats <team>`
 - Cooldown: `1 per 10.0 seconds`
