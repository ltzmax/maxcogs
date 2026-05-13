# TechNews

Auto posts new articles from Wccftech to a specified channel in your server.

## [p]technews

Manage Wccftech news auto-posting.<br/>

 - Usage: `[p]technews`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]technews channel

Set or clear the channel or thread for tech news in this server.<br/>

Supports both regular text channels and active threads.<br/>

Note: changing the channel does not reset the last posted article.<br/>
The bot will only post articles newer than the last one it posted.<br/>

**Examples:**<br/>
- `[p]technews channel #news` - post to a text channel.<br/>
- `[p]technews channel #some-thread` - post to a thread.<br/>
- `[p]technews channel` - disable auto-posting.<br/>

 - Usage: `[p]technews channel [channel=None]`

### [p]technews status

Check the current tech news posting status for this server.<br/>

 - Usage: `[p]technews status`

