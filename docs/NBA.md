# UNRELEASED COG
# NBA Help

Get the current NBA scoreboard.

# nbaset
 - Usage: `[p]nbaset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Settings for NBA.

## nbaset channel
 - Usage: `[p]nbaset channel <channel> <team>`
 - Aliases: `autopost, setchannel, and channelset`

Set the channel to send score updates for a specific team.<br/><br/>**Note:** This command requires a ``redis-server`` to be running and accessible to store the necessary data of each games.<br/><br/>**Examples:**<br/>- `[p]nbaset channel #nba heat` - it will send updates to #nba for the Miami Heat.<br/><br/>**Arguments:**<br/>- `<channel>` - The channel you want to send NBA updates to.<br/>- `<team>` - The team you want to get the scoreboard updates for.<br/>    - Must be a valid NBA team name. Check `[p]nba teams` for a list of valid teams.

Extended Arg Info
> ### channel: discord.channel.TextChannel
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
> ### team: str
> ```
> A single team, example heat
> ```
## nbaset settings
 - Usage: `[p]nbaset settings`
 - Aliases: `setting, showsettings, and showsetting`

Show the current settings.

## nbaset clear
 - Usage: `[p]nbaset clear`

Reset the channel and team settings to default.

## nbaset role
 - Usage: `[p]nbaset role <role>`

Set the role to mention when game start.<br/><br/>**Examples:**<br/>- `[p]nbaset role @NBA` - it will mention the @NBA role when the game starts.<br/><br/>**Arguments:**<br/>- `[role]` - The role you want to mention when the game starts.

Extended Arg Info
> ### role: Optional[discord.role.Role]
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
# nba (Hybrid Command)
 - Usage: `[p]nba`
 - Slash Usage: `/nba`
 - Checks: `server_only`

NBA commands.

## nba news (Hybrid Command)
 - Usage: `[p]nba news`
 - Slash Usage: `/nba news`
 - Cooldown: `1 per 3.0 seconds`

Get latest nba news

## nba scoreboard (Hybrid Command)
 - Usage: `[p]nba scoreboard [team=None]`
 - Slash Usage: `/nba scoreboard [team=None]`
 - Aliases: `score and scores`

Get the current NBA scoreboard.<br/><br/>- Scoreboard updates everyday between 12:00 PM ET and 1:00 PM ET.<br/>    - Feel free to convert the time to your timezone from https://dateful.com/time-zone-converter.<br/><br/>**Note**:<br/>- The NBA's regular season runs from October to April.<br/>- The [playoffs](https://www.nba.com/playoffs) is in April to June.<br/>- The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.<br/><br/>**Examples:**<br/>- `[p]nba scoreboard` - Returns the current NBA scoreboard.<br/>- `[p]nba scoreboard heat` - Returns the current NBA scoreboard for the Miami Heat.<br/><br/>**Arguments:**<br/>- `[team]` - The team you want to get the scoreboard for. If not specified, it will return all games.

Extended Arg Info
> ### team: Optional[str] = None
> ```
> A single team example heat
> ```
## nba schedule (Hybrid Command)
 - Usage: `[p]nba schedule`
 - Slash Usage: `/nba schedule`
 - Aliases: `s`
 - Cooldown: `1 per 3.0 seconds`

Get the current NBA schedule.

