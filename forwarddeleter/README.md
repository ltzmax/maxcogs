A cog that deletes forwarded messages and allows them in specified channels

# [p]forwarddeleter
Manage forward deleter settings<br/>
 - Usage: `[p]forwarddeleter`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]forwarddeleter action
Settings for actions when repeated offences happens.<br/>
 - Usage: `[p]forwarddeleter action`
### [p]forwarddeleter action listoffences
List all offences.<br/>
 - Usage: `[p]forwarddeleter action listoffences`
### [p]forwarddeleter action addoffence
Add a new offense level for forwarded message violations.<br/>

The action determines the punishment applied when a user reaches this offense level.<br/>
Use 'warn', 'kick', or 'ban' for instant actions, or specify a timeout duration<br/>
(e.g., '1m' for 1 minute, '12h' for 12 hours). The new level is automatically set<br/>
as the next highest level in the server's offense list.<br/>

**Parameters:**<br/>
- `action`: The action to take. Can be 'warn', 'kick', 'ban', or a duration string<br/>
(e.g., '30s', '5m', '2h', '1d').<br/>

**Examples:**<br/>
- `[p]forwarddeleter action addoffence warn`<br/>
    - Adds a warning (no timeout).<br/>
- `[p]forwarddeleter action addoffence 1h`<br/>
    - Adds a 1-hour timeout.<br/>
- `[p]forwarddeleter action addoffence kick`<br/>
    - Adds a kick action.<br/>
- `[p]forwarddeleter action addoffence ban`<br/>
    - Adds a ban action.<br/>
- `[p]forwarddeleter action addoffence 30m`<br/>
    - Adds a 30-minute timeout.<br/>

**Note:**<br/>
- Durations are parsed as seconds (s), minutes (m), hours (h), or days (d).<br/>
- If you only have 3 levels of offences, it will continue to repeat level 3 each time user continue to forward message(s).<br/>
 - Usage: `[p]forwarddeleter action addoffence <action>`
### [p]forwarddeleter action editoffence
Edit an existing offense level's duration<br/>

- See `[p]forwarddeleter action listoffences` for the level.<br/>

**Note**<br/>
- You can only edit duration of timeouts, you cannot change ban to kick etc.<br/>
 - Usage: `[p]forwarddeleter action editoffence <level> <duration>`
### [p]forwarddeleter action removeoffence
Remove an offense level.<br/>

**Example**<br/>
- `[p]forwarddeleter action removeoffence 1`<br/>
    - This will remove offence level 1.<br/>
 - Usage: `[p]forwarddeleter action removeoffence <level>`
### [p]forwarddeleter action resetoffence
Reset a member's offense count.<br/>
 - Usage: `[p]forwarddeleter action resetoffence <member>`
## [p]forwarddeleter togglewarn
Toggle sending a warning message to users when their forwarded message is deleted<br/>
 - Usage: `[p]forwarddeleter togglewarn`
## [p]forwarddeleter setlog
Set or clear the channel for logging deleted forwarded messages<br/>
 - Usage: `[p]forwarddeleter setlog [channel=None]`
## [p]forwarddeleter addrole
Add a role to the forwarding whitelist<br/>
 - Usage: `[p]forwarddeleter addrole <role>`
## [p]forwarddeleter removerole
Remove a role from the forwarding whitelist<br/>
 - Usage: `[p]forwarddeleter removerole <role>`
## [p]forwarddeleter disallow
Remove channels from allowed list.<br/>
 - Usage: `[p]forwarddeleter disallow <channels>`
## [p]forwarddeleter settings
Show Forward Deleter settings with pagination.<br/>
 - Usage: `[p]forwarddeleter settings`
## [p]forwarddeleter setwarnmessage
Set a custom warning message for users<br/>
 - Usage: `[p]forwarddeleter setwarnmessage <message>`
 - Aliases: `setwarnmsg`
## [p]forwarddeleter allow
Add channels where forwarding is allowed list.<br/>
 - Usage: `[p]forwarddeleter allow <channels>`
## [p]forwarddeleter toggle
Toggle forward deleter on/off<br/>
 - Usage: `[p]forwarddeleter toggle`
