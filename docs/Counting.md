# Counting

Count from 1 to infinity!

## [p]countingset

Configure counting game settings.<br/>

 - Usage: `[p]countingset`
 - Restricted to: `ADMIN`
 - Checks: `guild_only`

### [p]countingset settings

Show current counting settings.<br/>

 - Usage: `[p]countingset settings`

### [p]countingset roles

Manage role-related settings for counting.<br/>

 - Usage: `[p]countingset roles`

#### [p]countingset roles ruin

Set or clear the role assigned for ruining the count, with an optional temporary duration.<br/>

Duration can be specified like '60s', '5m', '1h', '2d' (seconds, minutes, hours, days).<br/>
Valid range: 60 seconds to 30 days. Omit duration for a permanent role.<br/>
Example: `[p]countingset roles ruinrole @Role 5m` to set a role for 5 minutes.<br/>

 - Usage: `[p]countingset roles ruin [role=None] [duration=None]`

Extended Arg Info

> ### role: Optional[discord.role.Role] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
> ### duration: Optional[str] = None
> ```
> You will need a number to set duration for.
> ```

#### [p]countingset roles reset

Set or clear roles allowed to reset the count.<br/>

Only guild owners can set these roles. If no roles are provided, clears the list.<br/>

**Example usage**:<br/>
- `[p]countingset roles reset @Moderator @Admin`<br/>
- `[p]countingset roles reset` (to clear)<br/>

 - Usage: `[p]countingset roles reset <roles>`
 - Restricted to: `GUILD_OWNER`

Extended Arg Info

> ### *roles: discord.role.Role
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     

#### [p]countingset roles exclude

Set roles to exclude from receiving the ruin role.<br/>

 - Usage: `[p]countingset roles exclude <roles>`

Extended Arg Info

> ### *roles: discord.role.Role
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     

### [p]countingset misc

Manage miscellaneous counting settings.<br/>

 - Usage: `[p]countingset misc`

#### [p]countingset misc emoji

Set the reaction emoji for correct counts.<br/>

Emoji can be a Unicode emoji, a custom emoji, or an emoji shortcode.<br/>

**Example usage**:<br/>
- `[p]countingset misc emoji :thumbsup:`<br/>
- `[p]countingset misc emoji 👍`<br/>
- `[p]countingset misc emoji <a:custom_emoji_name:123456789012345678>`<br/>

**Arguments**:<br/>
- `<emoji_input>`: The emoji to set as the reaction. This can be a Unicode emoji, a custom emoji, or an emoji shortcode (e.g., `:thumbsup:`).<br/>

 - Usage: `[p]countingset misc emoji <emoji_input>`
 - Aliases: `setemoji`

### [p]countingset goalsettings

See current counting goals.<br/>

This will show all counting goals set for the server.<br/>

 - Usage: `[p]countingset goalsettings`

### [p]countingset toggle

Interactive toggle setup panel.<br/>

Shows all counting toggles with their current state.<br/>
Click any button to enable or disable that feature instantly.<br/>

 - Usage: `[p]countingset toggle`

### [p]countingset reset

Manage reset actions for counting.<br/>

 - Usage: `[p]countingset reset`

#### [p]countingset reset count

Reset the count back to 0.<br/>

Only guild owners or users with specified reset roles can use this.<br/>

 - Usage: `[p]countingset reset count`

#### [p]countingset reset all

Reset all counting settings back to default.<br/>

 - Usage: `[p]countingset reset all`

### [p]countingset channel

Set or clear the counting channel.<br/>

 - Usage: `[p]countingset channel [channel=None]`

Extended Arg Info

> ### channel: Optional[discord.channel.TextChannel] = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by channel URL.
>     4. Lookup by name
> 
>     

### [p]countingset messages

Manage custom messages for counting events.<br/>

 - Usage: `[p]countingset messages`

#### [p]countingset messages progress

Set the message sent for progress updates.<br/>

Use `{remaining}` for counts left and `{goal}` for the goal.<br/>

**Example usage**:<br/>
- `[p]countingset messages progress {remaining} to go until {goal}! Keep counting!`<br/>

**Arguments**:<br/>
- `<message>`: The custom message for progress updates.<br/>

 - Usage: `[p]countingset messages progress <message>`

#### [p]countingset messages message

Set custom messages for specific events.<br/>

