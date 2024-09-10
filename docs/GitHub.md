# GitHub Help

GitHub RSS Commit Feeds<br/><br/>Customizable system for GitHub commit updates similar to the webhook.

# githubset
 - Usage: `[p]githubset`
 - Restricted to: `ADMIN`
 - Aliases: `ghset`
 - Checks: `server_only`

GitHub Settings

## githubset short
 - Usage: `[p]githubset short <short>`

Set whether the GitHub message content should just include the title.

## githubset force
 - Usage: `[p]githubset force <user> <name>`

Force a specific GitHub feed to post the last commit.

## githubset listall
 - Usage: `[p]githubset listall`

List all GitHub RSS feeds in the server.

## githubset role
 - Usage: `[p]githubset role [role=None]`

Set the GitHub role requirement.

Note: Only those who are a mod or has permissions `manage_channels` can add / remove.
This is for you to lock to a speficially role to those with the permission to add / remove.
Only those who have the role can add / remove feeds, if they dont have the role, they will not be able to use this command.

## githubset channel
 - Usage: `[p]githubset channel <channel>`

Set the default GitHub RSS feed channel.

## githubset view
 - Usage: `[p]githubset view`

View the server settings for GitHub.

## githubset rename
 - Usage: `[p]githubset rename <user> <old_name> <new_name>`

Rename a user's GitHub RSS feed.

## githubset limit
 - Usage: `[p]githubset limit [num=5]`

Set the GitHub RSS feed limit per user.

## githubset forceall
 - Usage: `[p]githubset forceall`

Force a run of the GitHub feed fetching coroutine.

## githubset channeloverride
 - Usage: `[p]githubset channeloverride <user> <feed_name> [channel=None]`

Set a channel override for a feed (leave empty to reset).

## githubset color
 - Usage: `[p]githubset color <hex_color>`

Set the GitHub RSS feed embed color for the server (enter "None" to reset).

## githubset notify
 - Usage: `[p]githubset notify <true_or_false>`

Set whether to send repo addition/removal notices to the channel.

## githubset timestamp
 - Usage: `[p]githubset timestamp <true_or_false>`

Set whether GitHub RSS feed embeds should include a timestamp.

# github
 - Usage: `[p]github`
 - Aliases: `gh`
 - Checks: `server_only`

GitHub RSS Commit Feeds

## github whatlinks
 - Usage: `[p]github whatlinks`

What links can you submit to `[p]github add`?

## github add
 - Usage: `[p]github add <name> <url> [branch=]`

Add a GitHub RSS feed to the server.<br/><br/>For the accepted link formats, see `[p]github whatlinks`.

## github get
 - Usage: `[p]github get <entries> <url> [branch=None]`
 - Aliases: `fetch and test`

Test out fetching a GitHub repository url.

## github list
 - Usage: `[p]github list`

List your GitHub RSS feeds in the server.

## github remove
 - Usage: `[p]github remove <name>`
 - Aliases: `delete`

Remove a GitHub RSS feed from the server.
