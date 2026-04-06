# NBA

NBA information cog.<br/>- Get the current NBA schedule for the next game.<br/>- Get the current NBA scoreboard.<br/>- Get the latest NBA news.<br/>- Set the channel to send NBA game updates to.

## [p]nbaset

Settings for NBA.<br/>

 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]nbaset reset

Reset all NBA update settings for this server.<br/>

 - Usage: `[p]nbaset reset`
 - Aliases: `clear`

### [p]nbaset role

Manage the role pinged for pre-game notifications per team.<br/>

 - Usage: `[p]nbaset role`

#### [p]nbaset role set

Set a role to ping 30 minutes before a specific team's game starts.<br/>

**Example:**<br/>
- `[p]nbaset role set heat @HeatFans`<br/>

 - Usage: `[p]nbaset role set <team> <role>`

#### [p]nbaset role remove

Remove the pre-game ping role for a specific team.<br/>

**Example:**<br/>
- `[p]nbaset role remove heat`<br/>

 - Usage: `[p]nbaset role remove <team>`

### [p]nbaset remove

Remove a team from the NBA update list.<br/>

**Example:**<br/>
- `[p]nbaset remove heat`<br/>

 - Usage: `[p]nbaset remove <team>`

### [p]nbaset emojis

Sync NBA team logos as application emojis.<br/>

Uploads any missing team emojis to the bot's application emoji list,<br/>
then refreshes the in-memory cache. Already-uploaded emojis are skipped.<br/>
Team logo images are fetched from the NBA CDN.<br/>

 - Usage: `[p]nbaset emojis`
 - Restricted to: `BOT_OWNER`
 - Cooldown: `1 per 900.0 seconds`

### [p]nbaset channel

Add or update a team channel for NBA game updates.<br/>

Each team can have its own channel. Run the command again with the same<br/>
team to update the channel. When two configured teams play each other,<br/>
only the home team's channel receives the notification.<br/>

**Examples:**<br/>
- `[p]nbaset channel #heat-updates heat`<br/>
- `[p]nbaset channel #sixers-updates sixers`<br/>

**Arguments:**<br/>
- `channel`: The channel to send NBA game updates to.<br/>
- `team`: The team to get the game updates for.<br/>

**Valid Team Names:**<br/>
- heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards<br/>

 - Usage: `[p]nbaset channel <channel> <team>`

### [p]nbaset settings

View the current NBA settings.<br/>

 - Usage: `[p]nbaset settings`

## [p]nba (Hybrid Command)

Get the current NBA schedule for next game.<br/>

 - Usage: `[p]nba`
 - Slash Usage: `/nba`
 - Checks: `guild_only`

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

Shows West then East, sorted by conference rank.<br/>
Includes W, L, PCT, GB, last 10, and current streak.<br/>

**Note**:<br/>
- Data provided by ESPN. Full standings at https://www.nba.com/standings.<br/>

 - Usage: `[p]nba standings`
 - Slash Usage: `/nba standings`
 - Cooldown: `1 per 30.0 seconds`

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

### [p]nba playoffs (Hybrid Command)

Get the current NBA playoff bracket and series info.<br/>

Also shows Play-In tournament matchups when active.<br/>

 - Usage: `[p]nba playoffs`
 - Slash Usage: `/nba playoffs`
 - Cooldown: `1 per 10.0 seconds`

### [p]nba news (Hybrid Command)

Get latest NBA news.<br/>

 - Usage: `[p]nba news`
 - Slash Usage: `/nba news`
 - Cooldown: `1 per 3.0 seconds`
