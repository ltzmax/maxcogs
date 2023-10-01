# EmojiSpam Help

Similar emojispam filter to dyno but without ban, kick and mute.

# emojispam
 - Usage: `[p]emojispam `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the emoji spam filter.

## emojispam toggle
 - Usage: `[p]emojispam toggle [toggle=None] `

Toggle the emoji spam filter.<br/><br/>If no enabled state is provided, the current state will be toggled.

## emojispam logchannel
 - Usage: `[p]emojispam logchannel [channel=None] `

Set the log channel.<br/><br/>If no channel is provided, the log channel will be disabled.

## emojispam resetmsg
 - Usage: `[p]emojispam resetmsg `

Reset the message to the default message.

## emojispam listignored
 - Usage: `[p]emojispam listignored `

List ignored channels.

## emojispam embed
 - Usage: `[p]emojispam embed [toggle=None] `

Toggle the use of embeds for the message.<br/><br/>If no enabled state is provided, the current state will be toggled.

## emojispam msg
 - Usage: `[p]emojispam msg <msg> `

Set the message to send when a user goes over the emoji limit.<br/><br/>Default message is:<br/>`You are sending too many emojis!`.

## emojispam limit
 - Usage: `[p]emojispam limit <limit> `

Set the emoji limit.<br/><br/>Default limit is 5.<br/>Limit must be between 1 and 100.<br/><br/>If limit is set to 4, a user can send 4 emojis, but not 5.

## emojispam deleteafter
 - Usage: `[p]emojispam deleteafter [seconds=None] `

Set the delete after time for the message.<br/><br/>Default time is 10 seconds.<br/>Time must be between 1 and 120 seconds.<br/><br/>If time is set to 5, the message will be deleted after 5 seconds.

## emojispam ignore
 - Usage: `[p]emojispam ignore [channel=None] `

Ignore a channel.<br/><br/>When a channel is ignored, the emoji spam filter will not be applied to that channel.

## emojispam settings
 - Usage: `[p]emojispam settings `

Show the current settings.

## emojispam msgtoggle
 - Usage: `[p]emojispam msgtoggle <add_or_remove> `

Enable or disable the message.<br/><br/>If the message is disabled, no message will be sent when a user goes over the emoji limit.<br/><br/>Default state is disabled.<br/><br/>**Valid options:**<br/>- enable<br/>- disable<br/><br/>**Example:**<br/>- `[p]emojispam msgtoggle enable`<br/>  - This will enable the message and send it when a user goes over the emoji limit.<br/>- `[p]emojispam msgtoggle disable`<br/>  - This will disable the message and will not send it when a user goes over the emoji limit.

## emojispam unignore
 - Usage: `[p]emojispam unignore [channel=None] `

Unignore a channel.

## emojispam version
 - Usage: `[p]emojispam version `

Shows the version of the cog.

## emojispam reset
 - Usage: `[p]emojispam reset `

Reset all settings back to default.