# RedUpdate

Update [botname] to latest dev/stable changes.

## [p]redupdateset

Setting commands for redupdate cog.<br/>

 - Usage: `[p]redupdateset`
 - Restricted to: `BOT_OWNER`
 - Aliases: `redset`

### [p]redupdateset settings

Show the url for redupdate cog.<br/>

 - Usage: `[p]redupdateset settings`

### [p]redupdateset reseturl

Reset the url to default.<br/>

 - Usage: `[p]redupdateset reseturl`

### [p]redupdateset url

Set your custom fork url of red.<br/>

 - Usage: `[p]redupdateset url`

### [p]redupdateset whatlink

Show what a valid link looks like.<br/>

 - Usage: `[p]redupdateset whatlink`
 - Aliases: `whaturl`

## [p]updatered

Update Kofu to latest changes.<br/>

Arguments:<br/>
- `[version]`: `dev` to update to latest dev changes. Stable by default.<br/>

 - Usage: `[p]updatered <version>`
 - Restricted to: `BOT_OWNER`

## [p]forkupdate

Update Kofu to your fork.<br/>

This will update to your fork and not to red's main repo. Make sure you have set the url using `redset url` before using this command.<br/>

Note: If you do not have a fork, you can use `updatered` to update to latest stable changes.<br/>

 - Usage: `[p]forkupdate`
 - Restricted to: `BOT_OWNER`
 - Aliases: `updatefork`
