# EmojiSpam Help

Prevent users from spamming emojis.

# emojispam
 - Usage: `[p]emojispam`
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the emoji spam filter.

## emojispam logchannel
 - Usage: `[p]emojispam logchannel [channel=None]`

Set the log channel.<br/><br/>If no channel is provided, the log channel will be disabled.

## emojispam deleteafter
 - Usage: `[p]emojispam deleteafter <seconds>`

Set when the warn message should delete.<br/><br/>Default timeout is 10 seconds.<br/>Timeout must be between 10 and 120 seconds.

## emojispam settings
 - Usage: `[p]emojispam settings`

Show the current settings.

## emojispam version
 - Usage: `[p]emojispam version`

Shows the version of the cog.

## emojispam limit
 - Usage: `[p]emojispam limit <limit>`

Set the emoji limit.<br/><br/>Default limit is 5.<br/>Limit must be between 1 and 25.<br/><br/>NOTE: Some emojis may count more than 1. These are usually normal emojis that are combined to form a single emoji (e.g. face_with_spiral_eyes) This one count as 3 emojis in the limit of 5.

## emojispam message
 - Usage: `[p]emojispam message <message>`

Set the spoiler warning message.<br/><br/>Leave it empty to reset the message to the default message.<br/><br/>(Supports Tagscript)<br/><br/>**Blocks:**<br/>- [Assugnment Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#assignment-block)<br/>- [If Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#if-block)<br/>- [Embed Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#embed-block)<br/>- [Command Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#command-block)<br/><br/>**Variable:**<br/>- `{server}`: [Your server/server.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#server-block)<br/>- `{member}`: [Author of the message.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#author-block)<br/>- `{color}`: MAX's default color.<br/><br/>**Example:**<br/>```<br/>{embed(title):No spoiler allowed.}<br/>{embed(description):{member(mention)} Usage of spoiler is not allowed in this server.}<br/>{embed(color):{color}}<br/>```

## emojispam toggle
 - Usage: `[p]emojispam toggle <toggle>`

Toggle EmojiSpam filter on/off.

## emojispam reset
 - Usage: `[p]emojispam reset`

Reset all settings back to default.

## emojispam togglemessage
 - Usage: `[p]emojispam togglemessage`

Toggle to show a custom message when a user spams emojis.

