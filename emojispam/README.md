# EmojiSpam Help

Similar emojispam filter to dyno but without ban, kick and mute.

# emojispam
 - Usage: `[p]emojispam `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the emoji spam filter.

## emojispam logchannel
 - Usage: `[p]emojispam logchannel [channel=None] `

Set the log channel.<br/><br/>If no channel is provided, the log channel will be disabled.

Extended Arg Info

## emojispam toggle
 - Usage: `[p]emojispam toggle `

Enable or disable the emoji spam filter.<br/><br/>Default is disabled.

## emojispam msg
 - Usage: `[p]emojispam msg <msg> `

Set the message to send when a user goes over the emoji limit.<br/><br/>Default message is:<br/>`You are sending too many emojis!`.

Extended Arg Info

## emojispam resetmsg
 - Usage: `[p]emojispam resetmsg `

Reset the message to the default message.

## emojispam limit
 - Usage: `[p]emojispam limit <limit> `

Set the emoji limit.<br/><br/>Default limit is 5.

Extended Arg Info
> ### limit: int
> ```
> A number without decimal places.
> ```
## emojispam msgenable
 - Usage: `[p]emojispam msgenable [enabled] `

Enable or disable the message when a user goes over the emoji limit.<br/><br/>Default is disabled.

Extended Arg Info
> ### enabled: bool = None
> ```
> Can be 1, 0, true, false, t, f
> ```
## emojispam ignore
 - Usage: `[p]emojispam ignore [channel=None] `

Ignore a channel.<br/><br/>When a channel is ignored, the emoji spam filter will not be applied to that channel.     

Extended Arg Info
> ### channel: discord.channel.TextChannel = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
## emojispam listignored
 - Usage: `[p]emojispam listignored `

List ignored channels.

## emojispam unignore
 - Usage: `[p]emojispam unignore [channel=None] `

Unignore a channel.

Extended Arg Info
> ### channel: discord.channel.TextChannel = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
