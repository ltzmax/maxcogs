# Lockdown Help

Let moderators lockdown a channel to prevent messages from being sent.

# lockdownset
 - Usage: `[p]lockdownset`
 - Checks: `server_only`

Lockdown settings commands.

## lockdownset settings
 - Usage: `[p]lockdownset settings`

Get the current log channel.

## lockdownset logchannel
 - Usage: `[p]lockdownset logchannel <channel>`

Set the channel for logging lockdowns.

# lock (Hybrid Command)
 - Usage: `[p]lock [reason=None] [channel=None] [role=None]`
 - Slash Usage: `/lock [reason=None] [channel=None] [role=None]`
 - Aliases: `lockdown`
 - Checks: `server_only`

Lock a channel for a role or everyone.<br/><br/>If no channel is provided, the current channel will be locked for the provided role else the default role.

# unlock (Hybrid Command)
 - Usage: `[p]unlock [reason=None] [channel=None] [role=None]`
 - Slash Usage: `/unlock [reason=None] [channel=None] [role=None]`
 - Checks: `server_only`

Unlock a channel for a role or everyone.<br/><br/>If no channel is provided, the current channel will be unlocked for the provided role else the default role.
