# AutoPublisher Help

Automatically push news channel messages.

# autopublisher
 - Usage: `[p]autopublisher`
 - Restricted to: `ADMIN`
 - Aliases: `aph and autopub`
 - Checks: `server_only`

Manage AutoPublisher setting.

## autopublisher reset
 - Usage: `[p]autopublisher reset`

Reset AutoPublisher setting.

## autopublisher ignore
 - Usage: `[p]autopublisher ignore <add_or_remove> [channels=None]`
 - Aliases: `ignorechannels`

Add or remove channels for your server.<br/><br/>`<add_or_remove>` should be either `add` to add channels or `remove` to remove channels.<br/><br/>**Example:**<br/>- `[p]autopublisher ignore add #news`<br/>- `[p]autopublisher ignore remove #news`<br/><br/>**Note:**<br/>- You can add or remove multiple channels at once.<br/>- You can also use channel ID instead of mentioning the channel.

## autopublisher settings
 - Usage: `[p]autopublisher settings`
 - Aliases: `view`

Show AutoPublisher setting.

## autopublisher toggle
 - Usage: `[p]autopublisher toggle`

Toggle AutoPublisher enable or disable.<br/><br/>- It's disabled by default.<br/>    - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.<br/><br/>**Note:**<br/>- This cog requires News Channel. If you don't have it, you can't use this cog.<br/>    - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)

## autopublisher version
 - Usage: `[p]autopublisher version`

Shows the version of the cog.

