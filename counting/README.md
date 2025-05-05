Count from 1 to infinity!

# [p]counting (Hybrid Command)
Commands for the counting game.<br/>
 - Usage: `[p]counting`
 - Slash Usage: `/counting`
 - Checks: `server_only`
## [p]counting resetme (Hybrid Command)
Reset your own counting stats.<br/>
 - Usage: `[p]counting resetme`
 - Slash Usage: `/counting resetme`
 - Cooldown: `1 per 360.0 seconds`
## [p]counting stats (Hybrid Command)
Show counting stats for a user.<br/>
 - Usage: `[p]counting stats [user=None]`
 - Slash Usage: `/counting stats [user=None]`
 - Cooldown: `1 per 10.0 seconds`
# [p]countingset
Configure counting game settings.<br/>
 - Usage: `[p]countingset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]countingset minage
Set minimum account age to count.<br/>

The minimum age is set in days, and a value of 0 disables this restriction.<br/>

This setting requires the user to have an account age of at least the specified number of days to count.<br/>
This helps prevent alts or newly created accounts from participating in the counting game and ruining the experience for others.<br/>

**Example:**<br/>
- `[p]countingset minage 30` - Sets the minimum account age to 30 days.<br/>
- `[p]countingset minage 0` - Disables the minimum account age requirement.<br/>

**Arguments:**<br/>
- `<days>`: The minimum account age in days (0-365). A value of 0 disables the restriction.<br/>
 - Usage: `[p]countingset minage [days=0]`
## [p]countingset togglemessage
Toggle visibility of edit or count messages.<br/>
 - Usage: `[p]countingset togglemessage <msg_type>`
## [p]countingset toggle
Toggle the counting game on or off.<br/>
 - Usage: `[p]countingset toggle`
## [p]countingset sameuser
Toggle if the same user can count consecutively.<br/>
 - Usage: `[p]countingset sameuser`
## [p]countingset settings
Show current counting settings.<br/>
 - Usage: `[p]countingset settings`
## [p]countingset setemoji
Set the reaction emoji for correct counts.<br/>
 - Usage: `[p]countingset setemoji <emoji>`
## [p]countingset silent
Toggle silent mode for bot messages.<br/>
 - Usage: `[p]countingset silent`
## [p]countingset reactions
Toggle reactions for correct counts.<br/>
 - Usage: `[p]countingset reactions`
 - Aliases: `togglereaction and togglereact`
## [p]countingset ruincount
Toggle whether users can ruin the count.<br/>
 - Usage: `[p]countingset ruincount`
## [p]countingset reset
Reset all counting settings back to default.<br/>
 - Usage: `[p]countingset reset`
## [p]countingset message
Set custom messages for specific events.<br/>

**Available message types:**<br/>
- `edit`: Message shown when a user edits their message in the counting channel.<br/>
- `count`: Message shown when a user sends an incorrect number.<br/>
- `sameuser`: Message shown when a user tries to count consecutively.<br/>
- `ruincount`: Message shown when a user ruin the message count.<br/>

**Examples:**<br/>
- `[p]countingset setmessage edit You can't edit your messages here.`<br/>
- `[p]countingset setmessage count Next number should be {next_count}`<br/>
- `[p]countingset setmessage sameuser You cannot count until another user have counted`<br/>
- `[p]countingset setmessage ruincount {user} you ruinded the count, starting from {count}!`<br/>

**Arguments:**<br/>
- `<msg_type>`: The type of message to set (edit, count, or sameuser).<br/>
- `<message>`: The message content to set.<br/>
 - Usage: `[p]countingset message <msg_type> <message>`
## [p]countingset deleteafter
Set delete-after time for invalid messages (10-300 seconds).<br/>
 - Usage: `[p]countingset deleteafter <seconds>`
## [p]countingset channel
Set or clear the counting channel.<br/>
 - Usage: `[p]countingset channel [channel=None]`
## [p]countingset ruinrole
Set or clear the role assigned for ruining the count.<br/>

This role is assigned to users who ruin the count by sending an incorrect number or editing their message.<br/>
 - Usage: `[p]countingset ruinrole [role=None]`
