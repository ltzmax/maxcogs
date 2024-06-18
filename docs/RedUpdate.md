# RedUpdate Help

Update [botname] to latest dev/stable changes.

# redupdateset
 - Usage: `[p]redupdateset`
 - Restricted to: `BOT_OWNER`
 - Aliases: `redset`

Setting commands for redupdate cog.

## redupdateset whatlink
 - Usage: `[p]redupdateset whatlink`
 - Aliases: `whaturl`

Show what a valid link looks like.

## redupdateset reseturl
 - Usage: `[p]redupdateset reseturl`

Reset the url to default.

## redupdateset version
 - Usage: `[p]redupdateset version`

Shows information about the cog.

## redupdateset settings
 - Usage: `[p]redupdateset settings`

Show the url for redupdate cog.

## redupdateset url
 - Usage: `[p]redupdateset url <url>`

Set your custom fork url of red.<br/><br/>Has to be vaild link such as `git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=Red-DiscordBot` else it will not work.

# redupdate
 - Usage: `[p]redupdate <version>`
 - Restricted to: `BOT_OWNER`
 - Aliases: `updatered`

update MAX to latest changes.<br/><br/>it will update to latest stable changes by default unless you specify `dev` as version.<br/><br/>Arguments:<br/>- `[version]`: `dev` to update to latest dev changes. `stable` by default already.

# forkupdate
 - Usage: `[p]forkupdate`
 - Restricted to: `BOT_OWNER`
 - Aliases: `updatefork`

Update MAX to your fork.<br/><br/>This will update to your fork and not to red's main repo. Make sure you have set the url using `redset url` before using this command.<br/><br/>Note: If you do not have a fork, you can use `updatered` to update to latest stable changes.
