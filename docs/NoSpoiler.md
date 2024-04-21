# NoSpoiler Help

No spoiler in this server.

# nospoiler
 - Usage: `[p]nospoiler`
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the spoiler filter settings.

## nospoiler deleteafter
 - Usage: `[p]nospoiler deleteafter <seconds>`

Set when the warn message should delete.<br/><br/>Default timeout is 10 seconds.<br/>Timeout must be between 10 and 120 seconds.

## nospoiler version
 - Usage: `[p]nospoiler version`

Shows the version of the cog.

## nospoiler toggle
 - Usage: `[p]nospoiler toggle`

Toggle NoSpoiler filter on/off.

## nospoiler togglewarnmsg
 - Usage: `[p]nospoiler togglewarnmsg [toggle=None]`

Toggle the spoiler warning message on or off.

## nospoiler logchannel
 - Usage: `[p]nospoiler logchannel [channel=None]`

Set the channel where the bot will log the deleted spoiler messages.<br/><br/>If the channel is not set, the bot will not log the deleted spoiler messages.

## nospoiler settings
 - Usage: `[p]nospoiler settings`
 - Aliases: `view and views`

Show the settings.

## nospoiler message
 - Usage: `[p]nospoiler message <message>`

Set the spoiler warning message.<br/><br/>Leave it empty to reset the message to the default message.<br/><br/>(Supports Tagscript)<br/><br/>**Blocks:**<br/>- [Assugnment Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#assignment-block)<br/>- [If Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#if-block)<br/>- [Embed Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#embed-block)<br/>- [Command Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#command-block)<br/><br/>**Variable:**<br/>- `{server}`: [Your server/server.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#server-block)<br/>- `{member}`: [Author of the message.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#author-block)<br/>- `{color}`: MAX's default color.<br/><br/>**Example:**<br/>```<br/>{embed(title):No spoiler allowed.}<br/>{embed(description):{member(mention)} Usage of spoiler is not allowed in this server.}<br/>{embed(color):{color}}<br/>```

