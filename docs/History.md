A cog to display historical events for the current day in your timezone.

# [p]historyset
Settings for history events.<br/>
 - Usage: `[p]historyset`
 - Checks: `server_only`
## [p]historyset timezone
Set your timezone for history events to align with your local midnight.<br/>

Use the format `Continent/City`.<br/>
Find your timezone here: https://whatismyti.me/<br/>
Default timezone is UTC if not set by user or invalid.<br/>

**Example**:<br/>
- `[p]historyset timezone America/New_York`<br/>

**Arguments**:<br/>
- `<timezone>`: The timezone you want to set.<br/>
 - Usage: `[p]historyset timezone <timezone>`
# [p]todayinhistory
See all historical events that happened on this day.<br/>

Default timezone is UTC if not set by user.<br/>
Set your timezone with `[p]historyset timezone Continent/City` to align with your local midnight.<br/>
 - Usage: `[p]todayinhistory`
 - Aliases: `history`
 - Cooldown: `1 per 10.0 seconds`
 - Checks: `server_only`
