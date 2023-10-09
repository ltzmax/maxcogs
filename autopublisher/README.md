# NOTE
This cog requires News Channel. If you don't have it, you can't use this cog. Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)

# AutoPublisher Help

Automatically push news channel messages.

# autopublisher
 - Usage: `[p]autopublisher ``
 - Restricted to: `ADMIN`
 - Aliases: `aph` and `autopub`
 - Checks: `server_only`

Manage AutoPublisher setting.

## autopublisher toggle
 - Usage: `[p]autopublisher toggle <toggle> `

Toggle AutoPublisher enable or disable.<br/><br/>> This cog have a 5 secoud delay on each messages you post in a news channel to be sent to the channels users are following.<br/><br/>- It's disabled by default.<br/>    - Please ensure that the bot has access to view_channel in your news channels. it also need manage_messages to be able to publish.<br/><br/>**Note:**<br/>- This cog requires News Channel. If you don't have it, you can't use this cog.<br/>    - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)

Extended Arg Info
> ### toggle: bool
> ```
> Can be 1, 0, true, false, t, f
> ```

## autopublisher ignore
 - Usage: `[p]autopublisher ignore <add_or_remove> <channels>`
 - Aliases: `ignorechannels`

Ignores sepecific news channels from getting triggered by the autopublisher system.

## autopublisher settings
 - Usage: `[p]autopublisher settings `
 - Aliases: `view`

Show AutoPublisher setting.

## autopublisher version
 - Usage: `[p]autopublisher version `

Shows the version of the cog.
