# INFORMATION

This cog relies on red's `[p]autoimmune` command from core, to ignore a role or and a user, please do use that command from core. I will not make a copy of core's immune command for this cog as it already exist in core to make it much easier for moderation purposes as this cog is to moderate away spoilered messages / spoilered images.

# NoSpoiler Help

No spoiler in this server.

# nospoiler (Hybrid Command)
 - Usage: `[p]nospoiler `
 - Slash Usage: `/nospoiler `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

Manage the spoiler filter settings.

## nospoiler settings (Hybrid Command)
 - Usage: `[p]nospoiler settings `
 - Slash Usage: `/nospoiler settings `
 - Aliases: `view, views, setting, showsettings, and showsetting`

Show the settings.

## nospoiler toggle (Hybrid Command)
 - Usage: `[p]nospoiler toggle `
 - Slash Usage: `/nospoiler toggle `

Toggle the spoiler filter on or off.<br/><br/>Spoiler filter is disabled by default.

## nospoiler reset (Hybrid Command)
 - Usage: `[p]nospoiler reset `
 - Slash Usage: `/nospoiler reset `
 - Aliases: `clear`
 - Cooldown: `2 per 120.0 seconds`

Reset all settings back to default.

## nospoiler version (Hybrid Command)
 - Usage: `[p]nospoiler version `
 - Slash Usage: `/nospoiler version `

Shows the version of the cog.

## nospoiler set (Hybrid Command)
 - Usage: `[p]nospoiler set `
 - Slash Usage: `/nospoiler set `

Settings to manage custom messages sent.<br/><br/>This is when spoiler message(s) is deleted, it will send a custom message telling users they're not allowed to.

### nospoiler set message (Hybrid Command)
 - Usage: `[p]nospoiler set message [message] `
 - Slash Usage: `/nospoiler set message [message] `

Set the message to send when a user sends a spoiler message.<br/><br/>If no message is provided, the default message will be sent.<br/>If you want to disable the message, use [p]nospoiler set togglemessage.

Extended Arg Info
> ### message: str = None
> ```
> Something like: hello you cant do this stuff
> ```

### nospoiler set togglemessage (Hybrid Command)
 - Usage: `[p]nospoiler set togglemessage `
  - Aliases: `togglemsg`
 - Slash Usage: `/nospoiler set togglemessage `

Enable or disable the message to send when a user sends a spoiler message.<br/><br/>If the message is disabled, the bot will delete the spoiler message without sending a message.
