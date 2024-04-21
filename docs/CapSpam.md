# CapSpam Help

Prevent users from sending messages with too many caps.

# capspam
 - Usage: `[p]capspam`
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage CapSpam settings

## capspam allowedmentions
 - Usage: `[p]capspam allowedmentions <toggle>`
 - Aliases: `allowedmention and mention`

Toggle allowed mentions in the warning message.<br/><br/>Default is enabled.<br/>If allowed mentions are enabled, the bot will mention the user when sending the warning message.

## capspam ignorelinks
 - Usage: `[p]capspam ignorelinks <toggle>`

Toggle ignoring messages with links or attachments.<br/><br/>Default is enabled.<br/>If enabled, the bot will ignore messages with links or attachments that contain caps in the url.

## capspam version
 - Usage: `[p]capspam version`

Shows the version of the cog.

## capspam warnmsgtoggle
 - Usage: `[p]capspam warnmsgtoggle <toggle>`
 - Aliases: `warnmessagetoggle`

Toggle the warning message.<br/><br/>Default is disabled.<br/><br/>If the warning message is enabled, the bot will send a message when a user is warned.

## capspam ignorechannel
 - Usage: `[p]capspam ignorechannel <add_or_remove> <channels>`

Add or remove channel(s) from the ignore list.<br/><br/>If a channel is in the ignore list, the bot will not check messages in that channel.<br/><br/>**Example:**<br/>`[p]capspam ignorechannel add #channel`<br/>`[p]capspam ignorechannel remove #channel`<br/><br/>**arguments:**<br/>- `<add|remove>`: Add or remove the channel.<br/>- `<channel>`: The channel to add or remove.

## capspam deleteafter
 - Usage: `[p]capspam deleteafter <secounds>`

Set the time to delete the warning message.<br/><br/>Default is 10 seconds.<br/>Timeout must be between 10 and 120 seconds.

## capspam view
 - Usage: `[p]capspam view`
 - Aliases: `settings, setting, and info`

Show the informations about CapSpam in your server.

## capspam warnmsg
 - Usage: `[p]capspam warnmsg [message]`
 - Aliases: `warnmessage and warn`

Set the message to send when a user is warned.<br/><br/>If no message is provided, the default message will be used.

## capspam modlog
 - Usage: `[p]capspam modlog <channel>`

Set modlog channel for CapSpam.<br/><br/>If no channel is provided, the modlog channel will be reset.

## capspam limit
 - Usage: `[p]capspam limit <limit>`

Set the limit of caps allowed in a message.<br/><br/>Default limit is set to 3.

## capspam toggle
 - Usage: `[p]capspam toggle <toggle>`

Toggle CapSpam on/off.

