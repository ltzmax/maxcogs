# GitHub

GitHub RSS Commit Feeds<br/><br/>Customizable system for GitHub commit updates similar to the webhook.

## [p]githubset

GitHub Settings<br/>

 - Usage: `[p]githubset`
 - Restricted to: `ADMIN`
 - Aliases: `ghset`
 - Checks: `guild_only`

### [p]githubset short

Set whether the GitHub message content should just include the title.<br/>

 - Usage: `[p]githubset short <short>`

### [p]githubset timestamp

Set whether GitHub RSS feed embeds should include a timestamp.<br/>

 - Usage: `[p]githubset timestamp <true_or_false>`

### [p]githubset channeloverride

Set a channel override for a feed (leave empty to reset).<br/>

 - Usage: `[p]githubset channeloverride <user> <feed_name> [channel=None]`

### [p]githubset listall

List all GitHub RSS feeds in the server.<br/>

 - Usage: `[p]githubset listall`

### [p]githubset role

Set the GitHub role requirement.<br/>

Note: Only those who are a mod or has permissions `manage_channels` can add / remove.<br/>
This is for you to lock to a speficially role to those with the permission to add / remove.<br/>
Only those who have the role can add / remove feeds, if they dont have the role, they will not be able to use this command.<br/>

 - Usage: `[p]githubset role [role=None]`

### [p]githubset channel

Set the default GitHub RSS feed channel.<br/>

 - Usage: `[p]githubset channel <channel>`

### [p]githubset force

Force a specific GitHub feed to post the last commit.<br/>

 - Usage: `[p]githubset force <user> <name>`

### [p]githubset rename

Rename a user's GitHub RSS feed.<br/>

 - Usage: `[p]githubset rename <user> <old_name> <new_name>`

### [p]githubset notify

Set whether to send repo addition/removal notices to the channel.<br/>

 - Usage: `[p]githubset notify <true_or_false>`

### [p]githubset view

View the server settings for GitHub.<br/>

 - Usage: `[p]githubset view`

### [p]githubset limit

Set the GitHub RSS feed limit per user.<br/>

 - Usage: `[p]githubset limit [num=5]`

### [p]githubset color

Set the GitHub RSS feed embed color for the server (enter "None" to reset).<br/>

 - Usage: `[p]githubset color <hex_color>`

### [p]githubset forceall

Force a run of the GitHub feed fetching coroutine.<br/>

 - Usage: `[p]githubset forceall`

## [p]github

GitHub RSS Commit Feeds<br/>

 - Usage: `[p]github`
 - Restricted to: `MOD`
 - Aliases: `gh`
 - Checks: `guild_only`

### [p]github list

List your GitHub RSS feeds in the server.<br/>

 - Usage: `[p]github list`

### [p]github add

Add a GitHub RSS feed to the server.<br/>

For the accepted link formats, see `[p]github whatlinks`.<br/>

 - Usage: `[p]github add <name> <url> [branch=None]`

### [p]github whatlinks

What links can you submit to `[p]github add`?<br/>

 - Usage: `[p]github whatlinks`

### [p]github remove

Remove a GitHub RSS feed from the server.<br/>

 - Usage: `[p]github remove <name>`
 - Aliases: `delete`

### [p]github get

Test out fetching a GitHub repository url.<br/>

 - Usage: `[p]github get <entries> <url> [branch=None]`
 - Aliases: `fetch and test`
