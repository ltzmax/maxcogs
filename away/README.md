# Away Help

An away thingy to set away and be not away.

# away (Hybrid Command)
 - Usage: `[p]away <message> `
 - Slash Usage: `/away <message> `
 - Aliases: `afk`
 - Cooldown: `1 per 3.0 seconds`

Set your away status.<br/><br/>Use `[p]back` to remove your afk status.

Extended Arg Info
> ### message: str
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```
# back (Hybrid Command)
 - Usage: `[p]back `
 - Slash Usage: `/back `
 - Cooldown: `1 per 3.0 seconds`

Remove your away status / get back from away.<br/><br/>Use `[p]away <message>` to set your afk status.

# awayset (Hybrid Command)
 - Usage: `[p]awayset `
 - Slash Usage: `/awayset `
 - Aliases: `afkset`

Manage away settings.

## awayset nickname
 - Usage: `[p]awayset nickname <toggle> `
 - Aliases: `nick`
 - Cooldown: `1 per 3.0 seconds`

Toggle whether to change the nickname to name + [away]<br/><br/>Pass `True` to enable, `False` to disable.

Extended Arg Info
> ### toggle: bool
> ```
> Can be 1, 0, true, false, t, f
> ```
## awayset role
 - Usage: `[p]awayset role <role> `

Set the role to be used for away status.

Extended Arg Info
> ### role: discord.role.Role
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
## awayset autoback (Hybrid Command)
 - Usage: `[p]awayset autoback <toggle> `
 - Slash Usage: `/awayset autoback <toggle> `
 - Cooldown: `1 per 3.0 seconds`

Toggle whether to automatically stop autoback or enabled them.<br/><br/>Autoback is default enabled.<br/><br/>Pass `True` to enable, `False` to disable.

Extended Arg Info
> ### toggle: bool
> ```
> Can be 1, 0, true, false, t, f
> ```
## awayset showsettings
 - Usage: `[p]awayset showsettings `
 - Aliases: `settings and showsetting`
 - Cooldown: `1 per 5.0 seconds`

Show the current away settings.

## awayset toggle
 - Usage: `[p]awayset toggle <delete> `

Toggle whether to delete away messages or not.<br/><br/>Arguments:<br/>- `<delete>` - set to true or false.<br/>True to enable, false to disable.

Extended Arg Info
> ### delete: bool
> ```
> Can be 1, 0, true, false, t, f
> ```
## awayset version
 - Usage: `[p]awayset version `

Shows the version of the cog

## awayset timeout
 - Usage: `[p]awayset timeout <delete_after> `

Set the amount of time in seconds to delete the message after [p]away.

Extended Arg Info
> ### delete_after: int
> ```
> A number without decimal places.
> ```
## awayset deleterole
 - Usage: `[p]awayset deleterole `

Remove the away role set from `awayset role`.
