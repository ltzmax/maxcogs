Count from 1 to infinity!

# [p]counting (Hybrid Command)
Counting commands<br/>
 - Usage: `[p]counting`
 - Slash Usage: `/counting`
 - Checks: `server_only`
## [p]counting countstats (Hybrid Command)
Get your current counting statistics.<br/>
 - Usage: `[p]counting countstats [user=None]`
 - Slash Usage: `/counting countstats [user=None]`
 - Aliases: `stats`
 - Cooldown: `1 per 10.0 seconds`
## [p]counting resetme (Hybrid Command)
Reset your counting stats.<br/>
 - Usage: `[p]counting resetme`
 - Slash Usage: `/counting resetme`
## [p]counting leaderboard (Hybrid Command)
Get the counting leaderboard.<br/>
 - Usage: `[p]counting leaderboard`
 - Slash Usage: `/counting leaderboard`
 - Aliases: `lb`
 - Cooldown: `1 per 10.0 seconds`
# [p]countingset
Counting settings commands.<br/>
 - Usage: `[p]countingset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]countingset toggle
Toggle counting in the channel<br/>
 - Usage: `[p]countingset toggle`
## [p]countingset togglesameuser
Toggle whether the same user can count more than once consecutively.<br/>

Users cannot count consecutively if this is enabled meaning they have to wait for someone else to count.<br/>
 - Usage: `[p]countingset togglesameuser`
## [p]countingset togglesilent
Toggle silent mode for counting messages.<br/>

Silent is discords new feature.<br/>
 - Usage: `[p]countingset togglesilent`
## [p]countingset reset
Reset the settings for the counting.<br/>
 - Usage: `[p]countingset reset`
## [p]countingset channel
Set the counting channel<br/>
 - Usage: `[p]countingset channel <channel>`
## [p]countingset deleteafter
Set the number of seconds to delete the incorrect message<br/>

Default is 5 seconds<br/>
 - Usage: `[p]countingset deleteafter <seconds>`
## [p]countingset setreaction
Set the reaction for correct numbers.<br/>
 - Usage: `[p]countingset setreaction <emoji_input>`
## [p]countingset togglereact
Toggle the reactions for correct numbers.<br/>
 - Usage: `[p]countingset togglereact`
## [p]countingset togglemessage
Toggle to show a message for a specific setting.<br/>

Available settings: edit, count<br/>

`count` - Show the next number message when a user sends an incorrect number. Default is disabled<br/>
`edit` - Shows a message when a user edits their message in the counting channel. Default is disabled<br/>
 - Usage: `[p]countingset togglemessage <setting>`
## [p]countingset setmessage
Set the default message for a specific type.<br/>

Available message types: edit, count<br/>

`edit` - The message to show when a user edits their message in the counting channel.<br/>
`count` - The message to show when a user sends an incorrect number in the counting channel.<br/>

**Examples:**<br/>
- `[p]countingset setmessage edit You can't edit your messages here.`<br/>
- `[p]countingset setmessage count Next number should be {next_count}`<br/>

**Arguments:**<br/>
- `<message_type>` The type of message to set (edit or count).<br/>
- `<message>` The message to set.<br/>
 - Usage: `[p]countingset setmessage <message_type> <message>`
## [p]countingset settings
Show the current counting settings.<br/>
 - Usage: `[p]countingset settings`
