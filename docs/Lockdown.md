# Lockdown Help

Let moderators lockdown a channel to prevent messages from being sent.<br/>This only works with the default role.

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
 - Usage: `[p]lock <channel>`
 - Slash Usage: `/lock <channel>`
 - Aliases: `lockdown`
 - Checks: `bot_can_manage_channel and server_only`

Lock a channel down.<br/><br/>This will remove the permission `send_messages` from the default role in the channel.<br/><br/>__Parameters__<br/>--------------<br/>channel: Optional[discord.TextChannel]<br/>    The channel to lock down. If no channel is provided, the current channel will be locked down.

# unlock (Hybrid Command)
 - Usage: `[p]unlock <channel>`
 - Slash Usage: `/unlock <channel>`
 - Checks: `server_only and bot_can_manage_channel`

Unlock a channel.<br/><br/>This will allow the default role to send messages in the channel.<br/><br/>__Parameters__<br/>--------------<br/>channel: Optional[discord.TextChannel]<br/>    The channel to unlock. If no channel is provided, the current channel will be unlocked.
