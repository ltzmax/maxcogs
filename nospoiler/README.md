# NOTE
This cog relies on autoimmune feature from core itself. you are not immune from any spoiler filter without setting up trusted roles to bypass any deletions. not even admin, mod or guild owners bypasses this filter.

# nospoiler
 - Usage: `[p]nospoiler `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the spoiler filter settings.

## nospoiler delete
 - Usage: `[p]nospoiler delete <amount> `
 - Aliases: `timeout`

Change when the warn message get's deleted.

## nospoiler version
 - Usage: `[p]nospoiler version `

Shows the version of the cog.

## nospoiler toggle
 - Usage: `[p]nospoiler toggle `

Toggle the spoiler filter on or off.<br/><br/>Spoiler filter is disabled by default.

## nospoiler settings
 - Usage: `[p]nospoiler settings `
 - Aliases: `view and views`

Show the settings.

## nospoiler warnmessage
 - Usage: `[p]nospoiler warnmessage <message> `

Set the spoiler warning message.<br/><br/>(Supports Tagscript)<br/><br/>**Blocks:**<br/>- [Assugnment Block](https://phen-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#assignment-block)<br/>- [If Block](https://phen-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#if-block)<br/>- [Embed Block](https://phen-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#embed-block)<br/>- [Command Block](https://phen-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#command-block)<br/><br/>**Variable:**<br/>- `{server}`: [Your server/server.](https://phen-cogs.readthedocs.io/en/latest/tags/default_variables.html#server-block)<br/>- `{member}`: [Author of the message.](https://phen-cogs.readthedocs.io/en/latest/tags/default_variables.html#author-block)<br/>- `{color}`: Atticus's default color.<br/><br/>**Example:**<br/>```<br/>{embed(title):No spoiler allowed.}<br/>{embed(description):{member(mention)} You cannot send spoilers here.}<br/>{embed(color):{color}}<br/>```

## nospoiler logchannel
 - Usage: `[p]nospoiler logchannel [channel=None] `

Set the channel where the bot will log the deleted spoiler messages.<br/><br/>If the channel is not set, the bot will not log the deleted spoiler messages.

## nospoiler warn
 - Usage: `[p]nospoiler warn `

Toggle warning message when a user tries to use spoiler.

