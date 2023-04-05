# Information:
This cog relies on red's autoimmune. If you wanna ignore roles / users, please do use `[p]autoimmune` for this purpose.

# NoSpoiler Help

No spoiler in this server.

# nospoiler (Hybrid Command)
 - Usage: `[p]nospoiler `
 - Slash Usage: `/nospoiler `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the spoiler filter settings.

## nospoiler ignorechannel (Hybrid Command)
 - Usage: `[p]nospoiler ignorechannel <channel> `
 - Slash Usage: `/nospoiler ignorechannel <channel> `

Add or remove ignore a channel from the spoiler filter.

Extended Arg Info
> ### channel: Union[discord.channel.TextChannel, discord.threads.Thread, discord.channel.ForumChannel]
>
>
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
>
>
## nospoiler warn (Hybrid Command)
 - Usage: `[p]nospoiler warn `
 - Slash Usage: `/nospoiler warn `

Toggle the warning message on or off.

## nospoiler warnmessage (Hybrid Command)
 - Usage: `[p]nospoiler warnmessage <message> `
 - Slash Usage: `/nospoiler warnmessage <message> `
 - Aliases: `warnmsg`

Set the warning message.

Extended Arg Info
> ### message: str
> ```
> A single word or something that you want the bot to tell on warn.
> ```
## nospoiler toggle (Hybrid Command)
 - Usage: `[p]nospoiler toggle `
 - Slash Usage: `/nospoiler toggle `

Toggle the spoiler filter on or off.

## nospoiler settings (Hybrid Command)
 - Usage: `[p]nospoiler settings `
 - Slash Usage: `/nospoiler settings `
 - Aliases: `view and views`

Show the settings.

## nospoiler resetwarnmsg (Hybrid Command)
 - Usage: `[p]nospoiler resetwarnmsg `
 - Slash Usage: `/nospoiler resetwarnmsg `
 - Aliases: `resetmsg and resetwarnmessage`

Reset the warning message back to default.

## nospoiler clear (Hybrid Command)
 - Usage: `[p]nospoiler clear `
 - Slash Usage: `/nospoiler clear `
 - Aliases: `reset`

Reset all settings back to default.

## nospoiler version (Hybrid Command)
 - Usage: `[p]nospoiler version `
 - Slash Usage: `/nospoiler version `

Shows the version of the cog.
