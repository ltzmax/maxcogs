# Enforce

Requires users to accept ToS and privacy policy before using any bot commands.

## [p]tosconfig

Manage ToS enforcement settings.<br/>

 - Usage: `[p]tosconfig`
 - Restricted to: `BOT_OWNER`
 - Aliases: `enforceset and enforce`

### [p]tosconfig set

Set ToS or Privacy Policy link.<br/>

**Example**:<br/>
- `[p]tosconfig set tos <url>`<br/>
- `[p]tosconfig set privacy <url>`<br/>

 - Usage: `[p]tosconfig set <tos_or_privacy> <url>`

Extended Arg Info

> ### tos_or_privacy: str
> ```
> you choose between tos or privacy to set your valid url.
> ```
> ### url: str
> ```
> A single valid url is needed otherwise it will fail.
> ```

### [p]tosconfig resetall

Reset ToS acceptance for all users.<br/>

 - Usage: `[p]tosconfig resetall`

### [p]tosconfig checkuser

Check when a user accepted the ToS, or whether they have at all.<br/>

 - Usage: `[p]tosconfig checkuser [user=None]`

Extended Arg Info

> ### user: Optional[discord.user.User] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by username#discriminator (deprecated).
>     4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
>     5. Lookup by user name.
>     6. Lookup by global name.
> 
>     

### [p]tosconfig toggle

Toggle ToS enforcement on or off.<br/>

 - Usage: `[p]tosconfig toggle`

### [p]tosconfig acceptedcount

Show how many users have accepted the ToS.<br/>

 - Usage: `[p]tosconfig acceptedcount`

### [p]tosconfig setdesc

Set custom prompt description.<br/>

Use `{tos_url}` and `{privacy_url}` as placeholders for the privacy policy and terms of service url.<br/>

 - Usage: `[p]tosconfig setdesc <desc>`
 - Aliases: `setdescription and setprompt`

Extended Arg Info

> ### desc: str
> ```
> A description of your choose.
> ```

### [p]tosconfig resetsettings

Reset all ToS settings to default.<br/>

 - Usage: `[p]tosconfig resetsettings`

### [p]tosconfig showsettings

Show current ToS enforcement settings.<br/>

 - Usage: `[p]tosconfig showsettings`

### [p]tosconfig setfooter

Set custom prompt footer.<br/>

 - Usage: `[p]tosconfig setfooter <footer>`

Extended Arg Info

> ### footer: str
> ```
> A footer text of your choose.
> ```

### [p]tosconfig settitle

Set custom prompt title.<br/>

 - Usage: `[p]tosconfig settitle <title>`

Extended Arg Info

> ### title: str
> ```
> A title of your choose.
> ```

### [p]tosconfig resetuser

Reset ToS acceptance for a user.<br/>

If no user is specified, resets for the command invoker.<br/>

 - Usage: `[p]tosconfig resetuser [user=None]`

Extended Arg Info

> ### user: Optional[discord.user.User] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by username#discriminator (deprecated).
>     4. Lookup by username#0 (deprecated, only gets users that migrated from their discriminator).
>     5. Lookup by user name.
>     6. Lookup by global name.
> 
>     

