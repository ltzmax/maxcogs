# AFK

AFK status cog.

## [p]afk

Set your AFK status with an optional message.<br/>

When someone pings you, they'll see your AFK message and<br/>
your pings will be logged for when you return.<br/>

**Examples:**<br/>
- `[p]afk` - sets AFK with default message<br/>
- `[p]afk Out for lunch, back soon!` - sets AFK with a custom message<br/>

 - Usage: `[p]afk [message]`
 - Checks: `guild_only`

Extended Arg Info

> ### message: str = "I'm away from my keyboard."
> ```
> Just write something you feel like?
> ```

## [p]afkset

AFK settings.<br/>

 - Usage: `[p]afkset`
 - Checks: `guild_only`

### [p]afkset list

View pings you received while AFK.<br/>

The list is cleared after viewing it.<br/>

 - Usage: `[p]afkset list`

### [p]afkset settings

View current AFK settings.<br/>

 - Usage: `[p]afkset settings`
 - Restricted to: `ADMIN`

### [p]afkset role

Set (or clear) the role assigned to AFK members.<br/>

Pass a role name/mention to set it, or nothing to clear it.<br/>

**Examples:**<br/>
- `[p]afkset role AFK` - assign the AFK role<br/>
- `[p]afkset role` - remove the configured AFK role<br/>

 - Usage: `[p]afkset role [role]`
 - Restricted to: `ADMIN`

Extended Arg Info

> ### role: Optional[discord.role.Role] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     

### [p]afkset nickname

Toggle appending `[AFK]` to members' nicknames when they go AFK.<br/>

Requires the bot to have **Manage Nicknames** permission and be<br/>
above the target member in the role hierarchy.<br/>

 - Usage: `[p]afkset nickname`
 - Restricted to: `ADMIN`

### [p]afkset autoremove

Toggle auto-removing your AFK status when you send a message.<br/>

When enabled (default), your AFK is cleared the next time you chat.<br/>
When disabled, you must set a new AFK or it stays indefinitely.<br/>

 - Usage: `[p]afkset autoremove`

### [p]afkset deleteafter

Set how long AFK notifications should last before being deleted.<br/>

 - Usage: `[p]afkset deleteafter <seconds>`

Extended Arg Info

> ### seconds: Optional[int]
> ```
> A number without decimal places.
> ```

