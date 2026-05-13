# MessageGuard

A unified message moderation cog combining:<br/>- ForwardDeleter: deletes forwarded messages<br/>- NoSpoiler: deletes messages with spoiler tags or attachments<br/>- RestrictPosts: restricts channels to attachments and links only

## [p]restrictposts

Settings for restricted channel management.<br/>

 - Usage: `[p]restrictposts`
 - Aliases: `restrictpost and restrict`
 - Checks: `guild_only`

### [p]restrictposts embed

Toggle sending the warning message as an embed.<br/>

 - Usage: `[p]restrictposts embed`

### [p]restrictposts message

Set or reset the custom warning message for deleted messages.<br/>

 - Usage: `[p]restrictposts message [message]`

### [p]restrictposts defaulttitle

Set or reset the default title for the warning embed.<br/>

 - Usage: `[p]restrictposts defaulttitle [title]`

### [p]restrictposts channel

Add, remove, or clear restricted channels where only attachments/links are allowed.<br/>

Specify a channel to toggle it in/out of the list.<br/>
Run without a channel to clear all restricted channels.<br/>

 - Usage: `[p]restrictposts channel [channel=None]`

### [p]restrictposts togglelog

Toggle logging of deleted restricted-channel messages.<br/>

 - Usage: `[p]restrictposts togglelog`

### [p]restrictposts deleteafter

Set or reset delete-after time for warning messages (10–300 seconds).<br/>

 - Usage: `[p]restrictposts deleteafter [seconds=None]`

### [p]restrictposts togglemessage

Toggle sending a warning message in the channel when a message is deleted.<br/>

 - Usage: `[p]restrictposts togglemessage`
 - Aliases: `togglemsg`

### [p]restrictposts autothread

Toggle automatic thread creation for valid messages in restricted channels.<br/>

 - Usage: `[p]restrictposts autothread`

### [p]restrictposts settings

View current RestrictPosts settings.<br/>

 - Usage: `[p]restrictposts settings`

### [p]restrictposts setlog

Set or clear the log channel for RestrictPosts deletions.<br/>

 - Usage: `[p]restrictposts setlog [channel=None]`

### [p]restrictposts mentionable

Toggle or set whether the warning message mentions the user.<br/>

 - Usage: `[p]restrictposts mentionable [mentionable=None]`

## [p]nospoiler

Manage spoiler filter settings for the server.<br/>

 - Usage: `[p]nospoiler`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]nospoiler deleteafter

Set how long before the spoiler warning is deleted (10–120 seconds).<br/>

 - Usage: `[p]nospoiler deleteafter <seconds>`

### [p]nospoiler settings

Display current spoiler filter settings.<br/>

 - Usage: `[p]nospoiler settings`
 - Aliases: `view and views`

### [p]nospoiler message

Set or reset the custom spoiler warning message.<br/>

 - Usage: `[p]nospoiler message [message]`

### [p]nospoiler togglewarnmsg

Toggle the spoiler warning message on or off.<br/>

 - Usage: `[p]nospoiler togglewarnmsg [toggle=None]`

### [p]nospoiler useembed

Toggle whether the spoiler warning uses an embed.<br/>

 - Usage: `[p]nospoiler useembed [toggle=None]`

### [p]nospoiler toggle

Toggle the spoiler filter on or off.<br/>

 - Usage: `[p]nospoiler toggle`

### [p]nospoiler togglelog

Toggle logging of deleted spoiler messages.<br/>

 - Usage: `[p]nospoiler togglelog`

### [p]nospoiler setlog

Set or clear the log channel for NoSpoiler deletions.<br/>

 - Usage: `[p]nospoiler setlog [channel=None]`

## [p]forwarddeleter

Manage forward deleter settings.<br/>

 - Usage: `[p]forwarddeleter`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]forwarddeleter disallow

Remove channels or threads from the forwarding allowed list.<br/>

 - Usage: `[p]forwarddeleter disallow <channels>`

### [p]forwarddeleter setlog

Set or clear the log channel for ForwardDeleter deletions.<br/>

 - Usage: `[p]forwarddeleter setlog [channel=None]`

### [p]forwarddeleter togglelog

Toggle logging of deleted forwarded messages.<br/>

 - Usage: `[p]forwarddeleter togglelog`

### [p]forwarddeleter setwarnmessage

Set a custom warning message for deleted forwarded messages.<br/>

 - Usage: `[p]forwarddeleter setwarnmessage <message>`
 - Aliases: `setwarnmsg`

### [p]forwarddeleter toggle

Toggle forward deleter on or off.<br/>

 - Usage: `[p]forwarddeleter toggle`

### [p]forwarddeleter allow

Add channels or threads where forwarding is allowed.<br/>

 - Usage: `[p]forwarddeleter allow <channels>`

### [p]forwarddeleter settings

Display Forward Deleter settings.<br/>

 - Usage: `[p]forwarddeleter settings`

### [p]forwarddeleter removerole

Remove a role from the forwarding whitelist.<br/>

 - Usage: `[p]forwarddeleter removerole <role>`

### [p]forwarddeleter addrole

Add a role to the forwarding whitelist.<br/>

 - Usage: `[p]forwarddeleter addrole <role>`

### [p]forwarddeleter togglewarn

Toggle sending warnings when forwarded messages are deleted.<br/>

 - Usage: `[p]forwarddeleter togglewarn`