Available types: edit, count, sameuser, ruincount.<br/>
The message must not exceed 2000 characters.<br/>

**Example usage**:<br/>
- `[p]countingset messages message count Next number is {next_count}.`<br/>
- `[p]countingset messages message edit You can't edit your messages here. Next number: {next_count}`<br/>
- `[p]countingset messages message sameuser You cannot count consecutively. Wait for someone else.`<br/>
- `[p]countingset messages message ruincount {user} ruined the count at {count}! Starting back at 1.`<br/>

- The placeholders `{next_count}` and `{user}` will be replaced with the appropriate values.<br/>
    - `{next_count}`: The next expected count number and only works for `count` and `edit`.<br/>
   - `{user}`: The user who ruined the count, only works for `ruincount`.<br/>

**Arguments**:<br/>
- `<msg_type>`: The type of message to set (edit, count, sameuser, ruincount).<br/>
- `<message>`: The custom message to set for the specified type.<br/>

 - Usage: `[p]countingset messages message <msg_type> <message>`

#### [p]countingset messages goalmessage

Set the message sent when the goal is reached.<br/>

Use `{user}` for the user and `{goal}` for the goal.<br/>

**Example usage**:<br/>
- `[p]countingset messages goal {user} reached the goal of {goal}! Congratulations!`<br/>
    - This will send a message like "User reached the goal of 100! Congratulations!" when the goal is reached.<br/>

**Arguments**:<br/>
- `<message>`: The custom message to set for the goal. This can include placeholders `{user}` and `{goal}`.<br/>

 - Usage: `[p]countingset messages goalmessage <message>`

### [p]countingset limits

Manage restrictions and goals for counting.<br/>

 - Usage: `[p]countingset limits`

#### [p]countingset limits goal

Manage counting goals.<br/>

**Note**: Goals must be unique and sorted in ascending order. If a goal already exists, it will not be added again.<br/>

**Example usage**:<br/>
- `[p]countingset limits goal 100 add`<br/>
- `[p]countingset limits goal 200 remove`<br/>
- `[p]countingset limits goal clear`<br/>

**Arguments**:<br/>
- `<goal>`: The goal value to add or remove (must be between 1 and 1 quadrillion).<br/>
- `<action>`: The action to perform (add, remove, or clear). Default is 'add'.<br/>
- If `clear` is used, all goals will be removed.<br/>

 - Usage: `[p]countingset limits goal [goal=None] [action=add]`

#### [p]countingset limits progressinterval

Set the interval for progress messages<br/>

Must be between 1 and 100 counts.<br/>

**Example usage**:<br/>
- `[p]countingset limits progressinterval 10`<br/>
    - This will send a progress message every 10 counts.<br/>

**Arguments**:<br/>
- `<interval>`: The number of counts after which a progress message will be sent.<br/>

 - Usage: `[p]countingset limits progressinterval <interval>`

#### [p]countingset limits minage

Set minimum account age to count (0-365 days).<br/>

 - Usage: `[p]countingset limits minage [days=0]`

## [p]counting (Hybrid Command)

Commands for the counting game.<br/>

 - Usage: `[p]counting`
 - Slash Usage: `/counting`
 - Checks: `guild_only`

### [p]counting resetme (Hybrid Command)

Reset your own counting stats.<br/>

This will clear your count and last counted timestamp.<br/>
This action cannot be undone, so use it carefully with the confirmation prompt.<br/>

 - Usage: `[p]counting resetme`
 - Slash Usage: `/counting resetme`
 - Cooldown: `1 per 460.0 seconds`

### [p]counting stats (Hybrid Command)

Show counting stats for a user.<br/>

 - Usage: `[p]counting stats [user=None]`
 - Slash Usage: `/counting stats [user=None]`
 - Cooldown: `1 per 10.0 seconds`

Extended Arg Info

> ### user: Optional[discord.member.Member] = None
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

### [p]counting leaderboard (Hybrid Command)

Show the counting leaderboard for the server.<br/>

Displays the top 15 users with the highest counts.<br/>
Please note that the leaderboard only includes users who have counted at least once.<br/>

 - Usage: `[p]counting leaderboard`
 - Slash Usage: `/counting leaderboard`
 - Aliases: `lb`
 - Cooldown: `1 per 10.0 seconds`

