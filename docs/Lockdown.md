# Lockdown Help

Let moderators lockdown a channel to prevent messages from being sent.<br/>This only works with the default role.

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

# lock (Hybrid Command)
 - Usage: `[p]lock [channel=None] [role=None]`
 - Slash Usage: `/lock [channel=None] [role=None]`
 - Aliases: `lockdown`
 - Checks: `bot_can_manage_channel and server_only`

Lock a channel down.<br/><br/>This will remove the permission `send_messages` from the provided role in the channel. If no role is provided, the default role will be used.<br/><br/>__Parameters__<br/>--------------<br/>channel: Optional[discord.TextChannel]<br/>    The channel to lock down. If no channel is provided, the current channel will be locked down.<br/>role: Optional[discord.Role]<br/>    The role to remove the `send_messages` permission from. If no role is provided, the default role will be used.

# unlock (Hybrid Command)
 - Usage: `[p]unlock [channel=None] [role=None]`
 - Slash Usage: `/unlock [channel=None] [role=None]`
 - Checks: `server_only and bot_can_manage_channel`

Unlock a channel.<br/><br/>This will allow the default role to send messages in the channel.<br/><br/>__Parameters__<br/>--------------<br/>channel: Optional[discord.TextChannel]<br/>    The channel to unlock. If no channel is provided, the current channel will be unlocked.<br/>role: Optional[discord.Role]<br/>    The role to remove the `send_messages` permission from. If no role is provided, the default role will be used.

