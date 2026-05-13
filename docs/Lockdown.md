# Lockdown

Let moderators lockdown a channel to prevent messages from being sent.

## [p]lock (Hybrid Command)

Lock a channel or thread for a specific role or everyone.<br/>

If no role is specified, it locks for @everyone.<br/>
For threads, roles are ignored and it locks for everyone.<br/>
Please note the button will only work for @everyone and not for any other role you specify to lock the channel.<br/>
If you want to unlock a channel with the role you locked it for, you have to use the `[p]unlock` command.<br/>

**Examples**:<br/>
- `[p]lock` - Locks for @everyone with no reason.<br/>
- `[p]lock @Member` - Locks for @Member with no reason (channels only).<br/>
- `[p]lock Reason: spam in this channel` - Locks for @everyone with reason.<br/>
- `[p]lock Reason: spam in this channel @Member` - Locks for @Member with reason (channels only).<br/>

 - Usage: `[p]lock [reason] [role]`
 - Slash Usage: `/lock [reason] [role]`
 - Checks: `guild_only`

## [p]unlock (Hybrid Command)

Unlock a channel or thread for a specific role or everyone.<br/>

If no role is specified, it unlocks for @everyone.<br/>
For threads, roles are ignored and it unlocks for everyone.<br/>

**Examples**:<br/>
- `[p]unlock` - Unlocks for @everyone with no reason.<br/>
- `[p]unlock @Member` - Unlocks for @Member with no reason (channels only).<br/>
- `[p]unlock Reason: spam in this channel` - Unlocks for @everyone with reason.<br/>
- `[p]unlock Reason: spam in this channel @Member` - Unlocks for @Member with reason (channels only).<br/>

 - Usage: `[p]unlock [reason] [role]`
 - Slash Usage: `/unlock [reason] [role]`
 - Checks: `guild_only`

## [p]thread

Manage thread(s) with Kofu.<br/>

 - Usage: `[p]thread`
 - Checks: `guild_only`

### [p]thread close

Close and archive a thread post.<br/>

 - Usage: `[p]thread close [reason]`

