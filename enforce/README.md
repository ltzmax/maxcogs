# Enforce

Requires users to accept ToS and privacy policy before using any bot commands.

## [p]tosconfig

Manage ToS enforcement settings.<br/>

 - Usage: `[p]tosconfig`
 - Restricted to: `BOT_OWNER`

### [p]tosconfig resetuser

Reset ToS acceptance for a user.<br/>

If no user is specified, resets for the command invoker.<br/>

 - Usage: `[p]tosconfig resetuser [user=None]`

### [p]tosconfig resetsettings

Reset all ToS settings to default.<br/>

 - Usage: `[p]tosconfig resetsettings`

### [p]tosconfig settitle

Set custom prompt title.<br/>

 - Usage: `[p]tosconfig settitle <title>`

### [p]tosconfig setfooter

Set custom prompt footer.<br/>

 - Usage: `[p]tosconfig setfooter <footer>`

### [p]tosconfig setdesc

Set custom prompt description.<br/>

Use `{tos_url}` and `{privacy_url}` as placeholders for the privacy policy and terms of service url.<br/>

 - Usage: `[p]tosconfig setdesc <desc>`
 - Aliases: `setdescription and setprompt`

### [p]tosconfig toggle

Toggle ToS enforcement on or off.<br/>

 - Usage: `[p]tosconfig toggle`

### [p]tosconfig showsettings

Show current ToS enforcement settings.<br/>

 - Usage: `[p]tosconfig showsettings`

### [p]tosconfig set

Set ToS or Privacy Policy link.<br/>

**Example**:<br/>
- `[p]tosconfig set tos <url>`<br/>
- `[p]tosconfig set privacy <url>`<br/>

 - Usage: `[p]tosconfig set <tos_or_privacy> <url>`
 - Restricted to: `BOT_OWNER`
