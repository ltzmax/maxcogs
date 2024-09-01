Automatically push news channel messages.

# [p]autopublisher
Manage AutoPublisher setting.<br/>
 - Usage: `[p]autopublisher`
 - Restricted to: `ADMIN`
 - Aliases: `aph and autopub`
 - Checks: `server_only`
## [p]autopublisher settings
Show AutoPublisher setting.<br/>
 - Usage: `[p]autopublisher settings`
 - Aliases: `view`
## [p]autopublisher toggle
Toggle AutoPublisher enable or disable.<br/>

- It's disabled by default.<br/>
    - Please ensure that the bot has access to `view_channel` in your news channels. it also need `manage_messages` to be able to publish.<br/>

**Note:**<br/>
- This cog requires News Channel. If you don't have it, you can't use this cog.<br/>
    - Learn more [here on how to enable](https://support.discord.com/hc/en-us/articles/360047132851-Enabling-Your-Community-Server) community server. (which is a part of news channel feature.)<br/>
 - Usage: `[p]autopublisher toggle`
## [p]autopublisher stats
Show the number of published messages.<br/>

NOTE: <br/>
- The count will never reset unless you manually reset it or and delete the data from the files. (not recommended)<br/>
- The weekly count will reset every Sunday at midnight UTC.<br/>
- The monthly count will reset every 1st of the month at midnight UTC.<br/>
 - Usage: `[p]autopublisher stats`
 - Restricted to: `BOT_OWNER`
## [p]autopublisher ignorechannel
Ignore a news channel to prevent AutoPublisher from publishing messages in it.<br/>

Please note select menu's can't view more than 25 channels.<br/>

- This command will show a select menu to choose one or more news channel(s) to ignore.<br/>

**Note:**<br/>
- Use `Confirm` button to confirm the selected channel(s) to ignore.<br/>
- Use `Remove` button to remove the selected channel(s) from the ignored list.<br/>
- You can confrim or remove multiple channels at once. (must go by one by one)<br/>
 - Usage: `[p]autopublisher ignorechannel`
## [p]autopublisher reset
Reset AutoPublisher setting.<br/>
 - Usage: `[p]autopublisher reset`
## [p]autopublisher version
Shows the version of the cog.<br/>
 - Usage: `[p]autopublisher version`
