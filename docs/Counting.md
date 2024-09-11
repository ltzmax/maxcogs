# Counting Help

Count from 1 to infinity!

# counting
 - Usage: `[p]counting`
 - Checks: `server_only`

Counting commands

## counting countstats
 - Usage: `[p]counting countstats`
 - Aliases: `stats`
 - Cooldown: `1 per 60.0 seconds`

Get your current counting statistics.

## counting resetme
 - Usage: `[p]counting resetme`

Reset your counting stats.

# countingset
 - Usage: `[p]countingset`
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Counting settings commands.

## countingset toggle
 - Usage: `[p]countingset toggle`

Toggle counting in the channel

## countingset channel
 - Usage: `[p]countingset channel <channel>`

Set the counting channel

## countingset deleteafter
 - Usage: `[p]countingset deleteafter <seconds>`

Set the number of seconds to delete the incorrect message<br/><br/>Default is 5 seconds

## countingset setmessage
 - Usage: `[p]countingset setmessage <message_type> <message>`

Set the default message for a specific type.<br/><br/>Available message types: edit, count<br/><br/>`edit` - The message to show when a user edits their message in the counting channel.<br/>`count` - The message to show when a user sends an incorrect number in the counting channel.<br/><br/>**Examples:**<br/>- `[p]countingset setmessage edit You can't edit your messages here.`<br/>- `[p]countingset setmessage count Next number should be {next_count}`<br/><br/>**Arguments:**<br/>- `<message_type>` The type of message to set (edit or count).<br/>- `<message>` The message to set.

## countingset togglesameuser
 - Usage: `[p]countingset togglesameuser`

Toggle whether the same user can count more than once consecutively.

## countingset reset
 - Usage: `[p]countingset reset`

Reset the settings for the counting

## countingset enable
 - Usage: `[p]countingset enable <setting>`

Toggle to show the edit message or next number message.<br/><br/>Available settings: edit, count<br/><br/>`count` - Show the next number message when a user sends an incorrect number. Default is disabled<br/>`edit` - Shows a message when a user edits their message in the counting channel. Default is disabled

## countingset settings
 - Usage: `[p]countingset settings`

Show the current counting settings.
