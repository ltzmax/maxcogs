# CapSpam Help

Prevent spamming in caps

# capspam
 - Usage: `[p]capspam `
 - Restricted to: `ADMIN`
 - Checks: `server_only`

CapSpam settings

## capspam enable
 - Usage: `[p]capspam enable <toggle> `
 - Aliases: `toggle`

Enable CapSpam in your server.<br/><br/>__Parameters__<br/><br/>**toggle** : Boolean<br/>    Enable or disable CapSpam in this server.

Extended Arg Info
> ### toggle: bool
> ```
> Can be 1, 0, true, false, t, f
> ```
## capspam view
 - Usage: `[p]capspam view `
 - Aliases: `settings and setting`

Show the informations about CapSpam in your server.

## capspam version
 - Usage: `[p]capspam version `

Shows the version of the cog

## capspam ignore
 - Usage: `[p]capspam ignore `

Manage the roles/channels ignore settings.<br/><br/>See [p]capspam info for a list of ignored roles/channels.

### capspam ignore removeroles
 - Usage: `[p]capspam ignore removeroles <roles> `
 - Aliases: `removerole, remrole, and rmrole`

Remove one or more roles to be ignored by CapSpam.<br/><br/>__Parameters__<br/><br/>**roles** : List of server roles<br/>    The roles to remove.

Extended Arg Info
> ### *roles: discord.role.Role
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
### capspam ignore addchannels
 - Usage: `[p]capspam ignore addchannels <channels> `
 - Aliases: `channels and channel`

Add one or more channels to be ignored by CapSpam.<br/><br/>If the author of the message has one of the ignored channels, he won't be treated by CapSpam filtering.<br/><br/>__Parameters__<br/><br/>**channels** : List of server channels<br/>    The channels to add.

Extended Arg Info
> ### *channels: discord.channel.TextChannel
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
### capspam ignore addroles
 - Usage: `[p]capspam ignore addroles <roles> `
 - Aliases: `roles and role`

Add one or more roles to be ignored by CapSpam.<br/><br/>If the author of the message has one of the ignored roles, he won't be treated by CapSpam filtering.<br/><br/>__Parameters__<br/><br/>**roles** : List of server roles<br/>    The roles to add.

Extended Arg Info
> ### *roles: discord.role.Role
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
### capspam ignore removechannels
 - Usage: `[p]capspam ignore removechannels <channels> `
 - Aliases: `remchannel and rmchannel`

Remove one or more channels to be ignored by CapSpam.<br/><br/>__Parameters__<br/><br/>**channels** : List of server channels<br/>    The channels to remove.

Extended Arg Info
> ### *channels: discord.channel.TextChannel
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
