# OnConnect Help

This cog is used to send shard events.

# connectset
 - Usage: `[p]connectset `
 - Restricted to: `BOT_OWNER`
 - Checks: `server_only`

Manage settings for onconnect.

## connectset channel
 - Usage: `[p]connectset channel [channel=None] `

Set the channel to log shard events to.<br/><br/>**Example:**<br/>- `[p]connectset channel #general`<br/>This will set the event channel to general.<br/><br/>**Arguments:**<br/>- `[channel]` - Is where you set the event channel. Leave it blank to disable.

Extended Arg Info
> ### channel: Union[discord.channel.TextChannel, discord.threads.Thread, NoneType] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
> 

## connectset emoji
 - Usage: `[p]connectset emoji `
 - Aliases: `emojis`

Settings to change default emoji.

### connectset emoji orange
 - Usage: `[p]connectset emoji orange [emoji] `

Change the orange emoji to your own.<br/><br/>**Example:**<br/>- `[p]connectset emoji orange :orange_heart:`<br/>This will change the orange emoji to :orange_heart:.<br/><br/>**Arguments:**<br/>- `[emoji]` - Is where you set the emoji. Leave it blank to reset.

### connectset emoji red
 - Usage: `[p]connectset emoji red [emoji] `

Change the red emoji to your own.<br/><br/>**Example:**<br/>- `[p]connectset emoji red :heart:`<br/>This will change the red emoji to :heart:.<br/><br/>**Arguments:**<br/>- `[emoji]` - Is where you set the emoji. Leave it blank to reset.

### connectset emoji green
 - Usage: `[p]connectset emoji green [emoji] `

Change the green emoji to your own.<br/><br/>**Example:**<br/>- `[p]connectset emoji green :green_heart:`<br/>This will change the green emoji to :green_heart:.<br/><br/>**Arguments:**<br/>- `[emoji]` - Is where you set the emoji. Leave it blank to reset.

## connectset version
 - Usage: `[p]connectset version `

Shows the cog version.

## connectset showsettings
 - Usage: `[p]connectset showsettings `
 - Aliases: `settings`

Shows the current settings for OnConnect.

## connectset reset
 - Usage: `[p]connectset reset `
 - Aliases: `clear`

Reset all settings for OnConnect.<br/><br/>This will reset all settings to their default values.
