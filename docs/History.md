# History

A cog to display historical events for a given day in your timezone.

## [p]historyset

Settings for history events.<br/>

 - Usage: `[p]historyset`

### [p]historyset timezone

Set your timezone for history events to align with your local midnight.<br/>

Use the format `Continent/City`.<br/>
Find your timezone here: https://whatismyti.me/<br/>
Default timezone is UTC if not set or invalid.<br/>

**Example**:<br/>
- `[p]historyset timezone America/New_York`<br/>

**Arguments**:<br/>
- `<timezone>`: The timezone to set.<br/>

 - Usage: `[p]historyset timezone <timezone>`

## [p]history (Hybrid Command)

View historical events that happened on this day or a specified date.<br/>

Uses your set timezone for today's date (default: UTC). Set it with `[p]historyset timezone Continent/City`.<br/>
Optionally provide month (1-12) and day (1-31) for a custom date.<br/>

**Examples**:<br/>
- `[p]history` - Events for today.<br/>
- `[p]history 12 25` - Events for December 25.<br/>

 - Usage: `[p]history [month=None] [day=None]`
 - Slash Usage: `/history [month=None] [day=None]`
 - Cooldown: `1 per 10.0 seconds`

