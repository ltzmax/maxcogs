This will allow you to self-timeout yourself, similar to Twitch's timeout command from streamelemets and fossabot and probably hundered of other twitch bots.

Note to admins: It is not recommended to set the timeout duration to very high values as users will not be able to interact in any way in the server during the timeout period.

# [p]vanish
Timeout yourself, just like you do on twitch.<br/>

It won't delete your messages like it does on twitch but you will be unable to send messages or react to messages for the configured duration.<br/>
 - Usage: `[p]vanish`
 - Checks: `server_only`
# [p]vanishconfig
Configuration commands for the Vanish cog.<br/>
 - Usage: `[p]vanishconfig`
 - Restricted to: `ADMIN`
 - Checks: `server_only`
## [p]vanishconfig toggle
Enable or disable the vanish command in the server.<br/>

Disabled by default.<br/>

**Arguments:**<br/>
- `<on_off>`: `True` to enable, `False` to disable.<br/>
 - Usage: `[p]vanishconfig toggle <on_off>`
## [p]vanishconfig timeout
Set the default vanish timeout duration for the server.<br/>

default is 1 minute.<br/>
Duration must be between 60 seconds and 28 days.<br/>
Moderators, administrators and the server owner cannot timeout themselves using the vanish command.<br/>

NOTE: It is not recommended to set this value to very high values as users will not be able to interact in any way in the server during the timeout period.<br/>

**Examples:**<br/>
- `[p]vanishconfig timeout 10m` (10 minutes)<br/>
- `[p]vanishconfig timeout 1h` (1 hour)<br/>

**Arguments:**<br/>
- `<duration>`: The duration for the timeout (e.g., 10m, 1h, 2d).<br/>
 - Usage: `[p]vanishconfig timeout <duration>`
