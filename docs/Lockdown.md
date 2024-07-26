# Lockdown Help

Let moderators lockdown a channel to prevent messages from being sent.

# lockdownset
 - Usage: `[p]lockdownset`
 - Checks: `server_only`

Lockdown settings commands.

## lockdownset logchannel
 - Usage: `[p]lockdownset logchannel <channel>`

Set the channel for logging lockdowns.

## lockdownset settings
 - Usage: `[p]lockdownset settings`

Get the current log channel.

## lockdownset useembed
 - Usage: `[p]lockdownset useembed <value>`

Set whether to use embeds or not.

# lock (Hybrid Command)
 - Usage: `[p]lock [reason] [channel] [role]`
 - Slash Usage: `/lock [reason] [channel] [role]`
 - Aliases: `lockdown`
 - Checks: `server_only`

Lock a channel for a role or everyone.<br/><br/>If no channel is provided, the current channel will be locked for the provided role else the default role.

# unlock (Hybrid Command)
 - Usage: `[p]unlock [reason] [channel] [role]`
 - Slash Usage: `/unlock [reason] [channel] [role]`
 - Checks: `server_only`

Unlock a channel for a role or everyone.<br/><br/>If no channel is provided, the current channel will be unlocked for the provided role else the default role.

# thread
 - Usage: `[p]thread`
 - Checks: `server_only`

Manage thread(s) with MAX.

## thread close
 - Usage: `[p]thread close`

Close and archive a thread post.<br/><br/>If you want to only lock a thread post, you'll have to use `[p]lock` command.
