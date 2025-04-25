Let moderators lockdown a channel to prevent messages from being sent.

# [p]lockdownset
Lockdown settings commands.<br/>
 - Usage: `[p]lockdownset`
 - Checks: `server_only`
## [p]lockdownset logchannel
Set the channel for logging lockdowns.<br/>
 - Usage: `[p]lockdownset logchannel <channel>`
## [p]lockdownset useembed
Set whether to use embeds or not.<br/>
 - Usage: `[p]lockdownset useembed <value>`
## [p]lockdownset settings
Get the current log channel.<br/>
 - Usage: `[p]lockdownset settings`
# [p]lock (Hybrid Command)
Lock a channel for a specific role or everyone.<br/>

If no role is specified, the channel is locked for @everyone.<br/>
Please note the button will only work for the @everyone role and not for any other role you specify to lock the channel.<br/>
If you want to unlock a channel with the role you locked it for, you have to use the `[p]unlock` command.<br/>

**Examples**:<br/>
- `[p]lock` - Locks for @everyone with no reason.<br/>
- `[p]lock @Member` - Locks for @Member with no reason.<br/>
- `[p]lock Reason: spam in this channel` - Locks for @everyone with reason.<br/>
- `[p]lock Reason: spam in this channel @Member` - Locks for @Member with reason.<br/>
 - Usage: `[p]lock [reason] [role]`
 - Slash Usage: `/lock [reason] [role]`
 - Checks: `server_only`
# [p]unlock (Hybrid Command)
Unlock a channel for a specific role or everyone.<br/>

If no role is specified, the channel is unlocked for @everyone.<br/>

**Examples**:<br/>
- `[p]unlock` - Unlocks for @everyone with no reason.<br/>
- `[p]unlock @Member` - Unlocks for @Member with no reason.<br/>
- `[p]unlock Reason: spam in this channel` - Unlocks for @everyone with reason.<br/>
- `[p]unlock Reason: spam in this channel @Member` - Unlocks for @Member with reason.<br/>
 - Usage: `[p]unlock [reason] [role]`
 - Slash Usage: `/unlock [reason] [role]`
 - Checks: `server_only`
# [p]thread
Manage thread(s) with MAX.<br/>
 - Usage: `[p]thread`
 - Checks: `server_only`
## [p]thread lockdown
Lock a thread post.<br/>
 - Usage: `[p]thread lockdown [reason]`
## [p]thread close
Close and archive a thread post.<br/>

If you want to only lock a thread post, you'll have to use `[p]lock` command.<br/>
 - Usage: `[p]thread close [reason]`
## [p]thread open
Open a thread post.<br/>
 - Usage: `[p]thread open [reason]`
