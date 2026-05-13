# GitHub

GitHub RSS Commit Feeds<br/><br/>Customizable system for GitHub commit updates similar to the webhook.

## [p]githubset

GitHub Settings<br/>

 - Usage: `[p]githubset`
 - Restricted to: `ADMIN`
 - Aliases: `ghset`
 - Checks: `guild_only`

### [p]githubset timestamp

Set whether GitHub RSS feed embeds should include a timestamp.<br/>

 - Usage: `[p]githubset timestamp <true_or_false>`

Extended Arg Info

> ### true_or_false: bool
> ```
> Can be 1, 0, true, false, t, f
> ```

### [p]githubset role

Set the GitHub role requirement.<br/>

Note: Only those who are a mod or has permissions `manage_channels` can add / remove.<br/>
This is for you to lock to a speficially role to those with the permission to add / remove.<br/>
Only those who have the role can add / remove feeds, if they dont have the role, they will not be able to use this command.<br/>

 - Usage: `[p]githubset role [role=None]`

Extended Arg Info

> ### role: discord.role.Role = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     

### [p]githubset limit

Set the GitHub RSS feed limit per user.<br/>

 - Usage: `[p]githubset limit [num=5]`

Extended Arg Info

> ### num: int = 5
> ```
> A number without decimal places.
> ```

### [p]githubset short

Set whether the GitHub message content should just include the title.<br/>

 - Usage: `[p]githubset short <short>`

Extended Arg Info

> ### short: bool
> ```
> Can be 1, 0, true, false, t, f
> ```

### [p]githubset channel

Set the default GitHub RSS feed channel.<br/>

 - Usage: `[p]githubset channel <channel>`

Extended Arg Info

> ### channel: discord.channel.TextChannel
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by channel URL.
>     4. Lookup by name
> 
>     

### [p]githubset listall

List all GitHub RSS feeds in the server.<br/>

 - Usage: `[p]githubset listall`

### [p]githubset rename

Rename a user's GitHub RSS feed.<br/>

 - Usage: `[p]githubset rename <user> <old_name> <new_name>`

Extended Arg Info

> ### user: discord.member.Member
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by username#discriminator (deprecated).
>     4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
>     5. Lookup by user name.
>     6. Lookup by global name.
>     7. Lookup by guild nickname.
> 
> 

### [p]githubset notify

Set whether to send repo addition/removal notices to the channel.<br/>

 - Usage: `[p]githubset notify <true_or_false>`

Extended Arg Info

> ### true_or_false: bool
> ```
> Can be 1, 0, true, false, t, f
> ```

### [p]githubset view

View the server settings for GitHub.<br/>

 - Usage: `[p]githubset view`

### [p]githubset color

Set the GitHub RSS feed embed color for the server (enter "None" to reset).<br/>

 - Usage: `[p]githubset color <hex_color>`

Extended Arg Info

> ### hex_color: Union[discord.colour.Colour, github.converters.ExplicitNone]
> Converts to a :class:`~discord.Colour`.
> 
>     

### [p]githubset forceall

Force a run of the GitHub feed fetching coroutine.<br/>

 - Usage: `[p]githubset forceall`

### [p]githubset channeloverride

Set a channel override for a feed (leave empty to reset).<br/>

 - Usage: `[p]githubset channeloverride <user> <feed_name> [channel=None]`

Extended Arg Info

> ### user: discord.member.Member
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by username#discriminator (deprecated).
>     4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
>     5. Lookup by user name.
>     6. Lookup by global name.
>     7. Lookup by guild nickname.
> 
>     
> ### feed_name: str
> ```
> The name of your feed.
> ```
> ### channel: discord.channel.TextChannel = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by channel URL.
>     4. Lookup by name
> 
>     

### [p]githubset force

Force a specific GitHub feed to post the last commit.<br/>

 - Usage: `[p]githubset force <user> <name>`

Extended Arg Info

> ### user: discord.member.Member
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by username#discriminator (deprecated).
>     4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
>     5. Lookup by user name.
>     6. Lookup by global name.
>     7. Lookup by guild nickname.
> 
> 

## [p]github

GitHub RSS Commit Feeds<br/>

 - Usage: `[p]github`
 - Restricted to: `MOD`
 - Aliases: `gh`
 - Checks: `guild_only`

### [p]github get

Test out fetching a GitHub repository url.<br/>

 - Usage: `[p]github get <entries> <url> [branch=None]`
 - Aliases: `fetch and test`

Extended Arg Info

> ### entries: Optional[int]
> ```
> A number without decimal places.
> ```

### [p]github add

Add a GitHub RSS feed to the server.<br/>

For the accepted link formats, see `[p]github whatlinks`.<br/>

 - Usage: `[p]github add <name> <url> [branch=None]`

### [p]github list

List your GitHub RSS feeds in the server.<br/>

 - Usage: `[p]github list`

### [p]github whatlinks

What links can you submit to `[p]github add`?<br/>

 - Usage: `[p]github whatlinks`

### [p]github remove

Remove a GitHub RSS feed from the server.<br/>

 - Usage: `[p]github remove <name>`
 - Aliases: `delete`

