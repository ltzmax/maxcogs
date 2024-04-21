# Achievements Help

Earn achievements by chatting in channels.

# customset
 - Usage: `[p]customset`
 - Restricted to: `GUILD_OWNER`
 - Checks: `server_only`

Custom achievements commands.<br/><br/>Only server owners can use these commands.<br/><br/>Custom achievements are disabled by default. Enable them with `[p]customset enable`.<br/>This will allow you to add, remove, and list custom achievements for your server.

## customset clear
 - Usage: `[p]customset clear`

Clear all custom achievements.

## customset enable
 - Usage: `[p]customset enable`

Toggle custom achievements.

## customset remove
 - Usage: `[p]customset remove <name>`

Remove a custom achievement.<br/><br/>Example:<br/>- `[p]achievement custom remove Epic`<br/>- `[p]achievement custom remove Legendary`<br/><br/>Arguments:<br/>- `<name>`: The name of the achievement. You can get the name from `[p]achievement list`.

## customset add
 - Usage: `[p]customset add <name> <value>`

Add a custom achievement.<br/><br/>You must have custom achievements enabled to use this command.<br/><br/>Example:<br/>- `[p]achievement custom add Epic 1000`<br/>- `[p]achievement custom add Legendary 10000`<br/><br/>Arguments:<br/>- `<name>`: The name of the achievement. (must be between 1 and 256 characters)<br/>- `<value>`: The message count required to unlock the achievement. (must be an integer)

# achievementset
 - Usage: `[p]achievementset`
 - Restricted to: `ADMIN`
 - Aliases: `achieveset`
 - Checks: `server_only`

Achievement settings.

## achievementset toggle
 - Usage: `[p]achievementset toggle`

Toggle achievements.

## achievementset emoji
 - Usage: `[p]achievementset emoji`

Emoji settings.

### achievementset emoji cross
 - Usage: `[p]achievementset emoji cross <emoji>`

Set the cross emoji.<br/><br/>This only shows in `[p]achievements list` and `[p]achievements unlocked` commands.<br/><br/>**Examples:**<br/>- `[p]achievements emoji cross :x:`<br/>- `[p]achievements emoji cross :heavy_multiplication_x:`<br/><br/>**Arguments:**<br/>- `<emoji>`: The emoji to set as the cross emoji.

### achievementset emoji check
 - Usage: `[p]achievementset emoji check <emoji>`

Set the check emoji.<br/><br/>This only shows in `[p]achievements list` and `[p]achievements unlocked` commands.<br/><br/>**Examples:**<br/>- `[p]achievements emoji check :white_check_mark:`<br/>- `[p]achievements emoji check :heavy_check_mark:`<br/><br/>**Arguments:**<br/>- `<emoji>`: The emoji to set as the check emoji.

## achievementset channel
 - Usage: `[p]achievementset channel <channel>`

Set the channel to notify about achievements.

## achievementset notify
 - Usage: `[p]achievementset notify`

Toggle achievement notifications.<br/><br/>If channel is not set, it will use channels where they unlocked the achievement.

## achievementset blacklist
 - Usage: `[p]achievementset blacklist <add_or_remove> <channels>`
 - Aliases: `bl`

Add or remove a channel from the blacklisted channels list.<br/><br/>This will prevent the bot from counting messages in the blacklisted channels.<br/><br/>**Examples:**<br/>- `[p]achievement blacklist add #general`<br/>- `[p]achievement blacklist remove #general`<br/><br/>**Arguments:**<br/>- `<add_or_remove>`: Whether to add or remove the channel from the blacklisted channels list.<br/>- `<channels>`: The channels to add or remove from the blacklisted channels list.

## achievementset reset
 - Usage: `[p]achievementset reset <member>`
 - Restricted to: `BOT_OWNER`

Reset a member's profile.<br/><br/>This will reset the message count and unlocked achievements and cannot be undone without a backup.

## achievementset settings
 - Usage: `[p]achievementset settings`

Check the current settings.

## achievementset listblacklisted
 - Usage: `[p]achievementset listblacklisted`
 - Aliases: `listbl`

List all blacklisted channels.

# achievements
 - Usage: `[p]achievements`
 - Aliases: `achieve`
 - Checks: `server_only`

Achievements commands.

## achievements list
 - Usage: `[p]achievements list`

List all available achievements.

## achievements unlocked
 - Usage: `[p]achievements unlocked [member=None]`

Check your unlocked achievements or someone else's.

## achievements leaderboard
 - Usage: `[p]achievements leaderboard`
 - Aliases: `lb`

Check the leaderboard.

## achievements profile
 - Usage: `[p]achievements profile [member=None]`

Check your profile or someone else's.

## achievements ignoreme
 - Usage: `[p]achievements ignoreme`

Ignore yourself from earning achievements.<br/><br/>This will prevent you from earning achievements until you run the command again.<br/>It will stop from counting your messages and unlocking achievements.

